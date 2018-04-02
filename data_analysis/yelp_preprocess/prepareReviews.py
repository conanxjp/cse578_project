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



def loadReviews():
    """
    load review.json file and filter the reviews based on business ids,
    consolidate them based on state and store as csv file for further
    preprocessing the text in them
    """
    usStates, businessIds = pp.getBusinessInfo(stateAbbPath, dataPath)

    # parse based on state
    headers = ['review_id', 'user_id', 'business_id', 'stars', 'date', 'text', 'useful', 'funny', 'cool']
    directory = dataPath + 'processed_reviews'
    reviews = {}
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(reviewPath) as json_data:
        print('parsing review data based on state names')
        for i, line in enumerate(tqdm(json_data)):
            if i > 500:
                break
            review = json.loads(line)
            state, city = pp.checkBusinessLocation(review['business_id'], businessIds)
            if state is not None:
                # print(list(review.values()))
                # if state not in reviews.keys():
                #     reviews[state] = []
                # reviews[state].append(review.values())
                filepath = directory + '/%s_reviews.csv' % state
                mode = 'a'
                if not os.path.exists(filepath):
                    mode = 'w+'
                with open(filepath, mode) as f:
                    writer = csv.writer(f)
                    if mode == 'w+':
                        writer.writerow(headers)
                    writer.writerow(review.values())
    # json_data.close()
    # for state, review in reviews.items():
    #     filepath = directory + '/%s_reviews.csv' % state
    #     review_df = pd.DataFrame(review, columns = headers)
    #     review_df.to_csv(filepath)

def cleanReviewText():
    """
    clean the review text
    """
    directory = dataPath + 'processed_reviews/'
    print('load dictionary')
    dictionary = getDict(dictPath)
    usStates = pp.getStateAbbs(stateAbbPath)
    for state in tqdm(usStates):
        filepath = directory + '%s_reviews.csv' % state
        texts = []
        if os.path.exists(filepath):
            reviews = pd.read_csv(filepath)
            for i, text in enumerate(reviews['text']):
                text = sent_tokenize(text)
                text = cleanup(text, dictionary)
                reviews.at[i, 'text'] = text
                [texts.append(sentence) for sentence in text]
            cleanFilepath = directory + '%s_clean_reviews.csv' % state
            reviews.to_csv(cleanFilepath)
            print('create %s vocabulary' % state)
            createStateVocabulary(texts, state)

def cleanup(text, dictionary):
    text = cleanOp(text, re.compile(r'-'), dictionary, correctDashWord)
    text = cleanOp(text, re.compile(r'-'), dictionary, cleanDashWord)
    text = cleanOp(text, re.compile(r':'), dictionary, cleanTime)
    text = cleanOp(text, re.compile('\+'), dictionary, cleanPlus)
    text = cleanOp(text, re.compile(r'\d+'), dictionary, cleanNumber)
    text = cleanOp(text, re.compile(r''), dictionary, correctSpell)
    return text

def getDict(dictPath):
    dictionary = []
    with open(dictPath) as f:
        for line in tqdm(f):
            values = line.split()
            word = values[0]
            dictionary.append(word)
    f.close()
    return dictionary

def spellcheck(text):
    dictionary = embeddingDict(embeddingPath)
    text = cleanOp(text, re.compile(r''), dictionary, correctSpell)
    return text

def cleanOp(text, regex, dictionary, op):
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
        elif bool(dawb_re.match(word)):
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

def createStateVocabulary(texts, state):
    words = sorted(set([word for l in texts for word in l.split(' ')]))
    global dictPath
    vocabulary = filterWordEmbedding(words, dictPath, state)
    return vocabulary

def filterWordEmbedding(words, dictPath, state):
    vocabulary = []
    filteredDict = []
    words = [word.lower() for word in words]
    with open(dictPath) as f:
        for line in tqdm(f):
            values = line.split()
            word = values[0]
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


if __name__ == '__main__':

    dataPath = cf.ROOT_PATH + cf.DATA_PATH
    stateAbbPath = dataPath + cf.STATE
    reviewPath = dataPath + cf.REVIEW
    dictPath = dataPath + cf.DICT

    hobj = hunspell.HunSpell(cf.HUNSPELL_PATH + cf.HUNSPELL_DICT[0],
                             cf.HUNSPELL_PATH + cf.HUNSPELL_DICT[1])
    loadReviews()
    cleanReviewText()
    createVocabulary()
