import json
import pandas as pd
import numpy as np
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


def loadDictionary():
    with open(dataPath + '%s_filtered.txt' % cf.WORD2VEC_FILE[0:-4], 'r') as f:
        for line in f:
            values = line.split()
            word = pp.joinWord(values[:-300])
            vector = np.array(values[-300:], dtype='float32')
            dictionary[word] = vector
    f.close()

def encodeReview(filePath, state):
    index = list(dictionary.keys())
    header = ['reviewid', 'sentence', 'length']
    encoding = pd.DataFrame(columns = header)
    with open(filePath) as json_data:
        max = 0
        j = 0
        reviewIndex = []
        for i, line in enumerate(json_data):
            reviews = json.loads(line)
            for review in tqdm(reviews):
                texts = review['text']
                reviewId = review['review_id']
                sentences = sent_tokenize(texts)
                for sentence in sentences:
                    words = word_tokenize(sentence)
                    encoding.loc[j] = [reviewId, sentence, len(words)]
                    j = j + 1
                    sentenceIndex = []
                    for word in words:
                        try:
                            idx = index.index(word)
                        except ValueError:
                            idx = 4859
                        sentenceIndex.append(idx)
                    if max < len(sentenceIndex):
                        max = len(sentenceIndex)
                    reviewIndex.append(sentenceIndex)
    print(max)
    np.save(dataPath + '%s' % state, np.array(reviewIndex))
    encoding.to_csv(dataPath + '%s.csv' % state, index = False)


def run_aspect(reviewFile, encodeFile):
    # hyperparameters
    batch_iterations = 10000
    batch_size = 32
    full_iterations = 200
    learning_rate = 0.001
    reg_eta = 0.001

    # dimensionalities
    dim_lstm = 300
    dim_word = 300
    dim_aspect = 5
    dim_sentence = 80

    # setup utils object
    isSample = True
    u = utils.UTILS(batch_size, dim_sentence, dim_aspect, isSample)

    # define tf placeholders
    X = tf.placeholder(tf.int32, [None, dim_sentence])
    y = tf.placeholder(tf.float32, [None, dim_aspect])
    seqlen = tf.placeholder(tf.int32, [None])

    # define tf variables
    with tf.variable_scope('bilstm_vars'):
        with tf.variable_scope('weights', reuse = tf.AUTO_REUSE):
            lstm_w = tf.get_variable(
                name = 'softmax_w',
                shape = [dim_lstm * 2, dim_aspect],
                initializer = tf.random_uniform_initializer(-0.003, 0.003),
                regularizer = tf.contrib.layers.l2_regularizer(reg_eta)
            )
        with tf.variable_scope('biases', reuse = tf.AUTO_REUSE):
            lstm_b = tf.get_variable(
                name = 'softmax_b',
                shape = [dim_aspect],
                initializer = tf.random_uniform_initializer(-0.003, 0.003),
                regularizer = tf.contrib.layers.l2_regularizer(reg_eta)
            )


    # define lstm model
    def dynamic_lstm(inputs, seqlen):
        inputs = tf.nn.dropout(inputs, keep_prob=1.0)
        with tf.name_scope('bilstm_model'):
            forward_lstm_cell = tf.contrib.rnn.LSTMCell(dim_lstm)
            backward_lstm_cell = tf.contrib.rnn.LSTMCell(dim_lstm)
            outputs, states = tf.nn.bidirectional_dynamic_rnn(
                forward_lstm_cell,
                backward_lstm_cell,
                inputs = inputs,
                sequence_length = seqlen,
                dtype = tf.float32,
                scope = 'bilstm'
            )
            forward_outputs, backward_outputs = outputs
            backward_outputs = tf.reverse_sequence(backward_outputs, tf.cast(seqlen, tf.int64), seq_dim=1)
            outputs = tf.concat([forward_outputs, backward_outputs], 2)
            size = tf.shape(outputs)[0]
            index = tf.range(0, size) * dim_sentence + seqlen - 1
            output = tf.gather(tf.reshape(outputs, [-1, dim_lstm * 2]), index)  # batch_size * n_hidden * 2
        predict = tf.matmul(output, lstm_w) + lstm_b
        return predict

    # define operations
    pred = dynamic_lstm(tf.nn.embedding_lookup(u.gloveDict, X), seqlen)
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits = pred, labels = y))
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(loss)
    correct = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))

    saver = tf.train.Saver()

    reviews = pd.read_csv(reviewFile)
    reviewEncode = np.load(encodeFile)
    reviewEncode = np.pad(reviewEncode, (0, dim_sentence - len(words)), 'constant')
    with tf.Session() as sess:

        saver = tf.train.import_meta_graph('./saved_model/aspect-200.meta')
        saver.restore(sess, tf.train.latest_checkpoint('./saved_model'))





dictionary = {}
dataPath = cf.ROOT_PATH + cf.DATA_PATH
loadDictionary()
encodeReview(dataPath + 'AZ_reviews.json', 'AZ')
