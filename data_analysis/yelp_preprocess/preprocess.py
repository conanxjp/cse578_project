import config as cf
import json
import pandas as pd
import os
from tqdm import tqdm
import xml.etree.ElementTree as et
import types
import argparse
import sys
import csv


def parseBusiness():
    """
    parse business into separate and smaller json files by city and state which
    will be used in js, the separated business files are saved by city in stated
    folder, in json format
    Business Ids are picked during parsing and used for filtering reviews in
    parseReview()
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
    usStates = getStateAbbs()
    # parse us-cities.json file
    cities = []
    with open(cityPath) as c:
        cityDict = json.load(c)
        cityDict = cityDict['features']
        for city in cityDict:
            cities.append(city['properties']['city'])
    c.close()
    # read categoryies.txt file
    categories = []
    with open(categoryPath) as c:
        for line in c:
            categories.append(line[:-1])
    c.close()

    # parse based on state
    with open(businessPath) as json_data:
        print('parsing business based on state names')
        states = {}
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
            if state in usStates and city in cities and checkCategory(category):
                checkResult, foundState = checkZipcode(zipcode, state)
                if not checkResult and foundState != '':
                    # print(i, address, zipcode, city, state, foundState)
                    state = foundState
                    business['state'] = foundState
                if state not in states.keys():
                    states[state] = []
                states[state].append(business)
    json_data.close()

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
    parse review.json data, filter the reviews based on the businuss id picked
    from each state and city, filtered review files are saved by business ids in
    json format and stored in the corresponding city folders.
    Also generate the user id json files for each city, which will be used for
    filtering user data in parseUser()
    """
    usStates, businessIds = getBusinessInfo()

    # parse based on state
    userIds = {}
    reviews = {}
    with open(reviewPath) as json_data:
        print('parsing review data based on state names')
        for i, line in enumerate(tqdm(json_data)):
            # if i > 1000:
            #     break
            review = json.loads(line)
            state, city = checkBusinessLocation(review['business_id'], businessIds)
            if state is not None:
                if state not in userIds.keys():
                    userIds[state] = {}
                    reviews[state] = {}
                if city not in userIds[state].keys():
                    userIds[state][city] = {}
                    reviews[state][city] = {}
                if review['business_id'] not in reviews[state][city].keys():
                    userIds[state][city][review['business_id']] = []
                    reviews[state][city][review['business_id']] = []
                reviews[state][city][review['business_id']].append(review)
                userIds[state][city][review['business_id']].append(review['user_id'])
    json_data.close()

    for state in userIds.keys():
        directory = dataPath + 'user/' + state
        if not os.path.exists(directory):
            os.makedirs(directory)
        for city in userIds[state].keys():
            directory = dataPath + 'user/' + state + '/%s' % city
            if not os.path.exists(directory):
                os.makedirs(directory)
            for businessId in userIds[state][city].keys():
                with open(directory + '/%s_user-ids.json' % businessId, 'w+') as f:
                    json.dump(userIds[state][city][businessId], f)
                f.close()

    for state in reviews.keys():
        directory = dataPath + 'review/' + state
        if not os.path.exists(directory):
            os.makedirs(directory)
        for city in reviews[state].keys():
            directory = dataPath + 'review/' + state + '/%s' % city
            if not os.path.exists(directory):
                os.makedirs(directory)
            for businessId in reviews[state][city].keys():
                with open(directory + '/%s_reviews.json' % businessId, 'w+') as f:
                    json.dump(reviews[state][city][businessId], f)
                f.close()

def parseCheckIn():
    """
    parse the checkin.json file and separete the checkin information based on
    state and city, reorganize the data as business id as key and time as value,
    saved in json file
    """
    usStates, businessIds = getBusinessInfo()
    checkins = {}
    print('parse the checkin data based on business id')
    with open(checkinPath) as f:
        for i, line in enumerate(tqdm(f)):
            # if i > 1000:
            #     break
            entry = json.loads(line)
            id = entry['business_id']
            state, city = checkBusinessLocation(id, businessIds)
            if state is not None:
                if state not in checkins.keys():
                    checkins[state] = {}
                if city not in checkins[state].keys():
                    checkins[state][city] = {}
                checkins[state][city][id] = entry['time']
    f.close()

    for state in checkins.keys():
        directory = dataPath + 'checkin/' + state
        if not os.path.exists(directory):
            os.makedirs(directory)
        for city in checkins[state].keys():
            directory = dataPath + 'checkin/%s/%s/' % (state, city)
            # print(directory)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(directory + '%s_checkin.json' % city, 'w+') as f:
                json.dump(checkins[state][city], f)
            f.close()

def parseUser():
    """
    parse user.json data and filter out all users based on the user ids found in
    the filtered reviews, the filtered users are saved in a single json file wICtovzHT9HW5SlWf3cQ
    the 'friends' information dropped
    """
    usStates = getStateAbbs()
    # read %state_user-ids.json files
    # check dependent files
    directory = dataPath + 'user/'
    if not os.path.exists(directory):
        parseReview()

    userIds = {}
    print('read user ids reviewed for each business id')
    for state in usStates:
        directory = dataPath + 'user/' + state
        if not os.path.exists(directory):
            continue
        for subdir, _, files in tqdm(os.walk(directory)):
            for file in files:
                if "user-ids.json" in file:
                    with open(os.path.join(subdir, file), 'r') as f:
                        for line in f:
                            ids = json.loads(line)
                            for id in ids:
                                city = subdir.split('/')[-1]
                                if id not in userIds.keys():
                                    userIds[id] = []
                                if [state, city, file[:-14]] not in userIds[id]:
                                    userIds[id].append([state, city, file[:-14]])
                    f.close()

    # parse user.json based on user id grouped by state and city
    headers = ['user_id',
                'name',
                'review_count',
                'yelping_since',
                'useful',
                'funny',
                'cool',
                'fans',
                'elite',
                'average_stars',
                'compliment_hot',
                'compliment_more',
                'compliment_profile',
                'compliment_cute',
                'compliment_list',
                'compliment_note',
                'compliment_plain',
                'compliment_cool',
                'compliment_funny',
                'compliment_writer',
                'compliment_photos']
    with open(userPath) as json_data:
        print('parsing user data based on user ids')
        for i, line in enumerate(tqdm(json_data)):
            # if i > 1000:
            #     break
            user = json.loads(line)
            id = user['user_id']
            if id in userIds.keys():
                for location in userIds[id]:
                    directory = dataPath + 'user/%s/%s/' % (location[0], location[1])
                    filepath = directory + '%s_users.csv' % location[2]
                    mode = 'a'
                    if not os.path.exists(filepath):
                        mode = 'w+'
                    with open(filepath, mode) as f:
                        writer = csv.DictWriter(f, fieldnames=headers)
                        if mode == 'w+':
                            writer.writeheader()
                        user = {key: value for key, value in user.items() if key != 'friends'}
                        writer.writerow(user)
                    f.close()
    json_data.close()


def checkBusinessLocation(businessId, businessIds):
    for state in businessIds.keys():
        for city in businessIds[state].keys():
            if businessId in businessIds[state][city]:
                return state, city
    return None, None

def getStateAbbs():
    # parse state2abb.json file
    usStates = []
    with open(stateAbbPath) as s:
        stateDict = json.load(s)
        for state in stateDict.values():
            usStates.append(state)
    s.close()
    return usStates

def getBusinessInfo():
    usStates = getStateAbbs()
    # read business-ids.txt
    # check dependent files
    directory = dataPath + 'business/'
    if not os.path.exists(directory):
        parseBusiness()
    businessIds = {}
    for state in usStates:
        directory = dataPath + 'business/' + state
        if not os.path.exists(directory):
            continue
        with open(directory + '/%s_business-ids.json' % state, 'r') as f:
            for line in f:
                id = json.loads(line)
                businessIds[state] = id
        f.close()
    return usStates, businessIds


def preprocess():
    """wrapper for full run"""
    parseUser()
    parseCheckin()

if __name__ == '__main__':
    """
    To run the preprocess, you need all required raw data in the correct directory,
    here is a list of the dependent data files:
    Outside the root folder of the project, add the following path:
    /data/yelp_dataset/
    Then copy the following raw data files into the above folder:
    "business.json"
    "review.json"
    "user.json"
    "checkin.json"
    "state2abb.json"
    "us-cities.json"
    "zip-code.xml"
    "categories.txt"
    The above data files can be downloaded from this link:
    https://drive.google.com/open?id=11ZC2-xb5eTQtOU160BEIJUrV3ZHNUTcj

    Modules in this script in dependent on one another, the correct sequences to
    run are parseBusiness -> parseReview -> parseUser or parseBusiness ->
    parseCheckIn, use --full_run 1 flag to run the script in this order.
    Other requests of running selected module will by default run the dependent
    module first as necessary.
    """
    argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('--business', type=int, choices=[0, 1], default=0)
    parser.add_argument('--review', type=int, choices=[0, 1], default=0)
    parser.add_argument('--checkin', type=int, choices=[0, 1], default=0)
    parser.add_argument('--user', type=int, choices=[0, 1], default=0)
    parser.add_argument('--full_run', type=int, choices=[0, 1], default=0)

    args, _ = parser.parse_known_args(argv)

    dataPath = cf.ROOT_PATH + cf.DATA_PATH
    businessPath = dataPath + cf.BUSINESS
    stateAbbPath = dataPath + cf.STATE
    cityPath = dataPath + cf.CITY
    zipCodePath = dataPath + cf.ZIP_CODE
    categoryPath = dataPath + cf.CATEGORY
    reviewPath = dataPath + cf.REVIEW
    userPath = dataPath + cf.USER
    checkinPath = dataPath + cf.CHECKIN

    if args.full_run == 1 or args.user == 1:
        preprocess()
    elif args.review == 1:
        parseReview()
    elif args.checkin == 1:
        parseCheckIn()
    elif args.business == 1:
        parseBusiness()
    else:
        parser.print_help()
