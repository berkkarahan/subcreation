import logging

from backend.utils.talents import encode_talent_string
from backend.utils.wcl.utils import canonical_talent_order, wcl_find_report


def wcl_extract_talents(ranking, require_in=None):
    names_in_set = []
    name_id_icons = []

    for i, j in enumerate(ranking["talents"]):
        if j["talentID"] == 0:  # talents are now numbers, not strings
            continue

        talent_id = j["talentID"]

        if require_in != None:
            if talent_id not in require_in:
                continue

        names_in_set += [
            talent_id
        ]  # need to make it a string since every other id is a string
        name_id_icons += [j]

    return canonical_talent_order(names_in_set, require_in), name_id_icons


def wcl_get_talent_ids(ranking):
    talent_ids = {}
    points = 0
    for i, j in enumerate(ranking["talents"]):
        if "talentID" not in j:  # skip if we lack talent id info
            continue
        if j["talentID"] == 0:  # skip empty talents
            continue
        if "points" not in j:  # skip if we lack point info
            continue

        tid = j["talentID"]

        if tid not in talent_ids:
            talent_ids[tid] = 0
        talent_ids[tid] = j["points"]
        points += j["points"]

    #    logging.info(talent_ids)
    if points < 52:
        logging.info(
            "fewer than 52 points (only %d) in a talent string (%d, %d, %s)"
            % (points, ranking["class"], ranking["spec"], ranking["reportID"])
        )

    return talent_ids


def wcl_get_talent_strings(parsed, rankings, spec_name):
    talent_strings = []
    for k in parsed:
        if len(k) < 3:
            continue
        if len(k[2]) < 1:
            continue
        if len(k[2][0]) < 4:
            continue
        tid = wcl_get_talent_ids(wcl_find_report(k[2][0][3], k[2][0][4], rankings))
        if tid == {}:
            talent_strings += [""]  # no talent string available
            continue
        talent_strings += [encode_talent_string(tid, spec_name)]

    return talent_strings
