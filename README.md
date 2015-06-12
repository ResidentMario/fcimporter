# FC-Importer
A script that handles tedius setup tasks for the featured content report section of the Wikipedia Signpost.

<h2>About</h2>

The "Featured content report" (or the FC report, or FC, for short) is a report published as a part of the weekly "Wikipedia Signpost", a community-organized and -written internal newspaper on the English Wikipedia that covers the Wikipedia movement at large. FC reports on the status and contents of the various types of "Featured content" promoted on Wikipedia: featured articles, lists, portals, topics, and pictures.

Traditionally a part of the compliation process has always been visiting the nomination pages and transcribing the pages, the nominations, and the nominators, the first step to writing this report. This is a time-consuming and rather boring process that takes ~20-30 minutes of work a week on the part of the section's writers. This script eliminates this process for the section's writers by doing the same thing autonomously.

"Wikipedia:Goings-on" or a subpage of this page contains a user-maintained list of all content promoted in any particular week, going back all the way to 2010 or so. This script works by using a combination of API queries and raw page scrubbing to take a list of all articles promoted a certain week from this page, find and add nomination and nominator information, store it in a dictionary, and then do various text transforms to this information to output the requestively-formatted section information, in wikicode.

This script uses the requests library to simplify API request construction and retrieval and the pywikibot library to handle writing content to Wikipedia smoothly.

<h2>Input</h2>

Running this script directly requires:
* Installation of Python 3 and its availability from the directory in which this script is run.
* Installation and proper configuration of the pywikibot package and its availability from the directory in which the script is run.

Currently I am running this script manually on my own machine on a weekly basis. I am working on making it available remotely from Wikimedia Labs.

The simplest and most usual way to run the script is to run it without any parameters at all:

    run FC-Importer.py

The script will seek out and draw content from the most recent archived WP:GO page it can find by working backwards from the current date as of the day that the script is run.

If you wish to display some additional information during runtime, for debugging purposes, you can use the "-d" parameter:

    run FC-Importer.py -d

Unfortunately debugging remains poorly implemented, however, and this will not generate as much useful information as it ought to. Beautiful debugging is on the to-do list.

Instead of running on the most recent findable page you can you run on a subpage of your choosing (but be aware of the limitations discussed in the section below). For instance:

    run FC-Importer.py -p "Wikipedia:Goings-on/March 2, 2014"

By default the script throws the content at my sandbox, "User:Resident Mario/sandbox", for testing purposes. To have the script splash the proper Signpost subpage instead, use the "-t" parameter:

    run FC-Importer.py -t "Wikipedia:Wikipedia Signpost/2015-06-17/Featured_content

And of course you can combine these three options in one execution:

    run FC-Importer.py -t "Wikipedia:Wikipedia Signpost/2015-06-17/Featured_content -p "Wikipedia:Goings-on/March 15, 2015" -d

<h2>Limitations</h2>

This script has a number of important limitations that are worth taking into account in regular use.

* This script is written for and meant to be used with the most recent WP:GO pages available. Support for the input of older archived pages was added primarily for testing purposes, to catch as many as possible of the bugs that can occur. Although the script can nominally be executed on any archived WP:GO pages, it may fail on execution with increasing possibility as you try to run it on archives further back in history. The last time a major change in nomination formatting occurred was in late 2011---at this point this script will begin to reliably fail.
* Because of a lack of standardization amongst the featured nomination processes, mining them for information is a difficult task in general. The script catches and accounts for the most common errors and ambiguities that occur in peoples' nominations, but when working not with data but with raw HTML it is nonetheless impossible to catch every possible error that will occur. Thus expect this script will still occassionally fail when it encounters a new and unexpected 'quirk' in peoples' nomination formatting. Please bring these errors up with the author: most are easily accounted for once discovered (though some are not).
* Oftentimes the script will not be able to find a certain piece of information. In these cases it will print a non-fatal warning and continue execution after writing in '???' for that particular piece of information, necessitating the that the user input that info manually.
* Certain kinds of username formatting will cause the script to return garbled output as a page's "nominator". This should be easy to spot and fix manually, and is akin to the '???' that the script returns in other such instances. The difference is that because of peoples' freedom of expression (specifically, freedom to do what they please with their username signatures) there's no obvious way to tell when a username is breaking or being returned incorrectly or not.
* A known limitation: because of the way that the script is written, a file that has been renamed since its nomination will reliably break the script.
* A known limitation: because of substandard standardization even by the standards of the featured content processes, to find the nominaters for featured topics and featured portals this script finds and returns the first username that appears on those pages. This will cause it to fail to return the correct (or fully correct) output in cases when there are co-nominators present. Thought the script will be in the right 95% of the time, featured portals and featured topics ought to still be checked by the writers to make sure everything is in the right.
* The page target has to be in the domain of the Wikipedia Signpost (ae. a subpage of "Wikipedia:Wikipedia Signpost").

<h2>History</h2>

| Date  | Comment |
| ------------- | ------------- |
| 6/03/2015  | First version posted here. |
| 6/07/2015  | This documentation was written!  |
