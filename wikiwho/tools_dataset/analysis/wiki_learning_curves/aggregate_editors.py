import glob
import argparse
import csv
import pytz
from collections import defaultdict
from time import strftime
from dateutil import parser
from datetime import datetime


def aggregate_over_editors(partitions, output, header, min_edits, first_edit_year):
    # {'editor': {ts: rev_id, ..}, ..}
    aggregation = defaultdict(dict)
    # Read each partition.
    for partition_file in partitions:
        print("Parsing ", partition_file)
        with open(partition_file) as f:
            partition = csv.reader(f, delimiter=',')
            next(partition, None)  # skip the headers
            for line in partition:
                # editor,edit_no,rev_id,rev_ts,page_id
                rev_ts = parser.parse(line[3])
                aggregation[line[0]][rev_ts] = (line[2], line[4])

    # output aggregated editors data
    first_edit_date = datetime(first_edit_year, 1, 1, tzinfo=pytz.UTC)
    last_date = datetime(2016, 10, 31, tzinfo=pytz.UTC)
    with open(output, 'w') as f_out:
        f_out.write(header)
        for editor, data in aggregation.items():
            if len(data) < min_edits:
                # min 250 edits in total
                continue
            sorted_timestamps = sorted(data)
            if sorted_timestamps[0] < first_edit_date:
                # first edit after 2014
                continue
            weeks = (last_date - sorted_timestamps[0]).days / 7.0
            if len(data) / weeks < 1:
                # print(len(data), weeks, sorted_timestamps[0])
                # min 1 edit per week on average
                continue
            for i, rev_ts in enumerate(sorted_timestamps):
                rev_id, page_id = data[rev_ts]
                f_out.write(editor + ',' + str(i) + ',' + rev_id + ',' + str(rev_ts) + '\n')


def get_args():
    """
    python aggregate_editors.py -i /home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors
    """
    parser = argparse.ArgumentParser(description='Aggregate survival data of oadds and deletions in all partitions '
                                                 'over year-month-string.')
    parser.add_argument('-i', '--input_folder', required=True, help='Where all partitions take place.')
    parser.add_argument('-e', '--edits', type=int, help='Min # edits that editor should have done. Default is 250')
    # parser.add_argument('-s', '--size', type=int, help='Number of editors that each csv max contains. Default is 100')
    parser.add_argument('-y', '--year', type=int, help='Year that editor first made an edit. Default is 2014')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    min_edits = args.edits or 250
    first_edit_year = args.year or 2014
    input_folder = args.input_folder
    input_folder = input_folder if input_folder.endswith('/') else input_folder + '/'
    partitions = glob.glob(input_folder + "editors-part*.csv")
    output = input_folder + "editors-all-parts-filtered.csv"
    header = 'editor,edit_no,rev_id,rev_ts,page_id\n'
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    aggregate_over_editors(partitions, output, header, min_edits, first_edit_year)
    print("End: ", strftime("%Y-%m-%d-%H:%M:%S"))

if __name__ == '__main__':
    main()
