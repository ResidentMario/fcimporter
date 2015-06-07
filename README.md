# FC-Importer
A script that handles tedius setup tasks for the featured content report section of the Wikipedia Signpost.

<h2>About</h2>

The "Featured content report" (or the FC report, or FC, for short) is a report published as a part of the weekly "Wikipedia Signpost", a community-organized and -written internal newspaper on the English Wikipedia that covers the Wikipedia movement at large. FC reports on the status and contents of the various types of "Featured content" promoted on Wikipedia: featured articles, lists, portals, topics, and pictures.

Traditionally a part of the compliation process has always been visiting the nomination pages and transcribing the pages, the nominations, and the nominators, the first step to writing this report. This is a time-consuming and rather boring process that takes ~20-30 minutes of work a week on the part of the section's writers. This script eliminates this process for the section's writers by doing the same thing autonomously.

"Wikipedia:Goings-on" or a subpage of this page contains a user-maintained list of all content promoted in any particular week, going back all the way to 2010 or so. This script works by using a combination of API queries and raw page scrubbing to take a list of all articles promoted a certain week from this page, find and add nomination and nominator information, store it in a dictionary, and then do various text transforms to this information to output the requestively-formatted section information, in wikicode.

This script uses the requests library to simplify API request construction and retrieval and the pywikibot library to handle writing content to Wikipedia smoothly.

<h2>History</h2>

| Date  | Comment |
| ------------- | ------------- |
| 6/03/2015  | First version posted here. |
| 6/07/2015  | This documentation was written!  |
