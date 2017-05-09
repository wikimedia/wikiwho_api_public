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


def aggregate_over_yms(partitions, output_file, header, is_separated, string_set, string_set_startswith):
    # {'y-m': {'string': ['oadds', 'oadds_48h', 'dels', 'dels_48h', 're_ins', 're_ins_48h'], }, {}}
    aggregation = defaultdict(dict)
    # Read each partition.
    for partition_file in partitions:
        print("Parsing ", partition_file)
        with open(partition_file) as f:
            partition = csv.reader(f, delimiter=',')
            next(partition, None)  # skip the headers
            for line in partition:
                # year,month,string,oadds,oadds_48h,dels,dels_48h,reins,reins_48h
                period = (int(line[0]), int(line[1]))
                string_ = line[2]
                if string_ == '':
                    continue
                if not is_separated:
                    for w in string_set_startswith:
                        if string_.startswith(w):
                            string_ = w + '*'
                            break
                if string_ in aggregation[period]:
                    aggregation[period][string_][0] += int(line[3])
                    aggregation[period][string_][1] += int(line[4])
                    aggregation[period][string_][2] += int(line[5])
                    aggregation[period][string_][3] += int(line[6])
                    aggregation[period][string_][4] += int(line[7])
                    aggregation[period][string_][5] += int(line[8])
                else:
                    aggregation[period][string_] = [int(line[3]), int(line[4]), int(line[5]),
                                                    int(line[6]), int(line[7]), int(line[8])]

    with open(output_file, 'w') as f_out:
        f_out.write(header)
        for year_month in month_year_iter(1, 2001, 11, 2016):
            (year, month) = year_month
            for string_, data in aggregation[year_month].items():
                f_out.write(str(year) + ',' + str(month) + ',' + string_ + ',' +
                            str(data[0]) + ',' + str(data[1]) + ',' +
                            str(data[2]) + ',' + str(data[3]) + ',' +
                            str(data[4]) + ',' + str(data[5]) + ',' +
                            '\n')


def get_args():
    """
    python aggregate_string_data.py -i /home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_strings
    """
    parser = argparse.ArgumentParser(description='Aggregate survival data of oadds and deletions in all partitions '
                                                 'over year-month-string.')
    parser.add_argument('-i', '--input_folder', required=True, help='Where all partitions take place.')
    parser.add_argument('-s', '--strings', help='Strings comma separated. There is a default list.')
    parser.add_argument('-d', '--separated', action='store_true', default=False,
                        help='Aggregate wildcards separately. Default is False')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    is_separated = args.separated
    string_set = args.strings
    if string_set:
        string_set = set(string_set.split(','))
    else:
        string_set = {'conservative*', 'liberal*', 'democratic*', 'anxious*', 'notably*', 'interestingly*',
                      'tragical*', 'comprises', 'comprised', 'remarkabl*', 'however', 'apparent*', 'famous*',
                      'literally', 'figuratively'}
    string_set_startswith = {s[:-1] for s in string_set if s.endswith('*')}  # will be check for startswith
    string_set = {s for s in string_set if not s.endswith('*')}  # will be checked for is equal
    input_folder = args.input_folder
    input_folder = input_folder if input_folder.endswith('/') else input_folder + '/'
    partitions = glob.glob(input_folder + "strings-part*.csv")
    output = input_folder + "strings-all-parts.csv"
    header = 'year,month,string,oadds,oadds_48h,dels,dels_48h,reins,reins_48h\n'
    print('string_set_startswith:', string_set_startswith)
    print('string_set:', string_set)
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    aggregate_over_yms(partitions, output, header, is_separated, string_set, string_set_startswith)
    print("End: ", strftime("%Y-%m-%d-%H:%M:%S"))

if __name__ == '__main__':
    main()
