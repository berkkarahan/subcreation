import webapp2
import logging
import os
import json
import pdb
import copy
import operator

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

# season 3 only
from warcraft import beguiling_weeks

# wcl handling
from models import SpecRankings
from auth import api_key
from wcl import wcl_specs, dungeon_encounters

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
    else:
        ka.put() # put it back to update last seen

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
def update_dungeon_affix_region(dungeon, affixes, region, season="season-bfa-3", page=0):
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
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(update_dungeon_affix_region, dungeon, affixes, region, season, page, _retry_options=options)

    except urlfetch.Error:
        logging.exception('caught exception fetching url: ' + req_url)

def update_current():
    global dungeons, regions
    for region in regions:
        for dungeon in dungeons:
            for page in range(0, MAX_PAGE):
                options = TaskRetryOptions(task_retry_limit = 1)
                deferred.defer(update_dungeon_affix_region,
                               dungeon,
                               "current",
                               region,
                               page=page,
                               _retry_options=options)

## end raider.io processing


## data analysis start

from numpy import average, std
from math import sqrt


# new: spit out all measurements for boxplot fun
def gen_box_plot(counts):
    buckets = {}
    for name, runs in counts.iteritems():
        if name not in buckets:
            buckets[name] = []
        for r in runs:
            buckets[name] += [r.mythic_level]
    print buckets

# new: generate a dungeon tier list
def gen_dungeon_tier_list(dungeons_report):

    # super simple tier list -- figure out the max and the min, and then bucket tiers
    cimax = -1
    cimin = -1
    for k in dungeons_report:       
        if cimax == -1:
            cimax = float(k[0])
        if cimin == -1:
            cimin = float(k[0])
        if float(k[0]) < cimin:
            cimin = float(k[0])
        if float(k[0]) > cimax:
            cimax = float(k[0])

    cirange = cimax - cimin
    cistep = cirange / 6

    added = []

    tiers = {}
    tm = {}
    tm[0] = "S"
    tm[1] = "A"
    tm[2] = "B"
    tm[3] = "C"
    tm[4] = "D"
    tm[5] = "F"

    for i in range(0, 6):
        tiers[tm[i]] = []
    
    for i in range(0, 6):
        for k in dungeons_report:
            if float(k[0]) >= (cimax-cistep*(i+1)):
                if k not in added:
                    if tm[i] not in tiers:
                        tiers[tm[i]] = []
                    tiers[tm[i]] += [k]
                    added += [k]


    # add stragglers to last tier
    for k in dungeons_report:
        if k not in added:
            if tm[5] not in tiers:
                tiers[tm[5]] = []
            tiers[tm[5]] += [k]
            added += [k]

    def miniicon(dname, dslug):
        return '<div class="innertier"><img src="images/dungeons/%s.jpg" title="%s" alt="%s" /><br/>%s</div>' % (dslug, dname, dname, dname)
     
    dtl = {}
    dtl["S"] = ""
    dtl["A"] = ""
    dtl["B"] = ""
    dtl["C"] = ""
    dtl["D"] = ""
    dtl["F"] = ""

    for i in range(0, 6):
        for k in tiers[tm[i]]:
            dtl[tm[i]] += miniicon(k[1], k[4])        
    
    return dtl


# new: generate a specs tier list
def gen_spec_tier_list(specs_report, role):
    global role_titles

    # take the highest max and the highest min
    cimax = {}
    cimin = {}
    
    # super simple tier list -- figure out the max and the min, and then bucket tiers
    for i in range(0, 4):
        cimax[role_titles[i]] = -1
        cimin[role_titles[i]] = -1
        for k in specs_report[role_titles[i]]:
            if cimax[role_titles[i]] == -1:
                cimax[role_titles[i]] = float(k[0])
            if cimin[role_titles[i]] == -1:
                cimin[role_titles[i]] = float(k[0])
            if float(k[0]) < cimin[role_titles[i]]:
                cimin[role_titles[i]] = float(k[0])
            if float(k[0]) > cimax[role_titles[i]]:
                cimax[role_titles[i]] = float(k[0])
    

    cimax_c = []
    cimin_c = []

    for i in range(0, 4):
        cimax_c += [cimax[role_titles[i]]]
        cimin_c += [cimin[role_titles[i]]]
    
    cimaxx = max(cimax_c)
    ciminn = max(cimin_c) # we want the highest minimum, thus max

    cirange = cimaxx - ciminn
    cistep = cirange / 6

    added = []

    tiers = {}
    tm = {}
    tm[0] = "S"
    tm[1] = "A"
    tm[2] = "B"
    tm[3] = "C"
    tm[4] = "D"
    tm[5] = "F"


    for i in range(0, 6):
        tiers[tm[i]] = []
    
    for i in range(0, 6):
        for k in specs_report[role]:
            if float(k[0]) >= (cimaxx-cistep*(i+1)):
                if k not in added:
                    tiers[tm[i]] += [k]
                    added += [k]

    # add stragglers to last tier
    for k in specs_report[role]:
        if k not in added:
            tiers[tm[5]] += [k]
            added += [k]

    def miniicon(dname, dslug):
        return '<div class="innertier"><a href="%s.html"><img src="images/specs/%s.jpg" title="%s" alt="%s" /><br/>%s</a></div>' % (dslug, dslug, dname, dname, dname)
     
    dtl = {}
    dtl["S"] = ""
    dtl["A"] = ""
    dtl["B"] = ""
    dtl["C"] = ""
    dtl["D"] = ""
    dtl["F"] = ""

    for i in range(0, 6):
        for k in tiers[tm[i]]:
            dtl[tm[i]] += miniicon(k[1], k[4])        
    
    return dtl   


# todo: affix tier list (how do affixes compare with each other)
# have this show on all affixes?
# new: generate a dungeon tier list
def gen_affix_tier_list(affixes_report):

    # super simple tier list -- figure out the max and the min, and then bucket tiers
    cimax = -1
    cimin = -1
    for k in affixes_report:       
        if cimax == -1:
            cimax = float(k[0])
        if cimin == -1:
            cimin = float(k[0])
        if float(k[0]) < cimin:
            cimin = float(k[0])
        if float(k[0]) > cimax:
            cimax = float(k[0])

    cirange = cimax - cimin
    cistep = cirange / 6

    added = []

    tiers = {}
    tm = {}
    tm[0] = "S"
    tm[1] = "A"
    tm[2] = "B"
    tm[3] = "C"
    tm[4] = "D"
    tm[5] = "F"

    for i in range(0, 6):
        tiers[tm[i]] = []
    
    for i in range(0, 6):
        for k in affixes_report:
            if float(k[0]) >= (cimax-cistep*(i+1)):
                if k not in added:
                    if tm[i] not in tiers:
                        tiers[tm[i]] = []
                    tiers[tm[i]] += [k]
                    added += [k]


    # add stragglers to last tier
    for k in affixes_report:
        if k not in added:
            if tm[5] not in tiers:
                tiers[tm[5]] = []
            tiers[tm[5]] += [k]
            added += [k]

    def miniaffix(aname, aslug, size):
        return '<img src="images/affixes/%s.jpg" width="%d" height="%d" title="%s" alt="%s" />' % (aslug, size, size, aname, aname)
            
    def miniicon(dname, dslug):
        affixen = dname.split(", ")
        output = []
    
        for af in affixen:
            afname = af
            afslug = slugify.slugify(af)
            output += [miniaffix(afname, afslug, size=28)]

        output_string = output[0]
        output_string += output[1] #+ "<br/>"
        output_string += output[2]
        output_string += output[3]
        output_string += "<br/>%s" % dname
        return '<div class="innertier">%s</div>' % (output_string)
     
    dtl = {}
    dtl["S"] = ""
    dtl["A"] = ""
    dtl["B"] = ""
    dtl["C"] = ""
    dtl["D"] = ""
    dtl["F"] = ""

    for i in range(0, 6):
        for k in tiers[tm[i]]:
            dtl[tm[i]] += miniicon(k[1], k[4])        
    
    return dtl


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
        max_level = 0
        for r in runs:
            data += [r.score]
            if r.score >= max_found:
                max_found = r.score
                max_id = r.keystone_run_id
                max_level = r.mythic_level
        n = len(data)
        if n == 0:
            overall += [[name, 0, 0, n, [0, 0], [0, "", 0]]]
            continue
        mean = average(data)
        if n <= 1:
            overall += [[name, mean, 0, n, [0, 0], [max_found, max_id, max_level]]]
            continue
        stddev = std(data, ddof=1)
        t_bounds = t_interval(n)
        ci = [mean + critval * master_stddev / sqrt(n) for critval in t_bounds]
        maxi = [max_found, max_id, max_level]
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
    affix_counts = {} # compare affixes to each other (

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

                        if affix not in affix_counts:
                            affix_counts[affix] = []
                        affix_counts[affix] += [run]

                        # all this is spec / dungeon / comp breakdown
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
                            
    return dungeon_counts, spec_counts, set_counts, th_counts, dps_counts, affix_counts


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
                known_affixes_report += [[beguiling_affixes(k), prefix+"index"]]
            else:
                known_affixes_report += [[beguiling_affixes(k), prefix+slugify.slugify(unicode(k))]]
        else:
            known_affixes_report += [[beguiling_affixes(k), prefix+slugify.slugify(unicode(k))]]
            
    known_affixes_report.reverse()
    return known_affixes_report

def known_dungeon_links(affixes_slug, prefix=""):
    known_dungeon_list = dungeons

    known_dungeon_report = []

    for k in known_dungeon_list:
        known_dungeon_report += [[k, prefix+slugify.slugify(unicode(k))+"-" + affixes_slug]]
            
    return known_dungeon_report


def current_affixes():
    pull_query = KnownAffixes.query().order(-KnownAffixes.last_seen, -KnownAffixes.first_seen)
#    logging.info(pull_query)
#    logging.info(pull_query.fetch(1))
    current_affixes_save = pull_query.fetch(1)[0].affixes
    
    return current_affixes_save

## end getting data out into counts



## html generation start

##   generating common reports

# season 3 only
def beguiling_affixes(affixes):
    global beguiling_weeks
    if affixes in beguiling_weeks:
        return affixes + " (%s)" % beguiling_weeks[affixes]
    return affixes

# given a list of affixes, return a pretty affix string
# <img> Affix1, <img> Affix2, <img> Affix3, <img> Affix4
def pretty_affixes(affixes, size=16):
    if affixes=="All Affixes":
        return "All Affixes"

    def miniaffix(aname, aslug):
        return '<img src="images/affixes/%s.jpg" width="%d" height="%d" title="%s" alt="%s" />' % (aslug, size, size, aname, aname)

    # season 3 only
    affixes = beguiling_affixes(affixes)
    
    affixen = affixes.split(", ")
    output = []
    
    for af in affixen:
        afname = af
        afslug = slugify.slugify(af)
        output += [miniaffix(afname, afslug) + " %s" % afname]

    output_string = ', '.join(output)
    return output_string
        

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
        output_string += "<td class=\"%s\">%s</td>" % (k, k)
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
                            x[5][2], # level of the max run
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
                            x[5][1], # id of the maximum run
                            x[5][2], # level of the max run
                            ]] 

    return dungeon_output

def gen_affix_report(affix_counts):
    affixes_overall = construct_analysis(affix_counts)

    affix_output = []
    for x in affixes_overall:

        affix_output += [[str("%.2f" % x[4][0]),
                            beguiling_affixes(x[0]),
                            str("%.2f" % x[1]),
                            str(x[3]),
                            slugify.slugify(unicode(x[0])),
                            str("%.2f" % x[5][0]), # maximum run
                            x[5][1],
                            x[5][2], # level of the max run 
                            ]] # id of the maximum run

    return affix_output

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
                                k[5][2], # level of the max run
                                ]]
        role_package[role_titles[i]] = role_score
    return role_package


def can_tuple(elements):
    new_list = []
    for k in elements:
        new_list += [tuple((k))]
    return tuple(new_list)


def wcl_talents(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:
        talents = []
        for i, j in enumerate(k["talents"]):
            talents += [j["name"]]
            shadow += [j]

        add_this = tuple(talents)
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw

def wcl_essences(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:
        if "essencePowers" not in k:
            continue
        
        essences = []
        for i, j in enumerate(k["essencePowers"]):
            if i != 1: # skip the major's minor
                essences += [j["name"]]
                shadow += [j]


        major = essences[0]
        minors = sorted(essences[1:])
        essences = [major] + minors
        
        add_this = tuple(essences)
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw

def wcl_primary(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:

        primary = []
        # ignoring empowered traits
        for i, j in enumerate(k["azeritePowers"]):
            if i % 5 == 0 or i % 5 == 1: 
                primary += [j["name"]]
                shadow += [j]

        primary = sorted(primary)

        add_this = tuple(primary)
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw

def wcl_role(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:

        role = []
        # ignoring empowered traits
        for i, j in enumerate(k["azeritePowers"]):
            if i % 5 == 2:
                role += [j["name"]]
                shadow += [j]                

        role = sorted(role)

        add_this = tuple(role)
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw

def wcl_defensive(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:

        defensive = []
        # ignoring empowered traits
        for i, j in enumerate(k["azeritePowers"]):
            if i % 5 == 3:
                defensive += [j["name"]]
                shadow += [j]                

        defensive = sorted(defensive)

        add_this = tuple(defensive)
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw


def wcl_hsc(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:

        hsc = []
        for i, j in enumerate(k["gear"]):
            if i == 0 or i == 2 or i == 4:
                hsc += [j["name"]]
                shadow += [j]
        
        add_this = tuple(hsc)
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw

def wcl_rings(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:

        rings = []
        for i, j in enumerate(k["gear"]):
            if i == 10 or i == 11:
                rings += [j["name"]]
                shadow += [j]
        
        add_this = tuple(sorted(rings))
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw


def wcl_trinkets(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:

        trinkets = []
        for i, j in enumerate(k["gear"]):
            if i == 12 or i == 13:
                trinkets += [j["name"]]
                shadow += [j]
        
        add_this = tuple(sorted(trinkets))
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw

def wcl_weapons(rankings):
    groupings = {}
    shadow = []
    
    for k in rankings:

        weapons = []
        for i, j in enumerate(k["gear"]):
            if i == 15 or i == 16:
                weapons += [j["name"]]
                shadow += [j]
        
        add_this = tuple(weapons)
    
        if add_this not in groupings:
            groupings[add_this] = 0
        groupings[add_this] += 1


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    return groupings, shdw


def wcl_top10(d):
    dv = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
    output = []
    for i, (s, n) in enumerate(dv):
        if i >= 10:
            break
        output += [[n, s]]

    return output
    


def gen_wcl_spec_report(spec):
    wcl_query = SpecRankings.query(SpecRankings.spec==spec)
    results = wcl_query.fetch()

    global last_updated
    
    n_parses = 0

    rankings = []
    
    for k in results:
        if last_updated == None:
            last_updated = k.last_updated
        if k.last_updated > last_updated:
            last_updated = k.last_updated

        latest = json.loads(k.rankings)
        rankings += latest

    t, spells = wcl_talents(rankings)
    talents = wcl_top10(t)


    e, espells = wcl_essences(rankings)
    essences = wcl_top10(e)
    spells.update(espells) 


    p, pspells = wcl_primary(rankings)
    primary = wcl_top10(p)
    spells.update(pspells) 


    r, rspells = wcl_role(rankings)
    role = wcl_top10(r)
    spells.update(rspells) 

    
    d, dspells = wcl_defensive(rankings)
    defensive = wcl_top10(d)
    spells.update(dspells) 


    h, items = wcl_hsc(rankings)
    hsc = wcl_top10(h)

    r, ritems = wcl_rings(rankings)
    rings = wcl_top10(r)
    items.update(ritems)
    
    t, titems = wcl_trinkets(rankings)
    trinkets = wcl_top10(t)
    items.update(titems)

    w, witems = wcl_weapons(rankings)
    weapons = wcl_top10(w)
    items.update(witems)
    
    return len(rankings), talents, essences, primary, role, defensive, hsc, rings, trinkets, weapons, spells, items
   

def localized_time(last_updated):
    if last_updated == None:
        return "N/A"
    return pytz.utc.localize(last_updated).astimezone(pytz.timezone("America/New_York"))


def render_affixes(affixes, prefix=""):
    dungeon_counts, spec_counts, set_counts, th_counts, dps_counts, affix_counts = generate_counts(affixes)
    affixes_slug = slugify.slugify(unicode(affixes))
    
    dungeons_report = gen_dungeon_report(dungeon_counts)
    specs_report = gen_spec_report(spec_counts)
    set_report = gen_set_report(set_counts)
    th_report = gen_set_report(th_counts)
    dps_report = gen_set_report(dps_counts)
    affixes_report = gen_affix_report(affix_counts)


    dtl = gen_dungeon_tier_list(dungeons_report)
    tankstl = gen_spec_tier_list(specs_report, "Tanks")
    healerstl = gen_spec_tier_list(specs_report, "Healers")
    meleetl = gen_spec_tier_list(specs_report, "Melee")
    rangedtl = gen_spec_tier_list(specs_report, "Ranged")
    aftl = gen_affix_tier_list(affixes_report)
    
    template = env.get_template('by-affix.html')
    rendered = template.render(title=affixes,
                               prefix=prefix,
                               affixes=affixes,
                               pretty_affixes=pretty_affixes(affixes),
                               affixes_slug=affixes_slug,
                               dungeons=dungeons_report,
                               affixes_report=affixes_report,
                               aftl = aftl,
                               dtl = dtl,
                               tankstl = tankstl,
                               healerstl = healerstl,
                               meleetl = meleetl,
                               rangedtl = rangedtl,
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


def render_wcl_spec(spec, prefix=""):
    spec_slug = slugify.slugify(unicode(spec))

    n_parses, talents, essences, primary, role, defensive, hsc, rings, trinkets, weapons, spells, items = gen_wcl_spec_report(spec)
    
    template = env.get_template('spec.html')
    rendered = template.render(title = spec,
                               spec = spec,
                               spec_slug = spec_slug,
                               talents = talents,
                               essences = essences,
                               primary = primary,
                               role = role,
                               defensive = defensive,
                               hsc = hsc,
                               rings = rings,
                               trinkets = trinkets,
                               weapons = weapons,
                               spells = spells,
                               items = items,
                               n_parses = n_parses,
                               prefix=prefix,
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


def render_and_write(af):
    rendered = render_affixes(af)
    
    filename_slug = slugify.slugify(unicode(af))

    if af == current_affixes():
        filename_slug = "index"

    affix_slug = slugify.slugify(unicode(af))

    options = TaskRetryOptions(task_retry_limit = 1)
    deferred.defer(write_to_storage, filename_slug + ".html", rendered,
                   _retry_options=options)
    
def write_overviews():
    affixes_to_write = []
    affixes_to_write += ["All Affixes"]
    affixes_to_write += known_affixes()

    for af in affixes_to_write:
        options = TaskRetryOptions(task_retry_limit = 1)        
        deferred.defer(render_and_write, af,
                       _retry_options=options))


def create_spec_overview(s):
    spec_slug = slugify.slugify(unicode(s))    
    print "rendering %s" % (spec_slug)    
    rendered = render_wcl_spec(s)
    print "writing %s" % (spec_slug)
    filename = "%s.html" % (spec_slug)
    options = TaskRetryOptions(task_retry_limit = 1)        
    deferred.defer(write_to_storage, filename, rendered,
                       _retry_options=options)     
        
def write_spec_overviews():
    for s in specs:
        options = TaskRetryOptions(task_retry_limit = 1)        
        deferred.defer(create_spec_overview, s,
                       _retry_options=options)   
  
        
        # no longer doing dungeons
        # for dg in dungeons:
        #     rendered = render_dungeon(af, dg)
        #     dungeon_slug = slugify.slugify(unicode(dg))
        #     filename = "%s-%s.html" % (dungeon_slug, affix_slug)
        #     deferred.defer(write_to_storage, filename, rendered,
        #                    _retry_options=options)

    # no longer doing specs per affix
    # for s in specs:
    #     for af in affixes_to_write:
    #         rendered = render_spec(af, "all", s)
    #         spec_slug = slugify.slugify(unicode(s))
    #         affix_slug = slugify.slugify(unicode(af))
    #         filename = "%s-%s.html" % (spec_slug, affix_slug)
    #         deferred.defer(write_to_storage, filename, rendered,
    #                        _retry_options=options)   
            

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
        return destination + render_wcl_spec(spec,
                                         prefix=prefix)
    if dung != "all":
        return destination + render_dungeon(affixes,
                                            dung,
                                            prefix=prefix)

    return destination + render_affixes(affixes, prefix=prefix)


## wcl querying
def _rankings(encounterId, class_id, spec, page=1, season=3):
    url = "https://www.warcraftlogs.com:443/v1/rankings/encounter/%d?partition=%d&class=%d&spec=%d&page=%d&api_key=%s" % (encounterId, season, class_id, spec, page, api_key)
    result = urlfetch.fetch(url)
    data = json.loads(result.content)
    return data



def update_wcl_rankings(spec, dungeon, page):
    if spec not in wcl_specs:
        return "invalid spec [%s]" % spec
    spec_key = slugify.slugify(unicode(spec))
    if dungeon not in dungeon_encounters:
        return "invalid dungeon [%s]" % dungeon
    dungeon_id = dungeon_encounters[dungeon]
    dungeon_slug = slugify.slugify(unicode(dungeon))

    aggregate = []
    
    stopFlag = False
    rankings = _rankings(dungeon_id, wcl_specs[spec][0], wcl_specs[spec][1], page=page)
    for k in rankings["rankings"]:
        if int(k["keystoneLevel"]) >= 16:
            aggregate += [k]
        else:
            stopFlag = True
    
    key = ndb.Key('SpecRankings', "%s-%s-%d" % (spec_key, dungeon_slug, page))
    sr = SpecRankings(key=key)
    sr.spec = spec
    sr.dungeon = dungeon
    sr.page = page
    sr.rankings = json.dumps(aggregate)
    sr.put()
    
    return stopFlag

    
def update_wcl_spec(spec):
    if spec not in wcl_specs:
        return "invalid spec [%s]" % spec
    spec_key = slugify.slugify(unicode(spec))

    print "Updating %s..." % (spec)

    aggregate = []
    for k, v in dungeon_encounters.iteritems():
        page = 1
        stopFlag = False
        while stopFlag != True and page <= 10:
            print "%s %s %d" % (spec, k, page)
            stopFlag = update_wcl_rankings(spec, k, page)
            page += 1

    return spec, spec_key,  wcl_specs[spec]


# get the data
def update_wcl_update():
    for i, s in enumerate(specs):
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(update_wcl_spec, s, _countdown=150*i, _retry_options=options)
    
    

# update all the wcl
def update_wcl_all():
    update_wcl_update()

    options = TaskRetryOptions(task_retry_limit = 1)
    deferred.defer(write_spec_overviews, _countdown=40*150,
                   _retry_options=options)




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
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(write_overviews, _countdown=20,
                       _retry_options=options)        

class GenerateHTML(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Queueing updates\n")
        update_current()
        self.response.write("Writing templates to cloud storage...\n")
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(write_overviews, _countdown=20,
                       _retry_options=options)

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

class WCLGetRankings(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Queueing updates...\n")
        update_wcl_all()

class WCLGenHTML(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Writing WCL HTML...\n")
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(write_spec_overviews, _retry_options=options)        
        

app = webapp2.WSGIApplication([
        ('/update_current_dungeons', UpdateCurrentDungeons),
        ('/generate_html', GenerateHTML),
        ('/only_generate_html', OnlyGenerateHTML),
        ('/view', TestView),
        ('/known_affixes', KnownAffixesShow),
        ('/update_wcl', WCLGetRankings),
        ('/generate_wcl_html', WCLGenHTML),
        ], debug=True)
