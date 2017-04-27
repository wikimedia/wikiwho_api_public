import glob
import argparse
import csv
from collections import defaultdict
from time import strftime


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m+1


def aggregate_over_user(partitions, output_file, header):
    aggregation = defaultdict(dict)  # {y-m: {editor: [oadds, not_survived], editor2: ..}, y-m: ..}
    # Read each partition.
    for partition_file in partitions:
        print("Parsing ", partition_file)
        with open(partition_file) as f:
            partition = csv.reader(f, delimiter=',')
            next(partition, None)  # skip the headers
            for line in partition:
                # year,month,editor,not_survived_48h,oadds/deletions
                period = (int(line[0]), int(line[1]))
                editor = line[2]
                if editor in aggregation[period]:
                    aggregation[period][editor][0] += int(line[4])
                    aggregation[period][editor][1] += int(line[3])
                else:
                    aggregation[period][editor] = [int(line[4]), int(line[3])]

    with open(output_file, 'w') as f_out:
        f_out.write(header)
        for year_month in month_year_iter(1, 2001, 12, 2016):
            (year, month) = year_month
            if year_month in aggregation:
                for editor, data in aggregation[year_month].items():
                    editor = '"{}"'.format(editor) if ',' in editor else editor
                    f_out.write(str(year) + "," + str(month) + ',' + editor + ',' + str(data[1]) + "," + str(data[0]) + "\n")
            else:
                f_out.write(str(year) + "," + str(month) + ',0,0,0' + "\n")


def get_args():
    """
    python aggregate_oadds_or_deletions.py -i /home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/outputs_oadds_48h_survivals --oadds
    python aggregate_oadds_or_deletions.py -i /home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_deletions  --deletions
    """
    parser = argparse.ArgumentParser(description='Aggregate oadds/deletions and survivals over partitions.')
    parser.add_argument('-i', '--input_folder', required=True, help='Where all partitions take place.')
    parser.add_argument('-o', '--oadds', action='store_true', default=False, help='Aggregate oadds, default is False.')
    parser.add_argument('-d', '--deletions', action='store_true', default=False,
                        help='Aggregate deletions, default is False.')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    input_folder = args.input_folder
    input_folder = input_folder if input_folder.endswith('/') else input_folder + '/'
    is_oadds = args.oadds
    is_deletions = args.deletions
    if is_oadds:
        partitions = glob.glob(input_folder + "oadds-part*.csv")
        output = input_folder + "oadds-all-parts.csv"
        header = 'year,month,editor,not_survived_48h,oadds\n'
    elif is_deletions:
        partitions = glob.glob(input_folder + "deletions-part*.csv")
        output = input_folder + "deletions-all-parts.csv"
        header = 'year,month,editor,not_survived_48h,deletions\n'
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    aggregate_over_user(partitions, output, header)
    print("End: ", strftime("%Y-%m-%d-%H:%M:%S"))

if __name__ == '__main__':
    main()
