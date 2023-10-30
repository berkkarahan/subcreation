from functools import cache
from typing import Optional

import slugify

from backend.constants.config import RIO_MAX_PAGE, MIN_KEY_LEVEL
from backend.constants.dragonflight import dungeons
from backend.constants.warcraft import regions
from backend.mplus.models import (
    KnownAffixes,
    SubcreationConfig,
    DungeonAffixRegion,
    Run,
)


def affix_rotation_affixes(val):
    # this was just returning the original value so its never implemented
    return val


def get_current_dungeons():
    return dungeons


@cache
def get_current_dungeon_slugs():
    dungeon_slugs = []
    for d in get_current_dungeons():
        dungeon_slugs += [slugify.slugify(str(d))]
    return dungeon_slugs


@cache
def get_slugs_to_dungeons():
    slugs_to_dungeons = {}
    for d in get_current_dungeons():
        slugs_to_dungeons[slugify.slugify(str(d))] = d
    return slugs_to_dungeons


def get_regions():
    return regions


def get_current_affixes():
    qs = KnownAffixes.objects.order_by("-last_seen", "-first_seen")[:1]
    obj: KnownAffixes = qs[0]
    return obj.affixes


def get_known_affixes():
    known_affixes = []
    qs = KnownAffixes.objects.order_by("first_seen")
    for obj in qs:
        if not obj.affixes:
            continue
        known_affixes += [obj.affixes]
    return known_affixes


def generate_counts(affixes="All Affixes", dungeon="all", spec="all"):
    from backend.mplus.selectors.warcraft import get_specs
    from backend.utils.iterables import canonical_order

    dungeons = get_current_dungeons()
    regions = get_regions()
    specs = get_specs()
    last_updated = SubcreationConfig.load().last_updated

    affixes_to_get = [affixes]
    if affixes == "All Affixes":
        affixes_to_get = get_known_affixes()

    dungeon_counts = {}
    spec_counts = {}
    set_counts = {}
    th_counts = {}  # tank healer
    dps_counts = {}  # just dps
    affix_counts = {}  # compare affixes to each other (
    dung_spec_counts = {}  # spec per dungeons

    for s in specs:
        spec_counts[s] = []

    for d in dungeons:
        dung_spec_counts[d] = {}
        for s in specs:
            dung_spec_counts[d][s] = []

    for affix in affixes_to_get:
        affixes_slug = slugify.slugify(str(affix))
        for region in regions:
            for dung in dungeons:
                for page in range(0, RIO_MAX_PAGE):
                    dungeon_slug = slugify.slugify(str(dung))
                    key_string = (
                        dungeon_slug
                        + "-"
                        + affixes_slug
                        + "-"
                        + region
                        + "-"
                        + str(page)
                    )
                    dar: Optional[
                        DungeonAffixRegion
                    ] = DungeonAffixRegion.objects.filter(dar_slug=key_string).first()

                    if not dar:
                        continue

                    if last_updated is None or dar.last_updated > last_updated:
                        SubcreationConfig.set_last_updated(dar.last_updated)

                    run: Run
                    for run in dar.runs.all():
                        if (
                            run.mythic_level < MIN_KEY_LEVEL
                        ):  # don't count runs under a +16
                            continue

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
                                    if (
                                        ch in spec_counts
                                    ):  # handle "fire paladin" errors
                                        spec_counts[ch] += [run]
                                        dung_spec_counts[dung][ch] += [run]

    return (
        dungeon_counts,
        spec_counts,
        set_counts,
        th_counts,
        dps_counts,
        affix_counts,
        dung_spec_counts,
    )
