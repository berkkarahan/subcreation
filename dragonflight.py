import slugify

dungeons = ["Brackenhide Hollow",
            "Freehold",
            "Halls of Infusion",
            "Neltharion's Lair",
            "Neltharus",
            "The Underrot",
            "The Vortex Pinnacle",
            "Uldaman: Legacy of Tyr"]            

dungeon_short_names = {}
dungeon_short_names["Brackenhide Hollow"] = "BH"
dungeon_short_names["Freehold"] = "FH"
dungeon_short_names["Halls of Infusion"] = "HOI"
dungeon_short_names["Neltharion's Lair"] = "NL"
dungeon_short_names["Neltharus"] = "NELT"
dungeon_short_names["The Underrot"] = "UNDR"
dungeon_short_names["The Vortex Pinnacle"] = "VP"
dungeon_short_names["Uldaman: Legacy of Tyr"] = "ULD"

dungeon_slugs = []
for d in dungeons:
    dungeon_slugs += [slugify.slugify(unicode(d))]

slugs_to_dungeons = {}
for d in dungeons:
    slugs_to_dungeons[slugify.slugify(unicode(d))] = d



tier_items = [ ### aberrus tier
             202464, 202462, 202461, 202460, 202459, # dk
             202527, 202525, 202524, 202523, 202522, # dh
             202518, 202516, 202515, 202514, 202513, # druid
             202491, 202489, 202488, 202487, 202486, # evoker
             202482, 202480, 202479, 202478, 202477, # hunter
             202554, 202552, 202551, 202550, 202549, # mage
             202509, 202507, 202506, 202505, 202504, # monk
             202455, 202453, 202452, 202451, 202450, # paladin
             202543, 202542, 202541, 202545, 202540, # priest  
             202500, 202498, 202497, 202496, 202495, # rogue
             202473, 202471, 202470, 202469, 202468, # shaman
             202534, 202533, 202532, 202536, 202531, # warlock
             202446, 202444, 202443, 202442, 202441, # warrior
             ### vault tier
             200405, 200407, 200408, 200409, 200410, # dk
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


### ARCHIVE ###

# dungeons = ["Algeth'ar Academy",
#             "Court of Stars",
#             "Halls of Valor",
#             "Ruby Life Pools",
#             "Shadowmoon Burial Grounds",
#             "Temple of the Jade Serpent",
#             "The Azure Vault",
#             "The Nokhud Offensive"]            

# dungeon_short_names["Algeth'ar Academy"] = "AA"
# dungeon_short_names["Court of Stars"] = "COS"
# dungeon_short_names["Halls of Valor"] = "HOV"
# dungeon_short_names["Ruby Life Pools"] = "RLP"
# dungeon_short_names["Shadowmoon Burial Grounds"] = "SBG"
# dungeon_short_names["Temple of the Jade Serpent"] = "TJS"
# dungeon_short_names["The Azure Vault"] = "AV"
# dungeon_short_names["The Nokhud Offensive"] = "NO"

# t30_items = [200405, 200407, 200408, 200409, 200410, # dk
#              200342, 200344, 200345, 200346, 200347, # dh
#              200351, 200353, 200354, 200355, 200356, # druid
#              200378, 200380, 200381, 200382, 200383, # evoker
#              200387, 200389, 200390, 200391, 200392, # hunter
#              200315, 200317, 200318, 200319, 200320, # mage
#              200360, 200362, 200363, 200364, 200365, # monk
#              200414, 200416, 200417, 200418, 200419, # paladin
#              200326, 200327, 200328, 200324, 200329, # priest  
#              200369, 200371, 200372, 200373, 200374, # rogue
#              200396, 200398, 200399, 200400, 200401, # shaman
#              200335, 200336, 200337, 200333, 200338, # warlock
#              200423, 200425, 200426, 200427, 200428, # warrior
#             ]