import config as cf
import preprocess as pp
import json
import pandas as pd
import os
from tqdm import tqdm
import xml.etree.ElementTree as et
import types
import argparse
import sys
import csv


def filterBusiness():
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
    usStates = pp.getStateAbbs(stateAbbPath)
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
    filteredBusiness = {}
    with open(businessPath) as json_data:
        print('parsing business based on state names')
        states = {}
        for i, line in enumerate((tqdm(json_data))):
            business = json.loads(line)
            state = business['state']
            city = business['city']
            category = business['categories']
            zipcode = business['postal_code']
            if state in usStates and city in cities and checkCategory(category):
                checkResult, foundState = checkZipcode(zipcode, state)
                if not checkResult and foundState != '':
                    state = foundState
                    business['state'] = foundState
                filteredBusiness.append(business)
    json_data.close()

    with open(dataPath + 'business_filtered.json', 'w+') as f:
        json.dump(filteredBusiness, f)

if __name__ == '__main__':

    dataPath = cf.ROOT_PATH + cf.DATA_PATH
    dataPath = cf.ROOT_PATH + cf.DATA_PATH
    businessPath = dataPath + cf.BUSINESS
    stateAbbPath = dataPath + cf.STATE
    cityPath = dataPath + cf.CITY
    zipCodePath = dataPath + cf.ZIP_CODE
    categoryPath = dataPath + cf.CATEGORY
    # filterBusiness()
    with open(dataPath + 'business_filtered.json', 'r') as f:
        for line in f:
            data = json.loads(line)
            for business in data:
                print(business['business_id'])
