import slugify


def icon_spec(dname, prefix="", size=56):
    dslug = slugify.slugify(str(dname))
    return (
        '<a href="%s.html"><img src="images/spec-icons/%s.jpg" width="%d" height="%d" title="%s" alt="%s" /><br/>%s</a>'
        % (prefix + dslug, dslug, size, size, dname, dname, dname)
    )


def icon_affix(dname, size=28):
    # This was just a function returning the input
    # dname = affix_rotation_affixes(dname)
    dslug = slugify.slugify(str(dname))

    def miniaffix(aname, aslug, size):
        return (
            '<img src="images/affixes/%s.jpg" class="zoom-icon" width="%d" height="%d" title="%s" alt="%s" />'
            % (aslug, size, size, aname, aname)
        )

    affixen = dname.split(", ")
    output = []

    for af in affixen:
        afname = af
        afslug = slugify.slugify(af)
        output += [miniaffix(afname, afslug, size=size)]

    output_string = output[0]
    output_string += output[1]
    output_string += output[2]

    return output_string


def pretty_affixes(affixes, size=16, no_text=False):
    from backend.mplus.selectors.mplus import affix_rotation_affixes

    if affixes == "All Affixes":
        return "All Affixes"

    output_string = ""
    if no_text:
        output_string = icon_affix(affixes, size=size)
    else:
        output_string = icon_affix(affixes, size=size) + " %s" % affix_rotation_affixes(
            affixes
        )
    return output_string
