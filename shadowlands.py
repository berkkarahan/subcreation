import slugify

dungeons = ["De Other Side",
            "Halls of Atonement",
            "Mists of Tirna Scithe",
            "Plaguefall",
            "Sanguine Depths",
            "Spires of Ascension",
            "The Necrotic Wake",
            "Theater of Pain"]

dungeon_short_names = {}
dungeon_short_names["De Other Side"] = "DOS"
dungeon_short_names["Halls of Atonement"] = "HOA"
dungeon_short_names["Mists of Tirna Scithe"] = "MISTS"
dungeon_short_names["Plaguefall"] = "PF"
dungeon_short_names["Sanguine Depths"] = "SD"
dungeon_short_names["Spires of Ascension"] = "SOA"
dungeon_short_names["The Necrotic Wake"] = "NW"
dungeon_short_names["Theater of Pain"] = "TOP"

dungeon_slugs = []
for d in dungeons:
    dungeon_slugs += [slugify.slugify(unicode(d))]

# no rotation, will just be a pass through when empty
prideful_weeks = {}

covenantID_mapping = {}
covenantID_mapping[1] = {"name" : "Kyrian",
                         "id" : 321076,
                         "icon" : ""}
covenantID_mapping[2] = {"name" : "Venthyr",
                         "id" : 321079,
                         "icon" : ""}
covenantID_mapping[3] = {"name" : "Night Fae",
                         "id" : 321077,
                         "icon" : ""}
covenantID_mapping[4] = {"name" : "Necrolord",
                         "id" : 321078,
                         "icon" : ""}




