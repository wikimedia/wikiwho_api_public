# -*- coding: utf-8 -*-
import time
# import os
import io
import fcntl
import errno
from os.path import getsize

from six.moves import cPickle as pickle

from django.conf import settings


class OpenFileLock:
    """
    Modified from:
    https://github.com/derpston/python-simpleflock
    """
    def __init__(self, path, mode, timeout=None):
        self._path = path
        self._mode = mode
        self._timeout = timeout
        self._fd = None

    def __enter__(self):
        self._fd = io.open(self._path, self._mode)
        if self._timeout:
            start_lock_search = time.time()
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Lock acquired!
                # if self._mode == 'rb':
                #     # TODO do not prevent other reads, just check if file is locked.
                #     # but then it is possible that during reading, file is over written by some other process
                #     # and read data is not correct
                #     # if read mode, check only if file is locked
                #     fcntl.flock(self._fd, fcntl.LOCK_UN)
                return self._fd
            except (OSError, IOError) as ex:
                if ex.errno != errno.EAGAIN:  # Resource temporarily unavailable
                    raise
                elif self._timeout is not None and time.time() > (start_lock_search + self._timeout):
                    # Exceeded the user-specified timeout.
                    raise
            # without a delay is also undesirable.
            time.sleep(0.1)

    def __exit__(self, *args):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        # os.close(self._fd)
        self._fd.close()


def pickle_dump(obj, pickle_path):
    # try to lock file:
    # 1) if not already locked, then lock, write and then unlock
    # 2) if already locked, wait until unlocked (in timeout) and then lock, write and unlock
    with OpenFileLock(pickle_path, 'wb', timeout=settings.PICKLE_OPEN_TIMEOUT) as f:
        pickle.dump(obj, f, protocol=-1)  # -1 to select HIGHEST_PROTOCOL available
    # print('?', f.closed)


def pickle_load(pickle_path):
    # try to lock file:
    # 1) if not already locked, then lock, read and then unlock
    # 2) if already locked, wait until unlocked (in timeout) and then lock, read and unlock
    retries = 3
    while retries:
        retries -= 1
        try:
            with OpenFileLock(pickle_path, 'rb', timeout=settings.PICKLE_OPEN_TIMEOUT) as f:
                obj = pickle.load(f)
            return obj
        except EOFError:
            # EOFError Ran out of input
            # EOFError usually happens when pickle file is empty (size 0)
            # TODO is this case valid for us? is this True
            time.sleep(0.1)
            if not retries:
                raise


def get_pickle_size(page_id):
    pickle_path = "{}/{}.p".format(settings.PICKLE_FOLDER, page_id)
    try:
        size = getsize(pickle_path)  # [byte]
    except FileNotFoundError:
        size = 0
    return size
