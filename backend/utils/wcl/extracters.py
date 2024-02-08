import logging

from backend.constants.dragonflight import (
    primordial_stones,
    tier_items,
    embellished_items,
    crafted_items,
)
from backend.constants.enchants import enchant_collapse


def wcl_generic_extract(ranking, category):
    names_in_set = []
    name_id_icons = []
    if category not in ranking:
        return [], []

    for i, j in enumerate(ranking[category]):
        names_in_set += [j["id"]]
        name_id_icons += [j]

    return names_in_set, name_id_icons


# extract gear a single ranking
def wcl_extract_gear(ranking, slots):
    names_in_set = []
    name_id_icons = []
    for i, j in enumerate(ranking["gear"]):
        if i in slots:
            names_in_set += [j["id"]]
            name_id_icons += [j]

    return names_in_set, name_id_icons


def wcl_extract_gems(ranking, primordial=False):
    names_in_set = []
    name_id_icons = []

    for i, j in enumerate(ranking["gear"]):
        if "gems" in j:
            for each_gem in j["gems"]:
                if primordial:  # filter just to primordial
                    if each_gem["id"] not in primordial_stones:
                        continue
                else:  # filter out primordials
                    if each_gem["id"] in primordial_stones:
                        logging.info("filtering out primordials")
                        continue
                names_in_set += [each_gem["id"]]
                name_id_icons += [each_gem]

    return names_in_set, name_id_icons


def wcl_extract_tier(ranking):
    names_in_set = []
    name_id_icons = []

    for i, j in enumerate(ranking["gear"]):
        if "id" in j:
            if j["id"] in tier_items:
                names_in_set += [j["id"]]
                name_id_icons += [j]

    return names_in_set, name_id_icons


def wcl_extract_embellishments(ranking):
    names_in_set = []
    name_id_icons = []

    for i, j in enumerate(ranking["gear"]):
        if "id" in j:
            if j["id"] in embellished_items:
                names_in_set += [j["id"]]
                name_id_icons += [j]

    return names_in_set, name_id_icons


def wcl_extract_crafted(ranking):
    names_in_set = []
    name_id_icons = []

    for i, j in enumerate(ranking["gear"]):
        if "id" in j:
            if j["id"] in crafted_items:
                names_in_set += [j["id"]]
                name_id_icons += [j]

    return names_in_set, name_id_icons


def wcl_extract_essences(ranking):
    names_in_set = []
    name_id_icons = []
    if "essencePowers" not in ranking:
        return [], []

    essences = []
    for i, j in enumerate(ranking["essencePowers"]):
        if i != 1:  # skip the major's minor
            essences += [j["id"]]
            name_id_icons += [j]

    major = essences[0]
    minors = sorted(essences[1:])
    names_in_set = [major] + minors

    return names_in_set, name_id_icons


def wcl_extract_enchants(ranking, slots, type="permanentEnchant"):
    names_in_set = []
    name_id_icons = []
    for i, j in enumerate(ranking["gear"]):
        if i in slots:
            if type in j:
                enchant_id = j[type]
                # collapse lower ranks into the highest rank
                if enchant_id in enchant_collapse:
                    enchant_id = enchant_collapse[enchant_id]
                names_in_set += [enchant_id]
                name_id_icons += [{"id": enchant_id}]

    return names_in_set, name_id_icons
