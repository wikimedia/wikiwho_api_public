# -*- coding: utf-8 -*-
"""
Workflow for partitioning:
1) split -d --lines=21000000 mac-tokens-all.csv /home/nuser/dumps/wikiwho_dataset/partitions/tokens/mac-tokens-all.csv_part
2) adjust_paritions.py for all tokens
# 3) python wikiwho/tools_dataset/split_the_dataset.py -i 'wikiwho_currentcontent_20161226_test.csv' -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/' -s 500000 -t 11523567 -m 1
3) python wikiwho/tools_dataset/split_the_dataset.py -i 'wikiwho_currentcontent_20161226_test.csv' -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/' -m 4
4) python wikiwho/tools_dataset/split_the_dataset.py -i 'mac-revisions-all.tsv' -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/' -m 2
5) python wikiwho/tools_dataset/split_the_dataset.py -i 'mac-articles-all.txt' -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/' -m 3
6) delete_from_all_content.py to substract current content from all content in order to get deleted content
"""
import csv
import argparse
import sys
from os.path import exists
from os import mkdir, listdir


def write_into_partition_file(first_article_id_in_part, last_article_id_in_part, output_folder,
                              header, partition_content, output_name, output_counter=None, total_files=None):
    partition_file = '{}-20161226-part{}-{}-{}.csv'.format(output_name, output_counter,
                                                           first_article_id_in_part,
                                                           last_article_id_in_part)
    with open(output_folder + '/' + partition_file, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(header)
        writer.writerows(partition_content)

    if output_counter and total_files:
        sys.stdout.write('\r{}-{:.3f}%'.format(output_counter, output_counter*100/total_files))
    elif output_counter:
        sys.stdout.write('\r{}'.format(output_counter))
    return True


def split_tokens_with_size(base_path, current_content_file, partition_size, total_size, output_name):
    output_folder = '{}/{}'.format(base_path, 'partitions')
    if not exists(output_folder):
        mkdir(output_folder)
    output_folder = '{}/{}'.format(output_folder, 'current_tokens' if output_name == 'current_content' else output_name)
    if not exists(output_folder):
        mkdir(output_folder)
    total_files = int(total_size/partition_size)
    with open(base_path + '/' + current_content_file, newline='') as f:
        reader = csv.reader(f)
        article_id = None
        partition_content = []
        output_counter = 1
        header = next(reader)
        for i, row in enumerate(reader, 1):
            # if 'article_id' == row[0]:
            #     header = row
            #     continue
            if article_id is None:
                first_article_id_in_part = int(row[0])
            if i >= (partition_size * output_counter) and article_id != int(row[0]):
                write_into_partition_file(first_article_id_in_part, article_id,
                                          output_folder, header, partition_content,
                                          output_name, output_counter, total_files)
                output_counter += 1
                partition_content = [row]
                first_article_id_in_part = int(row[0])
            else:
                partition_content.append(row)
            article_id = int(row[0])
    # last partition
    write_into_partition_file(first_article_id_in_part, article_id,
                              output_folder, header, partition_content,
                              output_name, output_counter, total_files)


def split_revisions(base_path, revisions_file):
    tokens_folder = '{}/{}/tokens'.format(base_path, 'partitions')
    if not exists(tokens_folder):
        raise Exception('Tokens folder does not exist: {}'.format(tokens_folder))
    output_folder = '{}/{}/revisions'.format(base_path, 'partitions')
    if not exists(output_folder):
        mkdir(output_folder)

    token_parts = {}
    for token_partition_file in listdir(tokens_folder):
        if not token_partition_file.endswith('.csv'):
            continue
        token_parts[token_partition_file.split('-')[3][4:]] = token_partition_file

    # print(len(token_parts), token_parts['1'])
    partition_limits = []
    for k in sorted(token_parts, key=int):
        ids = token_parts[k].split('-')[-2:]
        first_id = int(ids[0])
        last_id = int(ids[1].split('.')[0])
        partition_limits.append([first_id, last_id])
    print('len(partition_limits):', len(partition_limits))

    with open(base_path + '/' + revisions_file, newline='') as f:
        reader = csv.reader(f, delimiter='\t')
        article_id = None
        partition_content = []
        output_counter = 1
        # header = 'article_id,revision_id,editor,timestamp,oadds'.split(',')  # output for analysis
        header = 'page_id,rev_id,timestamp,editor'.split(',')  # output for served dataset
        next(reader, None)  # skip the header
        for row in reader:
            # skip problematic article id 17387412.
            # if int(row[0]) == 17387412:
            #     continue
            row[-1] = '0' if row[-1] == '\\N' else row[-1]
            if article_id is None:
                first_article_id_in_part = int(row[0])
            if article_id != int(row[0]) and [first_article_id_in_part, article_id] in partition_limits:
                partition_limits.remove([first_article_id_in_part, article_id])
                write_into_partition_file(first_article_id_in_part, article_id,
                                          output_folder, header, partition_content, 'revisions', output_counter)
                output_counter += 1
                partition_content = [row]
                first_article_id_in_part = int(row[0])
            else:
                # partition_content.append(row)  # output for analysis
                partition_content.append([row[0], row[1], row[3], row[2]])  # output for served dataset
            article_id = int(row[0])
    # last partition
    if [first_article_id_in_part, article_id] in partition_limits:
        partition_limits.remove([first_article_id_in_part, article_id])
        write_into_partition_file(first_article_id_in_part, article_id,
                                  output_folder, header, partition_content, 'revisions', output_counter)
    # print(partition_limits)
    assert len(partition_limits) == 0


def split_tokens(base_path, tokens_file):
    tokens_folder = '{}/{}/tokens'.format(base_path, 'partitions')
    if not exists(tokens_folder):
        raise Exception('Tokens folder does not exist: {}'.format(tokens_folder))
    output_folder = '{}/{}/current_tokens'.format(base_path, 'partitions')
    if not exists(output_folder):
        mkdir(output_folder)

    token_parts = {}
    for token_partition_file in listdir(tokens_folder):
        if not token_partition_file.endswith('.csv'):
            continue
        token_parts[token_partition_file.split('-')[3][4:]] = token_partition_file

    # print(len(token_parts), token_parts['1'])
    partition_limits = []
    for k in sorted(token_parts, key=int):
        ids = token_parts[k].split('-')[-2:]
        first_id = int(ids[0])
        last_id = int(ids[1].split('.')[0])
        partition_limits.append([first_id, last_id])
    print('len(partition_limits):', len(partition_limits))

    with open(base_path + '/' + tokens_file, newline='') as f:
        reader = csv.reader(f)
        article_id = None
        partition_content = []
        output_counter = 1
        # header = 'article_id,revision_id,token_id,str,origin,inbound,outbound'.split(',')
        header = 'page_id,last_rev_id,token_id,str,origin_rev_id,in,out'.split(',')
        next(reader, None)  # skip the header
        for row in reader:
            # if 'article_id' == row[0]:
            #     continue
            if article_id is None:
                first_article_id_in_part = int(row[0])
            if article_id != int(row[0]) and [first_article_id_in_part, article_id] in partition_limits:
                partition_limits.remove([first_article_id_in_part, article_id])
                write_into_partition_file(first_article_id_in_part, article_id,
                                          output_folder, header, partition_content, 'current_content', output_counter)
                output_counter += 1
                partition_content = [row]
                first_article_id_in_part = int(row[0])
            else:
                partition_content.append(row)
            article_id = int(row[0])
    # last partition
    if [first_article_id_in_part, article_id] in partition_limits:
        partition_limits.remove([first_article_id_in_part, article_id])
        write_into_partition_file(first_article_id_in_part, article_id,
                                  output_folder, header, partition_content, 'current_content', output_counter)
    # print(partition_limits)
    assert len(partition_limits) == 0


def split_articles(base_path, articles_file):
    tokens_folder = '{}/{}/tokens'.format(base_path, 'partitions')
    if not exists(tokens_folder):
        raise Exception('Tokens folder does not exist: {}'.format(tokens_folder))
    output_folder = '{}/{}/articles'.format(base_path, 'partitions')
    if not exists(output_folder):
        mkdir(output_folder)

    token_parts = {}
    for token_partition_file in listdir(tokens_folder):
        if not token_partition_file.endswith('.csv'):
            continue
        token_parts[token_partition_file.split('-')[3][4:]] = token_partition_file

    # print(len(token_parts), token_parts['1'])
    partition_limits = []
    for k in sorted(token_parts, key=int):
        ids = token_parts[k].split('-')[-2:]
        first_id = int(ids[0])
        last_id = int(ids[1].split('.')[0])
        partition_limits.append([first_id, last_id])
    print('len(partition_limits):', len(partition_limits))

    with open(base_path + '/' + articles_file) as f:
        article_id = None
        partition_content = []
        output_counter = 1
        # header = ['article_id']
        header = ['page_id']
        lines = f.read().splitlines()
        lines.sort(key=int)
        for row in lines:
            if 'article_id' == row:
                continue
            row = int(row)
            if article_id is None:
                first_article_id_in_part = row
            # skip problematic article id 17387412.
            # if row == 17387412:
            #     print([first_article_id_in_part, row])
            #     continue
            if article_id != row and [first_article_id_in_part, article_id] in partition_limits:
                partition_limits.remove([first_article_id_in_part, article_id])
                write_into_partition_file(first_article_id_in_part, article_id,
                                          output_folder, header, partition_content, 'articles', output_counter)
                output_counter += 1
                partition_content = [[row]]
                first_article_id_in_part = row
            else:
                partition_content.append([row])
            article_id = row
    # last partition
    if [first_article_id_in_part, article_id] in partition_limits:
        partition_limits.remove([first_article_id_in_part, article_id])
        write_into_partition_file(first_article_id_in_part, article_id,
                                  output_folder, header, partition_content, 'articles', output_counter)
    # print(len(partition_limits))
    assert len(partition_limits) == 0


def get_args():
    parser = argparse.ArgumentParser(description='Split the data set into partitions.')
    # parser.add_argument('input_file', help='File to analyze')
    parser.add_argument('-i', '--input_file', required=True, help='File to split')
    parser.add_argument('-f', '--base_path', required=True,
                        help='Base folder where input file is and where outputs will be')
    parser.add_argument('-s', '--partition_size',  type=int,
                        help='Line number where to split current token file. Default is 21.000.000 lines')
    parser.add_argument('-t', '--total_size',  type=int,
                        help='Total number of lines in input file. Default is 7572311408 lines')
    # NOTE by default there must be ~360 partition files
    parser.add_argument('-m', '--mode', required=True, type=int,
                        help='1: tokens_with_size, 2: revisions, 3:articles, 4: tokens')
    # parser.add_argument('-d', '--debug', help='Run in debug mode', action='store_true')

    args = parser.parse_args()

    if args.mode not in [1, 2, 3, 4]:
        parser.error("argument -m/--mode must be 1, 2, 3 or 4")

    return args


def main():
    args = get_args()
    input_file = args.input_file
    base_path = args.base_path
    base_path = base_path[:-1] if base_path and base_path.endswith('/') else base_path
    mode = args.mode
    # assert type(partition_size) == int
    if mode == 1:
        partition_size = args.partition_size or 21 * 1000 * 1000  # lines
        total_size = args.total_size or 7572311408  # lines
        split_tokens_with_size(base_path, input_file, partition_size, total_size, 'tokens')
        # split_tokens(base_path, input_file, partition_size, total_size, 'current_content')
    elif mode == 2:
        split_revisions(base_path, input_file)
    elif mode == 3:
        split_articles(base_path, input_file)
    elif mode == 4:
        split_tokens(base_path, input_file)

if __name__ == "__main__":
    main()
    print('\nDone!')
