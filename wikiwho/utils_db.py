import uuid
import json
import pytz
from datetime import datetime

from collections import defaultdict
from django.db import connection
from django.utils.dateparse import parse_datetime

from WikiWho.utils import iter_rev_tokens
from api.handler import WPHandler
from api.utils_pickles import pickle_load
# from api.utils import revert_rvcontinue
from .models import Article, EditorDataEnNotIndexed, EditorDataEn, EditorDataEuNotIndexed, EditorDataEu, \
    EditorDataDeNotIndexed, EditorDataDe

EDITOR_MODEL = {'en': EditorDataEnNotIndexed, 'eu': EditorDataEuNotIndexed, 'de': EditorDataDeNotIndexed}


def wikiwho_to_db(wikiwho, language, save_tables=('article', 'revision', 'token', )):
    # TODO go over this method and test it
    from .models import Article, Revision, Token
    article, created = Article.objects.get_or_create(id=wikiwho.page_id,
                                                     defaults={'title': wikiwho.title,
                                                               'spam_ids': wikiwho.spam_ids,
                                                               'rvcontinue': wikiwho.rvcontinue})
    if not created:
        article_last_rev_ts = parse_datetime(article.rvcontinue.split('|')[0])
    revisions = []
    # article_token_ids = set()
    # tokens = []
    for rev_id in wikiwho.ordered_revisions:
        revision = wikiwho.revisions[rev_id]
        rev_timestamp = parse_datetime(revision.timestamp)
        if created or rev_timestamp >= article_last_rev_ts:
            # TODO is it possible to have revisions with save ts in an article
            token_ids = []
            added_tokens = []
            reinserted_tokens = []
            deleted_tokens = []
            for token in iter_rev_tokens(revision):
                token_ids.append(token.token_id)
                if rev_id == token.origin_rev_id:
                    added_tokens.append(token.value)  # TODO ids too?
                elif rev_id in token.inbound:
                    reinserted_tokens.append(token.value)
                elif rev_id in token.outbound:
                    deleted_tokens.append(token.value)
            r = Revision(id=rev_id,
                         article_id=wikiwho.page_id,
                         editor_id=revision.editor if not revision.editor.startswith('0|') else 0,
                         editor_name='' if not revision.editor.startswith('0|') else revision.editor[2:],
                         timestamp=rev_timestamp,
                         length=revision.length,
                         original_adds=revision.original_adds,
                         token_ids=[t.token_id for t in iter_rev_tokens(revision)],
                         added_tokens=','.join(added_tokens),
                         added_tokens_count=len(added_tokens),
                         reinserted_tokens=','.join(reinserted_tokens),
                         reinserted_tokens_count=len(reinserted_tokens),
                         deleted_tokens=','.join(deleted_tokens),
                         deleted_tokens_count=len(deleted_tokens),
                         language=language)
            revisions.append(r)

            # for word in iter_rev_tokens(revision):
            #     if word.token_id not in article_token_ids:
            #         origin_rev_ts = parse_datetime(wikiwho.revisions[word.origin_rev_id].timestamp)
            #         t = Token(id=uuid.uuid3(uuid.NAMESPACE_X500, '{}-{}'.format(wikiwho.page_id, word.token_id)),
            #                   value=word.value,
            #                   origin_rev_id=word.origin_rev_id,
            #                   token_id=word.token_id,
            #                   last_rev_id=word.last_rev_id,
            #                   inbound=word.inbound,
            #                   outbound=word.outbound,
            #                   article_id=wikiwho.page_id,
            #                   editor=wikiwho.revisions[word.origin_rev_id].editor,
            #                   timestamp=origin_rev_ts
            #                   )
            #         tokens.append(t)
            #         article_token_ids.add(word.token_id)
            #         # prev tokens that are updated by last_used, in or out
            #         if last_rev_ts and origin_rev_ts <= last_rev_ts:
            #             updated_prev_tokens[word.token_id] = word
            #
    if len(revisions) == 1:
        revisions[0].save()
    elif len(revisions) > 1:
        # TODO how to do this most efficiently
        Revision.objects.bulk_create(revisions, batch_size=1000000)

    updated_prev_tokens = {}
    tokens = []
    for word in wikiwho.tokens:
        origin_rev_ts = parse_datetime(wikiwho.revisions[word.origin_rev_id].timestamp)
        last_rev_ts = parse_datetime(wikiwho.revisions[word.last_rev_id].timestamp)
        if last_rev_ts <= article_last_rev_ts:
            continue
        # prev tokens that are updated by last_used, in or out
        if not created and last_rev_ts > article_last_rev_ts >= origin_rev_ts:
            updated_prev_tokens[word.token_id] = word
        else:
            t = Token(id=uuid.uuid3(uuid.NAMESPACE_X500, '{}-{}'.format(wikiwho.page_id, word.token_id)),
                      value=word.value,
                      origin_rev_id=word.origin_rev_id,
                      token_id=word.token_id,
                      last_rev_id=word.last_rev_id,
                      inbound=word.inbound,
                      outbound=word.outbound,
                      article_id=wikiwho.page_id,
                      editor=wikiwho.revisions[word.origin_rev_id].editor,
                      timestamp=origin_rev_ts
                      )
            tokens.append(t)

    if updated_prev_tokens:
        tokens_to_update = Token.objects.filter(id__in=list(updated_prev_tokens.keys()))
        for token in tokens_to_update:
            token_ = updated_prev_tokens[token.id]
            update_fields = []
            if token.last_used != token_.last_used:
                token.last_used = token_.last_used
                update_fields.append('last_used')
            if token.inbound != token_.inbound:
                token.inbound = token_.inbound
                update_fields.append('inbound')
            if token.outbound != token_.outbound:
                token.outbound = token_.outbound
                update_fields.append('outbound')
            token.save(update_fields=update_fields)
        del updated_prev_tokens

    # del wikiwho
    if tokens:
        Token.objects.bulk_create(tokens, batch_size=1000000)


def fill_editor_table(pickle_path, from_ym, to_ym, language, update=False):
    wikiwho = pickle_load(pickle_path)

    if update:
        # update pickle until latest revision
        with WPHandler(wikiwho.title, page_id=wikiwho.page_id, language=language) as wp:
            # TODO what to do with Long failed and recursion articles
            wp.handle(revision_ids=[], is_api_call=False)
            wikiwho = wp.wikiwho

    article, created = Article.objects.update_or_create(page_id=wikiwho.page_id, language=language,
                                                        defaults={'title': wikiwho.title,
                                                                  'spam_ids': wikiwho.spam_ids,
                                                                  'rvcontinue': wikiwho.rvcontinue})
    # if not created:
    #     article_last_rev_ts = parse_datetime(revert_rvcontinue(article.rvcontinue))
    #     if article_last_rev_ts >= to_ym:
    #         raise Exception('Article ({}) is already processed in this period (from {} to {}). '
    #                         'article db rvcontinue in db: {}'.
    #                         format(wikiwho.title, from_ym, to_ym, article.rvcontinue))

    seconds_limit = 172800  # 48 hours
    # {rev_id: datetime(rev_ts)}
    article_revisions_dict = {}
    for rev_id in wikiwho.ordered_revisions:
        article_revisions_dict[rev_id] = parse_datetime(wikiwho.revisions[rev_id].timestamp)
    # {'y-m': 'editor_id': [oadd, oadd_48, dels, dels_48, reins, reins_48, persistent_o_adds, persistent_actions]}
    editors_dict = {}
    ym_start = 12 * from_ym.year + from_ym.month - 1
    ym_end = 12 * to_ym.year + to_ym.month
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        m += 1
        editors_dict[datetime.strptime('{}-{:02}'.format(y, m), '%Y-%m').replace(tzinfo=pytz.UTC).date()] = \
            defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0, 0])

    for token in wikiwho.tokens:
        # oadd
        oadd_rev_ts = article_revisions_dict[token.origin_rev_id]
        if from_ym <= oadd_rev_ts <= to_ym:
            oadd_ym = oadd_rev_ts.date().replace(day=1)
            oadd_editor = wikiwho.revisions[token.origin_rev_id].editor  # oadd action
            editors_dict[oadd_ym][oadd_editor][0] += 1
            if token.outbound:
                first_out_ts = article_revisions_dict[token.outbound[0]]
                if (first_out_ts - oadd_rev_ts).total_seconds() >= seconds_limit:
                    # survived 48 hours
                    editors_dict[oadd_ym][oadd_editor][1] += 1
                    if first_out_ts.year != oadd_ym.year or first_out_ts.month != oadd_ym.month:
                        # not deleted in this month
                        editors_dict[oadd_ym][oadd_editor][6] += 1
                        editors_dict[oadd_ym][oadd_editor][7] += 1
            else:
                editors_dict[oadd_ym][oadd_editor][1] += 1
                editors_dict[oadd_ym][oadd_editor][6] += 1
                editors_dict[oadd_ym][oadd_editor][7] += 1

        # rein and del
        in_rev_id = None
        for i, out_rev_id in enumerate(token.outbound):
            # rein
            if i != 0:
                # there is out for this in
                if from_ym <= in_rev_ts <= to_ym:
                    rein_ym = in_rev_ts.date().replace(day=1)
                    rein_editor = wikiwho.revisions[in_rev_id].editor
                    editors_dict[rein_ym][rein_editor][2] += 1  # action rein is done
                    out_rev_ts = article_revisions_dict[out_rev_id]
                    if (out_rev_ts - in_rev_ts).total_seconds() >= seconds_limit:
                        editors_dict[rein_ym][rein_editor][3] += 1  # rein survived 48 hours
                        if out_rev_ts.year != rein_ym.year or out_rev_ts.month != rein_ym.month:
                            editors_dict[rein_ym][rein_editor][7] += 1  # persistent action

            # del
            in_rev_id = None
            out_rev_ts = article_revisions_dict[out_rev_id]
            if from_ym <= out_rev_ts <= to_ym:
                del_ym = out_rev_ts.date().replace(day=1)
                del_editor = wikiwho.revisions[out_rev_id].editor
                try:
                    in_rev_id = token.inbound[i]
                except (IndexError, KeyError):
                    # no in for this out
                    editors_dict[del_ym][del_editor][4] += 1
                    editors_dict[del_ym][del_editor][5] += 1
                    editors_dict[del_ym][del_editor][7] += 1
                    break
                else:
                    # there is in for this out
                    editors_dict[del_ym][del_editor][4] += 1
                    in_rev_ts = article_revisions_dict[in_rev_id]
                    if (in_rev_ts - out_rev_ts).total_seconds() >= seconds_limit:
                        editors_dict[del_ym][del_editor][5] += 1
                        if in_rev_ts.year != del_ym.year or in_rev_ts.month != del_ym.month:
                            editors_dict[del_ym][del_editor][7] += 1
            else:
                break
        # last rein
        if in_rev_id is not None:
            # no out for this in
            if from_ym <= in_rev_ts <= to_ym:
                rein_ym = in_rev_ts.date().replace(day=1)
                rein_editor = wikiwho.revisions[in_rev_id].editor
                editors_dict[rein_ym][rein_editor][2] += 1
                editors_dict[rein_ym][rein_editor][3] += 1
                editors_dict[rein_ym][rein_editor][7] += 1

    EDITOR_MODEL[language].objects.bulk_create(
        [
            EDITOR_MODEL[language](
                article_id=wikiwho.page_id,
                editor_id=0 if editor.startswith('0|') else int(editor),
                editor_name=editor[2:] if editor.startswith('0|') else '',
                year_month=ym,
                o_adds=data[0],
                o_adds_surv_48h=data[1],
                dels=data[2],
                dels_surv_48h=data[3],
                reins=data[4],
                reins_surv_48h=data[5],
                persistent_o_adds=data[6],
                persistent_actions=data[7],
            )
            for ym, editor_data in editors_dict.items()
            for editor, data in editor_data.items()
        ],
        batch_size=1000000
    )


def wikiwho_to_csv(wikiwho, output_folder):
    content = ''
    current_content = ''
    deleted_content = ''
    article_last_rev_id = wikiwho.ordered_revisions[-1]
    # for word in iter_wikiwho_tokens(wikiwho):
    for word in wikiwho.tokens:
        # page_id,last_rev_id,token_id,str,origin_rev_id,in,out
        if word.inbound:
            if len(word.inbound) == 1:
                inbound = '{{{}}}'.format(word.inbound[0])
            else:
                inbound = '"{{{}}}"'.format(','.join(map(str, word.inbound)))
        else:
            inbound = '{}'
        if word.outbound:
            if len(word.outbound) == 1:
                outbound = '{{{}}}'.format(word.outbound[0])
            else:
                outbound = '"{{{}}}"'.format(','.join(map(str, word.outbound)))
        else:
            outbound = '{}'
        # test_strings = ['"', '"press', 'te""st', 'tes,t"', 'tes,t', 'test123']
        value = word.value.replace('"', '""')
        value = '"{}"'.format(value) if (',' in value or '"' in value) else value
        row = '{},{},{},{},{},{},{}\n'.format(wikiwho.page_id, word.last_rev_id, word.token_id, value,
                                              word.origin_rev_id, inbound, outbound)
        content += row
        if word.last_rev_id == article_last_rev_id:
            current_content += row
        else:
            deleted_content += row
    with open('{}/{}_content.csv'.format(output_folder, wikiwho.page_id), 'w') as f:
        f.write(content[:-1])
    with open('{}/{}_current_content.csv'.format(output_folder, wikiwho.page_id), 'w') as f:
        f.write(current_content[:-1])
    with open('{}/{}_deleted_content.csv'.format(output_folder, wikiwho.page_id), 'w') as f:
        f.write(deleted_content[:-1])
    with open('{}/{}_revisions.csv'.format(output_folder, wikiwho.page_id), 'w') as f:
        f.write('page_id,rev_id,timestamp,editor\n')
        for rev_id in wikiwho.ordered_revisions:
            rev = wikiwho.revisions[rev_id]
            f.write('{},{},{},{}\n'.format(wikiwho.title, str(rev_id), str(rev.timestamp), rev.editor))


def wikiwho_to_graph_json(wikiwho, folder_path):
    json_data = wikiwho.get_all_content_as_graph()
    with open('{}/{}_graph_content.json'.format(folder_path, wikiwho.page_id), 'w') as f:
        f.write(json.dumps(json_data, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))


def tokens_custom(rev_id, values_list, ordered=True, explain=False, return_dict=True):
    select = []
    columns = []
    extra_inner = []
    if 'token_id' in values_list:
        select.append('"wikiwho_token"."token_id"')
        columns.append('token_id')
    elif 't_id' in values_list:
        select.append('"wikiwho_token"."token_id"')
        columns.append('t_id')
    if 'inbound' in values_list:
        select.append('"wikiwho_token"."inbound"')
        columns.append('inbound')
    elif 'in' in values_list:
        select.append('"wikiwho_token"."inbound"')
        columns.append('in')
    if 'outbound' in values_list:
        select.append('"wikiwho_token"."outbound"')
        columns.append('outbound')
    elif 'out' in values_list:
        select.append('"wikiwho_token"."outbound"')
        columns.append('out')
    if 'rev_id' in values_list:
        select.append('"wikiwho_token"."label_revision_id"')
        columns.append('rev_id')
    if 'str' in values_list:
        select.append('"wikiwho_token"."value"')
        columns.append('str')
    if 'editor' in values_list:
        select.append('"wikiwho_token"."editor"')
        columns.append('editor')
    if 'timestamp' in values_list:
        select.append('"wikiwho_token"."timestamp"')
        columns.append('timestamp')

    if ordered:
        order = """
                \nORDER BY "wikiwho_revisionparagraph"."position" ASC,
                "wikiwho_paragraphsentence"."position" ASC,
                "wikiwho_sentencetoken"."position" ASC
                """
    else:
        order = ''

    query = """
            {}SELECT {}
            FROM "wikiwho_token"
            INNER JOIN "wikiwho_sentencetoken" ON ("wikiwho_token"."id" = "wikiwho_sentencetoken"."token_id")
            INNER JOIN "wikiwho_paragraphsentence" ON ("wikiwho_sentencetoken"."sentence_id" = "wikiwho_paragraphsentence"."sentence_id")
            INNER JOIN "wikiwho_revisionparagraph" ON ("wikiwho_paragraphsentence"."paragraph_id" = "wikiwho_revisionparagraph"."paragraph_id")
            {}WHERE "wikiwho_revisionparagraph"."revision_id" = %s{}
             """.format('EXPLAIN ' if explain else '',
                        ',\n'.join(select),
                        '\n'.join(extra_inner),
                        order)
    # print(query)
    with connection.cursor() as cursor:
        cursor.execute(query, [rev_id])
        if explain:
            return cursor.fetchall()
        if return_dict:
            tokens = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
                ]
        else:
            tokens = cursor.fetchall()
    return tokens
