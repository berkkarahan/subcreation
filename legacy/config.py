

# raider.io api configuration
RIO_MAX_PAGE = 25

# need to update in templates/stats_table.html
# need to update in templates/compositions.html
# need to update in templates/navbar.html
RIO_SEASON = "season-df-2" 

# used for m+
# this is a season partition, so usually this is 1
# unless the season has been partitioned (rarely happens)
WCL_SEASON = 1

# used for raid
WCL_PARTITION = 4

# config
RAID_NAME = "Aberrus, the Shadowed Crucible"

# for heroic week, set this to 10
# after that in the season, set this at 16
MIN_KEY_LEVEL = 16

# to generate a tier list based on heroic week data
# have to manually toggle this
MAX_RAID_DIFFICULTY = "Mythic"
#MAX_RAID_DIFFICULTY = "Heroic"

import datetime

# patch times in UTC, god help us because of mktime
# used for filtering out logs using old talents
# do not change the times, just year, month, date

# tuesday
latest_patch_us = datetime.datetime(2023, 9, 5, 16, 0) #0 date
latest_patch_eu = datetime.datetime(2023, 9, 6, 4, 0)  #+1 date
# wednesday
latest_patch_tw = datetime.datetime(2023, 9, 6, 23, 0) #+1 date
latest_patch_kr = datetime.datetime(2023, 9, 6, 23, 0) #+1 date
