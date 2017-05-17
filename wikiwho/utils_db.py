import uuid

from django.db import connection
from django.utils.dateparse import parse_datetime

from WikiWho.utils import iter_rev_tokens  # , iter_wikiwho_tokens


def wikiwho_to_db(wikiwho, save_tables=('article', 'revision', 'token', )):
    from .models import Article, Revision, Token
    save_article = 'article' in save_tables
    save_revision = 'revision' in save_tables
    save_token = 'token' in save_tables
    created = True
    # Article
    if save_article:
        article_obj, created = Article.objects.get_or_create(id=wikiwho.page_id,
                                                             defaults={'title': wikiwho.title,
                                                                       'spam_ids': wikiwho.spam_ids,
                                                                       'rvcontinue': wikiwho.rvcontinue})
        if not created:
            if article_obj.rvcontinue != wikiwho.rvcontinue and article_obj.spam_ids != wikiwho.spam_ids:
                article_obj.rvcontinue = wikiwho.rvcontinue
                article_obj.spam_ids = wikiwho.spam_ids
                article_obj.save(update_fields=['rvcontinue', 'spam_ids'])
            elif article_obj.rvcontinue != wikiwho.rvcontinue:
                article_obj.rvcontinue = wikiwho.rvcontinue
                article_obj.save(update_fields=['rvcontinue'])
            elif article_obj.spam_ids != wikiwho.spam_ids:
                article_obj.spam_ids = wikiwho.spam_ids
                article_obj.save(update_fields=['spam_ids'])

    # Revisions and Tokens
    if save_revision or save_token:
        if created:
            last_revision_ts = None
        else:
            last_revision = Revision.objects.order_by('timestamp').last().only('timestamp')
            last_revision_ts = last_revision.timestamp if last_revision else None
        revisions = []
        tokens = []
        # TODO update and iterate wikiwho.tokens + test it
        article_token_ids = set()
        updated_prev_tokens = {}
        for rev_id in wikiwho.ordered_revisions:
            revision = wikiwho.revisions[rev_id]
            rev_timestamp = parse_datetime(revision.timestamp)
            if last_revision_ts and rev_timestamp <= last_revision_ts:
                continue

            if save_revision:
                r = Revision(id=rev_id,
                             article_id=wikiwho.page_id,
                             editor=revision.editor,
                             timestamp=rev_timestamp,
                             length=revision.length,
                             original_adds=revision.original_adds,
                             token_ids=[t.token_id for t in iter_rev_tokens(revision)])
                revisions.append(r)

            if save_token:
                for word in iter_rev_tokens(revision):
                    if word.token_id not in article_token_ids:
                        origin_rev_id_ts = parse_datetime(wikiwho.revisions[word.origin_rev_id].timestamp)
                        t = Token(id=uuid.uuid3(uuid.NAMESPACE_X500, '{}-{}'.format(wikiwho.page_id, word.token_id)),
                                  value=word.value,
                                  origin_rev_id=word.origin_rev_id,
                                  token_id=word.token_id,
                                  last_rev_id=word.last_rev_id,
                                  inbound=word.inbound,
                                  outbound=word.outbound,
                                  article_id=wikiwho.page_id,
                                  editor=wikiwho.revisions[word.origin_rev_id].editor,
                                  timestamp=origin_rev_id_ts
                                  )
                        tokens.append(t)
                        article_token_ids.add(word.token_id)
                        # prev tokens that are updated by last_used, in or out
                        if last_revision_ts and origin_rev_id_ts <= last_revision_ts:
                            updated_prev_tokens[word.token_id] = word

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
        if revisions:
            Revision.objects.bulk_create(revisions, batch_size=1000000)
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
    # TODO write into revisions csv


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
