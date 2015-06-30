# signpostlib.py
# This library provides a loose collection of methods useful for tasks associated with the Wikipedia Signpost.
# Prerequisites to using this library:
# You must have the `pywikibot` package installed and set up.
# Furthermore it is recommended that you edit `user_config.py` directly to contain as many global definitions as possible, ae.:
# + usernames['wikipedia']['*'] = u'Resident Mario'
# + usernames['commons']['*'] = u'Resident Mario'
# + ...

import pywikibot
import requests
import datetime

#############################
# SIGNPOST-SPECIFIC METHODS #
#############################

# SEEKER METHOD: Finds the next Signpost issue date.
# RETURNS: A datetime object corresponding to the date of the next issue's publication.
def getNextSignpostPublicationDate():
	data = getPageHTML('User:Resident Mario/pubdate')
	data = data[data.index('BOF') + 4:data.index('EOF') - 1]
	return datetime.datetime.strptime(data, '%Y-%m-%d')

# SEEKER METHOD: Returns the formatted string at which the next Signpost issue will be published.
# PARAMETERS:
# (opt) ns:				Whether or not to return the namespace (a.e. `Wikipedia:Wikipedia Signpost` or just `Wikipedia Signpost`). True by default.
def getNextSignpostPublicationString(ns=True):
	if ns:
		return 'Wikipedia:Wikipedia Signpost/' + getNextSignpostPublicationDate().strftime('%Y-%m-%d')
	else:
		return 'Wikipedia Signpost/' + getNextSignpostPublicationDate().strftime('%Y-%m-%d')

# SEEKER METHOD: Finds the previous Signpost issue date.
# RETURNS: A time object corresponding to the date of the previous issue's publication.
def getPreviousSignpostPublicationDate():
	return getNextSignpostPublicationDate() - datetime.timedelta(days=7)

# SEEKER METHOD: Returns the formatted string at which the previous Signpost issue was published.
# PARAMETERS:
# (opt) ns:				Whether or not to return the namespace (a.e. `Wikipedia:Wikipedia Signpost` or just `Wikipedia Signpost`). True by default.
def getPreviousSignpostPublicationString(ns=True):
	if ns:
		return 'Wikipedia:Wikipedia Signpost/' + getPreviousSignpostPublicationDate().strftime('%Y-%m-%d')
	else:
		return 'Wikipedia Signpost/' + getPreviousSignpostPublicationDate().strftime('%Y-%m-%d')

# SEEKER METHOD: Sniffs and returns the contents of the Signpost issue for a certain date as a list.
# PARAMETERS:
# (req) pub_string:		The string-title to look for things in (e.g. `Wikipedia:Wikipedia Signpost/2015-04-09`)
# NOTE: To get the the sections of the latest issue use `getSignpostContents(getPreviousSignpostPublicationString(ns=False))`.
def getSignpostContents(pub_string):
	return makeRawAPIQuery(action='query', list='allpages', apnamespace='4', apprefix=pub_string, aplimit=20)

########################
# GENERAL DATA METHODS #
########################

# EXECUTION METHOD: Returns the HTML contents of a wiki page.
# PARAMATERS:
# (req) page:			Page to return the contents of.
# (opt) language:		Language of the project, en is the default.
# (opt) project:		Project, wikipedia is the default.
def getPageHTML(page, language='en', project='wikipedia'):
	return requests.get('https://' + language + '.' + project + '.org/wiki/' + page).text

# EXECUTION METHOD: Returns the wikicode contents of a wiki page.
# PARAMETERS:
# (req) page:			Page to return the contents of.
# (opt) language:		Language of the project, en is the default.
# (opt) project:		Project, wikipedia is the default.
def getPageWikicode(page, language='en', project='wikipedia'):
	return requests.get('https://' + language + '.' + project + '.org/w/index.php?&action=raw&title=' + page).text

# EXECUTION METHOD: A simple RESTBase API query method which converts HTML to Wikitext.
# PARAMETERS:
# (req) html:			HTML string to parse into wikicode.
def htmlToWikitext(html):
	return requests.post('https://rest.wikimedia.org:443/en.wikipedia.org/v1/transform/html/to/wikitext', data={'html': html}).text

# EXECUTION METHOD: A light wrapper of `pywikibot.data.api.Requests` that implements free-form JSON API queries.
# PARAMETERS:
# (opt) language:		Language of the project, en is the default.
# (opt) project:		Project, wikipedia is the default.
# (kwr) _params:		Additional parameters passed to the query.
def makeRawAPIQuery(language='en', project='wikipedia', **_params):
	_site = pywikibot.Site(language, project)
	_params.update({'formatversion': '2', 'continue': ''})
	return pywikibot.data.api.Request(site=_site, **_params).submit()

# EXECUTION METHOD: A heavy wrapper of `pywikibot.data.api.Requests` that makes use of the raw method above. Decapsulates requested data.
# NOTE: Currently only works for `query` requests.
# (opt) language:		Language of the project, en is the default.
# (opt) project:		Project, wikipedia is the default.
# (kwr) _params:		Additional parameters passed to the query.
def makeAPIQuery(language='en', project='wikipedia', **_params):
	if 'action' in _params and _params['action'] == 'query':
		if 'prop' in _params:
			return makeRawAPIQuery(language, project, **_params)['query']['pages'][0][_params['prop']]
		elif 'list' in _params:
			return makeRawAPIQuery(language, project, **_params)['query'][_params['list']]

# EXECUTION METHOD: Pretty printer for a list of dictionaries of the type returned by an API query.
def prettyPrintQuery(list_of_dicts):
	print('[')
	for list_item in list_of_dicts:
		print(" {")
		for dict_item in list(list_item.keys()):
			print("  " + str(dict_item) + ": " + str(list_item[dict_item]))
		print(" },")
	print(']')

# EXECUTION METHOD: Writes the contents of a string to a page on a project.
# PARAMETERS:
# (req) content: 		Content to be written.
# (req) target:			Target page on the project.
# (req) editsummary:	Edit summary.
# (opt) language:		Language of the project, en is the default.
# (opt) project:		Project, wikipedia is the default.
# NOTE: pywikibot handles all writing. See also the note at the top of this file on setting up `user_config.py`.
def saveContentToPage(content, target, editsummary, language='en', project='wikipedia'):
	site = pywikibot.Site(language, project)
	page = pywikibot.Page(site, target)
	page.text = content
	page.save(editsummary)

##############
# TEST STACK #
##############

# print(makeAPIQuery('Thomas Edison', 'categories'))
# saveContentToPage(content='Test', target='User:Resident Mario/sandbox', editsummary='Test')
# print(htmlToWikitext('<b>Test</b>'))
# print(getPageData('Wikipedia:Wikipedia Signpost/Issue'))
# print(getNextSignpostPublicationDate())
# print(getPreviousSignpostPublicationDate())
# print(getNextSignpostPublicationString())
# print(getPreviousSignpostPublicationString())
# print(getPageWikicode('Paris'))
# print(makeAPIQuery(project='meta', action='query', prop='links', titles='Tech/News/Latest'))
# print(makeAPIQuery(project='meta', action='query', list='alllinks', alfrom='B', alprop='ids|title'))
# print(getPreviousSignpostPublicationString(ns=False))
# print(getSignpostContents(getPreviousSignpostPublicationString(ns=False)))
# print("Done.")
