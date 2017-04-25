from time import strftime
import logging


def get_logger(name, log_folder, is_process=True, is_set=True):
    logger = logging.getLogger(name)
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                name,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
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
