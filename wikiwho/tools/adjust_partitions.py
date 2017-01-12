import subprocess
import csv
from os import listdir, rename
import time
import sys


def adjust_partitions(input_folder):
    """
    Adjust randomly splited partitions. Looks last line of each partition and appends rows with same article id in
    next partition.
    Split ex:
    split -d --lines=21000000 mac-tokens-all.csv /home/nuser/dumps/wikiwho_dataset/partitions/tokens/mac-tokens-all.csv_part
    split -d --line-bytes=1080M tokens_in_lastrevisions.csv tokens_in_lastrevisions/random/tokens_in_lastrevisions.csv_
    """
    # FIXME this script doesnt handle if a part contains only one article which exists in previous part and
    # continues in next part
    change_dict = {}
    rename_list = []
    previous_last_article_id = None
    files_all = len(listdir(input_folder))
    files_left = files_all
    i = 0
    for part in sorted(listdir(input_folder)):
        part_id = int(part.split('_part')[1])
        part = '{}/{}'.format(input_folder, part)
        content_for_previous = []
        if previous_last_article_id:
            with open(part, newline='') as f:
                reader = csv.reader(f, delimiter=',')
                for row in reader:
                    # if 'article_id' == row[0] or 'article' == row[0]:
                    #     continue
                    if int(row[0]) == previous_last_article_id:
                        content_for_previous.append(row)
                    else:
                        break
            # fill change dict
            # print(previous_part.split('/')[-1], part.split('/')[-1], len(content_for_previous))
            change_dict[previous_part.split('/')[-1]][0] = len(content_for_previous)
        change_dict[part.split('/')[-1]] = [0, -len(content_for_previous)]
        # make changes on parts
        if content_for_previous:
            # append into previous part
            with open(previous_part, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(content_for_previous)
            # delete from current part
            subprocess.call(['sed', '-i', '-e', '1,{}d'.format(len(content_for_previous)), part])
        # get info for previous part
        first_line = subprocess.check_output(['head', '-1', part])
        first_article_id = int(first_line.split(b',', 1)[0]) if first_line else None
        last_line = subprocess.check_output(['tail', '-1', part])
        last_article_id = int(last_line.split(b',', 1)[0]) if last_line else None
        if first_article_id == last_article_id:
            print('First and last article id in file ({}) same!'.format(part))
        else:
            previous_part = part
            previous_first_article_id = first_article_id
            previous_last_article_id = last_article_id
            i += 1
            rename_list.append([part, '{}-part{}-{}-{}.csv'.format(part.split('.csv')[0],
                                                                   i,
                                                                   previous_first_article_id,
                                                                   previous_last_article_id)])
        # time.sleep(5)
        files_left -= 1
        sys.stdout.write('\r{}-{:.3f}%'.format(files_left, ((files_all - files_left) * 100) / files_all))

    print('renaming ..')
    for old_name, new_name in rename_list:
        rename(old_name, new_name)
    return change_dict


if __name__ == '__main__':
    pass
