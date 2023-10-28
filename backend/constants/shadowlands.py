import slugify

dungeons = ["Tazavesh: Streets of Wonder",
            "Tazavesh: So'leah's Gambit",
            "Operation Mechagon: Junkyard",
            "Operation Mechagon: Workshop",
            "Return to Karazhan: Upper",
            "Return to Karazhan: Lower",
            "Iron Docks",
            "Grimrail Depot"]            

dungeon_short_names = {}
dungeon_short_names["Tazavesh: Streets of Wonder"] = "STRT"
dungeon_short_names["Tazavesh: So'leah's Gambit"] = "GMBT"
dungeon_short_names["Operation Mechagon: Junkyard"] = "YARD"
dungeon_short_names["Operation Mechagon: Workshop"] = "WORK"
dungeon_short_names["Return to Karazhan: Upper"] = "UPPR"
dungeon_short_names["Return to Karazhan: Lower"] = "LOWR"
dungeon_short_names["Iron Docks"] = "ID"
dungeon_short_names["Grimrail Depot"] = "GD"

dungeon_slugs = []
for d in dungeons:
    dungeon_slugs += [slugify.slugify(str(d))]

slugs_to_dungeons = {}
for d in dungeons:
    slugs_to_dungeons[slugify.slugify(str(d))] = d

# no rotation, will just be a pass through when empty
tormented_weeks = {}

covenantID_mapping = {}
covenantID_mapping[1] = {"name" : "Kyrian",
                         "id" : 321076,
                         "icon" : "ui_sigil_kyrian.jpg"}
covenantID_mapping[2] = {"name" : "Venthyr",
                         "id" : 321079,
                         "icon" : "ui_sigil_venthyr.jpg"}
covenantID_mapping[3] = {"name" : "Night Fae",
                         "id" : 321077,
                         "icon" : "ui_sigil_nightfae.jpg"}
covenantID_mapping[4] = {"name" : "Necrolord",
                         "id" : 321078,
                         "icon" : "ui_sigil_necrolord.jpg"}

covenantNameToID = {}
for k, v in covenantID_mapping.iteritems():
    covenantNameToID[v["name"]] = v["id"]


# itemIds for shards of domination

shards_of_domination = ["187057", "187284", "187293", "187302", "187312", # bek - blood
                        "187059", "187285", "187294", "187303", "187313", # jas
                        "187061", "187286", "187295", "187304", "187314", # rev
                        "187063", "187287", "187296", "187305", "187315", # cor - frost
                        "187065", "187288", "187297", "187306", "187316", # kyr
                        "187071", "187289", "187298", "187307", "187317", # tel
                        "187073", "187290", "187299", "187308", "187318", # dyz
                        "187076", "187291", "187300", "187309", "187319", # oth
                        "187079", "187292", "187301", "187310", "187320", # zed
                        ]

t29_items = [188863, 188864, 188866, 188867, 188868, # dk
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
