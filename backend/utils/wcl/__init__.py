from backend.constants.active_talents import class_active, spec_active
from backend.constants.config import MIN_KEY_LEVEL
from backend.constants.talent_ids import talent_id_class, talent_id_spec
from backend.mplus.models import SpecRankings, SubcreationConfig
from backend.utils.wcl.extracters import (
    wcl_extract_gear,
    wcl_extract_gems,
    wcl_extract_tier,
    wcl_extract_embellishments,
    wcl_extract_crafted,
    wcl_extract_essences,
    wcl_extract_enchants,
)
from backend.utils.wcl.talents import wcl_extract_talents, wcl_get_talent_strings
from backend.utils.wcl.utils import (
    identify_common_talents,
    remove_common_talents,
    canonical_talent_order,
)


def _wcl_parse(
    rankings,
    extractor,
    is_sorted=True,
    is_aggregated=True,
    only_use_ids=False,
    flatten=False,
):
    from backend.utils.wcl.parser import wcl_parse

    return wcl_parse(
        rankings,
        extractor,
        is_sorted=is_sorted,
        is_aggregated=is_aggregated,
        only_use_ids=only_use_ids,
        flatten=flatten,
    )


def wcl_gear(rankings, slots):
    is_sorted = True
    if 15 in slots:  # don't sort if there's an offhand
        is_sorted = False

    return _wcl_parse(
        rankings, lambda e: wcl_extract_gear(e, slots), is_sorted=is_sorted
    )


def wcl_gems(rankings):
    return _wcl_parse(rankings, wcl_extract_gems, only_use_ids=True, flatten=True)


def wcl_gem_builds(rankings):
    return _wcl_parse(rankings, wcl_extract_gems, only_use_ids=True)


def wcl_primordials(rankings):
    return _wcl_parse(
        rankings,
        lambda e: wcl_extract_gems(e, primordial=True),
        only_use_ids=True,
        flatten=True,
    )


def wcl_primordial_builds(rankings):
    return _wcl_parse(
        rankings, lambda e: wcl_extract_gems(e, primordial=True), only_use_ids=True
    )


def wcl_tier_items(rankings):
    return _wcl_parse(
        rankings, lambda e: wcl_extract_tier(e), only_use_ids=True, flatten=True
    )


def wcl_tier_builds(rankings):
    return _wcl_parse(rankings, lambda e: wcl_extract_tier(e), only_use_ids=True)


def wcl_embellished_items(rankings):
    return _wcl_parse(
        rankings,
        lambda e: wcl_extract_embellishments(e),
        only_use_ids=True,
        flatten=True,
    )


def wcl_embellished_builds(rankings):
    return _wcl_parse(
        rankings, lambda e: wcl_extract_embellishments(e), only_use_ids=True
    )


def wcl_crafted_items(rankings):
    return _wcl_parse(
        rankings, lambda e: wcl_extract_crafted(e), only_use_ids=True, flatten=True
    )


def wcl_crafted_builds(rankings):
    return _wcl_parse(rankings, lambda e: wcl_extract_crafted(e), only_use_ids=True)


def wcl_hsc(rankings):
    return _wcl_parse(
        rankings, lambda e: wcl_extract_gear(e, [0, 2, 4]), is_sorted=False
    )  # we want to show in helm, shoulders, chest order


def wcl_extract_azerite_powers(ranking, offsets):
    names_in_set = []
    name_id_icons = []
    for i, j in enumerate(ranking["azeritePowers"]):
        if i % 5 in offsets:
            names_in_set += [j["id"]]
            name_id_icons += [j]

    return names_in_set, name_id_icons


def wcl_primary(rankings):
    return _wcl_parse(rankings, lambda e: wcl_extract_azerite_powers(e, [0, 1]))


def wcl_role(rankings):
    return _wcl_parse(rankings, lambda e: wcl_extract_azerite_powers(e, [2]))


def wcl_defensive(rankings):
    return _wcl_parse(rankings, lambda e: wcl_extract_azerite_powers(e, [3]))


def wcl_essences(rankings):
    return _wcl_parse(rankings, wcl_extract_essences, is_sorted=False)


def wcl_talents(rankings, require_in=None):
    return _wcl_parse(
        rankings, lambda e: wcl_extract_talents(e, require_in), is_sorted=False
    )


def wcl_talents_top(rankings, require_in=None):
    return _wcl_parse(
        rankings,
        lambda e: wcl_extract_talents(e, require_in),
        is_sorted=False,
        flatten=True,
    )


def wcl_enchants(rankings, slots, type="permanentEnchant"):
    return _wcl_parse(
        rankings, lambda e: wcl_extract_enchants(e, slots, type), only_use_ids=True
    )


def gen_wcl_spec_report(spec, dungeon="all"):
    return base_gen_spec_report(spec, "mplus", dungeon)


def base_gen_spec_report(
    spec, mode, encounter="all", difficulty=MAX_RAID_DIFFICULTY, active_raid=""
):
    wcl_query = None

    if mode == "mplus":
        if encounter == "all":
            results = SpecRankings.objects.filter(spec=spec)
        else:
            results = SpecRankings.objects.filter(spec=spec, dungeon=encounter)
    elif mode == "raid":
        raise NotImplementedError("Raid analysis not implemented yet!")
        # if encounter == "all":
        #     wcl_query = SpecRankingsRaid.query(
        #         SpecRankingsRaid.spec == spec, SpecRankingsRaid.raid == active_raid
        #     )
        # else:
        #     wcl_query = SpecRankingsRaid.query(
        #         SpecRankingsRaid.spec == spec,
        #         SpecRankingsRaid.encounter == encounter,
        #         SpecRankingsRaid.raid == active_raid,
        #     )

    config_singleton = SubcreationConfig.load()
    last_updated = config_singleton.last_updated

    maxima = []
    n_parses = 0
    rankings = []

    available_difficulty = ""

    # add logs per difficulty per encounter
    mythic = {}
    heroic = {}
    normal = {}

    for k in results:
        if last_updated is None or k.last_updated > last_updated:
            config_singleton.set_last_updated(k.last_updated)

        # if mode == "raid":
        #     # filter out ignored encounters raid_ignore for all bosses
        #     if encounter == "all":
        #         raid_ignore = get_raid_ignore(active_raid)
        #         if k.encounter in raid_ignore:
        #             continue

        latest = k.rankings

        no_blanks = []
        # filter out reports that lack info (e.g. notalents)
        for kk in latest:
            if not kk["talents"]:
                continue
            no_blanks += [kk]

        latest = no_blanks

        # if mode == "mplus":
        filtered_latest = []
        for kk in latest:
            if kk["keystoneLevel"] < MIN_KEY_LEVEL:
                continue
            filtered_latest += [kk]

        rankings += filtered_latest
        # elif mode == "raid":
        #     if k.difficulty == "Mythic":
        #         if k.encounter not in mythic:
        #             mythic[k.encounter] = []
        #         mythic[k.encounter] += latest
        #     elif k.difficulty == "Heroic":
        #         if k.encounter not in heroic:
        #             heroic[k.encounter] = []
        #         heroic[k.encounter] += latest
        #     elif k.difficulty == "Normal":
        #         if k.encounter not in normal:
        #             normal[k.encounter] = []
        #         normal[k.encounter] += latest

    # if mode == "raid":
    #     # if it's all, go through encounter by c ounter
    #     # if it's a specific ecnounter
    #     if encounter == "all":
    #         seen_difficulties = set()
    #
    #         raid_encounters = get_raid_encounters(active_raid)
    #
    #         # go through encounter by encounter
    #         for k, v in raid_encounters.iteritems():
    #             if difficulty == "Mythic":
    #                 if k in mythic:
    #                     rankings += mythic[k]
    #                     seen_difficulties.add("Mythic")
    #                 elif k in heroic:
    #                     rankings += heroic[k]
    #                     seen_difficulties.add("Heroic")
    #                 elif k in normal:
    #                     rankings += normal[k]
    #                     seen_difficulties.add("Normal")
    #             elif difficulty == "Heroic":
    #                 if k in heroic:
    #                     rankings += heroic[k]
    #                     seen_difficulties.add("Heroic")
    #                 elif k in normal:
    #                     rankings += normal[k]
    #                     seen_difficulties.add("Normal")
    #
    #         canonical_order_difficulties = ["Mythic", "Heroic", "Normal"]
    #
    #         seen_difficulties_canonical = []
    #         for diff in canonical_order_difficulties:
    #             if diff in seen_difficulties:
    #                 seen_difficulties_canonical += [diff]
    #
    #         available_difficulty = " / ".join(seen_difficulties_canonical)
    #
    #     else:
    #         if difficulty == "Mythic":
    #             if mythic != [] and encounter in mythic:
    #                 rankings = mythic[encounter]
    #                 available_difficulty = "Mythic"
    #             elif heroic != [] and encounter in heroic:
    #                 rankings = heroic[encounter]
    #                 available_difficulty = "Heroic"
    #             else:
    #                 if encounter in normal:
    #                     rankings = normal[encounter]
    #                     available_difficulty = "Normal"
    #         elif difficulty == "Heroic":
    #             if heroic != [] and encounter in heroic:
    #                 rankings = heroic[encounter]
    #                 available_difficulty = "Heroic"
    #             else:
    #                 if encounter in normal:
    #                     rankings = normal[encounter]
    #                     available_difficulty = "Normal"

    unique_characters = set()
    for k in rankings:
        name_to_add = k["name"] + "-" + k["serverName"]
        unique_characters.add(name_to_add)
        if mode == "mplus":
            maxima += [k["keystoneLevel"]]

    n_uniques = len(unique_characters)

    # clean up difficulty display
    # a single boss should always be only one difficulty
    # this is for the all bosses view, where we might have a mix of
    # heroic and mythic bosses -- until all bosses are done on mythic for that spec

    items = {}
    spells = {}

    gear = {}

    gear_slots = []
    gear_slots += [["helms", [0]]]
    gear_slots += [["neck", [1]]]
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

    for slot_name, slots in gear_slots:
        gear[slot_name], update_items = wcl_gear(rankings, slots)
        items.update(update_items)

    # legendaries
    gear["legendaries"] = []

    gems, update_items = wcl_gems(rankings)
    items.update(update_items)

    gem_builds, update_items = wcl_gem_builds(rankings)
    items.update(update_items)

    # 9.2: bye bye shards
    # 10.0.7: hello primordials
    primordials = {}
    primordial_builds = {}
    primordials, update_items = wcl_primordials(rankings)
    items.update(update_items)

    primordial_builds, update_items = wcl_primordial_builds(rankings)
    items.update(update_items)

    tier_items, update_items = wcl_tier_items(rankings)
    items.update(update_items)

    tier_builds, update_items = wcl_tier_builds(rankings)
    items.update(update_items)

    embellished_items, update_items = wcl_embellished_items(rankings)
    items.update(update_items)

    embellished_builds, update_items = wcl_embellished_builds(rankings)
    items.update(update_items)

    crafted_items, update_items = wcl_crafted_items(rankings)
    items.update(update_items)

    crafted_builds, update_items = wcl_crafted_builds(rankings)
    items.update(update_items)

    enchants = {}
    enchant_ids = {}

    # slots are one LESS than what it is for macros because 0 indexing
    enchants["weapons"], update_enchant_ids = wcl_enchants(rankings, [15, 16])
    enchant_ids.update(update_enchant_ids)

    enchants["chests"], update_enchant_ids = wcl_enchants(rankings, [4])
    enchant_ids.update(update_enchant_ids)

    enchants["wrists"], update_enchant_ids = wcl_enchants(rankings, [8])
    enchant_ids.update(update_enchant_ids)

    enchants["leg"], update_enchant_ids = wcl_enchants(rankings, [6])
    enchant_ids.update(update_enchant_ids)

    enchants["feet"], update_enchant_ids = wcl_enchants(rankings, [7])
    enchant_ids.update(update_enchant_ids)

    enchants["cloaks"], update_enchant_ids = wcl_enchants(rankings, [14])
    enchant_ids.update(update_enchant_ids)

    enchants["rings"], update_enchant_ids = wcl_enchants(rankings, [10, 11])
    enchant_ids.update(update_enchant_ids)

    enchants["belts"], update_enchant_ids = wcl_enchants(
        rankings, [5], type="onUseEnchant"
    )
    enchant_ids.update(update_enchant_ids)

    max_maxima = 0
    min_maxima = 0

    if len(maxima) > 0:
        max_maxima = max(maxima)
        min_maxima = min(maxima)

    if mode == "raid":
        max_maxima = available_difficulty

    talents_container = {}
    talents_container["common"] = {}

    # wcl_parse returns [n, (talents), [[max_n, band, text, report]]]
    talents, update_spells = wcl_talents(rankings)
    talents_container["talents"] = talents
    spells.update(update_spells)
    talents_container["talents_string"] = wcl_get_talent_strings(
        talents, rankings, spec
    )

    talents_common = identify_common_talents(talents)
    talents = remove_common_talents(talents, talents_common)
    talents_container["common"]["talents"] = canonical_talent_order(
        list(talents_common)
    )

    #    talents_top, _ = wcl_talents_top(rankings, require_in=priority_talents)
    #    talents_container["top"] = talents_top
    #    talents_container["top_string"] = wcl_get_talent_strings(talents_top, rankings, spec)

    #    talents_priority, _ = wcl_talents(rankings, require_in=priority_talents)
    #    talents_container["priority"] = talents_priority
    #    talents_container["priority_string"] = wcl_get_talent_strings(talents_priority, rankings, spec)

    talents_class, _ = wcl_talents(rankings, require_in=talent_id_class)
    talents_container["class"] = talents_class
    talents_container["class_string"] = wcl_get_talent_strings(
        talents_class, rankings, spec
    )

    talents_class_common = identify_common_talents(talents_class)
    talents_class = remove_common_talents(talents_class, talents_class_common)
    talents_container["common"]["class"] = canonical_talent_order(
        list(talents_class_common)
    )

    talents_spec, _ = wcl_talents(rankings, require_in=talent_id_spec)
    talents_container["spec"] = talents_spec
    talents_container["spec_string"] = wcl_get_talent_strings(
        talents_spec, rankings, spec
    )

    talents_spec_common = identify_common_talents(talents_spec)
    talents_spec = remove_common_talents(talents_spec, talents_spec_common)
    talents_container["common"]["spec"] = canonical_talent_order(
        list(talents_spec_common)
    )

    talents_class_active, _ = wcl_talents(rankings, require_in=(class_active))
    talents_container["class_active"] = talents_class_active
    talents_container["class_active_string"] = wcl_get_talent_strings(
        talents_class_active, rankings, spec
    )

    talents_spec_active, _ = wcl_talents(rankings, require_in=(spec_active))
    talents_container["spec_active"] = talents_spec_active
    talents_container["spec_active_string"] = wcl_get_talent_strings(
        talents_spec_active, rankings, spec
    )

    # raid won't have a max_maxima and a min_maxima (could use dps but not much point)
    # raid will return available_difficulty in max_maxima
    return (
        len(rankings),
        n_uniques,
        max_maxima,
        min_maxima,
        talents_container,
        gear,
        enchants,
        gems,
        gem_builds,
        primordials,
        primordial_builds,
        spells,
        items,
        enchant_ids,
        tier_items,
        tier_builds,
        embellished_items,
        embellished_builds,
        crafted_items,
        crafted_builds,
    )
