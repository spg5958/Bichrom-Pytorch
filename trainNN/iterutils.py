""" Helper module with methods for one-hot sequence encoding and generators to
to enable whole genome iteration """

import h5py
import numpy as np
# import tensorflow as tf

from collections import defaultdict

from seqchromloader import SeqChromDatasetByBed

class Sequence:
    dic = {
        "A": 0,
        "T": 1,
        "G": 2,
        "C": 3
    }

    """ Methods for manipulation of DNA Sequence """
    def __init__(self):
        pass

    @staticmethod
    def map(buf, seqlength):
        numSeq = len(buf)        
        seqLen = len(buf[0])

        # initialize the matrix to seqlen x 4
        seqMatrixs = np.zeros((numSeq,seqLen,4), dtype=int)
        # change the value to matrix
        for i in range(0,numSeq):
            dnaSeq = buf[i].upper()
            seqMatrix = seqMatrixs[i]
            for j in range(0,seqLen):
                    try:
                        seqMatrix[j, Sequence.dic[dnaSeq[j]]] = 1
                    except KeyError:
                        continue
        return seqMatrixs

    @staticmethod
    def add_to_buffer(buf, line):
        buf.append(line.strip())


class Chromatin:
    """ Methods for manipulating discrete chromatin tag counts/ domain calls"""
    def __init__(self):
        pass

    @staticmethod
    def map(buf, seqlen):
        return np.array(buf)

    @staticmethod
    def add_to_buffer(buf, line):
        chrom = line.strip().split()
        val = [float(x) for x in chrom]
        buf.append(val)


def assign_handler(dtype):
    """ Choosing class based on input file type"""
    if dtype == "seq":
        # use Sequence methods
        handler = Sequence
    else:
        # use Chromatin methods
        handler = Chromatin
    return handler


def train_generator(h5file, filename, batchsize, seqlen, dtype, iterflag):
    """ A generator to return a batch of training data, while iterating over the file in a loop. """
    handler = assign_handler(dtype)
    with open(filename, "r") as fp:
        line_index = 0
        buf = [] # buf is my feature buffer
        while True:
            for line in fp:
                if line_index < batchsize:
                        handler.add_to_buffer(buf, line)
                        line_index += 1
                else:
                    yield handler.map(buf, seqlen)
                    buf = [] # clean buffer
                    handler.add_to_buffer(buf, line)
                    line_index = 1 # reset line index
            if iterflag == "repeat":
                # reset file pointer
                fp.seek(0)
            else:
                yield handler.map(buf, seqlen)
                break

def train_generator_h5(h5file, dspath, batchsize, seqlen, dtype, iterflag):
    """ A generator to return a batch of training data, while iterating over the file in a loop. """
    with h5py.File(h5file, 'r', libver='latest', swmr=True) as h5:
        ds = h5[dspath][:]
        num_samples = ds.shape[0]
        dim = len(ds.shape)
        
        start_index = 0
        end_index = 0
        while True:
            start_index = end_index
            end_index += batchsize
            if end_index >= num_samples:
                if iterflag == "repeat":
                    # reset
                    c1 = ds[start_index:num_samples]
                    end_index = batchsize - c1.shape[0]
                    c2 = ds[0: end_index]
                    chunk = np.vstack([c1, c2]) if dim>1 \
                        else np.concatenate([c1, c2])
                    yield chunk
                else:
                    yield ds[start_index:num_samples]
                    break
            else:
                yield ds[start_index:end_index]

def train_TFRecord_dataset(dspath, batchsize, dataflag, shuffle=True, drop_remainder=True):
    
    loader=None
    genome="/storage/home/spg5958/group/genomes/mm10/mm10.fa"
    chromtracks=["../sample_data/GSE80482_h3k27ac-0h.bw", \
                 "../sample_data/GSE80482_h3k27ac-12h.bw"]
    dataloader_kws={"num_workers":4,"batch_size":batchsize}
    
    print(dspath)
    loader=SeqChromDatasetByBed(dspath["TFRecord"],genome,chromtracks,dataloader_kws=dataloader_kws)

#     if dataflag=="seqonly":
#         loader=SeqChromDatasetByBed(dspath["TFRecord"],genome,chromtracks,dataloader_kws=dataloader_kws)
#     else:
#         loader=SeqChromDatasetByBed(dspath["TFRecord"],genome,chromtracks,dataloader_kws=dataloader_kws)
#         return {"seq":seq, "chrom_input":combined_chromatin_data}, label

    return loader
    
