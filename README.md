# mplus.subcreation.net

Source code for a site that used to show statistical analysis of M+ in WoW.

For a simpler version of the same idea, see https://github.com/alcaras/mplus-analysis

This code is what the site ran before it shutdown -- it's set up to run as an App Engine instance that runs a cron job that updates data and generates static HTML, writing directly to a Cloud Storage instance. A bit strange, but it scales quite nicely.

This hasn't been updated for 8.1 or any recent raider.io API changes, so may require some modification to get working.
