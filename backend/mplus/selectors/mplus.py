from functools import cache

import slugify

from backend.constants.dragonflight import dungeons
from backend.constants.warcraft import regions


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
