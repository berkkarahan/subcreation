# Setting up your local dev enviroment

0. Ensure you have python 2.7 Installed. https://www.python.org/downloads/release/python-2716/

1. Download the Google Cloud SDK. https://cloud.google.com/sdk/docs/install-sdk

2. Install the App Engine SDK. Make sure you grab the Python 2.7 version. You can follow the steps here: https://cloud.google.com/appengine/docs/standard/python/setting-up-environment

Note on Python 2.7: I am aware it is past end-of-life. Unfortunately some AppEngine libraries (notably taskqueue) are NOT a clean 1:1 substitution to move to Python 3. I'm considering whether I want to move to non-AppEngine architecture or another language entirely, but as that is a significant undertaking (i.e. rewrite of the site) for now we have the status quo.

# Running Subcreation locally

1. `git clone https://github.com/alcaras/mplus.subcreation.net/`

2. `cd mplus.subcreation.net`

3. Make sure your path is referencing a Python 2.7 compatible version of pip, then run
```
   mkdir lib
   pip install -r requirements.txt -t lib 
```
 
   More details at https://cloud.google.com/appengine/docs/standard/python/tools/using-libraries-python-27
   
   If you encounter issues getting the Google Cloud Storage library working, https://cloud.google.com/appengine/docs/standard/python/googlecloudstorageclient/setting-up-cloud-storage may be able to help.
   
4. You'll need to create an auth.py file for API keys. Here's an empty file to start with:

```
api_key = ""

cloudflare_api_key = ""

cloudflare_zone = ""

ludus_access_key = ""
```

if you just want m+ tier lists, you can leave this file as is, as the raider.io api doesn't require any api keys

api_key refers to the warcraft logs api key, which you'll need to provide if youwant to pull information from the WCL v1 api

cloudflare api keys shouldn't matter unless you're deploying the site somewhere (I use them to update caching once a page is updated)

the ludus_access_key is for updating from ludus lab's pvp api; you'll need to ask ludus labs to see if they'd be willing to provide a key

2. In the mplus.subcreation.net folder, run `dev_appserver ./`

You should see something like this:
```
INFO     2022-03-15 19:47:12,122 devappserver2.py:309] Skipping SDK update check.
INFO     2022-03-15 19:47:24,006 api_server.py:383] Starting API server at: http://localhost:51640
INFO     2022-03-15 19:47:24,061 dispatcher.py:267] Starting module "default" running at: http://localhost:8080
INFO     2022-03-15 19:47:24,062 admin_server.py:150] Starting admin server at: http://localhost:8000
INFO     2022-03-15 19:47:26,094 instance.py:294] Instance PID: 23580
```

3. If you go to http://localhost:8000 you should see a Google App Engine page.

4. If you go to http://localhost:8080 you should get a 404 page.

# Getting test data (raider.io)

1. Let's start with raider.io's API first. http://localhost:8080/test/affixes

This will query raider.io for leaderboards across regions / dungeons. It's a full data read for now, so please don't spam this or r.io will rate limit you.

2. You should now be able to go to http://localhost:8080/view and see some data

# Getting test data (wcl dungeons)

0. You'll need to obtain a WCL api key and add it to auth.py

1. Go to http://localhost:8080/test/dungeons

This will pull data for Havoc Demon Hunters for all current dungeons. You can edit which spec this pulls by editing TestWCLGetRankings.get() in mplus.py.

2. You should now able see http://localhost:8080/view?goto=havoc-demon-hunter.html

Note: You have to use the dropdown menus to navigate, as the tier list icons don't include view prefix.

# Getting test data (wcl raids)

0. You'll need to obtain a WCL api key and add it to auth.py

1. Go to http://localhost:8080/test/raids

This will pull data for Havoc Demon Hunters for the current raid. You can edit which spec this pulls by editing TestWCLGetRankingsRaid.get() in mplus.py.

2. You should now be able to see http://localhost:8080/raid?goto=havoc-demon-hunter.html (note the raid instead of view in the URL)

4. You should now be able to see http://localhost:8080/main?goto=top-covenants.html (note main instead of view or raid in the URL) as well, but it'll only have data for Havoc Demon Hunters (or whatever spec you included in step 1).

3. You'll also be able to go http://localhost:8080/raid but everything will be in F tier. 

To fix this, you'll need to refresh raids (replace test in the URL above with refresh). Note this is a LOT of queries toward WCL, so make sure you don't run this too often or WCL will rate limit you. You can check your rate limit at the bottom of https://www.warcraftlogs.com/profile

Once you that runs (it will take a while), you can /process/raid_counts on localhost:8080 -- this will crunch the numbers to generate the raid tier lists

Note: Once again, you have to use the dropdown menus to navigate, as the tier list icons don't include the view prefix.

# Questions?

Thanks for your interest in contributing. The easiest place to get answers to your questions is on the discord: https://discord.gg/X8dyq67
