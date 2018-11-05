import uuid
import json
from os.path import join

from django.db import connection
from django.utils.dateparse import parse_datetime

from WikiWho.utils import iter_rev_tokens


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
