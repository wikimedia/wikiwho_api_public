import json
import os
d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tmp_test_3/postgres2_branch_before_token_id_fix_with_wip_18-10-16'  # 80/2 = 40
d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/test_jsons/master_branch_after_token_id_fix_18-10-16'  # 4
d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/test_jsons/postgres2_branch_after_token_id_fix_19-10-16'  # 8/2 = 4
d = '/home/kenan/PycharmProjects/wikiwho_api/test'
# d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tmp_test_3/django_26-08-2016'  # 30
# d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/test_jsons/after_ordering_fix_but_sth_is_wrong'  # 30
# d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/test_jsons/before_ordering_fix'  # 30
# d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tmp_test_3/test_jsons_before_reverting_rev_comment_fix_17-10-16'  # 40
c = 0
for f in os.listdir(d):
    print(f)
    if f.endswith('.json') and not f.endswith('_without_tokenid.json'):
        p = d + '/' + f
        with open(p, 'r') as json_file:
            j = json.load(json_file)

        rev_id, rev = j['revisions'][0].popitem()
        token_ids = [x['tokenid'] for x in rev['tokens']]
        if len(token_ids) != len(set(token_ids)):
            c += 1
            print(f, len(token_ids), len(set(token_ids)), set([x for x in token_ids if token_ids.count(x) > 1]))
print(c)


# # to remove tokenids from jsons
# import json
# import os, io
# # d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tmp_test_3/django_26-08-2016'  # 30
# d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/test_jsons/after_ordering_fix_but_sth_is_wrong'  # 30
# # d = '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/test_jsons/before_ordering_fix'  # 30
# for f in os.listdir(d):
#     if f.endswith('.json'):
#         p = d + '/' + f
#         with open(p, 'r') as json_file:
#             j = json.load(json_file)
#
#         for rev_id, rev in j['revisions'][0].items():
#             for token in rev['tokens']:
#                 del token['tokenid']
#         p2 = p[:-5] + '_without_tokenid.json'
#         print(f)
#         with io.open(p2, 'w', encoding='utf-8') as json_file2:
#             json_file2.write(json.dumps(j, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))