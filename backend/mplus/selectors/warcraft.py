from functools import cache


@cache
def get_role_titles():
    role_titles = {}
    role_titles[0] = "Tanks"
    role_titles[1] = "Healers"
    role_titles[2] = "Melee"
    role_titles[3] = "Ranged"
    return role_titles


@cache
def get_spec_short_names():
    spec_short_names = {}
    spec_short_names["Frost Mage"] = "Frost"
    spec_short_names["Balance Druid"] = "Bal"
    spec_short_names["Restoration Druid"] = "RDru"
    spec_short_names["Vengeance Demon Hunter"] = "VDH"
    spec_short_names["Windwalker Monk"] = "WW"
    spec_short_names["Destruction Warlock"] = "Destro"
    spec_short_names["Holy Paladin"] = "HPal"
    spec_short_names["Arms Warrior"] = "Arms"
    spec_short_names["Brewmaster Monk"] = "Brew"
    spec_short_names["Retribution Paladin"] = "Ret"
    spec_short_names["Discipline Priest"] = "Disc"
    spec_short_names["Outlaw Rogue"] = "Outlaw"
    spec_short_names["Restoration Shaman"] = "RSha"
    spec_short_names["Blood Death Knight"] = "BDK"
    spec_short_names["Havoc Demon Hunter"] = "Havoc"
    spec_short_names["Guardian Druid"] = "Bear"
    spec_short_names["Subtlety Rogue"] = "Sub"
    spec_short_names["Beast Mastery Hunter"] = "BM"
    spec_short_names["Mistweaver Monk"] = "Mist"
    spec_short_names["Protection Paladin"] = "ProtP"
    spec_short_names["Affliction Warlock"] = "Aff"
    spec_short_names["Enhancement Shaman"] = "Enh"
    spec_short_names["Shadow Priest"] = "SPriest"
    spec_short_names["Survival Hunter"] = "Surv"
    spec_short_names["Assassination Rogue"] = "Sin"
    spec_short_names["Frost Death Knight"] = "FDK"
    spec_short_names["Elemental Shaman"] = "Ele"
    spec_short_names["Fury Warrior"] = "Fury"
    spec_short_names["Holy Priest"] = "Holy"
    spec_short_names["Arcane Mage"] = "Arcane"
    spec_short_names["Unholy Death Knight"] = "UDK"
    spec_short_names["Feral Druid"] = "Feral"
    spec_short_names["Protection Warrior"] = "ProtW"
    spec_short_names["Demonology Warlock"] = "Demo"
    spec_short_names["Marksmanship Hunter"] = "MM"
    spec_short_names["Fire Mage"] = "Fire"
    spec_short_names["Devastation Evoker"] = "Dev"
    spec_short_names["Preservation Evoker"] = "Pres"
    spec_short_names["Augmentation Evoker"] = "Aug"
    return spec_short_names


@cache
def get_specs():
    return [
        "Frost Mage",
        "Balance Druid",
        "Restoration Druid",
        "Vengeance Demon Hunter",
        "Windwalker Monk",
        "Destruction Warlock",
        "Holy Paladin",
        "Arms Warrior",
        "Brewmaster Monk",
        "Retribution Paladin",
        "Discipline Priest",
        "Outlaw Rogue",
        "Restoration Shaman",
        "Blood Death Knight",
        "Havoc Demon Hunter",
        "Guardian Druid",
        "Subtlety Rogue",
        "Beast Mastery Hunter",
        "Mistweaver Monk",
        "Protection Paladin",
        "Affliction Warlock",
        "Enhancement Shaman",
        "Shadow Priest",
        "Survival Hunter",
        "Assassination Rogue",
        "Frost Death Knight",
        "Elemental Shaman",
        "Fury Warrior",
        "Holy Priest",
        "Arcane Mage",
        "Unholy Death Knight",
        "Feral Druid",
        "Protection Warrior",
        "Demonology Warlock",
        "Marksmanship Hunter",
        "Fire Mage",
        "Devastation Evoker",
        "Preservation Evoker",
        "Augmentation Evoker",
    ]


@cache
def get_tanks():
    return [
        "Vengeance Demon Hunter",
        "Brewmaster Monk",
        "Blood Death Knight",
        "Guardian Druid",
        "Protection Paladin",
        "Protection Warrior",
    ]


@cache
def get_healers():
    return [
        "Restoration Druid",
        "Holy Paladin",
        "Discipline Priest",
        "Restoration Shaman",
        "Mistweaver Monk",
        "Holy Priest",
        "Preservation Evoker",
    ]


@cache
def get_melee():
    return [
        "Windwalker Monk",
        "Arms Warrior",
        "Retribution Paladin",
        "Outlaw Rogue",
        "Havoc Demon Hunter",
        "Subtlety Rogue",
        "Enhancement Shaman",
        "Survival Hunter",
        "Assassination Rogue",
        "Frost Death Knight",
        "Fury Warrior",
        "Unholy Death Knight",
        "Feral Druid",
    ]


@cache
def get_ranged():
    return [
        "Frost Mage",
        "Balance Druid",
        "Destruction Warlock",
        "Beast Mastery Hunter",
        "Affliction Warlock",
        "Shadow Priest",
        "Elemental Shaman",
        "Arcane Mage",
        "Demonology Warlock",
        "Marksmanship Hunter",
        "Fire Mage",
        "Devastation Evoker",
        "Augmentation Evoker",
    ]
