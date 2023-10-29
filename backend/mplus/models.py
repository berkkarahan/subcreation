from django.db import models
from model_utils.fields import AutoLastModifiedField


# All current model fields will be nullable for now. Until I get a better grasp of what
# does APIs return and what can be done about them.
NULL_CHAR_FIELD = models.CharField(null=True)
NULL_FLOAT_FIELD = models.FloatField(null=True)
NULL_DATETIME_FIELD = models.DateTimeField(null=True)
NULL_INTEGER_FIELD = models.IntegerField(null=True)
NULL_JSON_FIELD = models.JSONField(null=True)
# Common fields
INT_PAGE_FIELD = models.IntegerField(default=0)


class ManagerMixin:
    objects = models.Manager()


class Run(ManagerMixin, models.Model):
    keystone_run_id = models.CharField(unique=True)
    roster = NULL_CHAR_FIELD
    score = NULL_FLOAT_FIELD
    completed_at = NULL_DATETIME_FIELD
    clear_time_ms = NULL_INTEGER_FIELD
    keystone_time_ms = NULL_INTEGER_FIELD
    mythic_level = NULL_INTEGER_FIELD
    num_chests = NULL_INTEGER_FIELD
    faction = NULL_CHAR_FIELD
    affix_region = models.ForeignKey(
        "DungeonAffixRegion", related_name="runs", on_delete=models.PROTECT
    )


class DungeonAffixRegion(ManagerMixin, models.Model):
    dar_slug = models.CharField(unique=True)

    # when were these data last updated
    last_updated = AutoLastModifiedField()

    # which dungeon
    dungeon = NULL_CHAR_FIELD
    # which affixes
    affixes = NULL_CHAR_FIELD
    # which region
    region = NULL_CHAR_FIELD
    # which page (valid values are 0-4)
    page = INT_PAGE_FIELD


class KnownAffixes(ManagerMixin, models.Model):
    affixes = NULL_CHAR_FIELD
    affixes_slug = models.CharField(unique=True)
    first_seen = NULL_DATETIME_FIELD
    last_seen = NULL_DATETIME_FIELD


# from wcl api
class SpecRankings(ManagerMixin, models.Model):
    spec = NULL_CHAR_FIELD
    dungeon = NULL_CHAR_FIELD
    page = INT_PAGE_FIELD
    rankings = NULL_JSON_FIELD


# storing affix specific tier lists
class DungeonEaseTierList(ManagerMixin, models.Model):
    affixes = NULL_CHAR_FIELD
    tier_list = NULL_JSON_FIELD
    last_updated = AutoLastModifiedField()
