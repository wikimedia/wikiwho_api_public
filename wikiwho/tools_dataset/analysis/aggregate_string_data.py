import glob
import argparse
import csv
from collections import defaultdict
from time import strftime
from statistics import mean, median, pstdev, stdev


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m+1


def add_str_into_conflict_aggr_dict(aggregation, string_):
    for year_month in month_year_iter(1, 2001, 12, 2016):
        aggregation[year_month][string_] = []


def aggregate_conflict_over_yms(partitions, output_file, header, string_set, string_set_startswith):
    # {'y-m': {'string': [avg_ct, st_ct, med_ct], }, {}}
    aggregation = defaultdict(dict)
    # init aggregation dict
    for s in string_set:
        add_str_into_conflict_aggr_dict(aggregation, s)
    for s in string_set_startswith:
        add_str_into_conflict_aggr_dict(aggregation, s + '*')

    # Read each partition.
    for partition_file in partitions:
        print("Parsing ", partition_file)
        with open(partition_file) as f:
            partition = csv.reader(f, delimiter=',')
            next(partition, None)  # skip the headers
            for line in partition:
                # year,month,string,string_id,conflict_time
                period = (int(line[0]), int(line[1]))
                string_ = line[2]
                if string_ == '':
                    continue
                for w in string_set_startswith:
                    if string_.startswith(w):
                        string_ = w + '*'
                        break
                aggregation[period][string_].append(float(line[4]))

    with open(output_file, 'w') as f_out:
        f_out.write(header)
        for year_month in month_year_iter(1, 2001, 11, 2016):
            (year, month) = year_month
            for string_, conflict_scores in aggregation[year_month].items():
                # year,month,string,len_ct,mean_ct,pstdev_ct,stdev_ct,median_ct
                len_ct = len(conflict_scores)
                if len_ct == 0:
                    stdev_ct = 0
                elif len_ct == 1:
                    stdev_ct = 'Na'
                else:
                    stdev_ct = stdev(conflict_scores)
                f_out.write(str(year) + ',' + str(month) + ',' + string_ + ',' +
                            str(len_ct) + ',' +
                            str(mean(conflict_scores or [0])) + ',' +
                            str(pstdev(conflict_scores or [0])) + ',' +
                            str(stdev_ct) + ',' +
                            str(median(conflict_scores or [0])) +
                            '\n')


def add_str_into_aggr_dict(aggregation, string_):
    for year_month in month_year_iter(1, 2001, 12, 2016):
        aggregation[year_month][string_] = [0, 0, 0, 0, 0, 0]


def aggregate_over_yms(partitions, output_file, header, is_separated, string_set, string_set_startswith):
    # {'y-m': {'string': ['oadds', 'oadds_48h', 'dels', 'dels_48h', 're_ins', 're_ins_48h'], }, {}}
    aggregation = defaultdict(dict)
    # init aggregation dict
    for s in string_set:
        add_str_into_aggr_dict(aggregation, s)
    if not is_separated:
        for s in string_set_startswith:
            add_str_into_aggr_dict(aggregation, s + '*')
    string_set_startswith_separated = set()

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
                else:
                    if string_ not in string_set_startswith_separated:
                        string_set_startswith_separated.add(string_)
                        add_str_into_aggr_dict(aggregation, string_)
                aggregation[period][string_][0] += int(line[3])
                aggregation[period][string_][1] += int(line[4])
                aggregation[period][string_][2] += int(line[5])
                aggregation[period][string_][3] += int(line[6])
                aggregation[period][string_][4] += int(line[7])
                aggregation[period][string_][5] += int(line[8])

    with open(output_file, 'w') as f_out:
        f_out.write(header)
        for year_month in month_year_iter(1, 2001, 11, 2016):
            (year, month) = year_month
            for string_, data in aggregation[year_month].items():
                f_out.write(str(year) + ',' + str(month) + ',' + string_ + ',' +
                            str(data[0]) + ',' + str(data[1]) + ',' +
                            str(data[2]) + ',' + str(data[3]) + ',' +
                            str(data[4]) + ',' + str(data[5]) +
                            '\n')


def get_args():
    """
    python aggregate_string_data.py -i /home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_strings
    python aggregate_string_data.py -i /home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_strings_conflict -c
    """
    parser = argparse.ArgumentParser(description='Aggregate survival data of oadds and deletions or conflict score'
                                                 ' in all partitions over year-month-string.')
    parser.add_argument('-i', '--input_folder', required=True, help='Where all partitions take place.')
    parser.add_argument('-s', '--strings', help='Strings comma separated. There is a default list.')
    parser.add_argument('-d', '--separated', action='store_true', default=False,
                        help='Aggregate wildcards separately. Default is False')
    parser.add_argument('-c', '--conflict', action='store_true', default=False,
                        help='Compute conflict score for each script, default is False.')
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    is_conflict_computation = args.conflict
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
    if not is_conflict_computation:
        partitions = glob.glob(input_folder + "strings-part*.csv")
        if is_separated:
            output = input_folder + "strings-all-parts-separated.csv"
        else:
            output = input_folder + "strings-all-parts.csv"
        header = 'year,month,string,oadds,oadds_48h,dels,dels_48h,reins,reins_48h\n'
    else:
        partitions = glob.glob(input_folder + "strings-conflict-part*.csv")
        output = input_folder + "strings-conflict-all-parts.csv"
        header = 'year,month,string,len_ct,mean_ct,pstdev_ct,stdev_ct,median_ct\n'

    print('is_conflict_computation:', is_conflict_computation)
    print('string_set_startswith:', string_set_startswith)
    print('string_set:', string_set)
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    if not is_conflict_computation:
        aggregate_over_yms(partitions, output, header, is_separated, string_set, string_set_startswith)
    else:
        aggregate_conflict_over_yms(partitions, output, header, string_set, string_set_startswith)
    print("End: ", strftime("%Y-%m-%d-%H:%M:%S"))

if __name__ == '__main__':
    main()
