from django.db import connection


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
