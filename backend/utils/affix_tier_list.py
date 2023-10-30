from backend.mplus.selectors.mplus import get_current_affixes
from backend.utils.analysis import ckmeans


def render_affix_tier_list_api(tiers, tm):
    dtl = {}
    dtl["S"] = []
    dtl["A"] = []
    dtl["B"] = []
    dtl["C"] = []
    dtl["D"] = []
    dtl["F"] = []

    for i in range(0, 6):
        for k in tiers[tm[i]]:
            dtl[tm[i]] += [k[1]]

    return dtl


def render_affix_tier_list(tiers, tm, api=False):
    if api is True:
        return render_affix_tier_list_api(tiers, tm)

    dtl = {}
    dtl["S"] = ""
    dtl["A"] = ""
    dtl["B"] = ""
    dtl["C"] = ""
    dtl["D"] = ""
    dtl["F"] = ""

    template = env.get_template("affix-mini-icon.html")
    template_all = env.get_template("affixes-mini-icons.html")
    for i in range(0, 6):
        for k in tiers[tm[i]]:
            affixen = k[1].split(", ")
            current_set = get_current_affixes()
            this_set = k[1]
            affix_set = ""

            slug_link = slugify.slugify(k[1])
            if current_set in this_set:
                slug_link = "index"

            for each_affix in affixen:
                rendered = template.render(
                    affix_slug=slugify.slugify(each_affix), affix_name=each_affix
                )
                affix_set += rendered

            dtl[tm[i]] += template_all.render(affix_link=slug_link, affix_set=affix_set)

    return dtl


def gen_affix_tier_list(affixes_report, api=False):
    if len(affixes_report) < 6:
        return gen_affix_tier_list_small(affixes_report, api=api)

    # ckmeans
    scores = []
    for k in affixes_report:
        scores += [float(k[0])]

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
        for k in affixes_report:
            if float(k[0]) in buckets[i]:
                if k not in added:
                    if tm[i] not in tiers:
                        tiers[tm[i]] = []
                    tiers[tm[i]] += [k]
                    added += [k]

        # add stragglers to last tier
    for k in affixes_report:
        if k not in added:
            if tm[0] not in tiers:
                tiers[tm[0]] = []
            tiers[tm[0]] += [k]
            added += [k]

    return render_affix_tier_list(tiers, tm, api=api)


def gen_affix_tier_list_small(affixes_report, api=False):
    # super simple tier list -- figure out the max and the min, and then bucket tiers
    cimax = -1
    cimin = -1

    for k in affixes_report:
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
        for k in affixes_report:
            if float(k[0]) >= (cimax - cistep * (i + 1)):
                if k not in added:
                    if tm[i] not in tiers:
                        tiers[tm[i]] = []
                    tiers[tm[i]] += [k]
                    added += [k]

    # add stragglers to last tier
    for k in affixes_report:
        if k not in added:
            if tm[5] not in tiers:
                tiers[tm[5]] = []
            tiers[tm[5]] += [k]
            added += [k]

    return render_affix_tier_list(tiers, tm, api=api)
