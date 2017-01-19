import csv
import sys

csv.field_size_limit(sys.maxsize)


def delete_sample():
    current = '/home/nuser/dumps/wikiwho_dataset/partitions/samples/currentcontent-20161226-part1-12-316.csv'
    # article_id, revision_id, token_id, str, origin, inbound, outbound
    header = 'page_id,last_rev_id,token_id,str,origin_rev_id,in,out'.split(',')
    with open(current, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        current_content = {}
        for row in reader:
            if 'page_id' == row[0]:
                continue
            current_content['{}-{}'.format(row[0], row[2])] = True  # article id, token id
    print(len(current_content))

    all = '/home/nuser/dumps/wikiwho_dataset/partitions/samples/allcontent-12-316.csv'
    # page_id,last_rev_id,token_id,str,origin_rev_id,in,out
    header = 'page_id,last_rev_id,token_id,str,origin_rev_id,in,out'.split(',')
    counter = 0
    with open(all, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        deleted_content = []
        for row in reader:
            if 'page_id' == row[0]:
                continue
            counter += 1
            if not '{}-{}'.format(row[0], row[2]) in current_content:
                deleted_content.append(row)  # article id, token id
    print(len(deleted_content))
    print(counter)
    with open(all + '_deleted_.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(deleted_content)
    return True

if __name__ == '__main__':
    delete_sample()
    print('done!')

