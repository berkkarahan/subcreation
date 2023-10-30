def gen_dungeon_tier_list(dungeons_report):
    scores = []

    for k in dungeons_report:
        scores += [float(k[0])]

    if len(dungeons_report) < 6:
        # for some reason we're seeing fewer than 6 dungeons
        # might be early in the week, etc.
        return gen_dungeon_tier_list_small(dungeons_report)

    buckets = ckmeans(scores, 6)

    added = []

    tiers = {}
    tm = {}
    tm[5] = "S"
    tm[4] = "A"
    tm[3] = "B"
    tm[2] = "C"
    tm[1] = "D"
    tm[0] = "F"

    for i in range(0, 6):
        tiers[tm[i]] = []

    for i in range(0, 6):
        for k in dungeons_report:
            if float(k[0]) in buckets[i]:
                if k not in added:
                    if tm[i] not in tiers:
                        tiers[tm[i]] = []
                    tiers[tm[i]] += [k]
                    added += [k]

    # add stragglers to last tier
    for k in dungeons_report:
        if k not in added:
            if tm[0] not in tiers:
                tiers[tm[0]] = []
            tiers[tm[0]] += [k]
            added += [k]

    return render_dungeon_tier_list(tiers, tm)


def gen_dungeon_tier_list_small(dungeons_report):
    # super simple tier list -- figure out the max and the min, and then bucket tiers
    cimax = -1
    cimin = -1

    for k in dungeons_report:
        if cimax == -1:
            cimax = float(k[0])
        if cimin == -1:
            cimin = float(k[0])
        if float(k[0]) < cimin:
            cimin = float(k[0])
        if float(k[0]) > cimax:
            cimax = float(k[0])

    cirange = cimax - cimin
    cistep = cirange / 6

    added = []

    tiers = {}
    tm = {}
    tm[0] = "S"
    tm[1] = "A"
    tm[2] = "B"
    tm[3] = "C"
    tm[4] = "D"
    tm[5] = "F"

    for i in range(0, 6):
        tiers[tm[i]] = []

    for i in range(0, 6):
        for k in dungeons_report:
            if float(k[0]) >= (cimax - cistep * (i + 1)):
                if k not in added:
                    if tm[i] not in tiers:
                        tiers[tm[i]] = []
                    tiers[tm[i]] += [k]
                    added += [k]

    # add stragglers to last tier
    for k in dungeons_report:
        if k not in added:
            if tm[5] not in tiers:
                tiers[tm[5]] = []
            tiers[tm[5]] += [k]
            added += [k]

    return render_dungeon_tier_list(tiers, tm)


def render_dungeon_tier_list(tiers, tm):
    dtl = {}
    dtl["S"] = ""
    dtl["A"] = ""
    dtl["B"] = ""
    dtl["C"] = ""
    dtl["D"] = ""
    dtl["F"] = ""

    global dungeon_short_names
    template = env.get_template("dungeon-mini-icon.html")

    for i in range(0, 6):
        for k in tiers[tm[i]]:
            rendered = template.render(
                dungeon_slug=k[4],
                dungeon_name=k[1],
                dungeon_short_name=dungeon_short_names[k[1]],
            )
            dtl[tm[i]] += rendered

    return dtl
