from django.db import connection


def wikiwho_to_db(wikiwho, updated_prev_tokens=None, already_exists=False):
    from django.utils.dateparse import parse_datetime
    from .models import Article, Revision, Token
    from .utils import iter_rev_tokens
    import uuid
    # TODO check Article, Revision, Token fields and compare with structures
    # Article
    if not already_exists:
        Article.objects.create(id=wikiwho.page_id,
                               title=wikiwho.article_title,
                               spam_ids=wikiwho.spam_ids,
                               rvcontinue=wikiwho.rvcontinue)
    else:
        article_obj = Article.objects.get(id=wikiwho.page_id)
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
    revisions = []
    tokens = []
    # TODO loop revisions and check self.continue_rev_ts > rev.ts and detect new revisions
    for rev_id, revision in wikiwho.revisions.items():
        rev_token_ids = []
        timestamp = parse_datetime(revision.time)
        for word in iter_rev_tokens(revision):
            t = Token(id=uuid.uuid3(uuid.NAMESPACE_X500, '{}-{}'.format(wikiwho.page_id, word.token_id)),
                      value=word.value,
                      label_revision_id=word.origin_rev_id,
                      token_id=word.token_id,
                      last_used=word.last_rev_id,
                      inbound=word.inbound,
                      outbound=word.outbound,
                      article_id=wikiwho.page_id,
                      editor=word.editor,
                      timestamp=word.origin_ts
                      )
            tokens.append(t)
            rev_token_ids.append(word.token_id)
        r = Revision(id=rev_id,
                     article_id=wikiwho.page_id,
                     editor=revision.editor,
                     timestamp=timestamp,
                     length=revision.length,
                     position=revision.position,
                     original_adds=revision.original_adds,
                     token_ids=rev_token_ids)
        revisions.append(r)

        # TODO update updated_prev_tokens
        # if updated_prev_tokens:
        #     tokens_to_update = Token.objects.filter(id__in=updated_prev_tokens)
        #     for token in tokens_to_update:
        #         token_ = wikiwho.tokens_to_update[token.id]
        #         update_fields = []
        #         if token.last_used != token_.last_used:
        #             token.last_used = token_.last_used
        #             update_fields.append('last_used')
        #         if token.inbound != token_.inbound:
        #             token.inbound = token_.inbound
        #             update_fields.append('inbound')
        #         if token.outbound != token_.outbound:
        #             token.outbound = token_.outbound
        #             update_fields.append('outbound')
        #         token.save(update_fields=update_fields)
        # del updated_prev_tokens

        del wikiwho
        if revisions:
            Revision.objects.bulk_create(revisions, batch_size=1000000)
        if tokens:
            Token.objects.bulk_create(tokens, batch_size=1000000)


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
