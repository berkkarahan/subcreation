import operator


def wcl_top10(d, pop=None, top_n=10):
    # consider sorting by key level / dps instead?
    dv = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
    output = []
    for i, (s, n) in enumerate(dv):
        if i >= top_n:
            break
        if pop == None:
            output += [[n, s, []]]
        else:
            output += [[n, s, pop[s]]]

    return output


def identify_common_talents(talents):
    talent_lists = []
    for k in talents:
        talent_lists += [k[1]]
    if len(talent_lists) > 0:
        common = set(talent_lists[0])
    else:
        common = set()
    for s in talent_lists[1:]:
        common.intersection_update(s)
    return set(common)


def canonical_talent_order(talent_ids, require_in=None):
    # talent_order has the talent order (using talent_ids!)
    from backend.constants.talent_ids import talent_id_order

    d = {k: v for v, k in enumerate(talent_id_order)}

    talent_ids.sort(key=d.get)

    filtered_talent_ids = []
    for tid in talent_ids:
        if require_in is not None:
            if tid not in require_in:
                continue
        filtered_talent_ids += [tid]

    return filtered_talent_ids


def remove_common_talents(talents, common):
    for k in talents:
        k[1] = tuple(canonical_talent_order(list(set(k[1]) - common)))
    return talents


def wcl_find_report(reportID, fightID, rankings):
    for v in rankings:
        if v["reportID"] == reportID:
            if v["fightID"] == fightID:
                return v
    return None
