# -*- coding: utf-8 -*-
"""
python split_the_dataset.py -i 'test_currentcontent_20161226.csv' -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/'
"""
import csv
import argparse
import sys
from os.path import exists
from os import mkdir


def write_into_partition_file(first_article_id_in_part, last_article_id_in_part, output_folder,
                              header, partition_content, output_counter=None, total_files=None):
    partition_file = 'currentcontent-20161226-part{}-{}-{}.csv'.format(output_counter,
                                                                       first_article_id_in_part,
                                                                       last_article_id_in_part)
    with open(output_folder + '/' + partition_file, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(header)
        writer.writerows(partition_content)

    if output_counter and total_files:
        sys.stdout.write('\r{}-{:.3f}%'.format(output_counter, output_counter*100/total_files))
    return True


def split_the_dataset(base_path, current_content_file, partition_size, total_size):
    output_folder = '{}/{}'.format(base_path, 'partitions')
    total_files = int(total_size/partition_size)
    if not exists(output_folder):
        mkdir(output_folder)
    with open(base_path + '/' + current_content_file, newline='') as f:
        reader = csv.reader(f)
        article_id = None
        partition_content = []
        output_counter = 1
        for i, row in enumerate(reader, 1):
            if 'article_id' in row:
                header = row
                continue
            if article_id is None:
                first_article_id_in_part = int(row[0])
            if i >= (partition_size * output_counter) and article_id != int(row[0]):
                write_into_partition_file(first_article_id_in_part, article_id,
                                          output_folder, header, partition_content, output_counter, total_files)
                output_counter += 1
                partition_content = [row]
                first_article_id_in_part = int(row[0])
            else:
                partition_content.append(row)
            article_id = int(row[0])
    # last partition
    write_into_partition_file(first_article_id_in_part, article_id,
                              output_folder, header, partition_content, output_counter, total_files)


def get_args():
    parser = argparse.ArgumentParser(description='Split the data set into partitions.')
    # parser.add_argument('input_file', help='File to analyze')
    parser.add_argument('-i', '--input_file', required=True, help='Current token file to split')
    parser.add_argument('-f', '--base_path', required=True,
                        help='Base folder where input file is and where outputs will be')
    parser.add_argument('-s', '--partition_size',  type=int,
                        help='Line number where to split current token file. Default is 21.000.000 lines')
    parser.add_argument('-t', '--total_size',  type=int,
                        help='Total number of lines in input file. Default is 7572311408 lines')
    # NOTE by default there must be ~360 partition files
    # parser.add_argument('-d', '--debug', help='Run in debug mode', action='store_true')

    args = parser.parse_args()

    # if not args.input_file or not args.base_path:
    #     parser.error("argument -i/--input_file or -b/--base_path is required")

    return args


def main():
    args = get_args()
    current_content_file = args.input_file
    base_path = args.base_path
    base_path = base_path[:-1] if base_path and base_path.endswith('/') else base_path
    partition_size = args.partition_size or 21 * 1000 * 1000  # lines
    total_size = args.total_size or 7572311408  # lines
    # assert type(partition_size) == int
    split_the_dataset(base_path, current_content_file, partition_size, total_size)

if __name__ == "__main__":
    main()
    print('\nDone!')
