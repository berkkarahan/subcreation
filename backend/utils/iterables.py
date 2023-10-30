def canonical_order(s):
    from backend.mplus.selectors.warcraft import (
        get_tanks,
        get_healers,
        get_melee,
        get_ranged,
    )

    # given a list, return a tuple in canonical order
    output = []
    ta = []
    he = []
    me = []
    ra = []

    for c in s:
        if c in get_tanks():
            ta += [c]
        if c in get_healers():
            he += [c]
        if c in get_melee():
            me += [c]
        if c in get_ranged():
            ra += [c]

    output += sorted(ta) + sorted(he) + sorted(me) + sorted(ra)
    return tuple(output)


def pretty_set(s):
    output_string = ""
    for k in s:
        output_string += '<td class="comp %s">%s</td>' % (k, k)
    return output_string
