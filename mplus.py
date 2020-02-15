import webapp2
import logging
import os
import json
import pdb
import copy
import operator
import time

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

from warcraft import awakened_weeks as affix_rotation_weeks

# wcl handling
from models import SpecRankings, SpecRankingsRaid
from auth import api_key
from wcl import wcl_specs, dungeon_encounters

from wcl import nyalotha_encounters as raid_encounters
from raid import nyalotha_nox_notes_slugs as nox_notes_slugs
from raid import nyalotha_canonical_order as raid_canonical_order
from raid import nyalotha_short_names as raid_short_names

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

## @@season update
## also in templates/max_link and templates/by-affix
## also in wcl_ (also marked with @@)

def update_dungeon_affix_region(dungeon, affixes, region, season="season-bfa-4", page=0):
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
    return buckets


from ckmeans import ckmeans

# generate a dungeon tier list
def gen_dungeon_tier_list(dungeons_report):

    scores = []
    for k in dungeons_report:
        scores += [float(k[0])]

    buckets = ckmeans(scores, 6)
   
    added = []

    tiers = {}
    tm = {}
    tm[5] = "S"
    tm[4] = "A"
    tm[3] = "B"
    tm[2] = "C"
    tm[1] = "D"
    tm[0] = "F"

    for i in range(0, 6):
        tiers[tm[i]] = []
    
    for i in range(0, 6):
        for k in dungeons_report:
            if float(k[0]) in buckets[i]:
                if k not in added:
                    if tm[i] not in tiers:
                        tiers[tm[i]] = []
                    tiers[tm[i]] += [k]
                    added += [k]


    # add stragglers to last tier
    for k in dungeons_report:
        if k not in added:
            if tm[0] not in tiers:
                tiers[tm[0]] = []
            tiers[tm[0]] += [k]
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


def icon_spec(dname, prefix="", size=56):
    dslug = slugify.slugify(unicode(dname))
    return '<a href="%s.html"><img src="images/specs/%s.jpg" width="%d" height="%d" title="%s" alt="%s" /><br/>%s</a>' % (prefix+dslug, dslug, size, size, dname, dname, dname)

import pdb

# generate a specs tier list
def gen_spec_tier_list(specs_report, role, prefix=""):
    global role_titles


    scores = []
    for i in range(0, 4):
        for k in specs_report[role_titles[i]]:
            if int(k[3]) < 20: # ignore specs with fewer than 20 runs as they would skew the buckets; we'll add them to F later
                continue
            scores += [float(k[0])]

    if len(scores) < 6: # relax the fewer than 20 rule (early scans early in season)
        scores = []
        for i in range(0, 4):
            for k in specs_report[role_titles[i]]:
                scores += [float(k[0])]
        
    buckets = ckmeans(scores, 6)
            

    added = []

    tiers = {}
    tm = {}
    tm[5] = "S"
    tm[4] = "A"
    tm[3] = "B"
    tm[2] = "C"
    tm[1] = "D"
    tm[0] = "F"

    for i in range(0, 6):
        tiers[tm[i]] = []
    
    for i in range(0, 6):
        for k in specs_report[role]:
            if float(k[0]) in buckets[i]:
                if k not in added:
                    tiers[tm[i]] += [k]
                    added += [k]

    # add stragglers to last tier
    for k in specs_report[role]:
        if k not in added:
            tiers[tm[0]] += [k]
            added += [k]
    
    dtl = {}
    dtl["S"] = ""
    dtl["A"] = ""
    dtl["B"] = ""
    dtl["C"] = ""
    dtl["D"] = ""
    dtl["F"] = ""

    for i in range(0, 6):
        for k in tiers[tm[i]]:
            dtl[tm[i]] += '<div class="innertier">' + icon_spec(k[1], prefix) + "</div>"
    
    return dtl   




def icon_affix(dname, size=28):
    dname = affix_rotation_affixes(dname)
    dslug = slugify.slugify(unicode(dname))
    
    def miniaffix(aname, aslug, size):
        return '<img src="images/affixes/%s.jpg" width="%d" height="%d" title="%s" alt="%s" />' % (aslug, size, size, aname, aname)
    
    affixen = dname.split(", ")
    output = []
    
    for af in affixen:
        afname = af
        afslug = slugify.slugify(af)
        output += [miniaffix(afname, afslug, size=size)]
        
    output_string = output[0]
    output_string += output[1]
    output_string += output[2]
    output_string += output[3]
       
    return output_string

# todo: affix tier list (how do affixes compare with each other)
# have this show on all affixes?
# new: generate a dungeon tier list
def gen_affix_tier_list(affixes_report):
    if len(affixes_report) < 6:
        return gen_affix_tier_list_small(affixes_report)

    # ckmeans
    scores = []
    for k in affixes_report:
        scores += [float(k[0])]

    buckets = ckmeans(scores, 6)
    added = []

    tiers = {}
    tm = {}
    tm[5] = "S"
    tm[4] = "A"
    tm[3] = "B"
    tm[2] = "C"
    tm[1] = "D"
    tm[0] = "F"


    for i in range(0, 6):
        tiers[tm[i]] = []
    
    for i in range(0, 6):
        for k in affixes_report:
            if float(k[0]) in buckets[i]:
                if k not in added:
                    if tm[i] not in tiers:
                        tiers[tm[i]] = []
                    tiers[tm[i]] += [k]
                    added += [k]

        # add stragglers to last tier
    for k in affixes_report:
        if k not in added:
            if tm[0] not in tiers:
                tiers[tm[0]] = []
            tiers[tm[0]] += [k]
            added += [k]


        
    dtl = {}
    dtl["S"] = ""
    dtl["A"] = ""
    dtl["B"] = ""
    dtl["C"] = ""
    dtl["D"] = ""
    dtl["F"] = ""

    for i in range(0, 6):
        for k in tiers[tm[i]]:
            dtl[tm[i]] += '<div class="innertier">' + icon_affix(k[1]) + "<br/> %s</div>" % k[1]        
    
    return dtl
    

    
# use this if there are fewer than 6 affixes scanned
# since we can't cluster into 6 with uh, fewer than 6
def gen_affix_tier_list_small(affixes_report):
   
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
    
    dtl = {}
    dtl["S"] = ""
    dtl["A"] = ""
    dtl["B"] = ""
    dtl["C"] = ""
    dtl["D"] = ""
    dtl["F"] = ""

    for i in range(0, 6):
        for k in tiers[tm[i]]:
            dtl[tm[i]] += '<div class="innertier">' + icon_affix(k[1]) + "<br/> %s</div>" % k[1]        
    
    return dtl


# for background on the analytical approach of using the lower bound of a confidence interval:
# https://www.evanmiller.org/how-not-to-sort-by-average-rating.html
# https://www.evanmiller.org/ranking-items-with-star-ratings.html 

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
        all_runs = []
        for r in runs:
            data += [r.score]
            all_runs += [[r.score, r.mythic_level, r.keystone_run_id]]
            if r.score >= max_found:
                max_found = r.score
                max_id = r.keystone_run_id
                max_level = r.mythic_level
        n = len(data)
        if n == 0:
            overall += [[name, 0, 0, n, [0, 0], [0, "", 0], []]]
            continue
        mean = average(data)
        if n <= 1:
            overall += [[name, mean, 0, n, [0, 0], [max_found, max_id, max_level], all_runs]]
            continue
        stddev = std(data, ddof=1)
        t_bounds = t_interval(n)
        ci = [mean + critval * master_stddev / sqrt(n) for critval in t_bounds]
        maxi = [max_found, max_id, max_level]
        all_runs = sorted(all_runs, key=lambda x: x[0], reverse=True)
        overall += [[name, mean, stddev, n, ci, maxi, all_runs]]


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
    known_affixes_report += [["All Affixes", prefix+"all-affixes", ""]]
    for k in known_affixes_list:
        if use_index:
            if k == current_affixes():
                known_affixes_report += [[affix_rotation_affixes(k), prefix+"index",
                                          icon_affix(k)]]
            else:
                known_affixes_report += [[affix_rotation_affixes(k), prefix+slugify.slugify(unicode(k)),
                                          icon_affix(k)]]
            
        else:
            known_affixes_report += [[affix_rotation_affixes(k), prefix+slugify.slugify(unicode(k)),
                                      icon_affix(k)]]
            
    known_affixes_report.reverse()
    return known_affixes_report

def known_dungeon_links(affixes_slug, prefix=""):
    known_dungeon_list = dungeons

    known_dungeon_report = []

    for k in known_dungeon_list:
        known_dungeon_report += [[k, prefix+slugify.slugify(unicode(k))+"-" + affixes_slug]]
            
    return known_dungeon_report

def known_specs_links(prefix=""):
    global tanks, healers, melee, ranged
    known_specs_report = []
    for d in [sorted(tanks), sorted(healers), sorted(melee), sorted(ranged)]:
        for k in d:
            known_specs_report += [[k, slugify.slugify(unicode(k)), icon_spec(k, size=22)]]

    return known_specs_report

def known_specs_subset_links(subset, prefix=""):
    known_specs_report = []
    for d in [sorted(subset)]:
        for k in d:
            known_specs_report += [[k, slugify.slugify(unicode(k)), icon_spec(k, size=22)]]

    return known_specs_report


        


def current_affixes():
    pull_query = KnownAffixes.query().order(-KnownAffixes.last_seen, -KnownAffixes.first_seen)
#    logging.info(pull_query)
#    logging.info(pull_query.fetch(1))
    current_affixes_save = pull_query.fetch(1)[0].affixes
    
    return current_affixes_save

## end getting data out into counts



## html generation start

##   generating common reports

def affix_rotation_affixes(affixes):
    global affix_rotation_weeks
    if affixes in affix_rotation_weeks:
        return affixes + " (%s)" % affix_rotation_weeks[affixes]
    return affixes

# given a list of affixes, return a pretty affix string
# <img><img><img><img> Affix1, Affix2, Affix3, Affix4
def pretty_affixes(affixes, size=16):
    if affixes=="All Affixes":
        return "All Affixes"

    output_string = icon_affix(affixes, size=size) + " %s" % affix_rotation_affixes(affixes)
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
        output_string += "<td class=\"comp %s\">%s</td>" % (k, k)
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
                            x[6], # all runs info
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
                            x[6], # all runs info
                            ]] 

    return dungeon_output

def gen_affix_report(affix_counts):
    affixes_overall = construct_analysis(affix_counts)

    affix_output = []
    for x in affixes_overall:

        affix_output += [[str("%.2f" % x[4][0]),
                            affix_rotation_affixes(x[0]),
                            str("%.2f" % x[1]),
                            str(x[3]),
                            slugify.slugify(unicode(x[0])),
                            str("%.2f" % x[5][0]), # maximum run
                            x[5][1], # id of the maximum run
                            x[5][2], # level of the max run
                            x[6], # all runs info
                            ]] 

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
                                k[6], # all runs info
                                ]]
        role_package[role_titles[i]] = role_score
    return role_package


def can_tuple(elements):
    new_list = []
    for k in elements:
        new_list += [tuple((k))]
    return tuple(new_list)

# talents, essences, azerite combo
def wcl_tea(rankings):
    groupings = {}
    shadow = []
    popover = {}
    
    for k in rankings:
        if "essencePowers" not in k:
            continue
        
        talents = []
        for i, j in enumerate(k["talents"]):
            talents += [j["name"]]
            shadow += [j]

        
        essences = []
        for i, j in enumerate(k["essencePowers"]):
            if i != 1: # skip the major's minor
                essences += [j["name"]]
                shadow += [j]

        major = essences[0]
        minors = sorted(essences[1:])
        essences = [major] + minors

        primary = []
        # ignoring empowered traits
        for i, j in enumerate(k["azeritePowers"]):
            if i % 5 == 0 or i % 5 == 1: 
                primary += [j["name"]]
                shadow += [j]

        primary = sorted(primary)

        add_this = tuple(talents + essences + primary)
    
        if add_this not in groupings:
            groupings[add_this] = 0
            popover[add_this] = []
        groupings[add_this] += 1
        
        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]

    return groupings, shdw, popover


def wcl_talents(rankings):
    groupings = {}
    shadow = []
    popover = {}
    
    for k in rankings:
        talents = []
        for i, j in enumerate(k["talents"]):
            talents += [j["name"]]
            shadow += [j]

        add_this = tuple(talents)
        
        if add_this not in groupings:
            groupings[add_this] = 0
            popover[add_this] = []
        groupings[add_this] += 1
        
        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]

    return groupings, shdw, popover

def wcl_essences(rankings):
    groupings = {}
    shadow = []
    popover = {}
    
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
            popover[add_this] = []
        groupings[add_this] += 1

        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10        

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]

    return groupings, shdw, popover

def wcl_primary(rankings):
    groupings = {}
    shadow = []
    popover = {}
    
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
            popover[add_this] = []
        groupings[add_this] += 1

        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]
        
    return groupings, shdw, popover

def wcl_role(rankings):
    groupings = {}
    shadow = []
    popover = {}
    
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
            popover[add_this] = []
        groupings[add_this] += 1

        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]
        
    return groupings, shdw, popover

def wcl_defensive(rankings):
    groupings = {}
    shadow = []
    popover = {}
    
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
            popover[add_this] = []
        groupings[add_this] += 1

        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]
        
    return groupings, shdw, popover


def wcl_hsc(rankings):
    groupings = {}
    shadow = []
    popover = {}
    
    for k in rankings:

        hsc = []
        for i, j in enumerate(k["gear"]):
            if i == 0 or i == 2 or i == 4:
                hsc += [j["name"]]
                shadow += [j]
        
        add_this = tuple(hsc)
    
        if add_this not in groupings:
            groupings[add_this] = 0
            popover[add_this] = []
        groupings[add_this] += 1

        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]
        
    return groupings, shdw, popover

def wcl_rings(rankings):
    groupings = {}
    shadow = []
    popover = {}
    
    for k in rankings:

        rings = []
        for i, j in enumerate(k["gear"]):
            if i == 10 or i == 11:
                rings += [j["name"]]
                shadow += [j]
        
        add_this = tuple(sorted(rings))
    
        if add_this not in groupings:
            groupings[add_this] = 0
            popover[add_this] = []
        groupings[add_this] += 1

        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]
        
    return groupings, shdw, popover



def wcl_gear(rankings, slots):
    groupings = {}
    shadow = []
    popover = {}
    
    for k in rankings:

        gear = []
        for i, j in enumerate(k["gear"]):
            if i in slots:
                gear += [j["name"]]
                shadow += [j]

        # do NOT sort if weapon (we want the mainhand/offhand distinction)
        if 15 in slots:
            add_this = tuple((gear))
        else:
            add_this = tuple(sorted(gear))
    
        if add_this not in groupings:
            groupings[add_this] = 0
            popover[add_this] = []
        groupings[add_this] += 1

        link_text = ""
        sort_value = 0
        band_value = 0
        if "keystoneLevel" in k:
            link_text = "+%d" % k["keystoneLevel"]
            sort_value = int(k["keystoneLevel"])
            band_value = int(k["keystoneLevel"])
        elif "total" in k:
            link_text = "%.2fk" % (float(k["total"])/1000)
            sort_value = (float(k["total"])/1000)
            band_value = int((float(k["total"])/10000))*10

        popover[add_this] += [[sort_value, band_value, link_text, k["reportID"]]]


    shdw = {}
    for x in shadow:
        shdw[x["name"]] = [x["id"], x["icon"]]

    for k, v in popover.iteritems():
        popover[k] = sorted(v, key=operator.itemgetter(0), reverse=True)[:25]
        
    return wcl_top10(groupings, popover), shdw


def wcl_top10(d, pop=None, top_n = 10):
    # need to also expore these ... k["reportId"] + k["keystoneLevel"]    
    dv = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
    output = []
    for i, (s, n) in enumerate(dv):
        if i >= top_n:
            break
        if pop == None:
            output += [[n, s, []]]
        else:
            output += [[n, s, pop[s]]]

    return output
    


def gen_wcl_spec_report(spec):
    wcl_query = SpecRankings.query(SpecRankings.spec==spec) ##temp
    results = wcl_query.fetch()

    global last_updated

    key_levels = []
    
    n_parses = 0

    rankings = []
    
    for k in results:
        if last_updated == None:
            last_updated = k.last_updated
        if k.last_updated > last_updated:
            last_updated = k.last_updated

        latest = json.loads(k.rankings)
        rankings += latest


    for k in rankings:
        key_levels += [k["keystoneLevel"]]

    tea, spells, pop = wcl_tea(rankings)
    tea = wcl_top10(tea, pop, top_n = 25)
        
    t, tspells, pop = wcl_talents(rankings)
    talents = wcl_top10(t, pop)
    spells.update(tspells) 

    e, espells, pop = wcl_essences(rankings)
    essences = wcl_top10(e, pop)
    spells.update(espells) 

    p, pspells, pop = wcl_primary(rankings)
    primary = wcl_top10(p, pop)
    spells.update(pspells) 

    r, rspells, pop = wcl_role(rankings)
    role = wcl_top10(r, pop)
    spells.update(rspells) 

    d, dspells, pop = wcl_defensive(rankings)
    defensive = wcl_top10(d, pop)
    spells.update(dspells) 

    gear = {}

    h, items, pop = wcl_hsc(rankings)
    hsc = wcl_top10(h, pop)

    gear_slots = []
    gear_slots += [["helms", [0]]]
    gear_slots += [["shoulders", [2]]]
    gear_slots += [["chests", [4]]]
    gear_slots += [["belts", [5]]]
    gear_slots += [["legs", [6]]]
    gear_slots += [["feet", [7]]]
    gear_slots += [["wrists", [8]]]
    gear_slots += [["gloves", [9]]]
    gear_slots += [["rings", [10, 11]]]
    gear_slots += [["trinkets", [12, 13]]]
    gear_slots += [["cloaks", [14]]]
    gear_slots += [["weapons", [15, 16]]]

    for (slot_name, slots) in gear_slots:
        gear[slot_name], update_items = wcl_gear(rankings, slots) #popover is built into this function
        items.update(update_items)

    if len(key_levels) > 0:
        return len(rankings), max(key_levels), min(key_levels), tea, talents, essences, primary, role, defensive, hsc, gear, spells, items
    return 0, 0, 0, tea, talents, essences, primary, role, defensive, hsc, gear, spells, items

def gen_wcl_raid_spec_report(spec, encounter="all", difficulty="Heroic"):
    if encounter == "all":
        wcl_query = SpecRankingsRaid.query(SpecRankingsRaid.spec==spec,
                                           SpecRankingsRaid.difficulty==difficulty)
    else:
        wcl_query = SpecRankingsRaid.query(SpecRankingsRaid.spec==spec,
                                           SpecRankingsRaid.encounter==encounter,
                                           SpecRankingsRaid.difficulty==difficulty)
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

    tea, spells, pop = wcl_tea(rankings)
    tea = wcl_top10(tea, pop, top_n=25)

    t, tspells, pop = wcl_talents(rankings)
    talents = wcl_top10(t, pop)
    spells.update(tspells) 

    e, espells, pop = wcl_essences(rankings)
    essences = wcl_top10(e, pop)
    spells.update(espells) 


    p, pspells, pop = wcl_primary(rankings)
    primary = wcl_top10(p, pop)
    spells.update(pspells) 


    r, rspells, pop = wcl_role(rankings)
    role = wcl_top10(r, pop)
    spells.update(rspells) 

    
    d, dspells, pop = wcl_defensive(rankings)
    defensive = wcl_top10(d, pop)
    spells.update(dspells) 

    gear = {}

    h, items, pop = wcl_hsc(rankings)
    hsc = wcl_top10(h, pop)

    gear_slots = []
    gear_slots += [["helms", [0]]]
    gear_slots += [["shoulders", [2]]]
    gear_slots += [["chests", [4]]]
    gear_slots += [["belts", [5]]]
    gear_slots += [["legs", [6]]]
    gear_slots += [["feet", [7]]]
    gear_slots += [["wrists", [8]]]
    gear_slots += [["gloves", [9]]]
    gear_slots += [["rings", [10, 11]]]
    gear_slots += [["trinkets", [12, 13]]]
    gear_slots += [["cloaks", [14]]]
    gear_slots += [["weapons", [15, 16]]]

    for (slot_name, slots) in gear_slots:
        gear[slot_name], update_items = wcl_gear(rankings, slots) #popover built in
        items.update(update_items)
    
    return len(rankings), tea, talents, essences, primary, role, defensive, hsc, gear, spells, items
   

def localized_time(last_updated):
    if last_updated == None:
        return pytz.utc.localize(datetime.datetime.now()).astimezone(pytz.timezone("America/New_York"))
    return pytz.utc.localize(last_updated).astimezone(pytz.timezone("America/New_York"))

def render_affixes(affixes, prefix=""):
    dungeon_counts, spec_counts, set_counts, th_counts, dps_counts, affix_counts = generate_counts(affixes)
    affixes_slug = slugify.slugify(unicode(affixes))
    affixes_slug_special = affixes_slug
    if affixes == current_affixes():
        affixes_slug_special = "index"
    
    dungeons_report = gen_dungeon_report(dungeon_counts)
    specs_report = gen_spec_report(spec_counts)
    set_report = gen_set_report(set_counts)
    th_report = gen_set_report(th_counts)
    dps_report = gen_set_report(dps_counts)
    affixes_report = gen_affix_report(affix_counts)


    dtl = gen_dungeon_tier_list(dungeons_report)
    tankstl = gen_spec_tier_list(specs_report, "Tanks", prefix=prefix)
    healerstl = gen_spec_tier_list(specs_report, "Healers", prefix=prefix)
    meleetl = gen_spec_tier_list(specs_report, "Melee", prefix=prefix)
    rangedtl = gen_spec_tier_list(specs_report, "Ranged", prefix=prefix)
    aftl = gen_affix_tier_list(affixes_report)
    
    template = env.get_template('by-affix.html')
    rendered = template.render(title=affixes,
                               prefix=prefix,
                               affixes=affixes,
                               pretty_affixes=pretty_affixes(affixes),
                               pretty_affixes_large=pretty_affixes(affixes, size=56),
                               affixes_slug=affixes_slug,
                               affixes_slug_special=affixes_slug_special,
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
                               known_tanks = known_specs_subset_links(tanks, prefix=prefix),
                               known_healers = known_specs_subset_links(healers, prefix=prefix),
                               known_melee = known_specs_subset_links(melee, prefix=prefix),
                               known_ranged = known_specs_subset_links(ranged, prefix=prefix),
                               known_affixes = known_affixes_links(prefix=prefix),
                               last_updated = localized_time(last_updated))
    return rendered


def render_wcl_spec(spec, prefix=""):
    spec_slug = slugify.slugify(unicode(spec))
    affixes = "N/A"
    n_parses, key_max, key_min, tea, talents, essences, primary, role, defensive, hsc, gear, spells, items = gen_wcl_spec_report(spec)
    
    template = env.get_template('spec.html')
    rendered = template.render(title = spec,
                               spec = spec,
                               spec_slug = spec_slug,
                               tea = tea,
                               talents = talents,
                               affixes = affixes,
                               essences = essences,
                               primary = primary,
                               role = role,
                               defensive = defensive,
                               hsc = hsc,
                               gear = gear,
                               spells = spells,
                               items = items,
                               n_parses = n_parses,
                               key_max = key_max,
                               key_min = key_min,
                               prefix=prefix,
                               known_tanks = known_specs_subset_links(tanks, prefix=prefix),
                               known_healers = known_specs_subset_links(healers, prefix=prefix),
                               known_melee = known_specs_subset_links(melee, prefix=prefix),
                               known_ranged = known_specs_subset_links(ranged, prefix=prefix),
                               known_affixes = known_affixes_links(prefix=prefix),
                               last_updated = localized_time(last_updated))

    return rendered

def render_raid_index(prefix=""):
    template = env.get_template("raid-index.html")
    rendered = template.render(prefix=prefix,
                               active_page = "raid-index",
                               known_tanks = known_specs_subset_links(tanks, prefix=prefix),
                               known_healers = known_specs_subset_links(healers, prefix=prefix),
                               known_melee = known_specs_subset_links(melee, prefix=prefix),
                               known_ranged = known_specs_subset_links(ranged, prefix=prefix),
                               known_affixes = known_affixes_links(prefix=prefix),
                               last_updated = localized_time(last_updated))


    return rendered

def render_wcl_raid_spec(spec, encounter="all", difficulty="Heroic", prefix=""):
    spec_slug = slugify.slugify(unicode(spec))
    affixes = "N/A"
    n_parses, tea, talents, essences, primary, role, defensive, hsc, gear, spells, items = gen_wcl_raid_spec_report(spec, encounter, difficulty)

    encounter_pretty = encounter
    if encounter_pretty == "all":
        encounter_pretty = "Ny'alotha"

    encounter_slugs = {}
    for e in raid_canonical_order:
        encounter_slugs[e] = slugify.slugify(unicode(e))

    encounter_slug = slugify.slugify(unicode(encounter))
    difficulty_slug = slugify.slugify(unicode(difficulty))

    nox_role = "dps"
    if spec in tanks:
        nox_role = "tank"
    if spec in healers:
        nox_role = "healer"
    
    if encounter != "all":
        nox_slug = nox_notes_slugs[encounter]

    nox_link = ""
    if encounter != "all":
        nox_link += nox_slug + "/" + nox_role
        
    template = env.get_template('spec-raid.html')
    rendered = template.render(title = spec + " (%s %s)" % (difficulty, encounter_pretty),
                               spec = spec,
                               spec_slug = spec_slug,
                               active_page = spec_slug + "-" + encounter_slug + "-" + difficulty_slug,
                               tea = tea,
                               talents = talents,
                               affixes = affixes,
                               essences = essences,
                               primary = primary,
                               defensive = defensive,
                               role = role,
                               hsc = hsc,
                               gear = gear,
                               nox_link = nox_link,
                               spells = spells,
                               items = items,
                               raid_canonical_order = raid_canonical_order,
                               encounter_slugs = encounter_slugs,
                               raid_short_names = raid_short_names,
                               n_parses = n_parses,
                               encounter = encounter,
                               encounter_pretty = encounter_pretty,
                               difficulty = difficulty,
                               prefix=prefix,
                               known_tanks = known_specs_subset_links(tanks, prefix=prefix),
                               known_healers = known_specs_subset_links(healers, prefix=prefix),
                               known_melee = known_specs_subset_links(melee, prefix=prefix),
                               known_ranged = known_specs_subset_links(ranged, prefix=prefix),
                               known_affixes = known_affixes_links(prefix=prefix),
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

def raid_write_to_storage(filename, content):
    bucket_name = 'nyalotha.subcreation.net'
    
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
                       _retry_options=options)


def create_spec_overview(s):
    spec_slug = slugify.slugify(unicode(s))    
    rendered = render_wcl_spec(s)
    filename = "%s.html" % (spec_slug)
    options = TaskRetryOptions(task_retry_limit = 1)        
    deferred.defer(write_to_storage, filename, rendered,
                       _retry_options=options)

def create_raid_index():
    rendered = render_raid_index()
    filename = "index.html" 
    options = TaskRetryOptions(task_retry_limit = 1)        
    deferred.defer(raid_write_to_storage, filename, rendered,
                       _retry_options=options)
    
def create_raid_spec_overview(s, e="all", difficulty="Heroic"):
    spec_slug = slugify.slugify(unicode(s))
    rendered = render_wcl_raid_spec(s, encounter=e, difficulty=difficulty)
    if e == "all":
        if difficulty == "Mythic":
            filename = "%s-mythic.html" % (spec_slug)
        else:        
            filename = "%s.html" % (spec_slug)
    else:
        encounter_slug = slugify.slugify(unicode(e))
        if difficulty == "Mythic":
            filename = "%s-%s-mythic.html" % (spec_slug, encounter_slug)
        else:        
            filename = "%s-%s.html" % (spec_slug, encounter_slug)
    options = TaskRetryOptions(task_retry_limit = 1)        
    deferred.defer(raid_write_to_storage, filename, rendered,
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

            

def write_raid_spec_overviews():
    # write the index page
    options = TaskRetryOptions(task_retry_limit = 1)        
    deferred.defer(create_raid_index,
                   _retry_options=options)   
    
    for s in specs:
        options = TaskRetryOptions(task_retry_limit = 1)        
        deferred.defer(create_raid_spec_overview, s, "all", "Heroic",
                       _retry_options=options)
        deferred.defer(create_raid_spec_overview, s, "all", "Mythic",
                       _retry_options=options)
        
        for k, v in raid_encounters.iteritems():
            options = TaskRetryOptions(task_retry_limit = 1)        
            deferred.defer(create_raid_spec_overview, s, k, "Heroic",
                           _retry_options=options)
            deferred.defer(create_raid_spec_overview, s, k, "Mythic",
                           _retry_options=options)

            
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
        return render_wcl_spec(spec,
                               prefix=prefix)
    if dung != "all":
        return render_dungeon(affixes,
                              dung,
                              prefix=prefix)

    return render_affixes(affixes, prefix=prefix)


def test_raid_view(destination):
    affixes = current_affixes()
    spec = "all"
    encounter = "all"
    prefix = "raid?goto="
    difficulty = "Heroic"
    
    for s in specs:
        if slugify.slugify(unicode(s)) in destination:
            spec = s

    for e in raid_canonical_order:
        if slugify.slugify(unicode(e)) in destination:
            encounter = e


    if "mythic" in destination:
        difficulty = "Mythic"

    if "index" in destination:
        return render_raid_index(prefix=prefix)
            

    return render_wcl_raid_spec(spec, encounter=encounter,
                                difficulty = difficulty, prefix=prefix)


## wcl querying
# @@season update
def _rankings(encounterId, class_id, spec, page=1, season=4):
    # filter to the last 4 weeks
    now = datetime.datetime.now()
    wcl_date = "date."
    wcl_date += "%d000" % (time.mktime(now.timetuple())-4*7*60*60*24 )
    wcl_date += "." + "%d000" % (time.mktime(now.timetuple()))
    
    url = "https://www.warcraftlogs.com:443/v1/rankings/encounter/%d?partition=%d&class=%d&spec=%d&page=%d&filter=%s&api_key=%s" % (encounterId, season, class_id, spec, page, wcl_date, api_key)
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
        if int(k["keystoneLevel"]) >= 10: # reducing this to from +16 to +10 early in the season
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

# 4 - heroic
# 5 - mythic
def _rankings_raid(encounterId, class_id, spec, difficulty=4, page=1, season=4):
    # filter to the last 4 weeks
    now = datetime.datetime.now()
    wcl_date = "date."
    wcl_date += "%d000" % (time.mktime(now.timetuple())-4*7*60*60*24 )
    wcl_date += "." + "%d000" % (time.mktime(now.timetuple()))
    
    url = "https://www.warcraftlogs.com:443/v1/rankings/encounter/%d?difficulty=%d&class=%d&spec=%d&page=%d&filter=%s&api_key=%s" % (encounterId, difficulty, class_id, spec, page, wcl_date, api_key)
    
    result = urlfetch.fetch(url)
    data = json.loads(result.content)
    return data


def update_wcl_raid_rankings(spec, encounter, page=1, difficulty = "Heroic"):
    if spec not in wcl_specs:
        return "invalid spec [%s]" % spec
    spec_key = slugify.slugify(unicode(spec))
    if encounter not in raid_encounters:
        return "invalid encounter [%s]" % encounter
    encounter_id = raid_encounters[encounter]
    encounter_slug = slugify.slugify(unicode(encounter))

    aggregate = []
    
    stopFlag = False
    difficulty_code = 4
    if difficulty == "Heroic":
        difficulty_code = 4
    if difficulty == "Mythic":
        difficulty_code = 5
    
    rankings = _rankings_raid(encounter_id, wcl_specs[spec][0], wcl_specs[spec][1], difficulty_code, page=page)

    # no datas yet!
    if "rankings" not in rankings:
        return False
    
    for k in rankings["rankings"]:
        aggregate += [k]
    
    key = ndb.Key('SpecRankingsRaid', "%s-%s-%s-%d" % (spec_key, encounter_slug, difficulty, page))
    sr = SpecRankingsRaid(key=key)
    sr.spec = spec
    sr.encounter = encounter
    sr.difficulty = difficulty
    sr.page = page
    sr.rankings = json.dumps(aggregate)
    sr.put()
    
    return True

    
def update_wcl_spec(spec):
    if spec not in wcl_specs:
        return "invalid spec [%s]" % spec
    spec_key = slugify.slugify(unicode(spec))

    aggregate = []
    for k, v in dungeon_encounters.iteritems():
        stopFlag = update_wcl_rankings(spec, k, 1)

    return spec, spec_key,  wcl_specs[spec]



# get the data for dungeons
def update_wcl_update():
    for i, s in enumerate(specs):
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(update_wcl_spec, s, _countdown=15*i, _retry_options=options)


def update_wcl_update_subset(subset):
    for i, s in enumerate(subset):
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(update_wcl_spec, s, _countdown=15*i, _retry_options=options)
        

def update_wcl_raid_spec(spec, difficulty="Heroic"):
    if spec not in wcl_specs:
        return "invalid spec [%s]" % spec
    spec_key = slugify.slugify(unicode(spec))

    aggregate = []
    for k, v in raid_encounters.iteritems():
        stopFlag = update_wcl_raid_rankings(spec, k, page=1, difficulty=difficulty)

    return spec, spec_key,  wcl_specs[spec]
        
# update wcl for raids
def update_wcl_raid_update():
    for i, s in enumerate(specs):
        options = TaskRetryOptions(task_retry_limit = 1)    
        deferred.defer(update_wcl_raid_spec, s, "Heroic", _countdown=30*i, _retry_options=options)
        options = TaskRetryOptions(task_retry_limit = 1)    
        deferred.defer(update_wcl_raid_spec, s, "Mythic", _countdown=30*i+15, _retry_options=options)

def update_wcl_raid_update_subset(subset):
    for i, s in enumerate(subset):
        options = TaskRetryOptions(task_retry_limit = 1)    
        deferred.defer(update_wcl_raid_spec, s, "Heroic", _countdown=30*i, _retry_options=options)
        options = TaskRetryOptions(task_retry_limit = 1)    
        deferred.defer(update_wcl_raid_spec, s, "Mythic", _countdown=30*i+15, _retry_options=options)

        
def update_wcl_raid_all():
    update_wcl_raid_update()

    options = TaskRetryOptions(task_retry_limit = 1)
    deferred.defer(write_raid_spec_overviews, _countdown=40*30,
                   _retry_options=options)
    
# update all the wcl for dungeons
def update_wcl_all():
    update_wcl_update()

    options = TaskRetryOptions(task_retry_limit = 1)
    deferred.defer(write_spec_overviews, _countdown=40*15,
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

class TestRaidView(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        destination = self.request.get("goto", "index.html")
        self.response.write(test_raid_view(destination))
        

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

class TestWCLGetRankings(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Queueing updates...\n")
        update_wcl_update_subset(["Outlaw Rogue"])

class WCLGetRankingsRaid(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Queueing updates...\n")
        update_wcl_raid_all()

class WCLGetRankingsRaidOnly(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Queueing updates...\n")
        update_wcl_raid_update()

class TestWCLGetRankingsRaid(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Queueing updates...\n")
        update_wcl_raid_update_subset(["Assassination Rogue"]) 

class WCLGenHTML(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Writing WCL HTML...\n")
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(write_spec_overviews, _retry_options=options)

class WCLRaidGenHTML(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Writing WCL HTML...\n")
        options = TaskRetryOptions(task_retry_limit = 1)
        deferred.defer(write_raid_spec_overviews, _retry_options=options)   
        

app = webapp2.WSGIApplication([
        ('/update_current_dungeons', UpdateCurrentDungeons),
        ('/generate_html', GenerateHTML),
        ('/only_generate_html', OnlyGenerateHTML),
        ('/view', TestView),
        ('/raid', TestRaidView),    
        ('/known_affixes', KnownAffixesShow),
        ('/update_wcl', WCLGetRankings),
        ('/generate_wcl_html', WCLGenHTML),
        ('/update_wcl_raid', WCLGetRankingsRaid),
        ('/only_update_wcl_raid', WCLGetRankingsRaidOnly),
        ('/generate_wcl_raid_html', WCLRaidGenHTML),
        ('/test/update_wcl', TestWCLGetRankings),
        ('/test/update_wcl_raid', TestWCLGetRankingsRaid),
        ], debug=True)
