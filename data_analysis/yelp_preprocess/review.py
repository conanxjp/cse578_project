import json
import pandas as pd
from nltk.tokenize import sent_tokenize
from nltk.metrics import edit_distance
from nltk import (word_tokenize, pos_tag)
import hunspell
import argparse
import sys
import csv
import os
import re
from tqdm import tqdm
import config as cf
import preprocess as pp

def parseReviews():
    def isEnglish(s):
        try:
            s.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True
    headers = ['review_id', 'user_id', 'business_id', 'stars', 'date', 'text', 'useful', 'funny', 'cool']
    usStates, businessIds = pp.getBusinessInfo(stateAbbPath, dataPath)
    directory = dataPath + 'processed_reviews'
    stateReviews = {}
    stateCounter = {}

    with open(reviewPath) as json_data:
        print('parsing review data based on state names')
        for i, line in enumerate(tqdm(json_data)):
            # if i > 1000:
            #     break
            review = json.loads(line)
            state, city = checkBusinessLocation(review['business_id'], businessIds)
            if state is not None:
                if state not in stateReviews.keys():
                    stateCounter[state] = 0
                    stateReviews[state] = pd.DataFrame(columns = headers)
                else:
                    stateReviews[state].loc[stateCounter[state]] = review
                    stateCounter[state] = stateCounter[state] + 1
    json_data.close()

    for state, stateReview in stateReviews.items():
        stateReview.to_csv(dataPath + 'state reviews/%s_reviews.csv' %state, index = False)

def checkBusinessLocation(businessId, businessIds):
    for state in businessIds.keys():
        for city in businessIds[state].keys():
            if businessId in businessIds[state][city]:
                return state, city
    return None, None

def loadReviews():
    """
    load review.json file and filter the reviews based on business ids,
    consolidate them based on state and store as csv file for further
    preprocessing the text in them
    """
    def isEnglish(s):
        try:
            s.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True
    headers = ['review_id', 'user_id', 'business_id', 'stars', 'date', 'text', 'useful', 'funny', 'cool']
    usStates, businessIds = pp.getBusinessInfo(stateAbbPath, dataPath)
    directory = dataPath + 'processed_reviews'
#     stateReviews = {}
    i = 0
#     for state in usStates:
    statePath = reviewPath + state
    j = 0
    if os.path.exists(statePath):
        stateReviews = pd.DataFrame(columns = headers)
        for subdir, _, files in tqdm(os.walk(statePath)):
            for file in files:
                if '.json' in file:
                    with open(os.path.join(subdir, file)) as f:
                        for line in f:
                            reviews = json.loads(line)
                            for review in reviews:
                                if isEnglish(review['text']):
                                    stateReviews.loc[j] = review
                                    j = j + 1
                i = i + 1
    return stateReviews

def cleanReviewText(reviews):
    """
    clean the review text
    """
    for i, review in enumerate(reviews):
        review = sent_tokenize(review)
        reviews[i] = cleanup(review)
    return reviews

def joinWord(words):
    return ''.join([s + ' ' for s in words])[:-1]

def getDict(dictPath):
    dictionary = []
    with open(dictPath) as f:
        for line in tqdm(f):
            values = line.split()
            word = joinWord(values[:-300])
            dictionary.append(word)
    f.close()
    return dictionary

def spellcheck(text):
    dictionary = embeddingDict(embeddingPath)
    text = cleanOp(text, re.compile(r''), dictionary, correctSpell)
    return text

def cleanOp(text, regex, op):
    for i, sentence in enumerate(text):
        if bool(regex.search(sentence)):
            newSentence = ''
            for word in word_tokenize(sentence.lower()):
                if bool(regex.search(word)) and word not in dictionary:
                    word = op(word)
                newSentence = newSentence + ' ' + word
            text[i] = newSentence[1:]
    return text

def cleanTime(word):
    time_re = re.compile(r'^(([01]?\d|2[0-3]):([0-5]\d)|24:00)(pm|am)?$')
    if not bool(time_re.match(word)):
        return word
    else:
        dawn_re = re.compile(r'0?[234]:(\d{2})(am)?$')
        earlyMorning_re = re.compile(r'0?[56]:(\d{2})(am)?$')
        morning_re = re.compile(r'((0?[789])|(10)):(\d{2})(am)?$')
        noon_re = re.compile(r'((11):(\d{2})(am)?)|(((0?[01])|(12)):(\d{2})pm)$')
        afternoon_re = re.compile(r'((0?[2345]):(\d{2})pm)|((1[4567]):(\d{2}))$')
        evening_re = re.compile(r'((0?[678]):(\d{2})pm)|(((1[89])|20):(\d{2}))$')
        night_re = re.compile(r'(((0?9)|10):(\d{2})pm)|((2[12]):(\d{2}))$')
        midnight_re = re.compile(r'(((0?[01])|12):(\d{2})am)|(0?[01]:(\d{2}))|(11:(\d{2})pm)|(2[34]:(\d{2}))$')
        if bool(noon_re.match(word)):
            return 'noon'
        elif bool(evening_re.match(word)):
            return 'evening'
        elif bool(morning_re.match(word)):
            return 'morning'
        elif bool(earlyMorning_re.match(word)):
            return 'early morning'
        elif bool(night_re.match(word)):
            return 'night'
        elif bool(midnight_re.match(word)):
            return 'midnight'
        elif bool(dawn_re.match(word)):
            return 'dawn'
        else:
            return word

def cleanPlus(word):
    return re.sub('\+', ' +', word)

def cleanNumber(word):
    if bool(re.search(r'\d+', word)):
        return word
    else:
        search = re.search(r'\d+', word)
        pos = search.start()
        num = search.group()
        return word[:pos] + ' %s ' % num + parseNumber(word[pos+len(num):])

def checkSpell(word):
    global hobj
    return hobj.spell(word)

def correctSpell(word):
    global hobj
    suggestions = hobj.suggest(word)
    if len(suggestions) != 0:
        distance = [edit_distance(word, s) for s in suggestions]
        return suggestions[distance.index(min(distance))]
    else:
        return word

def splitDashWord(word):
    if '-' not in word:
        return [word]
    else:
        return word.split('-')

def cleanDashWord(word):
    return ''.join([s + ' ' for s in word.split('-')])

def correctDashWord(word):
    splittedWords = word.split('-')
    for i, word in enumerate(splittedWords):
        if not checkSpell(word):
            splittedWords[i] = correctSpell(word)
    return ''.join([s + '-' for s in splittedWords])[:-1]

def cleanup(text):
    text = cleanOp(text, re.compile(r'-'), correctDashWord)
    text = cleanOp(text, re.compile(r'-'), cleanDashWord)
    text = cleanOp(text, re.compile(r':'), cleanTime)
    text = cleanOp(text, re.compile('\+'), cleanPlus)
    text = cleanOp(text, re.compile(r'\d+'), cleanNumber)
    text = cleanOp(text, re.compile(r''), correctSpell)
    return text

def filterWordEmbedding(words, dictPath, state):
    vocabulary = []
    filteredDict = []
    words = [word.lower() for word in words]
    with open(dictPath) as f:
        for line in tqdm(f):
            values = line.split()
            word = joinWord(values[:-300])
            if word in words:
                vocabulary.append(word)
                filteredDict.append(line)
    f.close()
    unknownWords = [word for word in words if word not in vocabulary]
    directory = dataPath + 'state dictionaries/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(directory + '%s_%s.txt' % (cf.DICT[0:-4], state), 'w+') as f:
        for line in filteredDict:
            f.write(line)
    with open(directory + '%s_unknown.txt' % state, 'w+') as f:
        for i, word in enumerate(unknownWords):
            f.write(word + '\n')

def createStateVocabulary(reviews, state):
    words = []
    for review in reviews:
        for sentence in review:
            for word in sentence.split(' '):
                words.append(word)
    words = sorted(set(words))
    global dictPath
    vocabulary = filterWordEmbedding(words, dictPath, state)
    return vocabulary


def createVocabulary():
    usStates = pp.getStateAbbs(stateAbbPath)
    dictionary = []
    directory = dataPath + 'state dictionaries/'
    for state in usStates:
        filepath = directory + '%s_%s.txt' % (cf.DICT[0:-4], state)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                for line in tqdm(f):
                    dictionary.append(line)
            f.close()
    with open(directory + '%s_filtered.txt' % cf.DICT[0:-4], 'w+') as f:
        for line in set(dictionary):
            f.write(line)
    f.close()

dataPath = cf.ROOT_PATH + cf.DATA_PATH
stateAbbPath = dataPath + cf.STATE
reviewPath = dataPath + cf.REVIEW
dictPath = dataPath + cf.DICT

hobj = hunspell.HunSpell(cf.HUNSPELL_PATH + cf.HUNSPELL_DICT[0],
                         cf.HUNSPELL_PATH + cf.HUNSPELL_DICT[1])

parseReviews()
