import csv
import json


def convert_csv_into_json(input_file, unique=False, pretty=False):
    print('converting from csv to json ...')
    article_source_dict = {}
    # test = 0
    # test_set = set()
    with open(input_file, newline='') as f:
        reader = csv.reader(f)
        article_id = None
        sources = []
        targets = []
        for line in reader:
            # print(line)
            if 'article' in line or 'article_id' in line:
                continue
            # test_set.add(line[0])
            # if next article in csv
            if article_id is not None and article_id != line[0]:
                if unique:
                    article_source_dict[article_id] = {'sources': list(set(sources)), 'targets': list(set(targets))}
                else:
                    article_source_dict[article_id] = {'sources': sources, 'targets': targets}
                sources = [line[1]]
                # targets = [line[2]]
                targets = eval(line[2])
                # print(type(targets))
            else:
                sources.append(line[1])
                # targets.append(line[2])
                targets.extend(eval(line[2]))
            # print(sources, targets, article_id)
            article_id = line[0]
            # test += 1
            # if test == 1000000:
            #     break
    # if last article in csv
    if sources and targets:
        if unique:
            article_source_dict[article_id] = {'sources': list(set(sources)), 'targets': list(set(targets))}
        else:
            article_source_dict[article_id] = {'sources': sources, 'targets': targets}

    # print(article_source_dict)
    # assert len(article_source_dict) == len(test_set)
    article_ids = list(article_source_dict.keys())
    with open('{}.article_ids.txt'.format(input_file), 'w') as f:
        f.write('\n'.join(article_ids) + '\n')
    print(len(article_ids))

    print('writing into json ...')
    with open('{}.json'.format(input_file), 'w') as f:
        if pretty:
            json.dump(article_source_dict, f, ensure_ascii=False, indent=4, separators=(',', ': '), sort_keys=True)
        else:
            json.dump(article_source_dict, f, ensure_ascii=False)


def compare_reverts(input_file, input_file_sha):
    with open('{}.json'.format(input_file), 'r') as f:
        article_sources = json.load(f)
    with open('{}.json'.format(input_file_sha), 'r') as f:
        article_sources_sha = json.load(f)
    articles = list(article_sources.keys())
    articles_sha = list(article_sources_sha.keys())
    print('articles:', len(articles), len(set(articles)))
    print('articles_sha:', len(articles_sha), len(set(articles_sha)))
    print('articles - articles_sha:', set(articles) - set(articles_sha))
    print('articles_sha - articles:', set(articles_sha) - set(articles))

    articles_more = {}
    articles_sha_more = {}
    for article in article_sources:
        sources = set(article_sources[article]['sources'])
        sources_sha = set(article_sources_sha[article]['sources'])
        more = sources - sources_sha
        sha_more = sources_sha - sources
        if sha_more:
            articles_sha_more[article] = len(sha_more)
        if more:
            articles_more[article] = len(more)
    print(len(articles_more), sum(list(articles_more.values())))
    print(len(articles_sha_more), sum(list(articles_sha_more.values())))
    # 998    6047740
    # 995    18609


if __name__ == "__main__":
    # TODO directory is changed to /mac (locally)
    input_file = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/reverts-out.csv'
    input_file_sha = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/reverts-sha-out-new.csv'
    # convert_csv_into_json(input_file_sha)
    compare_reverts(input_file, input_file_sha)
    print('Done!')


