import pywikibot
import sys
import requests
import json
import datetime
# Debugging flag; turning this on greatly increases the amount of information displayed in the console on run.
debug = False
# Target page. Usually this will be WP:GO, the latest GO page, but for testing purposes a capacity exists for running against older ones as well.
target = "Wikipedia:Goings-on"
# Log of all messages that have been written by the program. These are non-fatal errors that are displayed after the code is successfully run.
log = ""
# TODO: Fully implement debugging reporting.

# IMPROVEMENTS TO-DO
# Implement a creator field for featured pictures. DONE
# Figure out how to get the start-end parameter in the report working.
# Add a snippet view for what an article is about.
# Run more tests to check for exceptional cases, document them, and figure out how to handle them.
# Point it at the weekly FC draft pages, instead of at my sandbox!

# A method to check the command line to see if debugging is enabled. Returns True if it is, False if it isn't.
# First method that is run at execution.
def setDebugStatus():
	for arg in sys.argv[1:]:
		if arg.startswith(('-d', '-debug')):
			print("Debug status has been set to True. More information will appear in output during runtime, primarily for the purposes of debugging.")
			return True
	return False

# A method to check the command line to see if a target argument has been provided. Returns either the new target, or resets the base target if none is provided.
# The base target is the most recent subpage of "Wikipedia:Goings-on", set by the helper method getNameOfLatestGOPage().
def setGOPage():
	i = 1
	while i < len(sys.argv):
		if sys.argv[i].startswith(('-p', '-page')):
			if sys.argv[i + 1].startswith('Wikipedia:Goings-on'):
				return sys.argv[i + 1]
				if debug:
					print("A command-line argument has changed the GO page for this instance of the FC-Importer script to " + sys.argv[i + 1])
			else:
				raise NameError("The optional argument '-p' allows you to specify pages besides the base 'Wikipedia:Goings-on' for putting together by the script. However, this argument expects arguments of a specific form: 'python FC-Importer -p Wikipedia:Goings-on/November_2,_2008', for instance. Please make sure your argument conforms to this.")
		i += 1
	if debug:
		print("No page-setting command-line argument has been detected, so the default GO page will be used.")
	return getNameOfLatestGOPage()

# A method which sets to page that which the content is to be written---the target.
# For reasons of security and as protection against abuse this is restricted to my sandbox, the default, and to pages within the Signpost domain.
def setContentTargetPage():
	i = 1
	while i < len(sys.argv):
		if sys.argv[i].startswith(('-t', '-target')):
			if sys.argv[i + 1].startswith('Wikipedia:Wikipedia Signpost/'):
				return sys.argv[i + 1]
				if debug:
					print("A command-line argument has changed the target page for this instance of the FC-Importer script to " + sys.argv[i + 1])
			else:
				raise NameError("The optional argument '-t' allows you to specify pages besides the base (Resident Mario's sandbox) for putting together by the script. However, this argument expects arguments of a specific form: 'python FC-Importer -t Wikipedia:Wikipedia Signpost/Newsroom/Test', for instance. It must always be a page within the Signpost's namespace. Please make sure your argument conforms to this.")
		i += 1
	if debug:
		print("No page-setting command-line argument has been detected, so the default target page will be used.")
	return 'User:Resident Mario/sandbox'


# A method to construct API requests with. Takes a dictionary of request parameters, returns the text of the query.
# Submethod of more specific submethod requesters used in the script.
# This method uses the requests library to handle concatenating the API request string and actually retrieving the data.
def requestData(api_request_parameters):
	r = requests.get("https://en.wikipedia.org/w/api.php?", params=api_request_parameters)
	if debug:
		print("\nMaking an API request using the following URL: " + r.url)
	return json.loads(r.text)

# A helper method which strips API data to get to the "core". The API is poorly designed, IMO, and you have to tunnel through a lot of junk to get at the actual data of interest.
# This method is meant to be called on the results of a requestData() call.
# It takes two parameters. One is the query, the other is the type of data being requested (for passing through the final layer).
# TODO: Lace this method through everywhere for the purposes of maintainability.
def stripAPIData(query, type):
	query = query['query']
	query = query['pages']
	page_id_key = list(query.keys())
	query = query[page_id_key[0]]
	query = query[type]
	return query

# A method which uses the requestData method to get a list of links from the Goings-on page.
# This method is used to get all of the featured articles, lists, portals, and pictures. It does not retrieve featured topics, which must be gotten more hackily.
# This is because featured topics are in the "Wikipedia" namespace, the results for which are buried under the torrent of links to other WP:GO pages present in the template at the foot of the page.
# Featured topic candidates are instead retrieved directly via scrubbing the raw HTML.
def getFeaturedContentCandidateLinks():
	api_request_parameters = {'action': 'query', 'titles': target, 'format': 'json', 'prop': 'links', 'pllimit': '500', 'plnamespace': '0|6|100'}
	links_dictionary = stripAPIData(requestData(api_request_parameters), 'links')
	return links_dictionary

# A method which gets the raw page data from the Goings-on page and filter it for featured articles.
# Used to retrieve the featured topics. This is done seperately from the more efficient procedure for getting the other types of featured content off the page for reasons described in the notes to the method getFeaturedContentCandidateLinks().
# Returns a list of dictionary pairs of featured topics.
def getGOData():
	ret = []
	page = "https://en.wikipedia.org/wiki/" + target
	data = requests.get(page)
	if debug:
		print("Making an API request using the following URL: " + data.url)
	return data

# A method which, given the raw page, returns a dictionary pair list of featured topics on that page. Implements getGOData().
# TODO: Investigate whether or not there is a better way of doing this.
def getFeaturedTopicsList():
	r = getGOData()
	ret = []
	# We now have the full HTML code of our target page. Now we have to manually grep it.
	# An arcane process, borish process prone to errors. Can it be avoided? Not to my knowledge.
	stripped_data = r.text[r.text.index("title=\"Wikipedia:Featured topics\""):]
	stripped_data = stripped_data[:stripped_data.index("</td>")]
	stripped_data = stripped_data[stripped_data.index("</p>") + 4:]
	while("<li>" in stripped_data):
		data = {"ns": 4, "title": stripped_data[stripped_data.index("\">") + 2 : stripped_data.index("</a>")]}
		stripped_data = stripped_data[stripped_data.index("<li>") + 4:]
		ret.append(data)
		# TODO: Check that this works when there are multiple featured topic promotions.
	return ret

# A method which, given a {"ns": "#", "title:" "article_title"} dictionary pair, tests to see if that page is an item of featured content.
# If it is not it returns an empty dict.
# If it is it then checks the item's featured content type.
# It returns this as a new quadruple, {"ns": "#", "title": "article_title", "pageid": "####", type": "article_type"}
def checkFeaturedContentCandidate(candidate_pair_dict):
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
		# print(page_id_key)
		# print(featured_topic_candidate_categories)
	# A loop to check featured articles and lists, and differenciating between them.
	elif candidate_pair_dict['ns'] == 0:
		# First, request the categories assigned to the article using the API, conditioning on that only the featured article and featured list categories are to return.
		api_request_parameters = {'action': 'query', 'prop': 'categories', 'titles': ret['title'], 'clcategories': 'Category:Featured lists|Category:Featured articles', 'format': 'json'}
		featured_content_candidate_categories = requestData(api_request_parameters)
		# Second, strip the data that has been returned to its bare essentials.
		# print("Featured article or list candidate: " + ret['title'])
		# print("Result of a query for the featured article or list candidate's categories: " + str(featured_content_candidate_categories))
		featured_content_candidate_categories = featured_content_candidate_categories['query']
		featured_content_candidate_categories = featured_content_candidate_categories['pages']
		# print("The same query after stripping the obvious parts: " + str(featured_content_candidate_categories))
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
		# print("Checkpoint.")
		ret['categories'] = ret['categories']['categories']
		# print("The contents of ret after checking it isn't empty and removing the redunandcy if it isn't: " + str(ret))
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
		# TODO: Fix this; for some reason it's not picking it up.
		if candidate_pair_dict['title'] == 'Portal:Contents':
			return {}
		else:
			ret['type'] = 'Featured portal'
	return ret

# A method which returns a basic list of featured content, broken up by title, namespace, and type.
# Implements getFeaturedContentCandidateLinks(), getFeaturedTopicsList() to build a basic list of candidates.
# Then it runs each candidate through checkFeaturedContentCandidate() to remove false positives and to add data about type.
# It returns a list of dicts of the form [{'title': 'article_title', 'ns': '#', 'type': 'Featured article'}, {...}, ...]
def getFeaturedContent():
	print("Getting non-topic featured content candidates...")
	featured_content_candidates = getFeaturedContentCandidateLinks()
	# print("Checkpoint 2.")
	print("Adding topic featured content candidates...")
	featured_content_candidates.extend(getFeaturedTopicsList())
	# print("Checkpoint 3.")
	print("Removing non-featured content from candidates list and adding featured status classes...")
	i = 0
	while i < len(featured_content_candidates):
		# print("Now checking the legitimacy of the following: " + str(featured_content_candidates[i]))
		item = checkFeaturedContentCandidate(featured_content_candidates[i])
		# print("Result of this check: " + str(item))
		if len(list(item.keys())) != 0:
			featured_content_candidates[i] = item
		else:
			featured_content_candidates.pop(i)
			i -= 1
		i += 1
	# print("Checkpoint 4.")
	return featured_content_candidates

# A method which takes as an input a dict of the form {'title': 'article_title', 'ns': '#', 'type': 'Featured article'}.
# It then searchs for the content's nomination page and attached new data to the dict: the nomination page and the nominator.
# It returns a dict of the form {'title': 'article_title', 'ns': '#', 'type': 'Featured article', 'nomination': 'nomination_page', 'nominators:': [userOne, userTwo, ...]}
def addLatestFeaturedContentNomination(featured_content_item):
	# print("Featured content item: " + str(featured_content_item))
	if featured_content_item['type'] == 'Featured article' or featured_content_item['type'] == 'Featured list':
		api_request_parameters = {'action': 'query', 'prop': 'links', 'titles': 'Talk:' + featured_content_item['title'], 'pltitles': createFeaturedCandidacyPageLinkChecklist(featured_content_item), 'format': 'json', 'pllimit': '500'}
	elif featured_content_item['type'] == 'Featured topic':
		# print("Contents of featured_content_item: " + str(featured_content_item))
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
	# print("Nominations page: " + str(nomination_pages))
	del nomination_pages['title'], nomination_pages['ns'], nomination_pages['pageid']
	nomination_pages = nomination_pages['links']
	# print("Nomination pages: " + str(nomination_pages))
	latest_nomination_page = nomination_pages[len(nomination_pages) - 1]['title']
	featured_content_item['nomination'] = latest_nomination_page
	return featured_content_item

# A submethod of getFeaturedContentNominationData which is used to generate and format the list of links to be checked which is sent to the API in the 'pltitles' parameter.
# Takes as an input a dict of the form {'title': 'article_title', 'ns': '#', 'type': 'Featured article'}.
# Returns a string of the form 'Wikipedia:Featured article candidates/Hydrogen/archive1|Wikipedia:Featured article candidates/Hydrogen/archive2|...'
# Ten archive links are generated for checking.
def createFeaturedCandidacyPageLinkChecklist(featured_content_item):
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
			# print("Featured topic ret string: " + ret)
	elif featured_content_item['type'] == 'Featured picture':
		# There is no consistent formatting for featured picture nominations, which are nominated with any one of three titles, none normalized.
		# The first is with the filename. This we can check.
		# The second is with a description of the image. This we cannot check unless we go back and grab the source of WP:GO again, a complexity I am unwilling to do.
		# The third is to nominate it with a description of the image that is furthermore independent of the description given at WP:GO. In this case nothing can be done.
		# As a result this script will almost never be able to pick up featured picture nomination information.
		# Therefore I have implemented methods for dealing with featured picture candidates, but they all either pass no information or empty sets.
		# I make no attempt to get information on the nomination page or on the nominators, this must be done manually until such time as they standardize their format.
		# The method bodies remain in place so that this script may be improved to include them in the future.
		pass
	ret = ret[0:len(ret) - 1]
	return ret

# A method which takes an input of a dict in the form {'title': 'article_title', 'ns': '6', 'type': 'Featured picture'}.
# It then discovers and attaches to this dict the featured picture's nomination page.
# This is written seperately from the rest of the loop present in addLatestFeaturedContentNomination, which calls this method.
# Featured pictures are a particularly difficult item to get through, and so call for special attention.
# There is no consistent formatting for featured picture nominations, which are nominated with any one of three titles, none normalized.
# The first is with the filename. The second is with a description of the image. The third is to nominate it with a description of the image that is furthermore independent of the description given at WP:GO.
# I work around these issues by discovering file usage directly off the featured picture's file usage page.
# This method is implemented seperately because it's a seperate and more difficult problem...
def addFeaturedPictureNomination(featured_picture_item):
	filename = featured_picture_item['title']
	api_request_parameters = {'action': 'query', 'prop': 'fileusage', 'funamespace': 4, 'fushow': '!redirect', 'fulimit': 500, 'titles': filename, 'format': 'json', 'pllimit': '500'}
	ret = requestData(api_request_parameters)
	ret = ret['query']
	ret = ret['pages']
	# print("The same query after stripping the obvious parts: " + str(featured_content_candidate_categories))
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

# A method which takes as an input a dict of the form {'title': 'article_title', 'ns': '#', 'type': 'Featured article', 'nomination': 'Wikipedia:Featured article candidates/article_title/archiveN'}.
# It then carves out the names of the content nominators. It does this by isolating the segment of data where the interesting users occur, and then sending it to getListOfUniqueUsersFromData().
def addFeaturedContentNominators(featured_content_item):
	data = requests.get('https://en.wikipedia.org/wiki/' + featured_content_item['nomination']).text
	# print(data + '\n\n\n')
	list_of_nominators = []
	if featured_content_item['type'] == 'Featured article' or featured_content_item['type'] == 'Featured list':
		# FAs/FLs have by far the most consistent nomination scheme for extraction.
		data = data[data.index('Nominator(s)'):]
		data = data[:data.index('</dl>') + 25]
		# print('\n' + data + '\n\n')
		# +100 to make sure that a space is in the pickup. Having a space isn't as sure a bet as I initially thought; this is a workaround.
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
		# print("Checkpoint: in the FP loop.")
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
		# print(list_of_nominators_raw)
		list_of_nominators_raw = list_of_nominators_raw[:list_of_nominators_raw.index('</li>') + 25]
		# print("Data inside of test: " + list_of_nominators_raw)
		list_of_nominators = getListOfUniqueUsersFromData(list_of_nominators_raw)
		# print(list_of_nominators)
		# Creator is a free-form field so it can be a little more difficult.
		# list_of_creators_raw = data[data.index('Creator'):]
		# list_of_creators_raw = list_of_creators_raw[:list_of_creators_raw.index('</a>')]
		# print(list_of_creators_raw)
		#  = getListOfUniqueUsersFromData(list_of_creators_raw)
		# print(list_of_creators)
		# pass
	featured_content_item['nominators'] = list_of_nominators
	# print(str(featured_content_item))
	return featured_content_item

# Pretty printer method for lists containing dicts.
# Useful for debugging: makes the output easier to read.
def prettyPrintListOfDicts(list_of_dicts):
	for list_item in list_of_dicts:
		print("{")
		for dict_item in list(list_item.keys()):
			print(" " + str(dict_item) + ": " + str(list_item[dict_item]))
		print("}")

# def prettyPrintSingleDict(dict_to_print):
#	print("{")
#	for item in list(dict_to_print.keys()):
#		print("}")

# A method which returns a list of users, given a bunch of data containing, amongst other things, users.
# After isolating the area on a page where usernames of interest appear, this method is called to extract them.
# This method assumes that the data is in HTML form, as would occur after doing an API request. This explains a few quirks:
# First of all, a space is searched for as the terminating character of the username (<a href> form). In wikicode, we would instead look for | or ]].
# Second of all, every second item that is found is instantly removed. This is because it is used in the ID identification of <a href>, and duplicates information.
def getListOfUniqueUsersFromData(data):
	ret = []
	# Populate the list.
	# print("\nData:\n\n " + data + "\n\n")
	# print("Is User: in data at the start? " + 'User:' in data)
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
	return ret

# A method which returns the most recent WP:GO subpage, the one that is to be used by the featured content report.
def getNameOfLatestGOPage():
	api_request_parameters = {'action': 'query', 'titles': makeStringOfGOPageCandidates(), 'format': 'json'}
	latest_go_page_candidates = requestData(api_request_parameters)
	# Because this particular query returns a list, it must be stripped differently than the other API queries I have used so far.
	# I have written this stipping procedure into this method manually.
	latest_go_page_candidates = latest_go_page_candidates['query']['pages']
	# print(latest_go_page_candidates)
	for item in list(latest_go_page_candidates.keys()):
		# print(item)
		if int(item) > 0:
			return latest_go_page_candidates[item]['title']
	# If you reach this point the method fell through, and couldn't find the most recent GO page. This breaks execution.
	return Exception("The most recent archived Wikipedia:Goings-on page could not be found.")

# A method which makes a string of GO page candidates by taking today's date and then extrapolating fourteen days back.
def makeStringOfGOPageCandidates():
	ret = ''
	pythonic_date = datetime.date.today()
	for i in range(7, 22):
		pythonic_date -= datetime.timedelta(days=1)
		ret += "Wikipedia:Goings-on/" + pythonic_date.strftime("%B" + " ")
		ret += str(pythonic_date.day).lstrip('0')
		ret += ", " + str(pythonic_date.year) + "|"
	ret = ret[0:len(ret) - 1]
	return ret

# A method which uses the pywikibot framework to write content to a page.
def writePage(content, page_to_write_to):
	site = pywikibot.Site()
	page = pywikibot.Page(site, page_to_write_to)
	text = page.text
	page.text = content
	page.save(u"FC Importer script test.")

# An extraction method that returns a list of dicts associated with one specific featured content type.
# This is used to de-glob the work that needs to be done in generating the output string.
def extractFeaturedContentOfOneType(list_param, content_type):
	ret = []
	for i in range(0, len(list_param)):
		if list_param[i]['type'] == content_type:
			ret.append(list_param[i])
	return ret

# Strips content before colons and slashes out of a string. Used as a text transform in writeContentStringForFeaturedContentType().
# Used to generate a link, so that we can get the simplest linking possible: either [[James Franco|]], not [[James Franco|James Franco]].
# And [[Wikipedia:Featured topics/Overview of Lorde|Overview of Lorde]], not [[Wikipedia:Featured topics/Overview of Lorde|Featured topics/Overview of Lorde]].
def stripSubpage(string):
	while ':' in string:
		string = string[string.index(':') + 1:]
	while '/' in string:
		string = string[string.index('/') + 1:]
	return string

# A method which returns the FC report section of a particular content type.
# Uses extractFeaturedContentOfOneType() to generate the list of promoted content of that type, and then iterates through it.
# Returns a content string.
def writeContentStringForFeaturedContentType(list_param, content_type):
	ret = ''
	list_of_stuff = extractFeaturedContentOfOneType(list_param, content_type)
	if len(list_of_stuff) == 0:
		return ret
	ret += '===' + content_type + 's===' + '\n'
	ret += '{{ucfirst:{{numtext|' + str(len(list_of_stuff)) + '}}}}' + ' [[Wikipedia:' + content_type + '|]]s were promoted this week.'
	# for i in range(0, len(list_of_stuff)):
		# print(str(list_of_stuff[i]))
	for item in list_of_stuff:
		ret += '\n* <b>' + '[[:' + item['title'] + '|' + stripSubpage(item['title']) + ']]</b> <small>\'\'('
		ret += '[[' + item['nomination'] + '|nominated]] by ' + makeContributorsStringFromList(item['nominators']) + ')\'\'</small> '
		# print(str(item))
	return ret

# A method that does the same as the above, but is special to featured pictures, which must provide two more things:
# 1. A creator.
# 2. Check the string to see if it contains File:, if not then use that string as the description instead of the filename.
def writeContentStringForFeaturedPicture(list_param):
	ret = ''
	list_of_stuff = extractFeaturedContentOfOneType(list_param, 'Featured picture')
	if len(list_of_stuff) == 0:
		return ret
	ret += '===' + 'Featured picture' + 's===' + '\n'
	ret += '{{ucfirst:{{numtext|' + str(len(list_of_stuff)) + '}}}}' + ' [[Wikipedia:' + 'Featured pictures' + '|]]s were promoted this week.'
	# for i in range(0, len(list_of_stuff)):
		# print(str(list_of_stuff[i]))
	for item in list_of_stuff:
		if 'File:' in item['nomination']:
			ret += '\n* <b>' + '[[:' + item['title'] + ']]</b> <small>\'\'('
		else:
			ret += '\n* <b>' + '[[:' + item['title'] + '|' + item['nomination'][item['nomination'].index('/') + 1:] + ']]</b> <small>\'\'('
		ret += 'created by ' + makeCreatorString(item['creator']) + '; ' + '[[' + item['nomination'] + '|nominated]] by ' + makeContributorsStringFromList(item['nominators']) + ')\'\'</small> '
#		ret += '[[' + item['nomination'] + '|nominated]] by ' + makeContributorsStringFromList(item['nominators']) + ')\'\'</small> '
		# print(str(item))
	return ret

# A method which retrieves the creator of a Featured picture, given raw data from a featured picture nomination.
def getCreator(raw_data):
	# print(raw_data)
	try:
		raw_data = raw_data[raw_data.index('Creator') + 8:]
		raw_data = raw_data[:raw_data.index('<li>')]
		raw_data = raw_data[raw_data.index('<dd>'):raw_data.index('</dd>') + 5]
	except ValueError:
		return '???'
	# print(raw_data)
	if 'User:' in raw_data:
		# If there are multiple links in the creator string, at least one pointing to a user and any number of others pointing elsewhere, this loop will initiate.
		# Since I can't reliably maintain that the output will be correct in this case, in this case the script will return an "unknown" string.
		if raw_data.count('</a>') > 1:
			return '???'
		else:
		# print("Checkpoint.\n\n")
		# return 'User:' + raw_data[raw_data.index('">') + 2:raw_data.index('</a>')]
			ret = raw_data[raw_data.index('title="') + 7:]
			return ret[:ret.index('">')]
	elif '/wiki/' in raw_data:
		return "$" + raw_data[raw_data.index('">') + 2:raw_data.index('</a>')]
		# The "$" here is a special character which is used by makeCreatorString to figure out whether or not a plaintitled nomination can be linked to or not.
		# So for instance Creator: [[Albert Duhrer]] will be stored as "$Albert Duhrer".
		# While Creator: "My mate in Calcuta" will be stored as just "My mate in calculta"
		# The script will determine in the method makeCreatorString() whether or not to add back the link based on the presence or absense of this first character.
	elif '</a>' not in raw_data:
		# print(raw_data)
		return raw_data[raw_data.index('<dd>') + 4:raw_data.index('</dd>')]
	else:
		return '???'

def makeCreatorString(creator):
	if 'User:' in creator:
		return '[[' + creator + '|]]'
	elif creator[0] == '$':
		return '[[' + creator[1:] + '|]]'
	else:
		return creator

# A method which returns a string of contributors, formatted for FC, given a list of contributors.
def makeContributorsStringFromList(list_param):
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

# A method which removes the red-linking string in a username.
def removeRedLinkedUsernames(name):
	ret = name
	if '&amp;action=edit&amp;redlink=1' in ret:
		ret = ret[0:ret.index('&amp;action=edit&amp;redlink=1')]
	return ret

# A helper method which removes underscores ('_') betwixt usernames. Care must be taken not to take away leading or trailing underscores.
def removeUnderscoresFromUsername(name):
	ret = name
	if '_' in name:
		for i in range(1, len(name) - 1):
			if ret[i] == '_' and ret[i - 1] != '_' and ret[i + 1] != '_':
				ret = ret[0:i] + ' ' + ret[i + 1:len(name)]
	return ret

# A method which creates a write-string to be passed to writePage() for writing at the end of this script's execution.
# Returns the formatted wiki-content string.
def writeContentString(list_of_featured_item_dicts):
	ret = '''
{{Signpost draft}}{{Wikipedia:Signpost/Template:Signpost-header|||}}

{{Wikipedia:Signpost/Template:Signpost-article-start|{{{1|(Your article's descriptive subtitle here)}}}|By [[User:{{subst:REVISIONUSER}}|]]| {{subst:#time:j F Y|{{subst:Wikipedia:Wikipedia Signpost/Issue|4}}}}}}

[[File:bar.jpg|thumb|600px|center|Lead image caption. Tweak width as appropriate]]

----
<center>'\'\'\'\'This \'\'Signpost\'\' \"Featured content\" report covers material promoted from START-END MONTH.\'\'\'\''</center>
----
'''
	ret += "\n<!-- Content initially imported from '" + target + "' via Resident Mario's FC-Importer script. -->" 
	ret += '\n' + '[[File:Foo.jpg|thumb|300px|Caption of first FA to display]] <!--Repeat as appropriate-->' + '\n' + writeContentStringForFeaturedContentType(list_of_featured_item_dicts, 'Featured article')
	ret += '\n' + '[[File:Foo.jpg|thumb|300px|Caption of first FL to display]] <!--Repeat as appropriate-->' + '\n' + writeContentStringForFeaturedContentType(list_of_featured_item_dicts, 'Featured list')
	ret += '\n' + writeContentStringForFeaturedContentType(list_of_featured_item_dicts, 'Featured portal')
	ret += '\n' + writeContentStringForFeaturedContentType(list_of_featured_item_dicts, 'Featured topic')
	ret += '\n'  + '[[File:Foo.jpg|thumb|300px|Caption of first FP to display]] <!--Repeat as appropriate-->' + '\n' + writeContentStringForFeaturedPicture(list_of_featured_item_dicts) # spare space?
	ret += '\n\n' + '''
	[[File:bar.jpg|thumb|600px|center|Footer image caption. Tweak width as appropriate]]

	{{Wikipedia:Signpost/Template:Signpost-article-comments-end||{{subst:Wikipedia:Wikipedia Signpost/Issue|1}}|{{subst:Wikipedia:Wikipedia Signpost/Issue|4}}}}
	'''
	return ret

# First step of script execution is setting the debug and target flags, if the user specified alternatives to the defaults.
debug = setDebugStatus()
target = setGOPage()
#### print(str(debug))
#### print(target)
### print(newgetFeaturedContentCandidateLinks())
### print(getFeaturedTopicsList())
## print(checkFeaturedContentCandidate({'ns': 0, 'title': '2010'}))
## print(checkFeaturedContentCandidate({'ns': 0, 'title': 'Hydrogen'}))
## print(checkFeaturedContentCandidate({'title': 'James Whiteside McCay', 'ns': 4}))
## print(checkFeaturedContentCandidate({'title': 'Millennium Park', 'ns': 4}))
## print(checkFeaturedContentCandidate({'title': 'James Whiteside McCay', 'ns': 0}))
## print(checkFeaturedContentCandidate({'title': 'List of awards and nominations received by Ariana Grande', 'ns': 0}))
## print(checkFeaturedContentCandidate({'title': 'File:Hohenzollernbrücke Köln.jpg', 'ns': 6}))
## print(checkFeaturedContentCandidate({'title': 'Portal:Volcanoes', 'ns': 100}))
# print(addLatestFeaturedContentNomination({'type': 'Featured article', 'ns': 0, 'title': 'A Quiet Night In'}))
# print(addLatestFeaturedContentNomination({'type': 'Featured article', 'ns': 0, 'title': 'Hawaii hotspot'}))
# print(addLatestFeaturedContentNomination({'type': 'Featured list', 'ns': 0, 'title': 'List of volcanoes in the Hawaiian – Emperor seamount chain'}))
# print(addLatestFeaturedContentNomination({'type': 'Featured portal', 'ns': 100, 'title': 'Portal:Volcanoes'}))
# print(addLatestFeaturedContentNomination({'type': 'Featured topic', 'ns': 4, 'title': 'Four Freedoms'}))
# print(addLatestFeaturedContentNomination({'title': 'File:Johannes Vermeer - Gezicht op huizen in Delft, bekend als \'Het straatje\' - Google Art Project.jpg', 'type': 'Featured picture'}))
# print(addFeaturedPictureNomination({'title': 'File:Johannes Vermeer - Gezicht op huizen in Delft, bekend als \'Het straatje\' - Google Art Project.jpg'}))
# print(addFeaturedContentNominators({'type': 'Featured article', 'ns': 0, 'title': 'A Quiet Night In', 'nomination': 'Wikipedia:Featured article candidates/A Quiet Night In/archive1'}))
# print(addFeaturedContentNominators({'type': 'Featured article', 'ns': 0, 'title': 'Mauna Kea', 'nomination': 'Wikipedia:Featured article candidates/Mauna Kea/archive1'}))
# print(addFeaturedContentNominators({'type': 'Featured article', 'ns': 0, 'title': 'List of works by Georgette Heyer', 'nomination': 'Wikipedia:Featured list candidates/List of works by Georgette Heyer/archive1'}))
# print(addFeaturedPictureNomination({'title': 'File:Johannes Vermeer - Gezicht op huizen in Delft, bekend als \'Het straatje\' - Google Art Project.jpg'}))
# print(addFeaturedContentNominators({'type': 'Featured picture', 'ns': 4, 'title': 'File:Girl in White by Vincent Van Gogh - NGA.jpg', 'nomination': 'Wikipedia:Featured picture candidates/Girl in White'}))
# print(getListOfUniqueUsersFromData(requests.get('https://en.wikipedia.org/wiki/Wikipedia:Featured_picture_candidates/Paper_wasp_in_nest').text))
# print(makeStringOfGOPageCandidates())
# print(getNameOfLatestGOPage())

print("Now adding nomination information to featured content list dictionaries...")
featuredContent = getFeaturedContent()
for item in featuredContent:
 	item = addLatestFeaturedContentNomination(item)
print("Adding nominator information to featured content list dictionaries...")
for item in featuredContent:
	item = addFeaturedContentNominators(item)
prettyPrintListOfDicts(featuredContent)
# prettyPrintListOfDicts(extractFeaturedContentOfOneType(featuredContent, 'Featured pictures'))
# print(writeContentStringForFeaturedContentType(featuredContent, 'Featured article'))
to_be_written = writeContentString(featuredContent)
writePage(to_be_written, setContentTargetPage())
print("Done!")
