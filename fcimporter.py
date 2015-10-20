'''FC-Importer.py
	This script handles tedious setup tasks for the featured content report section of the Wikipedia Signpost.
	Note that the fcimporter.py script in the signpostlab repository is a copy of this script.'''

import pywikibot
import sys
import requests
import json
import datetime
import signpostlib

####################
# ARGUMENT PARSING #
####################
#
# TODO:	 These two methods would be better handled by the argparse library.
#

def setGOPage():
	'''	ARGUMENT PARSING METHOD: A method to check the command line to see if a target argument has been provided.
		Returns either the new target, or resets the base target if none is provided.
		The base target is the most recent subpage of "Wikipedia:Goings-on", set by the helper method getPreviousGODateString().'''
	i = 1
	while i < len(sys.argv):
		if sys.argv[i].startswith(('-p', '-page')):
			if sys.argv[i + 1].startswith('Wikipedia:Goings-on'):
				return sys.argv[i + 1]
			else:
				raise NameError("The optional argument '-p' allows you to specify pages besides the base 'Wikipedia:Goings-on' for putting together by the script. However, this argument expects arguments of a specific form: 'python FC-Importer -p Wikipedia:Goings-on/November_2,_2008', for instance. Please make sure your argument conforms to this.")
		i += 1
	return getPreviousGODateString()

def setContentTargetPage():
	'''ARGUMENT PARSING METHOD: A method which sets to page that which the content is to be written---the target.
		This method is restricted to my own namespace and to pages within the Signpost domain.'''
	i = 1
	while i < len(sys.argv):
		if sys.argv[i].startswith(('-t', '-target')):
			if sys.argv[i + 1].startswith('Wikipedia:Wikipedia Signpost/') or sys.argv[i + 1].startswith('User:Resident Mario/'):
				return sys.argv[i + 1]
			else:
				raise NameError("The optional argument '-t' allows you to specify pages besides the base (Resident Mario's sandbox) for putting together by the script. However, this argument expects arguments of a specific form: 'python FC-Importer -t Wikipedia:Wikipedia Signpost/Newsroom/Test', for instance. It must always be a page within the Signpost's namespace. Please make sure your argument conforms to this.")
		i += 1
	return signpostlib.getNextSignpostPublicationString() + '/Featured content'

####################
# ABSTRACT METHODS #
####################
#
# These methods do simple stuff---whatever it reads on the tin. They are all helpers meant to be used within execution methods.
#

def getListOfUniqueUsersFromData(data):
	'''PARSER HELPER METHOD: This method takes as input an HTML string and outpus any and all usernames linked to within that string.
	1. A space is searched for as the terminating character of the username (<a href> form). In wikicode, we would instead look for | or ]].
	2. Every second item that is found is removed as a duplicate.
	3. Links to user subpages, such as `User:Resident Mario/blah`, are also removed.'''
	ret = []
	# Populate the list.
	while 'User:' in data:
		p = data[data.index('User:'):]
		p = p[:p.index(' ') - 1]
		ret.append(p)
		data = data[data.index('User:') + 5:]
	i = 1
	# Pop id duplicates.
	while i < len(ret):
		ret.pop(i)
		i += 1
	# Clean up duplicates.
	for user in ret:
		if ret.count(user) > 1:
			ret.remove(user)
	# Remove tunneled links containing "/", which are sometimes picked up but not wanted.
	for user in ret:
		if '/' in user:
			ret.remove(user)
	return ret

def makeCreatorString(creator):
	'''CONTENT HELPER METHOD: Parses a linked creator string and returns it properly formatted based on the presence or absense of the magic character `$` and of the string `User`.'''
	if 'User:' in creator:
		return '[[' + creator + '|]]'
	elif creator[0] == '$':
		return '[[' + creator[1:] + '|]]'
	else:
		return creator

def makeContributorsStringFromList(list_param):
	'''CONNTENT HELPER METHOD: Converts a list of contributors into a contribution string formatted for inclusion in FC.'''
	for i in range(0, len(list_param)):
		list_param[i] = removeUnderscoresFromUsername(list_param[i])
		list_param[i] = removeRedLinkedUsernames(list_param[i])
	ret = ''
	if len(list_param) == 1:
		ret = '[[' + list_param[0] + '|]]'
	elif len(list_param) == 0:
		return '???'
	else:
		for i in range(0, len(list_param) - 1):
			ret += '[[' + list_param[i] + '|]]' + ', '
		ret += 'and [[' + list_param[len(list_param) - 1] + '|]]'
	if ret.count(',') <= 1:
		ret = ret.replace(',', '')
	if ret == '[[|]]':
		ret = '???'
	return ret

def removeRedLinkedUsernames(name):
	'''CONTENT HELPER METHOD: Removes red-linking strings in a username ahead of the link's conversion to wikicode.'''
	ret = name
	if '&amp;action=edit&amp;redlink=1' in ret:
		ret = ret[0:ret.index('&amp;action=edit&amp;redlink=1')]
	return ret

def removeUnderscoresFromUsername(name):
	'''CONTENT HELPER METHOD: Removes underscores ('_') from amongst usernames. Care must be taken not to take away leading or trailing underscores; hence the relative complexity.'''
	ret = name
	if '_' in name:
		for i in range(1, len(name) - 1):
			if ret[i] == '_' and ret[i - 1] != '_' and ret[i + 1] != '_':
				ret = ret[0:i] + ' ' + ret[i + 1:len(name)]
	return ret

def getPreviousGODate():
	'''API HELPER METHOD: Returns the date of the most recent archived WP:GO report, accessed, for maintainability, via a query against a page in my namespace online.'''
	data = signpostlib.getPurgedPageHTML('User:Resident Mario/godate')
	data = data[data.index('BOF') + 4:data.index('EOF') - 1]
	datestring = datetime.datetime.strptime(data, '%Y-%m-%d')
	return datestring

def getPreviousGODateString(ns=True):
	'''API HELPER METHOD: A method which returns the most recent WP:GO subpage, the one that is to be used by the featured content report.'''
	datestring = getPreviousGODate().strftime('%B %d, %Y')
	# Need to remove the leading zero inserted by `%d`.
	datestring = datestring[:len(datestring) - 5].replace('0', '') + datestring[len(datestring) - 5:]
	if ns == False:
		return datestring
	else:
		return 'Wikipedia:Goings-on/' + datestring

def getDateRangeString():
	'''WRITER HELPER METHOD: Returns the date range string that is used to report the time period covered by the report.'''
	return getPreviousGODate().strftime('%d %B') + ' to ' + (getPreviousGODate() + datetime.timedelta(days=7)).strftime('%d %B')

def extractFeaturedContentOfOneType(list_param, content_type):
	'''DICTIONARY HELPER METHOD: An extraction method that returns a list of dicts associated with one specific featured content type.
	This is used to de-glob the work that needs to be done in generating the output string.'''
	ret = []
	for i in range(0, len(list_param)):
		if list_param[i]['type'] == content_type:
			ret.append(list_param[i])
	return ret

def stripSubpage(string):
	'''DICTIONARY HELPER METHOD: Strips content before colons and slashes out of a string. Used as a text transform in writeContentStringForFeaturedContentType().
		Used to generate a link, so that we can get the simplest linking possible: either [[James Franco|]], not [[James Franco|James Franco]].
		And [[Wikipedia:Featured topics/Overview of Lorde|Overview of Lorde]], not [[Wikipedia:Featured topics/Overview of Lorde|Featured topics/Overview of Lorde]].'''
	while ':' in string:
		string = string[string.index(':') + 1:]
	while '/' in string:
		string = string[string.index('/') + 1:]
	return string

###################
# RAW API METHODS #
###################
#
# These are deprecated in favor of methods in `signpostlib.py` and should be removed and replaced in the future.
# But this will be difficult and tedious, and so it remains to be done...

def requestData(api_request_parameters):
	'''API HELPER METHOD: A method to construct API requests with. Takes a dictionary of request parameters, returns the text of the query.
		This method uses the requests library to handle concatenating the API request string and actually retrieving the data.'''
	r = requests.get("https://en.wikipedia.org/w/api.php?", params=api_request_parameters)
	return json.loads(r.text)

def stripAPIData(query, type):
	'''API HELPER METHOD: A helper method which strips API data to get to the "core".
		This method is meant to be called on the results of a requestData() call.
		It takes two parameters. One is the query, the other is the type of data being requested (for passing through the final layer).'''
	query = query['query']
	query = query['pages']
	page_id_key = list(query.keys())
	query = query[page_id_key[0]]
	query = query[type]
	return query

def getFeaturedContentCandidateLinks():
	'''API EXECUTION METHOD: A method which uses the requestData method to get a list of links from the Goings-on page.
		This method is used to get all of the featured articles, lists, portals, and pictures.
		It does not retrieve featured topics, which are currently gotten more hackily:
		Featured topic candidates are instead retrieved directly via scrubbing the raw HTML, in a seperate loop.'''
	return signpostlib.makeAPIQuery(action='query', titles=target, format='json', prop='links', pllimit='500', plnamespace='0|6|100')

#
# TODO: Rewrite `getFeaturedTopicsList()` to use a continued link query to find out what featured topics were nominated.
#		This will parallel the process used for all the other content types, and will be far less prone to errors.
#

def getFeaturedTopicsList():
	'''API EXECUTION METHOD: A method which parses the raw go page to discover and return a dictionary pair list of featured topics on that page.'''
	r = signpostlib.getPageHTML(target)
	ret = []
	# We now have the full HTML code of our target page. Now we have to manually grep it.
	# An arcane process, borish process prone to errors. Can it be avoided? Not to my knowledge.
	stripped_data = r[r.index("title=\"Wikipedia:Featured topics\""):]
	stripped_data = stripped_data[:stripped_data.index("</td>")]
	stripped_data = stripped_data[stripped_data.index("</p>") + 4:]
	while("<li>" in stripped_data):
		data = {"ns": 4, "title": stripped_data[stripped_data.index("\">") + 2 : stripped_data.index("</a>")]}
		stripped_data = stripped_data[stripped_data.index("<li>") + 4:]
		ret.append(data)
	return ret

############################
# EXECUTIONARY API METHODS #
############################
#
# These are the methods that are called at runtime in order to construct a dictionary of featured content.
#

def checkFeaturedContentCandidate(candidate_pair_dict):
	'''DICTIONARY EXECUTION METHOD: A method which, given a {"ns": "#", "title:" "article_title"} dictionary pair, tests to see if that page is an item of featured content.
		If it is not it returns an empty dict.
		If it is it then checks the item's featured content type.
		It returns this as a new quadruple, {"ns": "#", "title": "article_title", "pageid": "####", type": "article_type"}'''
	ret = {}
	ret['ns'] = candidate_pair_dict['ns']
	if candidate_pair_dict['ns'] == 4:
		ret['title'] = "Wikipedia:Featured topics/" + candidate_pair_dict['title']
	else:
		ret['title'] = candidate_pair_dict['title']
	# A loop to handle featured topics.
	if candidate_pair_dict['ns'] == 4:
		# It could be junk. Check that is isn't.
		# We've already pre-appended WP:FT/, which we expect will ruin any junk links.
		# So just check that the category query we need to run anyway doesn't bounce.
		api_request_parameters = {'action': 'query', 'prop': 'categories', 'titles': ret['title'], 'clcategories': 'Category:Featured topics', 'format': 'json'}
		featured_topic_candidate_categories = requestData(api_request_parameters)
		featured_topic_candidate_categories = featured_topic_candidate_categories['query']
		featured_topic_candidate_categories = featured_topic_candidate_categories['pages']
		page_id_key = list(featured_topic_candidate_categories.keys())
		if page_id_key[0] == '-1':
			return {}
		# No need for an else here because ret will be returned as {} and break the loop, above.
		featured_topic_candidate_categories = featured_topic_candidate_categories[page_id_key[0]]
		ret = featured_topic_candidate_categories
		ret['type'] = 'Featured topic'
		del ret['pageid']
	# A loop to check featured articles and lists, and differenciating between them.
	elif candidate_pair_dict['ns'] == 0:
		# First, request the categories assigned to the article using the API, conditioning on that only the featured article and featured list categories are to return.
		api_request_parameters = {'action': 'query', 'prop': 'categories', 'titles': ret['title'], 'clcategories': 'Category:Featured lists|Category:Featured articles', 'format': 'json'}
		featured_content_candidate_categories = requestData(api_request_parameters)
		# Second, strip the data that has been returned to its bare essentials.
		featured_content_candidate_categories = featured_content_candidate_categories['query']
		featured_content_candidate_categories = featured_content_candidate_categories['pages']
		page_id_key = list(featured_content_candidate_categories.keys())
		featured_content_candidate_categories = featured_content_candidate_categories[page_id_key[0]]
		del featured_content_candidate_categories['pageid']
		del featured_content_candidate_categories['title']
		del featured_content_candidate_categories['ns']
		ret['categories'] = featured_content_candidate_categories
		# ret now has a new key-field, 'categories'. It contains one of two things.
		# 1. An empty dict, {..., 'categories: {}, ...}
		# 2. A list (completely different data structure!) of categories: {..., 'categories': {'categories': [{'ns': 14, 'title': 'Category:Featured article/list'}, ...].
		# Yes it is doubled!
		# Distinguishing between the two is impossibly annoying, this API was poorly written.
		# print("The same query after stripping everything but the category: " + str(featured_content_candidate_categories))
		# print("The contents of ret after adding in the categories parameter: " + str(ret))
		# Ok, first test to make sure that this isn't the trivial case, in which case we throw it out.
		if len(list(featured_content_candidate_categories.keys())) == 0:
			return {}
		# Now let's correct that doubling.
		ret['categories'] = ret['categories']['categories']
		# Now we need to figure out whether it's a featured article or a featured list---or neither!
		# Use the info in categories to test article type.
		if ret['categories'][0]['title'] == "Category:Featured articles":
			ret['type'] = 'Featured article'
			del ret['categories']
		elif ret['categories'][0]['title'] == "Category:Featured lists":
			ret['type'] = 'Featured list'
			del ret['categories']
	elif candidate_pair_dict['ns'] == 6:
			ret['type'] = 'Featured picture'
	elif candidate_pair_dict['ns'] == 100:
		# Manually parse out Portal:Contents
		if candidate_pair_dict['title'] == 'Portal:Contents':
			return {}
		else:
			ret['type'] = 'Featured portal'
	return ret

def getFeaturedContent():
	'''DICTIONARY EXECUTION METHOD: A method which returns a basic list of featured content, broken up by title, namespace, and type.
		Implements getFeaturedContentCandidateLinks(), getFeaturedTopicsList() to build a basic list of candidates.
		Then it runs each candidate through checkFeaturedContentCandidate() to remove false positives and to add data about type.
		It returns a list of dicts of the form [{'title': 'article_title', 'ns': '#', 'type': 'Featured article'}, {...}, ...]'''
	print("Getting non-topic featured content candidates...")
	featured_content_candidates = getFeaturedContentCandidateLinks()
	print("Adding topic featured content candidates...")
	featured_content_candidates.extend(getFeaturedTopicsList())
	print("Removing non-featured content from candidates list and adding featured status classes...")
	i = 0
	while i < len(featured_content_candidates):
		item = checkFeaturedContentCandidate(featured_content_candidates[i])
		if len(list(item.keys())) != 0:
			featured_content_candidates[i] = item
		else:
			featured_content_candidates.pop(i)
			i -= 1
		i += 1
	return featured_content_candidates

def addLatestFeaturedContentNomination(featured_content_item):
	'''DICTIONARY EXECUTION METHOD: A method which takes as an input a dict of the form {'title': 'article_title', 'ns': '#', 'type': 'Featured article'}.
		It then searchs for the content's nomination page and attached new data to the dict: the nomination page and the nominator.
		It returns a dict of the form {'title': 'article_title', 'ns': '#', 'type': 'Featured article', 'nomination': 'nomination_page', 'nominators:': [userOne, userTwo, ...]}'''
	if featured_content_item['type'] == 'Featured article' or featured_content_item['type'] == 'Featured list':
		api_request_parameters = {'action': 'query', 'prop': 'links', 'titles': 'Talk:' + featured_content_item['title'], 'pltitles': createFeaturedCandidacyPageLinkChecklist(featured_content_item), 'format': 'json', 'pllimit': '500'}
	elif featured_content_item['type'] == 'Featured topic':
		api_request_parameters = {'action': 'query', 'prop': 'links', 'titles': 'Wikipedia talk:Featured topics/' + featured_content_item['title'][featured_content_item['title'].index('/') + 1:], 'pltitles': createFeaturedCandidacyPageLinkChecklist(featured_content_item), 'format': 'json', 'pllimit': '500'}
	elif featured_content_item['type'] == 'Featured portal':
		api_request_parameters = {'action': 'query', 'prop': 'links', 'titles': 'Portal talk:' + featured_content_item['title'][featured_content_item['title'].index(':') + 1:], 'pltitles': createFeaturedCandidacyPageLinkChecklist(featured_content_item), 'format': 'json', 'pllimit': '500'}
	elif featured_content_item['type'] == 'Featured picture':
		featured_content_item['nomination'] = addFeaturedPictureNomination(featured_content_item)
		return featured_content_item
	nomination_pages = requestData(api_request_parameters)
	nomination_pages = nomination_pages['query']
	nomination_pages = nomination_pages['pages']
	page_id_key = list(nomination_pages.keys())
	nomination_pages = nomination_pages[page_id_key[0]]
	del nomination_pages['title'], nomination_pages['ns'], nomination_pages['pageid']
	nomination_pages = nomination_pages['links']
	latest_nomination_page = nomination_pages[len(nomination_pages) - 1]['title']
	featured_content_item['nomination'] = latest_nomination_page
	return featured_content_item

def createFeaturedCandidacyPageLinkChecklist(featured_content_item):
	'''DICTIONARY EXECUTION METHOD: A submethod of getFeaturedContentNominationData which is used to generate and format the list of links to be checked which is sent to the API in the 'pltitles' parameter.
		Takes as an input a dict of the form {'title': 'article_title', 'ns': '#', 'type': 'Featured article'}.
		Returns a string of the form 'Wikipedia:Featured article candidates/Hydrogen/archive1|Wikipedia:Featured article candidates/Hydrogen/archive2|...'
		Ten archive links are generated for checking.'''
	ret = ''
	if featured_content_item['type'] == 'Featured article':
		for n in range(1, 11):
			ret += "Wikipedia:Featured article candidates/" + featured_content_item['title'] + "/archive" + str(n) + "|"
	elif featured_content_item['type'] == 'Featured list':
		for n in range(1, 11):
			ret += "Wikipedia:Featured list candidates/" + featured_content_item['title'] + "/archive" + str(n) + "|"
	elif featured_content_item['type'] == 'Featured portal':
		for n in range(1, 11):
			ret += "Wikipedia:Featured portal candidates/" + featured_content_item['title'] + "/archive" + str(n) + "|"
			# Something of a hotfix below, FPOC can apparently still list without any /archiveN at all. ae. 'WP:FPOC/Portal:Volcanoes'
			ret += "Wikipedia:Featured portal candidates/" + featured_content_item['title'] + "|"
	elif featured_content_item['type'] == 'Featured topic':
		for n in range(1, 11):
			ret += "Wikipedia:Featured topic candidates/" + featured_content_item['title'][featured_content_item['title'].index('/') + 1:] + "/archive" + str(n) + "|"
	elif featured_content_item['type'] == 'Featured picture':
		# There is no consistent formatting for featured picture nominations, which are nominated with any one of three titles, none normalized.
		pass
	ret = ret[0:len(ret) - 1]
	return ret

def addFeaturedPictureNomination(featured_picture_item):
	'''DICTIONARY EXECUTION METHOD: A method which takes an input of a dict in the form {'title': 'article_title', 'ns': '6', 'type': 'Featured picture'}.
		It then discovers and attaches to this dict the featured picture's nomination page.
		This is written seperately from the rest of the loop present in addLatestFeaturedContentNomination, which calls this method.
		Featured pictures are a particularly difficult item to get through, and so call for special attention.
		There is no consistent formatting for featured picture nominations, which are nominated with any one of three titles, none normalized.
		The first is with the filename. The second is with a description of the image. The third is to nominate it with a description of the image that is furthermore independent of the description given at WP:GO.
		I work around these issues by discovering file usage directly off the featured picture's file usage page.
		This method is implemented seperately because it's a seperate and more difficult problem...'''
	filename = featured_picture_item['title']
	api_request_parameters = {'action': 'query', 'prop': 'fileusage', 'funamespace': 4, 'fushow': '!redirect', 'fulimit': 500, 'titles': filename, 'format': 'json', 'pllimit': '500'}
	ret = requestData(api_request_parameters)
	ret = ret['query']
	ret = ret['pages']
	page_id_key = list(ret.keys())
	ret = ret[page_id_key[0]]
	# Script will fail at this line (del ret['pageid']) if the file has been renamed post-nomination.
	# There is no easy solution for this, but it is not a highly relevant issue for a script only intended to be used when nominations are still fresh.
	try:
		del ret['pageid']
	except KeyError:
		print("FATAL ERROR: Could nor resolve a nomination page for " + featured_picture_item['title'] + ". Was this file renamed recently? Because of the limitations of this script, execution has been stopped.")
		raise KeyError
	del ret['title']
	del ret['ns']
	ret = ret['fileusage']
	i = 0
	while i < len(ret):
		if 'Wikipedia:Featured picture candidates' not in ret[i]['title'] or '-' + str(datetime.date.today().year) in ret[i]['title'] or '-' + str(datetime.date.today().year - 1) in ret[i]['title']:
			ret.pop(i)
			i -= 1
		i += 1
	# We will now have a list of all of the page's nominations. We have to find the highest one.
	# Luckily because of the link-page ordering if there were multiple nominations we expect the one we want to be the last of the remaining ones!
	ret = ret[len(ret) - 1]['title']
	return ret

def addFeaturedContentNominators(featured_content_item):
	'''DICTIONARY EXECUTION METHOD: A method which takes as an input a dict of the form `{'title': 'article_title', 'ns': '#', 'type': 'Featured article', 'nomination': 'Wikipedia:Featured article candidates/article_title/archiveN'}`.
		It then carves out the names of the content nominators. It does this by isolating the segment of data where the interesting users occur, and then sending it to getListOfUniqueUsersFromData().'''
	data = requests.get('https://en.wikipedia.org/wiki/' + featured_content_item['nomination']).text
	# print(data + '\n\n\n')
	list_of_nominators = []
	if featured_content_item['type'] == 'Featured article' or featured_content_item['type'] == 'Featured list':
		# FAs/FLs have by far the most consistent nomination scheme for extraction.
		data = data[data.index('Nominator'):]
		data = data[:data.index('</dl>') + 25]
		# +25 to make sure that a space is in the pickup. Having a space isn't as sure a bet as I initially thought; this is a workaround.
		list_of_nominators = []
		list_of_nominators = getListOfUniqueUsersFromData(data)
	elif featured_content_item['type'] == 'Featured portal':
		# No consistent format for FPs. Solution is to get a list of all users on the page and then discard all but the first.
		# Since there's no way to check co-nominations, whatever! Latitude of the FC writer.
		list_of_nominators = [getListOfUniqueUsersFromData(data)[0]]
	elif featured_content_item['type'] == 'Featured topic':
		# Same problem as with FPs. Solution is to get a list of all users on the page and then discard all but the first.
		# Since there's no way to check co-nominations, whatever! Latitude of the FC writer.
		list_of_nominators = [getListOfUniqueUsersFromData(data)[0]]
	if featured_content_item['type'] == 'Featured picture':
		# Features pictures need to have two fields of information, one for the nominator and one for the creator.
		# Thus we are actually passing two different fields in the case of featured pictures.
		# Both are fairly easily distinguishable, however.
		# First, nominators.
		featured_content_item['creator'] = getCreator(data)
		try:
			list_of_nominators_raw = data[data.index('Support as nominator'):]
		except ValueError:
			print("WARNING: " + featured_content_item['title'] + " is missing the 'Support as nominator' string, necessary for finding the FP's nominators. This step is being skipped in this case, and will have to be filled in manually.")
			featured_content_item['nominators'] = ['']
			return featured_content_item
		list_of_nominators_raw = list_of_nominators_raw[:list_of_nominators_raw.index('</li>') + 25]
		list_of_nominators = getListOfUniqueUsersFromData(list_of_nominators_raw)
	featured_content_item['nominators'] = list_of_nominators
	return featured_content_item

##################
# WRITER METHODS #
##################
#
# These are the methods that, in the end step of this script's running, compile the actual report to be published onto the wiki.
#

def writeContentStringForFeaturedContentType(list_param, content_type):
	'''DICTIONARY EXECUTION METHOD: A method which takes as an input a dict of the form `{'title': 'article_title', 'ns': '#', 'type': 'Featured article', 'nomination': 'Wikipedia:Featured article candidates/article_title/archiveN'}`.
		It then carves out the names of the content nominators. It does this by isolating the segment of data where the interesting users occur, and then sending it to getListOfUniqueUsersFromData().'''
	ret = ''
	list_of_stuff = extractFeaturedContentOfOneType(list_param, content_type)
	if len(list_of_stuff) == 0:
		return ret
	ret += '===' + content_type + 's===' + '\n'
	if list_of_stuff[0]['type'] == 'Featured article':
		ret += '\n' + '[[File:Foo.jpg|thumb|300px|Caption of first FA to display]] <!--Repeat as appropriate-->' + '\n' 
	elif list_of_stuff[0]['type'] == 'Featured list': # Featured list case.
		ret += '\n' + '[[File:Foo.jpg|thumb|300px|Caption of first FL to display]] <!--Repeat as appropriate-->' + '\n' 
	ret += '{{ucfirst:{{numtext|' + str(len(list_of_stuff)) + '}}}}' + ' [[Wikipedia:' + content_type.lower() + '|]]s were promoted this week.'
	for item in list_of_stuff:
		ret += '\n* <b>' + '[[:' + item['title'] + '|' + stripSubpage(item['title']) + ']]</b> <small>\'\'('
		ret += '[[' + item['nomination'] + '|nominated]] by ' + makeContributorsStringFromList(item['nominators']) + ')\'\'</small> '
	return ret

def writeContentStringForFeaturedPicture(list_param):
	'''DICTIONARY SUB-EXECUTION METHOD: A method that does the same as the above, but is special to featured pictures, which must provide two more things:
		1. A creator.
		2. Check the string to see if it contains File:, if not then use that string as the description instead of the filename.'''
	ret = ''
	list_of_stuff = extractFeaturedContentOfOneType(list_param, 'Featured picture')
	if len(list_of_stuff) == 0:
		return ret
	ret += '{{clear}}\n' + '===' + 'Featured picture' + 's===' + '\n'
	ret += '{{ucfirst:{{numtext|' + str(len(list_of_stuff)) + '}}}}' + ' [[Wikipedia:' + 'featured pictures' + '|]]s were promoted this week.'
	ret += "<gallery mode=packed heights=225px>"
	for item in list_of_stuff:
		if 'File:' in item['nomination']:
			ret += '\n' + item['title'] + '| '
		else:
			ret += '\n' + item['title'] + '| '
		ret += '<small>\'\'(created by ' + makeCreatorString(item['creator']) + '; ' + '[[' + item['nomination'] + '|nominated]] by ' + makeContributorsStringFromList(item['nominators']) + ')\'\'</small> '
	# Final loop: a workaround for a bug in picture captions that causes smart link piping, e.g. [[NASA|]] or [[User:Resident Mario|]] to not work.
	ret = ret.replace('|]]',']]')
	return ret

def getCreator(raw_data):
	'''DICTIONARY SUB-EXECUTION METHOD: A method which retrieves the creator of a Featured picture, given the raw HTML data of a featured picture nomination.'''
	try:
		raw_data = raw_data[raw_data.index('Creator') + 8:]
		raw_data = raw_data[:raw_data.index('<li>')]
		raw_data = raw_data[raw_data.index('<dd>'):raw_data.index('</dd>') + 5]
	except ValueError:
		return '???'
	if 'User:' in raw_data:
		# If there are multiple links in the creator string, at least one pointing to a user and any number of others pointing elsewhere, this loop will initiate.
		# Since I can't reliably maintain that the output will be correct in this case, in this case the script will return an "unknown" string.
		if raw_data.count('</a>') > 1:
			return '???'
		else:
			# This first if statement handles a code-breaker: links to userpages on other wikis that are formatted as external links would otherwise break the script.
			if 'class="external text"' in raw_data:
				return '???'
			else:
				ret = raw_data[raw_data.index('title="') + 7:]
				return ret[:ret.index('">')]
	elif '/wiki/' in raw_data:
		return "$" + raw_data[raw_data.index('">') + 2:raw_data.index('</a>')]
		# The "$" here is a special character which is used by makeCreatorString to figure out whether or not a plaintitled nomination can be linked to or not.
		# So for instance Creator: [[Albert Duhrer]] will be stored as "$Albert Duhrer".
		# While Creator: "My mate in Calcuta" will be stored as just "My mate in calculta"
		# The script will determine in the method makeCreatorString() whether or not to add back the link based on the presence or absense of this first character.
	elif '</a>' not in raw_data:
		return raw_data[raw_data.index('<dd>') + 4:raw_data.index('</dd>')]
	else:
		return '???'

def writeContentString(list_of_featured_item_dicts):
	'''RUNTIME METHOD: Generates the content string that will be written to the page at the end of this script's running time.
		This is the penultimate method to be called; once it is done all that remains is to write the content to wherever it needs to be.'''
	ret = '''{{Signpost draft}}
<noinclude>{{Wikipedia:Signpost/Template:Signpost-header|||}}</noinclude>

{{Wikipedia:Signpost/Template:Signpost-article-start|{{{1|This Week's Featured Content}}}|By [[User:{{subst:REVISIONUSER}}|]]| {{subst:#time:j F Y|{{subst:Wikipedia:Wikipedia Signpost/Issue|4}}}}}}

[[File:bar.jpg|thumb|600px|center|Lead image caption. Tweak width as appropriate]]

----
<center>'\'\'\'\'This \'\'Signpost\'\' \"Featured content\" report covers material promoted from ''' + getDateRangeString() + '''.\'\'\'\''</center>
----
'''
	ret += "\n<!-- Content initially imported from '" + target + "' via Resident Mario's FC-Importer script. -->" 
	ret += '\n' + '' + '\n' + writeContentStringForFeaturedContentType(list_of_featured_item_dicts, 'Featured article')
	ret += '\n' + '' + '\n' + writeContentStringForFeaturedContentType(list_of_featured_item_dicts, 'Featured list')
	ret += '\n' + writeContentStringForFeaturedContentType(list_of_featured_item_dicts, 'Featured portal')
	ret += '\n' + writeContentStringForFeaturedContentType(list_of_featured_item_dicts, 'Featured topic')
	ret += '\n' + '' + writeContentStringForFeaturedPicture(list_of_featured_item_dicts)
	# For reasons unknown to me removing the empty string ('') in the lines above causes consistent key error failures.
	ret += '\n\n' + '''
{{-}}
[[File:bar.jpg|thumb|600px|center|Footer image caption. Tweak width as appropriate]]

<noinclude>{{Wikipedia:Signpost/Template:Signpost-article-comments-end||{{subst:Wikipedia:Wikipedia Signpost/Issue|1}}|{{subst:Wikipedia:Wikipedia Signpost/Issue|5}}}}</noinclude>'''
	return ret

##################
# RUNTIME SCRIPT #
##################
if __name__ == '__main__':
	# The `target` is a runtime variable storing the `WP:GO` page or subpage from which nomination information is being taken.
	target = setGOPage()
	print("Now adding nomination information to featured content list dictionaries...")
	featuredContent = getFeaturedContent()
	for item in featuredContent:
		item = addLatestFeaturedContentNomination(item)
	print("Adding nominator information to featured content list dictionaries...")
	for item in featuredContent:
		item = addFeaturedContentNominators(item)
	# signpostlib.prettyPrintQuery(featuredContent)
	to_be_written = writeContentString(featuredContent)
	content_target = setContentTargetPage()
	signpostlib.saveContentToPage(to_be_written, content_target, 'Importing basic Featured Content report via the [https://github.com/ResidentMario/FC_Importer FC_Importer] script.')
	print("Done!")
