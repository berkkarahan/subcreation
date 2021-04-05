from google.appengine.ext import ndb

# store all the runs
class Run(ndb.Model):
    roster = ndb.StringProperty(repeated=True)
    score = ndb.FloatProperty(indexed=False)
    keystone_run_id = ndb.StringProperty(indexed=False)
    completed_at = ndb.DateTimeProperty(indexed=False)
    clear_time_ms = ndb.IntegerProperty(indexed=False)
    keystone_time_ms = ndb.IntegerProperty(indexed=False)
    mythic_level = ndb.IntegerProperty(indexed=False)
    num_chests = ndb.IntegerProperty(indexed=False)
    faction = ndb.StringProperty(indexed=False)



# a set of 20 runs for a specific dungeon affix combo in a region
# now with pagination!
class DungeonAffixRegion(ndb.Model):
    # when were these data last updated
    last_updated = ndb.DateTimeProperty(auto_now_add=True)
   
    # which dungeon
    dungeon = ndb.StringProperty()
    # which affixes
    affixes = ndb.StringProperty()
    # which region
    region = ndb.StringProperty()
    # which page (valid values are 0-4)
    page = ndb.IntegerProperty()

    runs = ndb.LocalStructuredProperty(Run, repeated=True)

class KnownAffixes(ndb.Model):
    affixes = ndb.StringProperty()
    first_seen = ndb.DateTimeProperty(auto_now_add=True)
    last_seen = ndb.DateTimeProperty(auto_now=True)


# new: for storing rankings from wcl's api
class SpecRankings(ndb.Model):
    # which spec
    spec = ndb.StringProperty()
    dungeon = ndb.StringProperty()
    page = ndb.IntegerProperty()
    rankings = ndb.JsonProperty()

    # when were these data last updated
    last_updated = ndb.DateTimeProperty(auto_now_add=True)


    
# new: for storing rankings from wcl's api for raids
class SpecRankingsRaid(ndb.Model):
    # which spec
    spec = ndb.StringProperty()
    encounter = ndb.StringProperty()
    difficulty = ndb.StringProperty()
    page = ndb.IntegerProperty()
    rankings = ndb.JsonProperty()

    # when were these data last updated
    last_updated = ndb.DateTimeProperty(auto_now_add=True)


# for storing affix specific tier lists
class DungeonEaseTierList(ndb.Model):
    affixes = ndb.StringProperty()
    tier_list = ndb.JsonProperty()
    last_updated = ndb.DateTimeProperty(auto_now_add=True)    
    
# for storing high level raid data for making the tier list / cov list
class RaidSummary(ndb.Model):
    spec = ndb.StringProperty()
    encounter = ndb.StringProperty()
    difficulty = ndb.StringProperty()
    metric_distribution = ndb.JsonProperty()
    max_link = ndb.StringProperty() # max_link for an encounter

    # when were these data last updated
    last_updated = ndb.DateTimeProperty(auto_now_add=True)    
