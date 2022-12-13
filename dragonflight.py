import slugify

dungeons = ["Algeth'ar Academy",
            "Court of Stars",
            "Halls of Valor",
            "Ruby Life Pools",
            "Shadowmoon Burial Grounds",
            "Temple of the Jade Serpent",
            "The Azure Vault",
            "The Nokhud Offensive"]            

dungeon_short_names = {}
dungeon_short_names["Algeth'ar Academy"] = "AA"
dungeon_short_names["Court of Stars"] = "COS"
dungeon_short_names["Halls of Valor"] = "HOV"
dungeon_short_names["Ruby Life Pools"] = "RLP"
dungeon_short_names["Shadowmoon Burial Grounds"] = "SBG"
dungeon_short_names["Temple of the Jade Serpent"] = "JADE"
dungeon_short_names["The Azure Vault"] = "TAV"
dungeon_short_names["The Nokhud Offensive"] = "TNO"

dungeon_slugs = []
for d in dungeons:
    dungeon_slugs += [slugify.slugify(unicode(d))]

slugs_to_dungeons = {}
for d in dungeons:
    slugs_to_dungeons[slugify.slugify(unicode(d))] = d

t30_items = [188863, 188864, 188866, 188867, 188868, # dk
             188898, 188896, 188894, 188893, 188892, # dh
             188853, 188851, 188849, 188848, 188847, # druid
             188861, 188860, 188859, 188858, 188856, # hunter
             188845, 188844, 188843, 188842, 188839, # mage
             188916, 188914, 188912, 188911, 188910, # monk
             188933, 188932, 188931, 188929, 188928, # paladin
             188881, 188880, 188879, 188878, 188875, # priest  
             188901, 188902, 188903, 188905, 188907, # rogue
             188925, 188924, 188923, 188922, 188920, # shaman
             188942, 188941, 188940, 188938, 188937, # warrior
             188890, 188889, 188888, 188887, 188884, # warlock
            ]
