blackboard_scraper
by Jason Giancono jasongi.com/blackboard-scraper
==================

Tool (with GUI) for easy downloading of lecture slides and other material from blackboard at UOIT

Blackboard Scraper: A tool for scraping unit material off Blackboard written in Python. Current functionality allows scraping of unit materials and scraping of iLectures if you visit the iLecture page and paste in the RSS feed link.

Using the program:

1) Log in by typing in your student ID and password. After loading, the fields should be populated with units and iLectures available to you on blackboard.

2) Choose the directory to download things to up the top.

3) To download unit materials select one or more item from the Blackboard Materials list and click Scrape. You can monitor the progress in the command window (it just lists the current link being downloaded). The filenames depend on what the lecturer names the link, so if they don't put in the file type, it won't have a file type. You can fix this by renaming, and I'll try to fix this in later versions.

4) To download ILectures, visit the iLecture site by clicking one and pressing Visit URL (You may need to be logged into blackboard in your browser for this). Go to the bottom left hand corner of the Echo360 screen where there is the RSS feed symbol, hover over it and press vodcast. Now copy the URL from the browser to the iLecture RSS field and press scrape. Progress is shown in the command window. This is an experimental feature and I'm trying to find other ways to automate this process.

# RoadMap - TheVella
In no particular order:

1) CLI or TUI for downloading on headless server, or as regular task

2) Asyncronous downloads with requests

3) Removal of selenium - May or may not be possible with current javascript filled blackboard

4) Usage of official blackboard api with a toggle

5) Download discussions in logical format

6) Interuptable downloads, skippable downloads

7) Reliable way to limit names/paths to those windows will accept without being useless.

I will continue to toddle away at this until I lose access to my school blackboard account, at which point I will archive this repository.
