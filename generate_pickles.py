# -*- coding: utf-8 -*-
"""
This script runs both with py3 and py2. But py3 works better concurrently and also for smaller and faster pickle
generation.
"""
import argparse
from collections import OrderedDict
from os import listdir
from os.path import isfile, join, exists, basename
import csv
import concurrent.futures
import logging
import re
from time import strftime

from handler import WPHandler


"""
Example usage:
python generate_pickles.py -s 311 -e 314 -p '/home/kenan/PycharmProjects/wikiwho_stats/ww/all_articles_list' -f '/home/kenan/PycharmProjects/wikiwho_stats/ww/all_articles_list/pickles/missing' -m 40
"""


def get_args():
    parser = argparse.ArgumentParser(description='Script to generate pickle files of articles in given path.')
    parser.add_argument('-p', '--path', help='Path where list of articles are saved', required=True)
    parser.add_argument('-f', '--pickle_folder', help='Folder where pickle files will be stored', required=True)
    parser.add_argument('-f2', '--pickle_folder_2', help='Second folder where pickle files are stored', required=False)
    parser.add_argument('-m', '--max_workers', type=int, help='Number of threads/processors to run parallel.',
                        required=True)
    parser.add_argument('-ppe', '--processor_pool_executor', action='store_true',
                        help='Use ProcessPoolExecutor, default is ThreadPoolExecutor', default=False, required=False)
    parser.add_argument('-s', '--start', type=int, help='From range', required=False)
    parser.add_argument('-e', '--end', type=int, help='To range', required=False)

    args = parser.parse_args()

    return args


def generate_pickle(article_name, already_list_file, pickle_folder, pickle_folder_2=''):
    pickle_article_name = article_name.replace(" ", "_").replace("/", "0x2f")
    pickle_path = '{}/{}.p'.format(pickle_folder, pickle_article_name)
    pickle_path_2 = '{}/{}.p'.format(pickle_folder_2, pickle_article_name) if pickle_folder_2 else ''
    already = exists(pickle_path)
    already = exists(pickle_path_2) if not already and pickle_folder_2 else already
    if not already:
        with WPHandler(article_name, pickle_folder) as wp:
            wp.handle([], 'json', is_api=False)
    # else:
    #     print('Already processed: ', article_name)
    return True


def main():
    args = get_args()
    path = args.path
    pickle_folder = args.pickle_folder
    pickle_folder_2 = args.pickle_folder_2
    max_workers = args.max_workers
    is_ppe = args.processor_pool_executor
    start = args.start
    end = args.end

    file_list = [join(path, f) for f in listdir(path) if isfile(join(path, f)) and re.search(r'-(\d*).', f)]
    ordered_file_list = sorted(file_list, key=lambda x: (int(re.search(r'-(\d*).', x).group(1)), x))
    article_list_files = OrderedDict()
    counter = 0
    for f in ordered_file_list:
        i = int(re.search(r'-(\d*).', f).group(1))
        if counter == 0 and not start and start != 0:
            start = i
        if counter == len(ordered_file_list) - 1 and not end and end != 0:
            end = i
        article_list_files[join(path, f)] = i
        counter += 1

    logging.basicConfig(level=logging.ERROR,
                        format='%(levelname)s:%(name)s:%(asctime)s:%(message)s')
    logger = logging.getLogger('')
    already_list_file = '{}/logs/already_at_{}.txt'.format(path, strftime("%H:%M:%S %d-%m-%Y"))
    for article_list_file in article_list_files:
        if start <= article_list_files[article_list_file] <= end:
            print('Start: {} at {}'.format(article_list_file, strftime("%H:%M:%S %d-%m-%Y")))
            handler = logging.FileHandler('{}/logs/{}_at_{}.log'.format(path,
                                                                        basename(article_list_file).split('.')[0],
                                                                        strftime("%Y-%m-%d-%H:%M:%S")))
            # print(logger.handlers)
            # logger.removeHandler(logging.StreamHandler)
            # logger.addHandler(handler)
            logger.handlers = [handler]
            success_list_file = '{}/logs/success_{}_at_{}.txt'.format(path, article_list_files[article_list_file],
                                                                      strftime("%H:%M:%S %d-%m-%Y"))
            fail_list_file = '{}/logs/failed_{}_at_{}.txt'.format(path, article_list_files[article_list_file],
                                                                strftime("%H:%M:%S %d-%m-%Y"))
            with open(article_list_file, 'r') as csv_file:
                input_articles = csv.reader(csv_file, delimiter=";")
                # for article in input_articles:
                #     try:
                #         generate_pickle(article[0], already_list_file, pickle_folder, pickle_folder_2)
                #         with open(success_list_file, 'a') as f:
                #             f.write('{}\n'.format(article[0]))
                #     except Exception as exc:
                #         logger.exception(article[0])
                #         with open(fail_list_file, 'a') as f:
                #             f.write('{}\n'.format(article[0]))

                # We can use a with statement to ensure threads are cleaned up promptly
                if is_ppe:
                    # use ProcessPoolExecutor
                    print('Not implemented')  # FIXME requests.session throws sslerror
                    # with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                    #     # Start the load operations and mark each future with its article
                    #     future_to_article = {executor.submit(generate_pickle, article[0], already_list_file,  pickle_folder, pickle_folder_2):
                    #                          article[0]
                    #                          for article in input_articles}
                    #     for future in concurrent.futures.as_completed(future_to_article):
                    #         article_name = future_to_article[future]
                    #         try:
                    #             data = future.result(timeout=None)
                    #         except Exception as exc:
                    #             # TODO use queue or lock for logging with multiPROCESSING
                    #             # https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
                    #             logger.exception(article_name)
                    #         # else:
                    #         #     print('Success: {}'.format(article_name))
                else:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Start the load operations and mark each future with its article
                        future_to_article = {executor.submit(generate_pickle, article[0], already_list_file,  pickle_folder, pickle_folder_2):
                                             article[0]
                                             for article in input_articles}
                        for future in concurrent.futures.as_completed(future_to_article):
                            article_name = future_to_article[future]
                            try:
                                data = future.result(timeout=None)
                            except Exception as exc:
                                # no need for lock, logger is thread safe
                                logger.exception(article_name)
                            # else:
                            #     print('Success: {}'.format(article_name))
            print('Done: {} at {}'.format(article_list_file, strftime("%H:%M:%S %d-%m-%Y")))

if __name__ == '__main__':
    main()
