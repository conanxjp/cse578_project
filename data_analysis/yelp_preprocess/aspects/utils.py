import os
import sys
import tensorflow as tf
import random
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import config as cf


class UTILS(object):
    ######################################
    # load all data files                #
    ######################################
    def __init__(self, batch_size = 32, dim_sentence = 80, dim_aspect = 3, isSample = True):
        # data file paths
        self.dataPath = cf.ROOT_PATH + cf.DATA_PATH
        if isSample:
            self.trainPath = self.dataPath + 'rest_train_sample.csv'
            self.testPath = self.dataPath + 'rest_test_sample.csv'
            self.trainEncodePath = self.dataPath + 'train_sample.npy'
            self.testEncodePath = self.dataPath + 'test_sample.npy'
        else:
            self.trainPath = self.dataPath + 'rest_train_2014_processed.csv'
            self.testPath = self.dataPath + 'rest_test_2014_processed.csv'
            self.trainEncodePath = self.dataPath + 'train.npy'
            self.testEncodePath = self.dataPath + 'test.npy'

        self.glovePath = self.dataPath + 'glove.npy'

        # hyperparameters of model
        self.batch_size = batch_size
        self.dim_sentence = dim_sentence
        self.dim_aspect = dim_aspect
        self.loadData()

    # loading all data
    def loadData(self):
        self.trainData = pd.read_csv(self.trainPath)
        self.testData = pd.read_csv(self.testPath)
        self.trainEncode = np.load(self.trainEncodePath)
        self.testEncode = np.load(self.testEncodePath)
        self.allEncode = np.concatenate((self.trainEncode, self.testEncode), 0)
        self.gloveDict = np.array(np.load(self.glovePath), dtype = 'float32')
        # self.aspect_indices = [[], [], [], [], []]
        self.aspect_encode = {'food': 0, 'price': 1, 'service': 2, 'ambience': 3, 'anecdotes/miscellaneous': 4}

        self.allData = pd.concat([self.trainData, self.testData])
        self.trainData, self.testData, self.trainEncode, self.testEncode = train_test_split(self.allData, self.allEncode, test_size = 0.1)
        for key, val in self.aspect_encode.items():
            # self.aspect_indices[val] = self.trainData.loc[self.trainData['aspect'] == key, 'aspect'].index
            self.trainData.loc[self.trainData['aspect'] == key, 'aspect'] = val
            self.testData.loc[self.testData['aspect'] == key, 'aspect'] = val
        # don't know why the polarity column in testData after above is object instead of int which causes problems later
        # so explicitly cast type here
        self.testData['aspect'] = [int(p) for p in self.testData['aspect']]
        self.trainData['aspect'] = [int(p) for p in self.trainData['aspect']]


    ######################################
    # helper functions                   #
    ######################################
    # get indices for next batch
    def getNextBatchIndices(self, batch_size):
        idx_X = [random.choice(self.aspect_indices[i % self.dim_aspect]) for i in range(self.batch_size)]
        # idx_X = [random.choice(self.trainData.index) for i in range(self.batch_size)]
        return idx_X

    # get the sentence index encoding for the batch
    def getSeqlen(self, indices):
        return [len(sentence) for sentence in self.trainEncode[indices]]

    # pad the sentence index encoding to dim_sentence
    def padEncoding(self, indices):
        return [np.pad(self.trainEncode[i], (0, self.dim_sentence - len(self.trainEncode[i])), 'constant') for i in indices]

    # get one hot representation for the batch labels
    def getOnehot(self, indices):
        onehot = np.zeros([self.batch_size, self.dim_aspect])
        onehot[np.arange(self.batch_size), self.trainData.loc[indices, 'aspect']] = 1
        return onehot

    def getOnehottest(self, indices, size):
        onehot = np.zeros([size, self.dim_aspect])
        onehot[np.arange(size), self.testData.loc[indices, 'aspect']] = 1
        return onehot

    # get model required data for the next training batch
    def nextBatch(self, batch_size):
        indices = self.getNextBatchIndices(batch_size)
        seqlen = self.getSeqlen(indices)
        X = self.padEncoding(indices)
        y = self.getOnehot(indices)
        return X, y, seqlen

    # get all data for model
    def getData(self, aim):
        aims = {'train': [self.trainEncode, self.trainData], 'test': [self.testEncode, self.testData]}
        X = [np.pad(aims[aim][0][i], (0, self.dim_sentence - len(aims[aim][0][i])), 'constant') for i in range(len(aims[aim][0]))]
        y = np.zeros([len(aims[aim][0]), self.dim_aspect])
        y[np.arange(len(aims[aim][0])), aims[aim][1]['aspect']] = 1
        seqlen = [len(sentence) for sentence in aims[aim][0]]
        return X, y, seqlen
