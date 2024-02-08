# old models

from google.appengine.ext import ndb


# keep track of data pulls
class Pull(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add=True)


# keep track of which affixes are current in each region for a pull
class AffixSet(ndb.Model):
    pull = ndb.StructuredProperty(Pull)
    region = ndb.StringProperty(indexed=True)
    affixes = ndb.StringProperty(indexed=True)


# store all the runs
class Run(ndb.Model):
    pull = ndb.StructuredProperty(Pull)
    region = ndb.StringProperty(indexed=True)
    affixes = ndb.StringProperty(indexed=True)
    dungeon = ndb.StringProperty(indexed=True)
    characters = ndb.StringProperty(indexed=True, repeated=True)
    score = ndb.FloatProperty(indexed=False)
