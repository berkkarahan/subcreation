import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Optional

import slugify
from django.db import transaction, connection

from api_clients.rio import get_mplus_runs
from backend.mplus.models import KnownAffixes, Run, DungeonAffixRegion
from backend.constants import config
from backend.mplus.selectors.mplus import get_current_dungeons, get_regions


def known_affixes_update(affixes, affixes_slug) -> KnownAffixes:
    if obj := KnownAffixes.objects.filter(affixes_slug=affixes_slug).first():
        obj.save()
        return obj
    return KnownAffixes.objects.create(
        affixes_slug=affixes_slug,
        affixes=affixes,
    )


def run_create(
    individual_rio_ranking: dict, dungeon_affix_region: DungeonAffixRegion
) -> Optional[Run]:
    score = individual_rio_ranking["score"]
    run = individual_rio_ranking["run"]

    roster = []
    ksrid = ""
    completed_at = ""
    completed_at = datetime.datetime.strptime(
        run["completed_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    clear_time_ms = run["clear_time_ms"]
    mythic_level = run["mythic_level"]
    if mythic_level < config.MIN_KEY_LEVEL:  # only track runs at +16 or above
        return None
    num_chests = run["num_chests"]
    keystone_time_ms = run["keystone_time_ms"]
    faction = run["faction"]
    ksrid = str(run["keystone_run_id"])

    obj, _ = Run.objects.get_or_create(
        keystone_run_id=ksrid,
        affix_region=dungeon_affix_region,
        defaults={
            "score": score,
            "roster": roster,
            "completed_at": completed_at,
            "clear_time_ms": clear_time_ms,
            "mythic_level": mythic_level,
            "num_chests": num_chests,
            "keystone_time_ms": keystone_time_ms,
            "faction": faction,
        },
    )
    return obj


@transaction.atomic
def dungeon_affix_region_create(
    rio_rankings: list[dict], dungeon: str, affixes: str, region: str, page: int
) -> DungeonAffixRegion:
    dungeon_slug = slugify.slugify(str(dungeon))

    if affixes == "current":
        affixes = ""
        affixes += rio_rankings[0]["run"]["weekly_modifiers"][0]["name"] + ", "
        affixes += rio_rankings[0]["run"]["weekly_modifiers"][1]["name"] + ", "
        affixes += rio_rankings[0]["run"]["weekly_modifiers"][2]["name"]
        # R.I.P. Seasonal Affix
    #        affixes += data[0]["run"]["weekly_modifiers"][3]["name"]

    affixes_slug = slugify.slugify(str(affixes))
    known_affixes_update(affixes, affixes_slug)

    key_string = dungeon_slug + "-" + affixes_slug + "-" + region + "-" + str(page)
    obj, _ = DungeonAffixRegion.objects.update_or_create(
        dar_slug=key_string,
        defaults={
            "dungeon": dungeon,
            "affixes": affixes,
            "region": region,
            "page": page,
        },
    )

    for individual_ranking in rio_rankings:
        run_create(individual_ranking, obj)

    return obj


def update_region(dungeon, affixes, region, season=config.RIO_SEASON, page=0):
    dungeon_slug = slugify.slugify(str(dungeon))

    # NOT DOING ANY HACKY FIXES(cn is already no longer available)
    # if region == "cn" and affixes == "current":  # not working properly for cn
    #     affixes = current_affixes()

    affixes_slug = slugify.slugify(str(affixes))
    content = get_mplus_runs(season, region, affixes_slug, dungeon_slug, page)
    rankings = content["rankings"]
    if not rankings:
        logging.info(
            "no rankings found for %s / %s / %s / %s", dungeon, affixes, region, page
        )
        return

    dungeon_affix_region_create(rankings, dungeon, affixes, region, page)


def update_all():
    def _update_region(dungeon, affixes, region, season=config.RIO_SEASON, page=0):
        update_region(dungeon, affixes, region, season=season, page=page)
        connection.close()

    futures = []

    dungeons = get_current_dungeons()
    regions = get_regions()
    max_page = config.RIO_MAX_PAGE
    with ThreadPoolExecutor(max_workers=4) as exc:
        for region in regions:
            for dungeon in dungeons:
                for page in range(0, max_page):
                    futures.append(
                        exc.submit(
                            _update_region,
                            dungeon,
                            "current",
                            region,
                            season=config.RIO_SEASON,
                            page=page,
                        )
                    )

    # return when all threads complete
    wait(futures)
