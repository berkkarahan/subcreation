import webapp2
import logging
import os
import json
import pdb
import copy

from google.appengine.api import urlfetch
from google.appengine.api import app_identity
from google.appengine.ext import ndb
from google.appengine.ext import deferred
from google.appengine.api.taskqueue import TaskRetryOptions
from google.appengine.runtime import DeadlineExceededError

from google.appengine.ext import vendor
# add libraries in lib
vendor.add('lib')

import slugify
import cloudstorage as gcs

from warcraft import dungeons, dungeon_slugs, regions
from warcraft import specs, tanks, healers, melee, ranged, role_titles
from t_interval import t_interval

from models import Run, DungeonAffixRegion, KnownAffixes
from old_models import Pull, AffixSet, Run as OldRun

## raider.io handling

def update_known_affixes(affixes, affixes_slug):
    key = ndb.Key('KnownAffixes', affixes_slug)
    ka = key.get()
#    logging.info("update_known_affixes %s %s %s" % (affixes,
#                                                    affixes_slug,
#                                                    str(ka)))
    if ka is None: # only add it if we haven't seen it before
        ka = KnownAffixes(id=affixes_slug, affixes=affixes)
        ka.put()

def parse_response(data, dungeon, affixes, region, page):
    dungeon_slug = slugify.slugify(unicode(dungeon))

    if affixes == "current":
#        logging.info(" Detected 'current' affixes... evaluating actual...")
        affixes = ""
        affixes += data[0]["run"]["weekly_modifiers"][0]["name"] + ", "
        affixes += data[0]["run"]["weekly_modifiers"][1]["name"] + ", "
        affixes += data[0]["run"]["weekly_modifiers"][2]["name"] + ", "
        affixes += data[0]["run"]["weekly_modifiers"][3]["name"]
#        logging.info("  %s " % (affixes))

    affixes_slug = slugify.slugify(unicode(affixes))
    update_known_affixes(affixes, affixes_slug)
        
    
    key_string = dungeon_slug + "-" + affixes_slug + "-" + region + "-" + str(page)
    key = ndb.Key('DungeonAffixRegion',
                  key_string)
    dar = DungeonAffixRegion(key=key)

    dar.dungeon = dungeon
    dar.affixes = affixes
    dar.region = region
    dar.page = page

    for d in data:
        r = d["run"]
        
        score = d["score"]
        roster = []
        ksrid = ""
        completed_at = ""
        completed_at = datetime.datetime.strptime(r["completed_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        
        clear_time_ms = r["clear_time_ms"]
        mythic_level = r["mythic_level"]
        num_chests = r["num_chests"]
        keystone_time_ms = r["keystone_time_ms"]
        faction = r["faction"]
        
        ksrid = str(r["keystone_run_id"])

        for c in r["roster"]:
            ch = c["character"]
            spec_class = ch["spec"]["name"] + " " + ch["class"]["name"]
            roster += [spec_class]
           
            
        dar.runs += [Run(score=score, roster=roster, keystone_run_id=ksrid,
                         completed_at=completed_at, clear_time_ms=clear_time_ms,
                         mythic_level=mythic_level, num_chests=num_chests,
                         keystone_time_ms=keystone_time_ms, faction=faction)]

    return dar


# update
def update_dungeon_affix_region(dungeon, affixes, region, season="season-bfa-2", page=0):
    dungeon_slug = slugify.slugify(unicode(dungeon))
    affixes_slug = slugify.slugify(unicode(affixes))

#    logging.info("Getting data for %s/%s/%s..." % (dungeon_slug,
#                                                   affixes_slug,
#                                                   region))

    req_url = "https://raider.io/api/v1/mythic-plus/runs?season=%s&region=%s&affixes=%s&dungeon=%s&page=%d" % (season, region, affixes_slug, dungeon_slug, page)

#    logging.info(" %s" % req_url)

    response = {}
    try:
        result = urlfetch.fetch(req_url)
        if result.status_code == 200:
            response = json.loads(result.content)["rankings"]
            if response == []: # empty rankings, as sometimes happens at week start
                logging.info("no rankings found for %s / %s / %s / %s" % (dungeon, affixes, region, page))
                return
            dar = parse_response(response,
                                 dungeon, affixes, region, page)
            dar.put()
    except DeadlineExceededError:
        logging.exception('deadline exception fetching url: ' + req_url)        
        options = TaskRetryOptions(task_retry_limit = 3)
        deferred.defer(update_dungeon_affix_region, dungeon, affixes, region, season, page, _retry_options=options)

    except urlfetch.Error:
        logging.exception('caught exception fetching url: ' + req_url)

def update_current():
    global dungeons, regions
    for region in regions:
        for dungeon in dungeons:
            for page in range(0, MAX_PAGE):
                deferred.defer(update_dungeon_affix_region,
                               dungeon,
                               "current",
                               region,
                               page=page)

## end raider.io processing


## data analysis start

from numpy import average, std
from math import sqrt


def construct_analysis(counts):
    overall = []
    all_data = []
    for name, runs in counts.iteritems():
        for r in runs:
            all_data += [r.score]
    master_stddev = std(all_data, ddof=1)
       
    for name, runs in counts.iteritems():
        data = []
        max_found = 0
        max_id = ""
        for r in runs:
            data += [r.score]
            if r.score >= max_found:
                max_found = r.score
                max_id = r.keystone_run_id
        n = len(data)
        if n == 0:
            overall += [[name, 0, 0, n, [0, 0], [0, ""]]]
            continue
        mean = average(data)
        if n <= 1:
            overall += [[name, mean, 0, n, [0, 0], [max_found, max_id]]]
            continue
        stddev = std(data, ddof=1)
        t_bounds = t_interval(n)
        ci = [mean + critval * master_stddev / sqrt(n) for critval in t_bounds]
        maxi = [max_found, max_id]
        overall += [[name, mean, stddev, n, ci, maxi]]


    overall = sorted(overall, key=lambda x: x[4][0], reverse=True)
    return overall

## end data analysis

## getting data out and into counts

# generate counts
def generate_counts(affixes="All Affixes", dungeon="all", spec="all"):
    global dungeons, regions, specs, last_updated, MAX_PAGE

    affixes_to_get = [affixes]
    if affixes == "All Affixes":
        affixes_to_get = known_affixes()

    dungeon_counts = {}
    spec_counts = {}
    set_counts = {}
    th_counts = {} # tank healer
    dps_counts = {} # just dps

    for s in specs:
        spec_counts[s] = []

    for affix in affixes_to_get:
        affixes_slug = slugify.slugify(unicode(affix))
        for region in regions:
            for dung in dungeons:
                for page in range(0, MAX_PAGE):
                    dungeon_slug = slugify.slugify(unicode(dung))
                    key_string = dungeon_slug + "-" + affixes_slug + "-" + region + "-" + str(page)
                    key = ndb.Key('DungeonAffixRegion',
                                  key_string)

                    dar = key.get()

                    if dar == None:
                        continue

                    if last_updated == None:
                        last_updated = dar.last_updated
                    if dar.last_updated > last_updated:
                        last_updated = dar.last_updated

                    for run in dar.runs:
                        if dung not in dungeon_counts:
                            dungeon_counts[dung] = []
                        dungeon_counts[dung] += [run]

                        if dungeon == "all" or dung == dungeon:
                                if spec == "all":
                                    if canonical_order(run.roster) not in set_counts:
                                        set_counts[canonical_order(run.roster)] = []
                                    set_counts[canonical_order(run.roster)] += [run]

                                    if canonical_order(run.roster)[:2] not in th_counts:
                                        th_counts[canonical_order(run.roster)[:2]] = []
                                    th_counts[canonical_order(run.roster)[:2]] += [run]

                                    if canonical_order(run.roster)[-3:] not in dps_counts:
                                        dps_counts[canonical_order(run.roster)[-3:]] = []
                                    dps_counts[canonical_order(run.roster)[-3:]] += [run]

                                    for ch in run.roster:
                                        if ch not in spec_counts:
                                            spec_counts[ch] = []
                                        spec_counts[ch] += [run]
                                else:
                                    if spec not in run.roster:
                                        continue

                                    if canonical_order(run.roster) not in set_counts:
                                        set_counts[canonical_order(run.roster)] = []
                                    set_counts[canonical_order(run.roster)] += [run]

                                    if canonical_order(run.roster)[:2] not in th_counts:
                                        th_counts[canonical_order(run.roster)[:2]] = []
                                    th_counts[canonical_order(run.roster)[:2]] += [run]

                                    if canonical_order(run.roster)[-3:] not in dps_counts:
                                        dps_counts[canonical_order(run.roster)[-3:]] = []
                                    dps_counts[canonical_order(run.roster)[-3:]] += [run]

                                    rc = copy.copy(run.roster)
                                    rc.remove(spec)
                                    for ch in rc:
                                        if ch not in spec_counts:
                                            spec_counts[ch] = []
                                        spec_counts[ch] += [run]
                            
    return dungeon_counts, spec_counts, set_counts, th_counts, dps_counts


# known affixes
known_affixes_save = []

def known_affixes():
#    global known_affixes_save
#    if known_affixes_save != []:
#        return known_affixes_save # poor man's caching

    known_affixes_save = []
    affix_query = KnownAffixes.query().order(KnownAffixes.first_seen)
    results = affix_query.fetch()
    for k in results:
        if k.affixes not in known_affixes_save:
            if k.affixes != None:
                known_affixes_save += [k.affixes]

    return known_affixes_save

def known_affixes_links(prefix="", use_index=True):
    known_affixes_list = known_affixes()
    known_affixes_report = []
    known_affixes_report += [["All Affixes", prefix+"all-affixes"]]
    for k in known_affixes_list:
        if use_index:
            if k == current_affixes():
                known_affixes_report += [[k, prefix+"index"]]
            else:
                known_affixes_report += [[k, prefix+slugify.slugify(unicode(k))]]
        else:
            known_affixes_report += [[k, prefix+slugify.slugify(unicode(k))]]
            
    known_affixes_report.reverse()
    return known_affixes_report

def known_dungeon_links(affixes_slug, prefix=""):
    known_dungeon_list = dungeons

    known_dungeon_report = []

    for k in known_dungeon_list:
        known_dungeon_report += [[k, prefix+slugify.slugify(unicode(k))+"-" + affixes_slug]]
            
    return known_dungeon_report


def current_affixes():
    pull_query = KnownAffixes.query().order(-KnownAffixes.first_seen)
#    logging.info(pull_query)
#    logging.info(pull_query.fetch(1))
    current_affixes_save = pull_query.fetch(1)[0].affixes
    
    return current_affixes_save

## end getting data out into counts



## html generation start

##   generating common reports

def canonical_order(s):
    # given a list, return a tuple in canonical order
    output = []
    ta = []
    he = []
    me = []
    ra = []

    for c in s:
        if c in tanks:
            ta += [c]
        if c in healers:
            he += [c]
        if c in melee:
            me += [c]
        if c in ranged:
            ra += [c]

    output += sorted(ta) + sorted(he) + sorted(me) + sorted(ra)
    return tuple(output)

def pretty_set(s):
    output_string = ""
    for k in s:
        output_string += "<td>%s</td>" % k
    return output_string

def gen_set_report(set_counts):
    set_overall = construct_analysis(set_counts)

    set_output = []
    for x in set_overall:
        if x[3] <= 1:
            continue
        set_output += [[str("%.2f" % x[4][0]),
                            pretty_set(x[0]),
                            str("%.2f" % x[1]),
                            str(x[3]),
                            str("%.2f" % x[5][0]), # maximum run
                            x[5][1],
                        ]]

    return set_output[:50]

def gen_dungeon_report(dungeon_counts):
    dungeons_overall = construct_analysis(dungeon_counts)

    dungeon_output = []
    for x in dungeons_overall:

        dungeon_output += [[str("%.2f" % x[4][0]),
                            x[0],
                            str("%.2f" % x[1]),
                            str(x[3]),
                            slugify.slugify(unicode(x[0])),
                            str("%.2f" % x[5][0]), # maximum run
                            x[5][1],
                            ]] # id of the maximum run

    return dungeon_output

def gen_spec_report(spec_counts):
    global role_titles, specs

    role_package = {}

    spec_overall = construct_analysis(spec_counts)

    for i, display in enumerate([tanks, healers, melee, ranged]):
        role_score = []
        for k in sorted(spec_overall, key=lambda x: x[4][0], reverse=True):
            if k[0] in display:
                role_score += [[str("%.2f" % k[4][0]),
                                str(k[0]),
                                str("%.2f" % k[1]),
                                str("%d" % k[3]).rjust(4),
                                slugify.slugify(unicode(str(k[0]))),
                                str("%.2f" % k[5][0]), # maximum run
                                k[5][1], # id of the maximum run
                                ]]
        role_package[role_titles[i]] = role_score
    return role_package

def localized_time(last_updated):
    if last_updated == None:
        return "N/A"
    return pytz.utc.localize(last_updated).astimezone(pytz.timezone("America/New_York"))


def render_affixes(affixes, prefix=""):
    dungeon_counts, spec_counts, set_counts, th_counts, dps_counts = generate_counts(affixes)
    affixes_slug = slugify.slugify(unicode(affixes))
    
    dungeons_report = gen_dungeon_report(dungeon_counts)
    specs_report = gen_spec_report(spec_counts)
    set_report = gen_set_report(set_counts)
    th_report = gen_set_report(th_counts)
    dps_report = gen_set_report(dps_counts)


    
    template = env.get_template('by-affix.html')
    rendered = template.render(title=affixes,
                               prefix=prefix,
                               affixes=affixes,
                               affixes_slug=affixes_slug,
                               dungeons=dungeons_report,
                               role_package=specs_report,
                               sets=set_report,
                               sets_th=th_report,
                               sets_dps=dps_report,
                               known_affixes = known_affixes_links(prefix=prefix),
                               last_updated = localized_time(last_updated))
    return rendered

def render_dungeon(affixes, dungeon, prefix=""):
    dungeon_counts, spec_counts, set_counts, th_counts, dps_counts  = generate_counts(affixes, dungeon)
    affixes_slug = slugify.slugify(unicode(affixes))
    dungeon_slug = slugify.slugify(unicode(dungeon))

    affixes_slug_special = affixes_slug
    if affixes == current_affixes():
        affixes_slug_special = "index"
    
    dungeons_report = gen_dungeon_report(dungeon_counts)
    specs_report = gen_spec_report(spec_counts)
    set_report = gen_set_report(set_counts)
    th_report = gen_set_report(th_counts)
    dps_report = gen_set_report(dps_counts)


    title = "%s: %s" % (dungeon, affixes)
    
    template = env.get_template('by-dungeon.html')
    rendered = template.render(title=title,
                               prefix=prefix,
                               affixes=affixes,
                               affixes_slug=affixes_slug,
                               affixes_slug_special=affixes_slug_special,
                               dungeon=dungeon,
                               dungeon_slug=dungeon_slug,
                               dungeons=dungeons_report,
                               role_package=specs_report,
                               sets=set_report,
                               sets_th=th_report,
                               sets_dps=dps_report,
                               known_dungeons = known_dungeon_links(prefix=prefix,
                                                                    affixes_slug=affixes_slug),
                               known_affixes = known_affixes_links(prefix=prefix),
                               last_updated = localized_time(last_updated))
    return rendered

def render_spec(affixes, dungeon, spec, prefix=""):
    dungeon_counts, spec_counts, set_counts, th_counts, dps_counts = generate_counts(affixes, dungeon, spec)
    affixes_slug = slugify.slugify(unicode(affixes))
    affixes_slug_index = affixes_slug
    if affixes == current_affixes():
        affixes_slug_index = "index"
    dungeon_slug = slugify.slugify(unicode(dungeon))
    spec_slug = slugify.slugify(unicode(spec))
    
    dungeons_report = gen_dungeon_report(dungeon_counts)
    specs_report = gen_spec_report(spec_counts)
    set_report = gen_set_report(set_counts)
    th_report = gen_set_report(th_counts)
    dps_report = gen_set_report(dps_counts)

    if dungeon == "all":
        title = "%s: %s" % (spec, affixes)
        dungeon = ""
        dungeon_slug = ""
    else:
        title = "%s: %s: %s" % (spec, dungeon, affixes)

    dungeon_blob = sorted(known_dungeon_links(affixes_slug=affixes_slug)) + [["All Dungeons", "all"]] 
    
    template = env.get_template('by-spec.html')
    rendered = template.render(title=title,
                               prefix=prefix,
                               affixes=affixes,
                               affixes_slug=affixes_slug,
                               affixes_slug_index=affixes_slug_index,
                               spec = spec,
                               spec_slug = spec_slug,
                               dungeon=dungeon,
                               dungeon_slug=dungeon_slug,
                               dungeons=dungeons_report,
                               sets = set_report,
                               sets_th=th_report,
                               sets_dps=dps_report,
                               role_package=specs_report,
                               known_dungeons = dungeon_blob,
                               known_affixes = known_affixes_links(use_index=False),
                               last_updated = localized_time(last_updated))

    return rendered

## end html generation
    
## templates

from jinja2 import Environment, FileSystemLoader
env = Environment(
    loader=FileSystemLoader('templates'),
)

## end templates

## cloud storage

def write_to_storage(filename, content):
    bucket_name = 'mplus.subcreation.net'
    
    filename = "/%s/%s" % (bucket_name, filename)
    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    gcs_file = gcs.open(filename,
                        'w', content_type='text/html',
                        retry_params=write_retry_params)
    gcs_file.write(str(content))
    gcs_file.close()

def write_overviews():
    affixes_to_write = []
    affixes_to_write += ["All Affixes"]
    affixes_to_write += known_affixes()

    for af in affixes_to_write:
        rendered = render_affixes(af)

        filename_slug = slugify.slugify(unicode(af))

        if af == current_affixes():
            filename_slug = "index"

        affix_slug = slugify.slugify(unicode(af))

        deferred.defer(write_to_storage, filename_slug + ".html", rendered)

        for dg in dungeons:
            rendered = render_dungeon(af, dg)
            dungeon_slug = slugify.slugify(unicode(dg))
            filename = "%s-%s.html" % (dungeon_slug, affix_slug)
            deferred.defer(write_to_storage, filename, rendered)

    for s in specs:
        for af in affixes_to_write:
            rendered = render_spec(af, "all", s)
            spec_slug = slugify.slugify(unicode(s))
            affix_slug = slugify.slugify(unicode(af))
            filename = "%s-%s.html" % (spec_slug, affix_slug)
            deferred.defer(write_to_storage, filename, rendered)            

            # no longer doing per dungeon spec -- too small granularity
            # for dg in dungeons:
            #     rendered = render_spec(af, dg, s)
            #     dungeon_slug = slugify.slugify(unicode(dg))
            #     spec_slug = slugify.slugify(unicode(s))
            #     filename = "%s-%s-%s.html" % (spec_slug, dungeon_slug, affix_slug)
            #     deferred.defer(write_to_storage, filename, rendered)   



##

def test_view(destination):
    affixes = current_affixes()
    spec = "all"
    dung = "all"
    prefix = "view?goto="

    if destination == "index.html":
        affixes = current_affixes()

    if "all-affixes" in destination:
        affixes = "All Affixes"

    for k in known_affixes():
        if slugify.slugify(unicode(k)) in destination:
            affixes = k
            break

    for s in specs:
        if slugify.slugify(unicode(s)) in destination:
            spec = s

    for i, k in enumerate(dungeon_slugs):
        if k in destination:
            dung = dungeons[i]

    if spec != "all":
        return destination + render_spec(affixes,
                                         dung,
                                         spec,
                                         prefix=prefix)
    if dung != "all":
        return destination + render_dungeon(affixes,
                                            dung,
                                            prefix=prefix)

    return destination + render_affixes(affixes, prefix=prefix)

## handlers

class UpdateCurrentDungeons(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        update_current()
        self.response.write("Updates queued.")

import datetime
import pytz
last_updated = None
MAX_PAGE = 5

class OnlyGenerateHTML(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Writing templates to cloud storage...")
        write_overviews()

class GenerateHTML(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Queueing updates\n")
        update_current()
        self.response.write("Writing templates to cloud storage...\n")
        deferred.defer(write_overviews, _countdown=20)

class TestView(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        destination = self.request.get("goto", "index.html")
        self.response.write(test_view(destination))
        

class KnownAffixesShow(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(str(current_affixes()))
        self.response.write(str(known_affixes()))
        


app = webapp2.WSGIApplication([
        ('/update_current_dungeons', UpdateCurrentDungeons),
        ('/generate_html', GenerateHTML),
        ('/only_generate_html', OnlyGenerateHTML),
        ('/view', TestView),
        ('/known_affixes', KnownAffixesShow),
        ], debug=True)
