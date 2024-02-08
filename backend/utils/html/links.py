import slugify


def known_affixes_links(prefix="", use_index=True):
    from backend.utils.html.components import icon_affix
    from backend.mplus.selectors.mplus import (
        affix_rotation_affixes,
        get_known_affixes,
        get_current_affixes,
    )

    known_affixes_list = get_known_affixes()
    known_affixes_report = []
    known_affixes_report += [["All Affixes", prefix + "all-affixes", ""]]
    for k in known_affixes_list:
        if use_index:
            if k == get_current_affixes():
                known_affixes_report += [
                    [affix_rotation_affixes(k), prefix + "index", icon_affix(k)]
                ]
            else:
                known_affixes_report += [
                    [
                        affix_rotation_affixes(k),
                        prefix + slugify.slugify(str(k)),
                        icon_affix(k),
                    ]
                ]

        else:
            known_affixes_report += [
                [
                    affix_rotation_affixes(k),
                    prefix + slugify.slugify(str(k)),
                    icon_affix(k),
                ]
            ]

    known_affixes_report.reverse()
    return known_affixes_report


def known_dungeon_links(affixes_slug, prefix=""):
    from backend.mplus.selectors.mplus import get_current_dungeons

    known_dungeon_list = get_current_dungeons()

    known_dungeon_report = []

    for k in known_dungeon_list:
        known_dungeon_report += [
            [k, prefix + slugify.slugify(str(k)) + "-" + affixes_slug]
        ]

    return known_dungeon_report


def known_specs_links(prefix=""):
    from backend.mplus.selectors.warcraft import (
        get_tanks,
        get_healers,
        get_melee,
        get_ranged,
    )
    from backend.utils.html.components import icon_spec

    tanks, healers, melee, ranged = (
        get_tanks(),
        get_healers(),
        get_melee(),
        get_ranged(),
    )
    known_specs_report = []
    for d in [sorted(tanks), sorted(healers), sorted(melee), sorted(ranged)]:
        for k in d:
            known_specs_report += [[k, slugify.slugify(str(k)), icon_spec(k, size=22)]]

    return known_specs_report


def known_specs_subset_links(subset, prefix=""):
    from backend.utils.html.components import icon_spec

    known_specs_report = []
    for d in [sorted(subset)]:
        for k in d:
            known_specs_report += [[k, slugify.slugify(str(k)), icon_spec(k, size=22)]]

    return known_specs_report
