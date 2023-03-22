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
dungeon_short_names["Temple of the Jade Serpent"] = "TJS"
dungeon_short_names["The Azure Vault"] = "AV"
dungeon_short_names["The Nokhud Offensive"] = "NO"

dungeon_slugs = []
for d in dungeons:
    dungeon_slugs += [slugify.slugify(unicode(d))]

slugs_to_dungeons = {}
for d in dungeons:
    slugs_to_dungeons[slugify.slugify(unicode(d))] = d

t30_items = [200405, 200407, 200408, 200409, 200410, # dk
             200342, 200344, 200345, 200346, 200347, # dh
             200351, 200353, 200354, 200355, 200356, # druid
             200378, 200380, 200381, 200382, 200383, # evoker
             200387, 200389, 200390, 200391, 200392, # hunter
             200315, 200317, 200318, 200319, 200320, # mage
             200360, 200362, 200363, 200364, 200365, # monk
             200414, 200416, 200417, 200418, 200419, # paladin
             200326, 200327, 200328, 200324, 200329, # priest  
             200369, 200371, 200372, 200373, 200374, # rogue
             200396, 200398, 200399, 200400, 200401, # shaman
             200335, 200336, 200337, 200333, 200338, # warlock
             200423, 200425, 200426, 200427, 200428, # warrior
            ]

embellished_items = [
    191623, 191985, 190522, 190523, 190526, 190519, # Plate
    193463, 193460, 193465, 193462, 193461, 193459, 193464, 193466, # Mail
    193452, 193457, 193458, 193451, 193454, 193456, 193455, 193494, 193453, # Leather
    193524, 193513, 193521, 193512, 193537, 193527, 193532, 193525, 193536, 193520, 193526, 193530, # Cloth
    193001, 193002, # Jewelry
    193496, 192081, 194894, # Weapons
]

primordial_stones = [
    # Fire
    "204002", "204003", "204004", "204005",
    # Frost
    "204010", "204011", "204012", "204013",
    # Earth
    "204006", "204007", "204009",
    # Nature
    "204000", "204001", "204020", "204022", "204030",
    # Arcane
    "204014", "204018", "204019", "204025",
    # Shadow
    "204015", "204029",
    # Necro
    "204021", "204027",
]
