from functools import cache

from backend.constants.aberrus import (
    aberrus_canonical_order,
    aberrus_short_names,
    aberrus_ignore,
)
from backend.constants.wcl_dragonflight import aberrus_encounters


@cache
def get_raid_encounters(_):
    return aberrus_encounters


@cache
def get_raid_canonical_order(_):
    return aberrus_canonical_order


@cache
def get_raid_short_names(_):
    return aberrus_short_names


@cache
def get_raid_ignore(_):
    return aberrus_ignore


@cache
def determine_raids_to_update(current_time=None):
    # rotate updating raids every day
    raids_to_update = ["aberrus"]
    return raids_to_update


@cache
def determine_raids_to_generate(current_time=None):
    # rotate updating raids every day
    raids_to_update = ["aberrus"]
    return raids_to_update
