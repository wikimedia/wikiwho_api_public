# -*- coding: utf-8 -*-
"""
This script runs only with py3.
"""
import argparse
from collections import OrderedDict
from os import listdir
from os.path import isfile, join, exists, basename
import csv
import concurrent.futures
import logging
import re

from handler import WPHandler


def get_args():
    parser = argparse.ArgumentParser(description='Script to generate pickle files of articles in given path.')
    parser.add_argument('-p', '--path', help='Path where list of articles are saved', required=True)
    parser.add_argument('-f', '--pickle_folder', help='Folder where pickle files will be stored', required=True)
    parser.add_argument('-f2', '--pickle_folder_2', help='Second folder where pickle files are stored', required=False)
    parser.add_argument('-t', '--thread', type=int, help='Number of threads per core', required=False)
    parser.add_argument('-s', '--start', type=int, help='From range', required=False)
    parser.add_argument('-e', '--end', type=int, help='To range', required=False)

    args = parser.parse_args()

    return args


def generate_pickle(article_name, pickle_folder, pickle_folder_2=''):
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
    max_workers = args.thread or None
    start = args.start
    end = args.end

    file_list = [join(path, f) for f in listdir(path) if isfile(join(path, f)) and re.search(r'-(\d*).', f)]
    ordered_file_list = sorted(file_list, key=lambda x: (int(re.search(r'-(\d*).', x).group(1)), x))
    article_list_files = OrderedDict()
    for f in ordered_file_list:
        article_list_files[join(path, f)] = int(re.search(r'-(\d*).', f).group(1))

    start = 0 if not start and end else start
    end = len(article_list_files) - 1 if not end and start else end

    for article_list_file in article_list_files:
        if not (start or end) or start <= article_list_files[article_list_file] <= end:
            print('Start: {}'.format(article_list_file))
            logging.basicConfig(level=logging.ERROR,
                                filename='{}/logs/{}.log'.format(path,
                                                                 basename(article_list_file).split('.')[0]),
                                format='%(levelname)s:%(name)s:%(asctime)s:%(message)s')
            with open(article_list_file, 'r') as csv_file:
                input_articles = csv.reader(csv_file, delimiter=";")

                # We can use a with statement to ensure threads are cleaned up promptly
                # with concurrent.futures.ProcessPoolExecutor() as executor:
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Start the load operations and mark each future with its article
                    future_to_article = {executor.submit(generate_pickle, article[0],  pickle_folder, pickle_folder_2):
                                         article[0]
                                         for article in input_articles}
                    for future in concurrent.futures.as_completed(future_to_article):
                        article_name = future_to_article[future]
                        try:
                            data = future.result(timeout=None)
                        except Exception as exc:
                            logging.exception(article_name)
                        # else:
                        #     print('Success: {}'.format(article_name))
            print('Done: {}'.format(article_list_file))

if __name__ == '__main__':
    main()
