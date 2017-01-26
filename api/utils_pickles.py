# -*- coding: utf-8 -*-
import io

from six.moves import cPickle as pickle


def pickle_dump(obj, pickle_path):
    with io.open(pickle_path, 'wb') as file_:
        pickle.dump(obj, file_, protocol=-1)  # -1 to select HIGHEST_PROTOCOL available


def pickle_load(pickle_path):
    with io.open(pickle_path, 'rb') as f:
        obj = pickle.load(f)
    return obj