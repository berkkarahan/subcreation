import slugify

from backend.mplus.selectors.warcraft import get_role_titles, get_spec_short_names
from backend.utils.analysis import ckmeans


def gen_spec_tier_list(specs_report, role, prefix="", api=False):
    role_titles = get_role_titles()

    scores = []
    for i in range(0, 4):
        for k in specs_report[role_titles[i]]:
            if (
                int(k[3]) < 20
            ):  # ignore specs with fewer than 20 runs as they would skew the buckets; we'll add them to F later
                continue
            scores += [float(k[0])]

    if len(scores) < 6:  # relax the fewer than 20 rule (early scans early in season)
        scores = []
        for i in range(0, 4):
            for k in specs_report[role_titles[i]]:
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
        for k in specs_report[role]:
            if len(buckets) > i:
                if float(k[0]) in buckets[i]:
                    if k not in added:
                        tiers[tm[i]] += [k]
                        added += [k]

    # add stragglers to last tier
    for k in specs_report[role]:
        if k not in added:
            tiers[tm[0]] += [k]
            added += [k]

    if api == False:
        dtl = {}
        dtl["S"] = ""
        dtl["A"] = ""
        dtl["B"] = ""
        dtl["C"] = ""
        dtl["D"] = ""
        dtl["F"] = ""

        spec_short_names = get_spec_short_names()
        template = env.get_template("spec-mini-icon.html")
        for i in range(0, 6):
            for k in tiers[tm[i]]:
                rendered = template.render(
                    spec_name=k[1],
                    spec_short_name=spec_short_names[k[1]],
                    spec_slug=slugify.slugify(str(k[1])),
                )
                dtl[tm[i]] += rendered

        return dtl
    else:
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
