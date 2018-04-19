import tensorflow as tf
import numpy as np
import pandas as pd
import utils
import random

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
init = tf.global_variables_initializer()

saver = tf.train.Saver()

# full dataset training
test_X, test_y, test_seqlen = u.getData('test')
train_X, train_y, train_seqlen = u.getData('train')
loss_train_array = np.zeros([full_iterations])
loss_test_array = np.zeros([full_iterations])
acc_train_array = np.zeros([full_iterations])
acc_test_array = np.zeros([full_iterations])
with tf.Session() as sess:
    sess.run(init)
    for i in range(full_iterations):
        sess.run(optimizer, feed_dict = {X: train_X, y: train_y, seqlen: train_seqlen})
        # if i > 0 and i % 4 == 0:
        loss_train, accuracy_train = sess.run([loss, accuracy], feed_dict = {X: train_X, y: train_y, seqlen: train_seqlen})
        print('step: %s, train loss: %s, train accuracy: %s' % (i, loss_train, accuracy_train))
        loss_test, accuracy_test = sess.run([loss, accuracy], feed_dict = {X: test_X, y: test_y, seqlen: test_seqlen})
        print('step: %s, test loss: %s, test accuracy: %s' % (i, loss_test, accuracy_test))
        loss_train_array[i] = loss_train
        loss_test_array[i] = loss_test
        acc_train_array[i] = accuracy_train
        acc_test_array[i] = accuracy_test
        if (i + 1) % 1 == 0:
            saver.save(sess, './saved_model/aspect', global_step = i + 1)
    np.save('train_loss', loss_train_array)
    np.save('test_loss', loss_test_array)
    np.save('train_acc', acc_train_array)
    np.save('test_acc', acc_test_array)
