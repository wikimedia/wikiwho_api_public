import json


def main():
    # one of the log file of compute_editor_data.py
    p = '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors/23660519-24601697_at_2017-05-22-21:57:52.log'
    logs = {'seconds': [], 'len': [], 'rev_id': [], 'summary': {'total': 0}}
    with open(p) as f:
        for line in f.read().splitlines():
            # token problematic (seconds < 0)
            # (not (0 <= len(outs) - len(ins) <= 1))
            # is not in revision file
            line = line.split('ERROR    ')[-1]
            if '(seconds < 0)' in line:
                logs['seconds'].append(line.split(':')[0].split(',')[0])
            elif '(not (0 <= len(outs) - len(ins) <= 1))' in line:
                logs['len'].append(line.split(':')[0].split(',')[0])
            elif'is not in revision file' in line:
                logs['rev_id'].append(line.split(':')[0])
            else:
                print('+-+-problem+-+-', line)
    for k, v in logs.items():
        logs['summary']['len_{}'.format(k)] = [len(v), len(set(v))]
        logs['summary']['total'] += len(set(v))
    with open('{}_output.json'.format(p), 'w', encoding='utf-8') as f:
        f.write(json.dumps(logs, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))

    p2 = '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors/problematic_articles.json'
    with open(p2, 'r') as f:
        problematic_articles = json.load(f)
    problematic_articles_list = set()
    for f, d in problematic_articles.items():
        for k, all_data in d.items():
            for data in all_data:
                problematic_articles_list.add(int(data[1]))

    for k, v in logs.items():
        if k in ['seconds', 'len', 'rev_id']:
            print(k, len(set(v)))
            for page_id in v:
                if int(page_id) not in problematic_articles_list:
                    print(page_id)

if __name__ == '__main__':
    main()
