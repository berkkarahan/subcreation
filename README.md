# mplus.subcreation.net

Source code for a site that used to show statistical analysis of M+ in WoW.

For a simpler version of the same idea, see https://github.com/alcaras/mplus-analysis

This code is what the site is currently running.

It's set up to run as an App Engine instance that runs a cron job that updates data and generates static HTML, writing directly to a Cloud Storage instance. A bit strange, but it scales quite nicely since it only ever serves static HTML pages externally.

CONTRIBUTING.md has details on how get a local version of the site running in case you'd like to do that so you locally test code before contributing to the site. Pull requests are welcome, though please do say hi on the discord: https://discord.gg/X8dyq67
