import random
import csv
from collections import defaultdict


def main():
    """
    Pick 1000 editors randomly.
    """
    # output of aggregate_editors.py script
    p = '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors/editors-all-parts-filtered.csv'
    editors = defaultdict(list)
    with open(p) as f:
        csv_ = csv.reader(f, delimiter=',')
        for row in csv_:
            # editor,edit_no,rev_id,rev_ts
            editors[row[0]].append([row[1], row[2], row[3]])

    editors_1000 = defaultdict(list)
    while True:
        editor, data = random.choice(list(editors.items()))
        editors_1000[editor] = data
        if len(editors_1000) == 1000:
            break

    header = 'editor,len_edits,edit_no,rev_id,rev_ts'
    output = '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors/' \
             'editors-all-parts-filtered-1000.csv'
    with open(output, 'w') as f_out:
        csv_ = csv.writer(f_out, delimiter=',')
        csv_.writerow(header.split(','))
        for editor, data in editors_1000.items():
            for row in data:
                csv_.writerow([editor, len(data)] + row)

if __name__ == '__main__':
    main()
