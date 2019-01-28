""" Iterate over the whole genome (with no looping) to measure genome-wide performance of a trained
neural network """

from __future__ import division
import sys
import numpy as np
import sklearn.metrics
# import sklearn.model_selection as ms
# user defined module
import iterutils as iu
# keras imports
from keras.models import Model
from keras.layers import Dense, Dropout, Activation, Flatten, concatenate, Input, LSTM, Bidirectional
from keras.layers import Conv1D, MaxPooling1D
from keras.optimizers import SGD, Adagrad, Adam
from keras.callbacks import EarlyStopping
from keras.models import model_from_yaml
from keras.models import load_model
from keras import backend as K


def merge_generators(filename,batchsize,seqlen, mode):
    X = iu.train_generator(filename + ".seq", batchsize, seqlen, "seq", mode) 
    A = iu.train_generator(filename + ".chromtracks", batchsize, seqlen, "accessibility", mode)
    y = iu.train_generator(filename + ".labels", batchsize, seqlen, "labels", mode)
    while True:
        yield [X.next(),A.next()], y.next()

def test_on_batch(gen, model, outfile):
    counter = 0 
    while True:
        try:
            print "batch", counter
            [X_test, acc_test], y = gen.next()
            probas = model.predict_on_batch([X_test,acc_test])
            # saving to file: 
            with open(outfile, "a") as fh:
                np.savetxt(fh,probas)
            counter += 1
        except StopIteration: # Catching a propagating exception here, be careful. 
            print "Completed Scan"
            break

if __name__ == "__main__":

    # parse these arguments from the command line eventually. 
    filename = sys.argv[1]
    batchsize = 5000
    seqlen = 500
    mode = "nr"
    outfile = sys.argv[3]
    # loading saved model 
    model = load_model(sys.argv[2])
    # instantiation the generator
    gen = merge_generators(filename, batchsize, seqlen, mode)
    print "instantiated generator"
    # testing on batch 
    test_on_batch(gen, model, outfile) 
    # Performance:
    probas = np.loadtxt(sys.argv[3])
    y = np.loadtxt(filename + ".labels")
    roc_auc = sklearn.metrics.roc_auc_score(y, probas)
    prc = sklearn.metrics.average_precision_score(y, probas)
    print roc_auc, prc

    # getting a rough confusion matrix/precide threshold matrix in eval scripts
    threshold = lambda t: 1 if t >= 0.5 else 0
    npthresh = np.vectorize(threshold)
    pred = npthresh(probas)
    print "Confusion Matrix:\n", sklearn.metrics.confusion_matrix(y, pred)
