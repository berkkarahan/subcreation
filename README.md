# mplus.subcreation.net

Source code for a site that used to show statistical analysis of M+ in WoW.

For a simpler version of the same idea, see https://github.com/alcaras/mplus-analysis

This code is what the site ran before it shutdown -- it's set up to run as an App Engine instance that runs a cron job that updates data and generates static HTML, writing directly to a Cloud Storage instance. A bit strange, but it scales quite nicely.

This hasn't been updated for 8.1 or any recent raider.io API changes, so may require some modification to get working.

There's also some crufty code that came from changing the database structure midway (and having to migrate from old to new since the r.io API didn't, at the time, allow calling back to an arbitrary week) -- old_models and models.py, for example. You can likely safely remove that code.
