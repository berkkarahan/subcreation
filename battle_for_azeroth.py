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


