import pandas as pd
import json
import config as cf
from tqdm import tqdm
import random
from pandas.io.json import json_normalize
from nltk.corpus import stopwords
from collections import Counter
from odict import odict
from nltk import word_tokenize
import math
import os

def log(x):
    try:
        return math.log(x)
    except ValueError:
        return 0

def notEnglish(s):
    results = []
    for t in s:
        try:
            t.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            results.append(True)
        else:
            results.append(False)
    return results

def loadReviews():
    df = pd.read_json(reviewPath, lines=True, chunksize=max_records)
    reviews = pd.DataFrame() # Initialize the dataframe
    print('next step')
    i = 0
    try:
       for df_chunk in tqdm(df):
           # if i > 0:
                # break
           reviews = pd.concat([reviews, df_chunk])
           # print(i)
           # i=i +1
    except ValueError:
           print ('\nSome messages in the file cannot be parsed')

    return reviews

def loadUsers():
    df = pd.read_json(userPath, lines=True, chunksize=max_records)
    users = pd.DataFrame() # Initialize the dataframe
    print('next step')
    i = 0
    try:
       for df_chunk in tqdm(df):
           # if i > 0:
           #      break
           users = pd.concat([users, df_chunk])
           # print(i)
           # i=i +1
    except ValueError:
           print ('\nSome messages in the file cannot be parsed')
    return users


def analyzeReviews(reviews, users):
    # filter out non-english reviews
    reviews = reviews.drop(reviews[notEnglish(reviews['text'])].index)
    reviews = reviews.merge(users[['user_id', 'cool', 'useful', 'funny', 'fans', 'review_count']], left_on='user_id', right_on='user_id')
    # calculate user_score
    reviews['user_score'] = 0
    reviews['user_score'] = ((reviews['useful_y'].apply(log) + reviews['funny_y'].apply(log) + reviews['cool_y'].apply(log) + reviews['fans'].apply(log))/reviews['review_count'])
    # calculate review_score
    reviews['review_score'] = 0
    reviews['review_score'] = reviews['useful_x'].apply(log) + reviews['cool_x'].apply(log) + reviews['funny_x'].apply(log)
    # filter out useless reviews
    reviews = reviews.drop(reviews[(reviews['user_score'] == 0) & (reviews['review_score'] == 0)].index)
    # calculate aspect scores
    aspects = ['food', 'price', 'service', 'ambience', 'misc']
    for aspect in aspects:
        reviews[aspect] = random.uniform(reviews['stars'], reviews['stars'] * 9/4 - 29/4) * (reviews['review_score'] + reviews['user_score'])

    # trim reviews df
    drop_cols = ['date', 'useful_x', 'funny_x', 'cool_x', 'useful_y', 'cool_y', 'funny_y', 'user_id', 'fans', 'review_count', 'user_score', 'review_score']
    reviews = reviews.drop(drop_cols, 1)
    return reviews

def createStateBusiness(reviews):
    for state in states:
        stateFolder = dataPath + '%s_processed' % state
        if not os.path.exists(stateFolder):
            os.makedirs(stateFolder)
        statePath = dataPath + 'business_consumer/' + state
        for subdir, _, files in tqdm(os.walk(statePath)):
            for file in files:
                if 'business-ids.json' not in file:
                    business = pd.read_json(os.path.join(statePath, file))
                    leftcols = ['business_id', 'text', 'stars', 'food', 'price', 'service', 'ambience', 'misc']
                    business = business.merge(reviews[leftcols], left_on='business_id', right_on='business_id')
                    dropcols = ['neighborhood', 'is_open']
                    buisness = business.drop(dropcols, 1)
                    business.to_json(stateFolder + '/%s_business.json' % file[:-5], orient= 'records')

def getStateAbbs(stateAbbPath):
    # parse state2abb.json file
    usStates = []
    with open(stateAbbPath) as s:
        stateDict = json.load(s)
        for state in stateDict.values():
            usStates.append(state)
    s.close()
    return usStates

def getBusinessInfo(stateAbbPath):
    usStates = getStateAbbs(stateAbbPath)
    # read business-ids.txt
    # check dependent files
    directory = dataPath + 'business_consumer/'
    businessIds = {}
    for state in usStates:
        directory = dataPath + 'business_consumer/' + state
        if os.path.exists(directory):
            with open(directory + '/%s_business-ids.json' % state, 'r') as f:
                for line in f:
                    id = json.loads(line)
                    businessIds[state] = id
            f.close()
    return usStates, businessIds


def processText():
    def checkBusinessLocation(df, state):
        index = {}
        for city in businessIds[state].keys():
            index[city] = pd.DataFrame()
            index[city] = df[df['business_id'].isin(businessIds[state][city])]
        return index

    _, businessIds = getBusinessInfo(stateAbbPath)
    s=set(stopwords.words('english'))
    for state in states:
        statePath = dataPath + '%s_processed' % state
        newPath = dataPath + '%s_analyzed' % state
        if not os.path.exists(newPath):
            os.makedirs(newPath)
        for subdir, _, files in tqdm(os.walk(statePath)):
            for file in files:
                if '.json' in file:
                    print('process text in %s ...' % file[:-5])
                    citybusiness = pd.read_json(os.path.join(statePath, file))
                    citybusiness['text'] = [dict(Counter(list(filter(lambda w: not w in s and w.isalpha(),word_tokenize(txt.lower()))))) for txt in tqdm(citybusiness['text'])]
                    filename = newPath + '/%s_business_processed.json' % file[:-14]
                    citybusiness.to_json(filename, orient = 'records')
        # print('collect city information')
        # cityBusiness = checkBusinessLocation(business, state)
        # print('save to city files')
        # for city, b in cityBusiness.items():

def summerize(business, filename):

    commonCols = ['address', 'business_id', 'city', 'latitude', 'longitude', 'name', 'postal_code', 'review_count', 'stars_x', 'state']
    dictCols = ['business_id', 'text', 'hours', 'categories', 'stars_y']
    dropCols = ['attributes', 'is_open', 'text', 'hours', 'categories', 'stars_y']
    print('\tstep1')
    sliced = business[dictCols]
    dropped = business.drop(dropCols, 1)
    text = sliced[['business_id', 'text', 'stars_y']]
    sliced = sliced.drop('text', 1)
    dropped = dropped.groupby(commonCols).sum()
    dropped = dropped.reset_index()
    goodText = text[text['stars_y'] >= 4.0]
    badText = text[text['stars_y'] <= 2.0]
    print('\tstep2')
    allId = text['business_id']
    badId = badText['business_id']
    goodId = goodText['business_id']
    between = text[(text['stars_y'] < 4.0) & (text['stars_y'] > 2.0)]
    beId = between['business_id']
    dropIds = beId[~beId.isin(goodId.append(badId))]
    print('\tstep3')
    dropped=dropped[~dropped['business_id'].isin(dropIds)]
    text = text[~text['business_id'].isin(dropIds)]
    sliced = sliced[~sliced['business_id'].isin(dropIds)]
    print('\tstep4')
    # calculate stars
    stars = text.groupby(['business_id', 'stars_y'])['stars_y'].size().unstack(fill_value=0)
    stars = stars.reset_index()
    stars[[1,2,3,4,5]] = stars[[1,2,3,4,5]].divide(stars.sum(1), 0) * 100
    print('\tstep5')
    def counter(df):
        return dict(sum((Counter(dict(x)) for x in df['text']), Counter()))

    def orderDict(x):
        d = odict(sorted(x.items(), key=lambda t: t[1], reverse=True))
        results = {}
        i = 0
        for key, value in d.items():
            if i > 19:
                break
            results[key] = value
            i += 1
        return results

    goodText = goodText.groupby('business_id').apply(counter).reset_index()
    badText = badText.groupby('business_id').apply(counter).reset_index()
    goodText[0] = goodText[0].apply(orderDict)
    badText[0] = badText[0].apply(orderDict)

    print('\tstep6')
    sliced = sliced.groupby('business_id').last().reset_index()
    sliced = sliced.drop('stars_y',1)
    print('\tstep7')
    # put everything together
    temp = pd.concat([sliced, goodText])
    temp = temp.groupby('business_id').last().reset_index()
    temp = temp.rename(index=str, columns={0: "good words"})
    temp = pd.concat([temp, badText])
    temp = temp.groupby('business_id').last().reset_index()
    temp = temp.rename(index=str, columns={0: "bad words"})
    temp = pd.concat([temp, stars]).groupby('business_id').last().reset_index()
    temp = pd.concat([dropped, temp]).groupby('business_id').last().reset_index()
    temp.to_json(filename, orient = 'records')
    print('\tfinished')

def summerizeBusinessInfo():
    for state in states:
        stateFolder = dataPath + 'business_final/' + state
        if not os.path.exists(stateFolder):
            os.makedirs(stateFolder)
        statePath = dataPath + '%s_analyzed/' % state
        stateBusiness = pd.DataFrame()
        for subdir, _, files in os.walk(statePath):
            for file in files:
                if '.json' in file:
                    business = pd.read_json(os.path.join(statePath, file))
                    print('process %s' % file[:-len('_business_processed.json')])
                    filename = stateFolder + '/%s_business_final.json' % file[:-len('_business_processed.json')]
                    summerize(business, filename)


if __name__ == '__main__':

    dataPath = cf.ROOT_PATH + cf.DATA_PATH
    reviewPath = dataPath + 'review.json'
    userPath = dataPath + 'user.json'
    stateAbbPath = dataPath + 'state2abb.json'
    states = ['AZ', 'NC', 'NV', 'IL', 'OH', 'PA', 'WI']
    max_records = 1e5
    # reviews = loadReviews()
    # users = loadUsers()
    # reviews = analyzeReviews(reviews, users)
    # createStateBusiness(reviews)
    # processText()
    summerizeBusinessInfo()
