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
            "Shrine of the Storm"]

dungeon_slugs = []
for d in dungeons:
    dungeon_slugs += [slugify.slugify(unicode(d))]

regions = ["tw", "kr", "eu", "us"]

specs = [u'Frost Mage', u'Balance Druid', u'Restoration Druid', u'Vengeance Demon Hunter', u'Windwalker Monk', u'Destruction Warlock', u'Holy Paladin', u'Arms Warrior', u'Brewmaster Monk', u'Retribution Paladin', u'Discipline Priest', u'Outlaw Rogue', u'Restoration Shaman', u'Blood Death Knight', u'Havoc Demon Hunter', u'Guardian Druid', u'Subtlety Rogue', u'Beast Mastery Hunter', u'Mistweaver Monk', u'Protection Paladin', u'Affliction Warlock', u'Enhancement Shaman', u'Shadow Priest', u'Survival Hunter', u'Assassination Rogue', u'Frost Death Knight', u'Elemental Shaman', u'Fury Warrior', u'Holy Priest', u'Arcane Mage', u'Unholy Death Knight', u'Feral Druid', u'Protection Warrior', u'Demonology Warlock', u'Marksmanship Hunter', u'Fire Mage']

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

