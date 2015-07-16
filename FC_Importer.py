'''This library provides a loose collection of methods useful for tasks associated with the Wikipedia Signpost.
	Prerequisites to using this library:
	You must have the `pywikibot` package installed and set up.
	Furthermore it is recommended that you edit `user_config.py` directly to contain as many global definitions as possible, ae.:
	+ usernames['wikipedia']['*'] = u'Resident Mario'
	+ usernames['commons']['*'] = u'Resident Mario'
	+ ...'''

import pywikibot
import requests
import datetime

#############################
# SIGNPOST-SPECIFIC METHODS #
#############################

def getNextSignpostPublicationDate():
	'''SEEKER METHOD: Finds the next Signpost issue date.
		RETURNS: A datetime object corresponding to the date of the next issue's publication.'''
	data = getPurgedPageHTML('User:Resident Mario/pubdate')
	data = data[data.index('BOF') + 4:data.index('EOF') - 1]
	return datetime.datetime.strptime(data, '%Y-%m-%d')

def getNextSignpostPublicationString(ns=True):
	'''SEEKER METHOD: Returns the formatted string at which the next Signpost issue will be published.
		PARAMETERS:
		(opt) ns:				Whether or not to return the namespace (a.e. `Wikipedia:Wikipedia Signpost` or just `Wikipedia Signpost`). True by default.'''
	if ns:
		return 'Wikipedia:Wikipedia Signpost/' + getNextSignpostPublicationDate().strftime('%Y-%m-%d')
	else:
		return 'Wikipedia Signpost/' + getNextSignpostPublicationDate().strftime('%Y-%m-%d')

def getPreviousSignpostPublicationDate():
	'''SEEKER METHOD: Finds the previous Signpost issue date.
		RETURNS: A time object corresponding to the date of the previous issue's publication.'''
	return getNextSignpostPublicationDate() - datetime.timedelta(days=7)

def getPreviousSignpostPublicationString(ns=True):
	'''SEEKER METHOD: Returns the formatted string at which the previous Signpost issue was published.
		PARAMETERS:
		(opt) ns:				Whether or not to return the namespace (a.e. `Wikipedia:Wikipedia Signpost` or just `Wikipedia Signpost`). True by default.'''
	if ns:
		return 'Wikipedia:Wikipedia Signpost/' + getPreviousSignpostPublicationDate().strftime('%Y-%m-%d')
	else:
		return 'Wikipedia Signpost/' + getPreviousSignpostPublicationDate().strftime('%Y-%m-%d')

def getSignpostContents(pub_string):
	'''SEEKER METHOD: Sniffs and returns the contents of the Signpost issue for a certain date as a list.
		PARAMETERS:
		(req) pub_string:		The string-title to look for things in (e.g. `Wikipedia:Wikipedia Signpost/2015-04-09`)
		NOTE: To get the the sections of the latest issue use `getSignpostContents(getPreviousSignpostPublicationString(ns=False))`.'''
	return makeRawAPIQuery(action='query', list='allpages', apnamespace='4', apprefix=pub_string, aplimit=20)

########################
# GENERAL DATA METHODS #
########################

def getPageHTML(page, language='en', project='wikipedia'):
	'''SEEKER METHOD: Returns a page's HTML.
		PARAMETERS:
		(req) pub_string:		The string-title to look for things in (e.g. `Wikipedia:Wikipedia Signpost/2015-04-09`)
		NOTE: To get the the sections of the latest issue use `getSignpostContents(getPreviousSignpostPublicationString(ns=False))`.'''
	return requests.get('https://' + language + '.' + project + '.org/wiki/' + page).text

def getPurgedPageHTML(page, language='en', project='wikipedia'):
	'''SEEKER METHOD: Returns a page's HTML, differing from the method above in implementation.
		This method does not suffer from a particular page-purging problem that the above method has.
		PARAMETERS:
		(req) pub_string:		The string-title to look for things in (e.g. `Wikipedia:Wikipedia Signpost/2015-04-09`)
		NOTE: To get the the sections of the latest issue use `getSignpostContents(getPreviousSignpostPublicationString(ns=False))`.'''
	# page = pywikibot.Page(pywikibot.Site(language, project), page)
	# page.purge()
	# return page.expand_text()
	# The above should work if the below does not.
	return requests.get('https://' + language + '.' + project + '.org/w/index.php?title=' + page + '&action=purge&action=view').text

def getPageWikicode(page, language='en', project='wikipedia'):
	'''EXECUTION METHOD: Returns the wikicode contents of a wiki page.
		PARAMETERS:
		(req) page:			Page to return the contents of.
		(opt) language:		Language of the project, en is the default.
		(opt) project:		Project, wikipedia is the default.'''
	return requests.get('https://' + language + '.' + project + '.org/w/index.php?&action=raw&title=' + page).text

def htmlToWikitext(html):
	'''EXECUTION METHOD: A simple RESTBase API query method which converts HTML to Wikitext.
		PARAMETERS:
		(req) html:			HTML string to parse into wikicode.'''
	return requests.post('https://rest.wikimedia.org:443/en.wikipedia.org/v1/transform/html/to/wikitext', data={'html': html}).text

def makeRawAPIQuery(language='en', project='wikipedia', **_params):
	'''EXECUTION METHOD: A light wrapper of `pywikibot.data.api.Requests` that implements free-form JSON API queries.
		PARAMETERS:
		(opt) language:		Language of the project, en is the default.
		(opt) project:		Project, wikipedia is the default.
		(kwr) _params:		Additional parameters passed to the query.'''
	_site = pywikibot.Site(language, project)
	_params.update({'formatversion': '2', 'continue': ''})
	return pywikibot.data.api.Request(site=_site, **_params).submit()

def makeAPIQuery(language='en', project='wikipedia', **_params):
	'''EXECUTION METHOD: A heavy wrapper of `pywikibot.data.api.Requests` that makes use of the raw method above. Decapsulates requested data.
		NOTE: Currently only works for `query` requests.
		(opt) language:		Language of the project, en is the default.
		(opt) project:		Project, wikipedia is the default.
		(kwr) _params:		Additional parameters passed to the query.'''
	if 'action' in _params and _params['action'] == 'query':
		if 'prop' in _params:
			return makeRawAPIQuery(language, project, **_params)['query']['pages'][0][_params['prop']]
		elif 'list' in _params:
			return makeRawAPIQuery(language, project, **_params)['query'][_params['list']]

def prettyPrintQuery(list_of_dicts):
	'''EXECUTION METHOD: Pretty printer for a list of dictionaries of the type returned by an API query.'''
	print('[')
	for list_item in list_of_dicts:
		print(" {")
		for dict_item in list(list_item.keys()):
			print("  " + str(dict_item) + ": " + str(list_item[dict_item]))
		print(" },")
	print(']')

def saveContentToPage(content, target, editsummary, language='en', project='wikipedia'):
	'''EXECUTION METHOD: Writes the contents of a string to a page on a project.
		PARAMETERS:
		(req) content: 		Content to be written.
		(req) target:			Target page on the project.
		(req) editsummary:	Edit summary.
		(opt) language:		Language of the project, en is the default.
		(opt) project:		Project, wikipedia is the default.
		NOTE: pywikibot handles all writing. See also the note at the top of this file on setting up `user_config.py`.'''
	site = pywikibot.Site(language, project)
	page = pywikibot.Page(site, target)
	page.text = content
	page.save(editsummary)

print(getPurgedPageHTML('User:Resident Mario/sandbox'))
print(getNextSignpostPublicationDate())
