import slugify

dungeons = ["Atal'dazar",
            "The Underrot",
            "Kings' Rest",
            "Temple of Sethraliss",
            "The MOTHERLODE!!",
            "Freehold",
            "Tol Dagor",
            "Waycrest Manor",
            "Siege of Boralus",
            "Shrine of the Storm",
            "Operation: Mechagon Junkyard",
            "Operation: Mechagon Workshop",]


dungeon_short_names = {}
dungeon_short_names["Atal'dazar"] = "AD"
dungeon_short_names["The Underrot"] = "UR"
dungeon_short_names["Kings' Rest"] = "KR"
dungeon_short_names["Temple of Sethraliss"] = "TOS"
dungeon_short_names["The MOTHERLODE!!"] = "ML"
dungeon_short_names["Freehold"] = "FH"
dungeon_short_names["Tol Dagor"] = "TD"
dungeon_short_names["Waycrest Manor"] = "WM"
dungeon_short_names["Siege of Boralus"] = "SOB"
dungeon_short_names["Shrine of the Storm"] = "SOTS"
dungeon_short_names["Operation: Mechagon Junkyard"] = "JY"
dungeon_short_names["Operation: Mechagon Workshop"] = "WS"

dungeon_slugs = []
for d in dungeons:
    dungeon_slugs += [slugify.slugify(unicode(d))]

regions = ["tw", "cn", "kr", "eu", "us"]

specs = [u'Frost Mage', u'Balance Druid', u'Restoration Druid', u'Vengeance Demon Hunter', u'Windwalker Monk', u'Destruction Warlock', u'Holy Paladin', u'Arms Warrior', u'Brewmaster Monk', u'Retribution Paladin', u'Discipline Priest', u'Outlaw Rogue', u'Restoration Shaman', u'Blood Death Knight', u'Havoc Demon Hunter', u'Guardian Druid', u'Subtlety Rogue', u'Beast Mastery Hunter', u'Mistweaver Monk', u'Protection Paladin', u'Affliction Warlock', u'Enhancement Shaman', u'Shadow Priest', u'Survival Hunter', u'Assassination Rogue', u'Frost Death Knight', u'Elemental Shaman', u'Fury Warrior', u'Holy Priest', u'Arcane Mage', u'Unholy Death Knight', u'Feral Druid', u'Protection Warrior', u'Demonology Warlock', u'Marksmanship Hunter', u'Fire Mage']


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

tanks =  [u'Vengeance Demon Hunter',
          u'Brewmaster Monk',
          u'Blood Death Knight',
          u'Guardian Druid',
          u'Protection Paladin',
          u'Protection Warrior']

healers = [u'Restoration Druid',
           u'Holy Paladin',
           u'Discipline Priest',
           u'Restoration Shaman',
           u'Mistweaver Monk',
           u'Holy Priest',]

melee = [u'Windwalker Monk',
         u'Arms Warrior',
         u'Retribution Paladin',
         u'Outlaw Rogue',
         u'Havoc Demon Hunter',
         u'Subtlety Rogue',
         u'Enhancement Shaman',
         u'Survival Hunter',
         u'Assassination Rogue',
         u'Frost Death Knight',
         u'Fury Warrior',
         u'Unholy Death Knight',
         u'Feral Druid',]

ranged = [u'Frost Mage',
          u'Balance Druid',
          u'Destruction Warlock',
          u'Beast Mastery Hunter',
          u'Affliction Warlock',
          u'Shadow Priest',
          u'Elemental Shaman',
          u'Arcane Mage',
          u'Demonology Warlock',
          u'Marksmanship Hunter',
          u'Fire Mage']

role_titles = {}
role_titles[0] = "Tanks"
role_titles[1] = "Healers"
role_titles[2] = "Melee"
role_titles[3] = "Ranged"


# season 3 only
beguiling_weeks = {}
beguiling_weeks["Tyrannical, Bursting, Skittish, Beguiling"] = "Enchanted"
beguiling_weeks["Fortified, Teeming, Quaking, Beguiling"] = "Tides"
beguiling_weeks["Tyrannical, Raging, Necrotic, Beguiling"] = "Void"
beguiling_weeks["Fortified, Bursting, Volcanic, Beguiling"] = "Enchanted"
beguiling_weeks["Tyrannical, Bolstering, Explosive, Beguiling"] =  "Tides"
beguiling_weeks["Fortified, Sanguine, Quaking, Beguiling"] = "Void"
beguiling_weeks["Tyrannical, Bursting, Necrotic, Beguiling"] = "Enchanted"
beguiling_weeks["Fortified, Bolstering, Skittish, Beguiling"] = "Tides"
beguiling_weeks["Tyrannical, Teeming, Volcanic, Beguiling"] = "Void"
beguiling_weeks["Fortified, Sanguine, Grievous, Beguiling"] = "Enchanted"
beguiling_weeks["Tyrannical, Raging, Explosive, Beguiling"] = "Tides"
beguiling_weeks["Fortified, Bolstering, Grievous, Beguiling"] = "Void"

# season 4 only
awakened_weeks = {}
awakened_weeks["Fortified, Bolstering, Skittish, Awakened"] = "A"
awakened_weeks["Tyrannical, Bursting, Necrotic, Awakened"] = "B"
awakened_weeks["Fortified, Sanguine, Quaking, Awakened"] = "B"
awakened_weeks["Tyrannical, Bolstering, Explosive, Awakened"] =  "A"
awakened_weeks["Fortified, Bursting, Volcanic, Awakened"] = "A"
awakened_weeks["Tyrannical, Raging, Necrotic, Awakened"] = "B"
awakened_weeks["Fortified, Teeming, Quaking, Awakened"] = "B"
awakened_weeks["Tyrannical, Bursting, Skittish, Awakened"] = "A"
awakened_weeks["Fortified, Bolstering, Grievous, Awakened"] = "A"
awakened_weeks["Tyrannical, Raging, Explosive, Awakened"] = "B"
awakened_weeks["Fortified, Sanguine, Grievous, Awakened"] = "B"
awakened_weeks["Tyrannical, Teeming, Volcanic, Awakened"] = "A"

affixes_short = {}
affixes_short["Fortified"] = "Fort"
affixes_short["Tyrannical"] = "Tyr"

affixes_short["Bursting"] = "Burst"
affixes_short["Bolstering"] = "Bolst"
affixes_short["Sanguine"] = "Sang"
affixes_short["Raging"] = "Rage"
affixes_short["Teeming"] = "Teem"

affixes_short["Necrotic"] = "Necr"
affixes_short["Quaking"] = "Quake"
affixes_short["Skittish"] = "Skit"
affixes_short["Grievous"] = "Griev"
affixes_short["Volcanic"] = "Volc"
affixes_short["Explosive"] = "Expl"

affixes_short["Awakened (A)"] = "A"
affixes_short["Awakened (B)"] = "B"



