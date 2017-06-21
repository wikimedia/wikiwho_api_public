"""
This module is to compare mwpersistence package with WikiWho in detail.
"""
from os import listdir
from os.path import join
from json import load, dumps
from difflib import Differ
import argparse


def jaccard_similarity(l1, l2):
    s1 = set(l1)
    s2 = set(l2)
    return len(s1.intersection(s2)) / float(len(s1.union(s2)))


def mw_pesistence_compare(ww_jsons, mw_jsons):
    articles = []
    for i in listdir(mw_jsons):
        if not i.endswith('_rev_ids.json'):
            articles.append(i[:-5])

    articles = ["Amstrad CPC", "Antarctica", "Apollo 11", "Armenian Genocide", "Barack_Obama",
                "Bioglass", "Bothrops_jararaca", "Chlorine", "Circumcision", "Communist Party of China",
                "Democritus", "Diana,_Princess_of_Wales", "Encryption", "Eritrean Defence Forces",
                "European Free Trade Association", "Evolution", "Geography of El Salvador",
                "Germany", "Home and Away", "Homeopathy", "Iraq War", "Islamophobia", "Jack the Ripper", "Jesus",
                "KLM destinations", "Lemur", "Macedonians (ethnic group)", "Muhammad", "Newberg, Oregon",
                "Race_and_intelligence", "Rhapsody_on_a_Theme_of_Paganini", "Robert Hues", "Saturn's_moons_in_fiction",
                "Sergei Korolev", "South_Western_Main_Line", "Special Air Service", "The_Holocaust",
                "Toshitsugu_Takamatsu", "Vladimir_Putin", "Wernher_von_Braun"]
    # articles = ['Bioglass', 'Amstrad_CPC', 'Lemur', 'Antarctica', 'Jesus']
    # articles = ['Bioglass', 'Amstrad_CPC']
    # articles = ['Bioglass']
    # articles = ['Evolution']
    output = {}
    for article_title in articles:
        article_title = article_title.replace(' ', '_')
        # calculate mw persistence for each token
        print('mw_article_tokens')
        mw_article_tokens = []  # [{'str': , 'o_rev_id': , 'in': , 'out': }]
        mw_token_values = []
        with open(join(mw_jsons, '{}_rev_ids.json'.format(article_title))) as f:
            d = load(f)
            article_rev_ids = d['revision_ids']
            article_rev_ids_dict = {rev_id: i for i, rev_id in enumerate(article_rev_ids)}

        with open(join(mw_jsons, '{}.json'.format(article_title))) as f:
            d = load(f)
            for rev_id, tokens in d['revisions'][0].items():
                for t in tokens['tokens']:
                    if not t['str'].replace('\\n', '').replace('\r\n', '\n').replace('\r', '\n').strip():
                        continue
                    o_rev_id = t['revisions'][0]
                    ins = []
                    outs = []
                    mw_article_tokens.append({'str': t['str'], 'o_rev_id': o_rev_id, 'in': ins, 'out': outs})
                    mw_token_values.append(t['str'])
                    # calculate in and outs
                    token_rev_indexes = [article_rev_ids_dict[r] for r in t['revisions']]
                    prev_rev_index = None
                    for rev_index in token_rev_indexes:
                        if prev_rev_index is not None and rev_index - prev_rev_index > 1:
                            # first rev id is o_rev_id, so skip it
                            # if there are more than 1 revs between, it means token is deleted and re-inserted.
                            outs.append(article_rev_ids[prev_rev_index+1])
                            ins.append(article_rev_ids[rev_index])
                        prev_rev_index = rev_index
        with open(join(mw_jsons, '{}_mw.csv'.format(article_title)), 'w') as f:
            f.write('str,o_rev_id\n')
            for t in mw_article_tokens:
                value = t['str'].replace('"', '""')
                value = '"{}"'.format(value) if (',' in value or '"' in value) else value
                f.write('{},{}\n'.format(value, t['o_rev_id']))

        # calculate wikiwho survival for each token
        print('ww_article_tokens')
        ww_article_tokens = []  # [{'str': , 'o_rev_id': , 'in': , 'out': }]
        ww_token_values = []
        with open(join(ww_jsons, '{}_ri_ai.json'.format(article_title))) as f:
            d = load(f)
            for rev_id, tokens in d['revisions'][0].items():
                for t in tokens['tokens']:
                    ww_article_tokens.append({'str': t['str'], 'o_rev_id': t['o_rev_id']})
                    ww_token_values.append(t['str'])
        rev_id = int(rev_id)
        ww_rev_ids = set()
        with open(join(ww_jsons, '{}_rev_ids.json'.format(article_title))) as f:
            d = load(f)
            for r in d['revisions']:
                # we have to do this, because ww analysis beyond given rev id
                if int(r['id']) == rev_id:
                    break
                else:
                    ww_rev_ids.add(int(r['id']))
        with open(join(ww_jsons, '{}_io.json'.format(article_title))) as f:
            d = load(f)
            for rev_id, tokens in d['revisions'][0].items():
                for i, t in enumerate(tokens['tokens']):
                    ins = [r for r in t['in'] if int(r) in ww_rev_ids]
                    outs = [r for r in t['out'] if int(r) in ww_rev_ids]
                    ww_article_tokens[i].update({'in': ins, 'out': outs})
        with open(join(mw_jsons, '{}_ww.csv'.format(article_title)), 'w') as f:
            f.write('str,o_rev_id\n')
            for t in ww_article_tokens:
                value = t['str'].replace('"', '""')
                value = '"{}"'.format(value) if (',' in value or '"' in value) else value
                f.write('{},{}\n'.format(value, t['o_rev_id']))

        print('comparing...')
        # compare results
        d = Differ()
        mw_vs_ww_tokens = []  # [{'str': {'same_o': , 'same_in': , 'same_out': }}]
        ww_article_tokens_iter = iter(ww_article_tokens)
        mw_article_tokens_iter = iter(mw_article_tokens)
        ww_found = 0
        ww_found_same_o = 0
        ww_found_same_in = 0
        ww_found_same_out = 0
        ww_found_same_in_out = 0
        not_found = 0
        for token in d.compare(ww_token_values, mw_token_values):
            op = token[0]
            token = token[2:]
            if op == '-':
                not_found += 1
                ww_token = next(ww_article_tokens_iter)
                mw_vs_ww_tokens.append({'str': token, 'op': op})
                assert token == ww_token['str']
            elif op == '+':
                not_found += 1
                mw_token = next(mw_article_tokens_iter)
                mw_vs_ww_tokens.append({'str': token, 'op': op})
                assert token == mw_token['str']
            elif op == ' ':
                ww_found += 1
                ww_token = next(ww_article_tokens_iter)
                assert token == ww_token['str']
                mw_token = next(mw_article_tokens_iter)
                assert token == mw_token['str']
                same_o = ww_token['o_rev_id'] == mw_token['o_rev_id']
                ww_found_same_o += 1 if same_o else 0
                if ww_token['in'] or mw_token['in']:
                    similarity_in = jaccard_similarity(ww_token['in'], mw_token['in'])
                else:
                    similarity_in = 1  # possible max value
                if ww_token['out'] or mw_token['out']:
                    similarity_out = jaccard_similarity(ww_token['out'], mw_token['out'])
                else:
                    similarity_out = 1  # possible max value
                same_in = ww_token['in'] == mw_token['in']
                ww_found_same_in += 1 if same_in else 0
                same_out = ww_token['out'] == mw_token['out']
                ww_found_same_out += 1 if same_out else 0
                ww_found_same_in_out += 1 if same_in and same_out else 0
                mw_vs_ww_tokens.append(
                    {
                        'str': token,
                        'op': op,
                        'same_o': same_o,
                        'similarity_in': similarity_in,
                        'similarity_out': similarity_out,
                        'same_in': same_in,
                        'same_out': same_out
                    }
                )
        assert len(list(ww_article_tokens_iter)) == 0, len(list(ww_article_tokens_iter))
        assert len(list(mw_article_tokens_iter)) == 0, len(list(mw_article_tokens_iter))

        output[article_title] = {'total': len(ww_article_tokens),
                                 'found': ww_found,
                                 '%_ww_found_same_origin': float(ww_found_same_o * 100) / ww_found,
                                 '%_ww_found_same_in': float(ww_found_same_in * 100) / ww_found,
                                 '%_ww_found_same_out': float(ww_found_same_out * 100) / ww_found,
                                 '%_ww_found_same_in_out': float(ww_found_same_in_out * 100) / ww_found,
                                 'not_found': not_found}
        with open('{}_diff.json'.format(join(mw_jsons, article_title)), 'w', encoding='utf-8') as f:
            f.write(dumps({article_title: mw_vs_ww_tokens}, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        with open('{}_diff.csv'.format(join(mw_jsons, article_title)), 'w') as f:
            # f.write('str,same_o,op\n')
            f.write('str,same_o,similarity_in,same_in,similarity_out,same_out,op\n')
            for t in mw_vs_ww_tokens:
                value = t['str'].replace('"', '""')
                value = '"{}"'.format(value) if (',' in value or '"' in value) else value
                # f.write('{},{},{}\n'.format(value, t.get('same_o', ''),
                f.write('{},{},{},{},{},{},{}\n'.format(value, t.get('same_o', ''),
                                                        t.get('similarity_in', ''), t.get('same_in', ''),
                                                        t.get('similarity_out', ''), t.get('same_out', ''),
                                                        t['op']))
        print('{}: {}'.format(article_title, output[article_title]))
    with open(join(mw_jsons, 'ww_vs_mw_comparison_output.json'), 'w', encoding='utf-8') as f:
        f.write(dumps(output, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))


def get_args():
    """
python mw_persistence_compare.py -w='/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/jsons/after_token_density_increase' -m='/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/mwpersistence/15'
    """
    parser = argparse.ArgumentParser(description='Compare computed content persistence and token authorship by '
                                                 'mwpersistence package in detail. This module is created to compare '
                                                 'results of mwpersistence with WikiWho.')

    parser.add_argument('-w', '--wikiwho_jsons', help='Path of the folder where all token persistence and '
                                                      'token authorship json files are.')
    parser.add_argument('-m', '--mediawiki_jsons', help='Path of the folder where all token persistence and '
                                                        'token authorship json files are.')
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    wikiwho_jsons = args.wikiwho_jsons
    mediawiki_jsons = args.mediawiki_jsons
    mw_pesistence_compare(wikiwho_jsons, mediawiki_jsons)

if __name__ == '__main__':
    main()
