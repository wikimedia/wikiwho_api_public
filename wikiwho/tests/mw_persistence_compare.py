from os import listdir
from os.path import join
from json import load, dumps
from difflib import SequenceMatcher, Differ


def main(ww_jsons, mw_jsons):
    """
    ww_jsons = '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/jsons/after_token_density_increase'
    mw_jsons = '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/mwpersistence'
    :param ww_jsons:
    :param mw_jsons:
    :return:
    """
    articles = []
    for i in listdir(mw_jsons):
        if not i.endswith('_rev_ids.json'):
            articles.append(i[:-5])

    articles = ['Bioglass', 'Amstrad_CPC', 'Lemur', 'Antarctica', 'Jesus']
    articles = ["Amstrad CPC", "Antarctica", "Apollo 11", "Armenian Genocide", "Barack_Obama",
                "Bioglass", "Bothrops_jararaca", "Chlorine", "Circumcision", "Communist Party of China",
                "Democritus", "Diana,_Princess_of_Wales", "Encryption", "Eritrean Defence Forces",
                "European Free Trade Association", "Evolution", "Geography of El Salvador",
                "Germany", "Home and Away", "Homeopathy", "Iraq War", "Islamophobia", "Jack the Ripper", "Jesus",
                "KLM destinations", "Lemur", "Macedonians (ethnic group)", "Muhammad", "Newberg, Oregon",
                "Race_and_intelligence", "Rhapsody_on_a_Theme_of_Paganini", "Robert Hues", "Saturn's_moons_in_fiction",
                "Sergei Korolev", "South_Western_Main_Line", "Special Air Service", "The_Holocaust",
                "Toshitsugu_Takamatsu", "Vladimir_Putin", "Wernher_von_Braun"]
    # articles = ['Bioglass', 'Amstrad_CPC']
    # articles = ['Bioglass']
    output = {}
    for article_title in articles:
        # calculate mw persistence for each token
        print('mw_article_tokens')
        mw_article_tokens = []  # [{'str': , 'o_rev_id': , 'in': , 'out': }]
        mw_token_values = []
        with open(join(mw_jsons, '{}_rev_ids.json'.format(article_title))) as f:
            d = load(f)
            article_rev_ids = d['revision_ids']
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
                    token_rev_index = [article_rev_ids.index(r) for r in t['revisions']]
                    prev_rev_index = None
                    for rev_index in token_rev_index:
                        if prev_rev_index is None:
                            # first rev id is o_rev_id, so skip it
                            prev_rev_index = rev_index
                            continue
                        if rev_index - prev_rev_index > 1:
                            outs.append(article_rev_ids[prev_rev_index+1])
                            ins.append(article_rev_ids[rev_index])
                        prev_rev_index = rev_index

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
        with open(join(ww_jsons, '{}_io.json'.format(article_title))) as f:
            d = load(f)
            for rev_id, tokens in d['revisions'][0].items():
                for i, t in enumerate(tokens['tokens']):
                    ww_article_tokens[i].update({'in': t['in'], 'out': t['out']})

        print('comparing...')
        # compare results
        d = Differ()
        mw_vs_ww_tokens = []  # [{'str': {'same_o': , 'same_in': , 'same_out': }}]
        ww_article_tokens_iter = iter(ww_article_tokens)
        mw_article_tokens_iter = iter(mw_article_tokens)
        ww_found = 0
        ww_found_same_o = 0
        ww_not_found = 0
        for token in d.compare(ww_token_values, mw_token_values):
            op = token[0]
            token = token[2:]
            if op == '-':
                ww_not_found += 1
                ww_token = next(ww_article_tokens_iter)
                mw_vs_ww_tokens.append({ww_token['str']: {'not_found': True}})
                assert token == ww_token['str']
                # for ww_token in ww_article_tokens_iter:
                #     if token == ww_token['str']:
                #         break
            elif op == ' ':
                ww_found += 1
                ww_token = next(ww_article_tokens_iter)
                assert token == ww_token['str']
                # for ww_token in ww_article_tokens_iter:
                #     if token == ww_token['str']:
                #         break
                for mw_token in mw_article_tokens_iter:
                    if token == mw_token['str']:
                        break
                ww_found_same_o += 1 if ww_token['o_rev_id'] == mw_token['o_rev_id'] else 0
                # similarity_in = SequenceMatcher(None, ww_token['in'], mw_token['in']).ratio()
                # similarity_out = SequenceMatcher(None, ww_token['out'], mw_token['out']).ratio()
                mw_vs_ww_tokens.append({
                    ww_token['str']: {
                        'same_o': ww_token['o_rev_id'] == mw_token['o_rev_id'],
                        # 'similartiy_in': similarity_in,
                        # 'similarity_out': similarity_out,
                        'same_in': ww_token['in'] == mw_token['in'],
                        'same_out': ww_token['out'] == mw_token['out']
                    }
                })
        assert len(list(ww_article_tokens_iter)) == 0, len(list(ww_article_tokens_iter))

        output[article_title] = {'total': len(ww_article_tokens),
                                 'found': ww_found,
                                 'ww_found_same_o': ww_found_same_o,
                                 'ww_found_same_o%': float(ww_found_same_o * 100) / ww_found,
                                 'not_found': ww_not_found}
        with open('{}_ww_comparison.json'.format(join(mw_jsons, article_title)), 'w', encoding='utf-8') as f:
            f.write(dumps(mw_vs_ww_tokens, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        print('{}: {}'.format(article_title, output[article_title]))
    with open(join(mw_jsons, 'comparison_output.json'), 'w', encoding='utf-8') as f:
        f.write(dumps(output, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
