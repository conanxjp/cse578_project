import config as cf
import json
import pandas as pd
import os
from tqdm import tqdm
import xml.etree.ElementTree as et
import types

dataPath = cf.ROOT_PATH + cf.DATA_PATH
businessPath = dataPath + cf.BUSINESS
stateAbbPath = dataPath + cf.STATE
cityPath = dataPath + cf.CITY
zipCodePath = dataPath + cf.ZIP_CODE
categoryPath = dataPath + cf.CATEGORY
businessIdPath = dataPath + cf.BUSINESS_ID
reviewPath = dataPath + cf.REVIEW
userPath = dataPath + cf.USER


def parseBusiness():
    """
    parse business into separate and smaller json files by city and state which
    will be used in js
    """
    def lookupZipcode(zipcode):
        for state in zipcodes:
            for zipRange in zipcodes[state]:
                if zipcode >= zipRange[0] and zipcode <= zipRange[1]:
                    return state
        return ''

    def checkZipcode(zipcode, state):
        if zipcode == '':
            return True, state
        else:
            zipcode = int(zipcode)
        for zipRange in zipcodes[state]:
            if zipcode >= zipRange[0] and zipcode <= zipRange[1]:
                return True, state
        return False, lookupZipcode(zipcode)

    def checkCategory(category):
        if len(category) == 0:
            return False
        else:
            if isinstance(category, list):
                intersection = [c for c in category if c in categories]
                if len(intersection) != 0:
                    return True
            else:
                if category in categories:
                    return True
        return False

    # parse zip-code.xml file
    tree = et.parse(zipCodePath)
    root = tree.getroot()
    zipcodes = {}
    for s in root.findall('tr'):
        d = s.findall('td')
        state = d[2].text
        if state not in zipcodes:
            zipcodes[state] = []
        zipcodes[state].append([int(d[3].text), int(d[4].text)])
    # parse state2abb.json file
    states = {}
    with open(stateAbbPath) as s:
        stateDict = json.load(s)
        for state in stateDict.values():
            states[state] = []
    # parse us-cities.json file
    cities = []
    with open(cityPath) as c:
        cityDict = json.load(c)
        cityDict = cityDict['features']
        for city in cityDict:
            cities.append(city['properties']['city'])
    # read categoryies.txt file
    categories = []
    with open(categoryPath) as c:
        for line in c:
            categories.append(line[:-1])

    # parse based on state
    with open(businessPath) as json_data:
        print('parsing business based on state names')
        for i, line in enumerate((tqdm(json_data))):
            business = json.loads(line)
            state = business['state']
            city = business['city']
            category = business['categories']
            zipcode = business['postal_code']
            # # all commented lines below are picking mistakes
            # # in the raw dataset, they were only used during initial scanning
            # address = business['address']
            # # filter out business that are not in the top 1000 cities or not a resturant
            if state in states and city in cities and checkCategory(category):
                checkResult, foundState = checkZipcode(zipcode, state)
                if not checkResult and foundState != '':
                    # print(i, address, zipcode, city, state, foundState)
                    state = foundState
                    business['state'] = foundState
                states[state].append(business)

    # parse based on city in a state and write to city.json files in state folder
    print('parsing business based on city names')
    businessIds = {}
    for state in tqdm(states):
        directory = dataPath + 'business/' + state
        if not os.path.exists(directory):
            os.makedirs(directory)
        businessIds[state] = {}
        cities = {}
        for business in states[state]:
            city = business['city']
            if city not in businessIds[state].keys():
                businessIds[state][city] = []
            businessIds[state][city].append(business['business_id'])
            if city not in cities:
                cities[city] = []
            cities[city].append(business)
        for city in cities:
            with open(directory + '/%s.json' % city, 'w+') as f:
                json.dump(cities[city], f)
            f.close()
        with open(directory + '/%s_business-ids.json' % state, 'w+') as f:
            json.dump(businessIds[state], f)
        f.close()

def parseReview():
    """
    """
    def checkReviewState(id):
        for state in businessIds.keys():
            for city in businessIds[state].keys():
                if id in businessIds[state][city]:
                    return state, city
        return None, None

    # parse state2abb.json file
    states = {}
    with open(stateAbbPath) as s:
        stateDict = json.load(s)
        for state in stateDict.values():
            states[state] = []
    # read business-ids.txt
    businessIds = {}
    for state in states:
        directory = dataPath + 'business/' + state
        with open(directory + '/%s_business-ids.json' % state, 'r') as f:
            for line in f:
                id = json.loads(line)
                businessIds[state] = id
        f.close()

    # parse based on state
    userIds = {}
    reviews = {}
    with open(reviewPath) as json_data:
        print('parsing review data based on state names')
        for i, line in enumerate(json_data):
            review = json.loads(line)
            state, city = checkReviewState(review['business_id'])
            if state is not None:
                if state not in userIds.keys():
                    userIds[state] = {}
                    reviews[state] = {}
                if city not in userIds[state].keys():
                    userIds[state][city] = []
                    reviews[state][city] = []
                userIds[state][city].append(review['user_id'])
                reviews[state][city].append(review)

    for state in userIds.keys():
        directory = dataPath + 'business/' + state
        with open(directory + '/%s_user-ids.json' % state, 'w+') as f:
            json.dump(userIds[state], f)
        f.close()
        with open(directory + '/%s_reviews.json' % state, 'w+') as f:
            json.dump(reviews[state], f)
        f.close()


def parseUser():
    """
    parse user.json file
    """
    # parse based on state
    with open(userPath) as json_data:
        print('parsing user data based on state names')
        for i, line in enumerate(json_data):
            user = json.loads(line)
            print(user['user_id'])
            print()

# parseBusiness()
parseReview()
# parseUser()
