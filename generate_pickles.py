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

from handler import WPHandler


def get_args():
    parser = argparse.ArgumentParser(description='Script to generate pickle files of articles in given path.')
    parser.add_argument('-p', '--path', help='Path where list of articles are saved', required=True)
    parser.add_argument('-f', '--pickle_folder', help='Folder where pickle files will be stored', required=True)
    parser.add_argument('-t', '--thread', type=int, help='Number of threads per core', required=False)
    parser.add_argument('-s', '--start', type=int, help='From range', required=False)
    parser.add_argument('-e', '--end', type=int, help='To range', required=False)

    args = parser.parse_args()

    return args


def generate_pickle(article_name, pickle_folder):
    article_name = article_name.replace(" ", "_").replace("/", "0x2f")
    if not exists('{}/{}.p'.format(pickle_folder, article_name)):
        with WPHandler(article_name, pickle_folder) as wp:
            wp.handle([], 'json', is_api=False)
    # else:
    #     print('Already processed: ', article_name)
    return True


def main():
    args = get_args()
    path = args.path
    pickle_folder = args.pickle_folder
    max_workers = args.thread or 5
    start = args.start
    end = args.end
    article_list_files = OrderedDict()
    file_list = listdir(path)
    file_list.sort()
    for f in file_list:
        if isfile(join(path, f)):
            pos1 = f.find("-")
            pos2 = f.find(".")
            if pos1 > -1 and pos2 > -1:
                i = int(f[pos1+1:pos2])
                article_list_files[join(path, f)] = i
    # article_list_files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]
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
                    future_to_article = {executor.submit(generate_pickle, article[0],  pickle_folder): article[0]
                                         for article in input_articles}
                    for future in concurrent.futures.as_completed(future_to_article):
                        article_name = future_to_article[future]
                        try:
                            data = future.result()
                        except Exception as exc:
                            logging.exception(article_name)
                        # else:
                        #     print('Success: {}'.format(article_name))
            print('Done: {}'.format(article_list_file))

if __name__ == '__main__':
    main()
