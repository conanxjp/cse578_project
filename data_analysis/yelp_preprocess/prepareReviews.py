import json
import pandas as pd
from nltk.tokenize import sent_tokenize
from nltk.metrics import edit_distance
from nltk import (word_tokenize, pos_tag)
import hunspell
import argparse
import sys
import os
import re
from tqdm import tqdm
import config as cf
import preprocess as pp



def loadReviews():
    """
    load all reviews for each business id, consolidate them based on state and
    store as csv file for further preprocessing the text in them
    """
    usStates = pp.getStateAbbs(stateAbbPath)
    for state in usStates:
        directory = dataPath + 'review/' + state
        if not os.path.exists(directory):
            continue
        reviews = pd.DataFrame(columns = ['review_id', 'user_id', 'business_id', 'stars', 'date', 'text', 'useful', 'funny', 'cool'])
        i = 0
        for subdir, _, files in tqdm(os.walk(directory)):
            for j, file in enumerate(files):
                # if j > 2:
                #     break
                if '_reviews.json' in file:
                    city = subdir.split('/')[-1]
                    print('load %s in %s, %s' % (file, city, state))
                    with open(os.path.join(subdir, file), 'r') as f:
                        for line in f:
                            data = json.loads(line)

                            for review in data:
                                reviews.loc[i] = [review[col] for col in reviews.columns.values]
                                i = i + 1
                    f.close()
        directory = dataPath + 'processed_reviews/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        print('write %s reviews to csv file' % state)
        reviews.to_csv(directory + '%s_reviews.csv' % state)

def cleanReviewText():
    """
    clean the review text
    """
    directory = dataPath + 'processed_reviews/'
    dictionary = getDict(dictPath)
    for _, _, files in tqdm(os.walk(directory)):
        for file in files:
            texts = []
            if '_reviews.csv' in file:
                state = file[0:2]
                reviews = pd.read_csv(os.path.join(directory, file), 'r')
                for i, review in enumerate(reviews):
                    # texts[review['review_id']] = []
                    text = sent_tokenize(reviews['text'])
                    text = cleanup(text, dictionary)
                    reviews.loc[i]['text'] = text
                    [texts.append(sentence) for sentence in text]
            createStateVocabulary(texts, state)

def cleanup(text, dictionary):
    text = cleanOp(text, re.compile(r'-'), dictionary, correctDashWord)
    text = cleanOp(text, re.compile(r'-'), dictionary, cleanDashWord)
    text = cleanOp(text, re.compile(r':'), dictionary, cleanTime)
    text = cleanOp(text, re.compile('\+'), dictionary, cleanPlus)
    text = cleanOp(text, re.compile(r'\d+'), dictionary, cleanNumber)
    text = cleanOp(text, re.compile(r''), dictionary, correctSpell)
    return wordData

def getDict(dictPath):
    dictionary = []
    with open(dictPath) as f:
        for line in tqdm(f):
            values = line.split()
            word = values[0]
            dictionary.append(word)
    f.close()
    return dictionary

def spellcheck(wordData):
    dictionary = embeddingDict(embeddingPath)
    wordData = cleanOp(wordData, re.compile(r''), dictionary, correctSpell)
    return wordData

def cleanOp(wordData, regex, dictionary, op):
    for i, sentence in enumerate(wordData):
        if bool(regex.search(sentence)):
            newSentence = ''
            for word in word_tokenize(sentence.lower()):
                if bool(regex.search(word)) and word not in dictionary:
                    word = op(word)
                newSentence = newSentence + ' ' + word
            wordData[i] = newSentence[1:]
    return wordData

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
    with open(dataPath + '%s_%s.txt' % (cf.DICT[0:-4], state), 'w+') as f:
        for line in filteredDict:
            f.write(line)
    with open('%s_unknown.txt' % state, 'w+') as f:
        for i, word in enumerate(unknownWords):
            f.write(word + '\n')


if __name__ == '__main__':

    dataPath = cf.ROOT_PATH + cf.DATA_PATH
    stateAbbPath = dataPath + cf.STATE
    dictPath = dataPath + cf.DICT
    loadReviews()
