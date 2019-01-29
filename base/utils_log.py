from os.path import exists, join
from os import mkdir
from time import strftime
import logging


def get_logger(name, log_folder, is_process=True, is_set=True, language=None, level=logging.INFO):
    if language:
        log_folder = join(log_folder, 'logs')
        if not exists(log_folder):
            mkdir(log_folder)
        log_folder = join(log_folder, language)
    else:
        log_folder = join(log_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    file_handler = logging.FileHandler(join(log_folder,'{}_at_{}.log'.format(name,
                                                                strftime("%Y-%m-%d-%H:%M:%S"))))

    if is_process:
        format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
    else:
        format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    if is_set:
        logger.handlers = [file_handler]
    else:
        logger.addHandler(file_handler)
    return logger


def get_base_logger(name, log_folder, level=logging.DEBUG):
    if not exists(log_folder):
        mkdir(log_folder)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(join(log_folder, f'{name}.log'))
    fh.setLevel(level)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


def get_stream_base_logger(name, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(ch)

    return logger

