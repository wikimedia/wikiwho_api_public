import pytz
from datetime import datetime
from collections import defaultdict
from os.path import basename, join, dirname, realpath

from django.db import connection
from django.utils.dateparse import parse_datetime
from django.db.utils import ProgrammingError

from api.handler import WPHandler, WPHandlerException
from api.utils_pickles import pickle_load
from api.utils import Timeout

from wikiwho.models import Article
from api_editor.models import (
    EditorDataEnNotIndexed, EditorDataEn,
    EditorDataEuNotIndexed, EditorDataEu,
    EditorDataDeNotIndexed, EditorDataDe,
    EditorDataEsNotIndexed, EditorDataEs,
    EditorDataTrNotIndexed, EditorDataTr,)

EDITOR_MODEL = {'en': (EditorDataEnNotIndexed, EditorDataEn, ),
                'eu': (EditorDataEuNotIndexed, EditorDataEu, ),
                'de': (EditorDataDeNotIndexed, EditorDataDe, ),
                'es': (EditorDataEsNotIndexed, EditorDataEs, ),
                'tr': (EditorDataTrNotIndexed, EditorDataTr, )}


def fill_notindexed_editor_tables(pickle_path, from_ym, to_ym, language, update=False):
    try:
        wikiwho = pickle_load(pickle_path)
        title = wikiwho.title
    except EOFError:
        title = None
        update = True
        # TODO log correpted pickle and dont set upgrade flag

    if update:
        # update pickle until latest revision
        page_id = int(basename(pickle_path)[:-2])
        try:
            timeout = 3600 * 6  # 6 hours
            with Timeout(seconds=timeout, error_message='Timeout {} seconds - page id {}'.format(timeout, page_id)):
                with WPHandler(title, page_id=page_id, language=language) as wp:
                    wp.handle(revision_ids=[],
                              is_api_call=False, timeout=timeout)
                    wikiwho = wp.wikiwho
        except WPHandlerException as e:
            if e.code != '30':
                raise e

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
        article_revisions_dict[rev_id] = parse_datetime(
            wikiwho.revisions[rev_id].timestamp)
    # {'y-m': 'editor_id': [oadd, oadd_48, dels, dels_48, reins, reins_48, persistent_o_adds, persistent_actions]}
    editors_dict = {}
    # {'y-m': 'editor_id': [adds_stopword_count, reins_stopword_count, dels_stopword_count]}
    editors_stop = {}
    ym_start = 12 * from_ym.year + from_ym.month - 1
    ym_end = 12 * to_ym.year + to_ym.month
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        m += 1
        editors_dict[datetime.strptime('{}-{:02}'.format(y, m), '%Y-%m').replace(tzinfo=pytz.UTC).date()] = \
            defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0, 0])
        editors_stop[datetime.strptime('{}-{:02}'.format(y, m), '%Y-%m').replace(tzinfo=pytz.UTC).date()] = \
            defaultdict(lambda: [[], [], []])

    for token in wikiwho.tokens:
        # if token.value in stopwords:
        #    stop_word = 1
        # else:
        #    stop_word = 0
        # oadd
        oadd_rev_ts = article_revisions_dict[token.origin_rev_id]
        if from_ym <= oadd_rev_ts <= to_ym:
            oadd_ym = oadd_rev_ts.date().replace(day=1)
            # oadd action
            oadd_editor = wikiwho.revisions[token.origin_rev_id].editor
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
            # stopword count for oadd
            editors_stop[oadd_ym][oadd_editor][0].append(token.value)

        # rein and del
        in_rev_id = None
        for i, out_rev_id in enumerate(token.outbound):
            # rein
            # if i != 0:
            if in_rev_id is not None:
                #in_rev_id = token.inbound[i-1]
                #in_rev_ts = article_revisions_dict[in_rev_id]
                # there is out for this in
                if from_ym <= in_rev_ts <= to_ym:
                    rein_ym = in_rev_ts.date().replace(day=1)
                    rein_editor = wikiwho.revisions[in_rev_id].editor
                    # action rein is done
                    editors_dict[rein_ym][rein_editor][4] += 1
                    out_rev_ts = article_revisions_dict[out_rev_id]
                    if (out_rev_ts - in_rev_ts).total_seconds() >= seconds_limit:
                        # rein survived 48 hours
                        editors_dict[rein_ym][rein_editor][5] += 1
                        if out_rev_ts.year != rein_ym.year or out_rev_ts.month != rein_ym.month:
                            # persistent action
                            editors_dict[rein_ym][rein_editor][7] += 1
                    # stopword count for rein
                    editors_stop[rein_ym][rein_editor][1].append(token.value)
                elif in_rev_ts > to_ym:
                    in_rev_id = None
                    break

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
                    editors_dict[del_ym][del_editor][2] += 1
                    editors_dict[del_ym][del_editor][3] += 1
                    editors_dict[del_ym][del_editor][7] += 1
                    # stopword count for del
                    editors_stop[del_ym][del_editor][2].append(token.value)
                    break
                else:
                    # there is in for this out
                    editors_dict[del_ym][del_editor][2] += 1
                    in_rev_ts = article_revisions_dict[in_rev_id]
                    if (in_rev_ts - out_rev_ts).total_seconds() >= seconds_limit:
                        editors_dict[del_ym][del_editor][3] += 1
                        if in_rev_ts.year != del_ym.year or in_rev_ts.month != del_ym.month:
                            editors_dict[del_ym][del_editor][7] += 1
                    # stopword count for del
                    editors_stop[del_ym][del_editor][2].append(token.value)
            elif out_rev_ts > to_ym:
                break
            else:
                try:
                    in_rev_id = token.inbound[i]
                except:
                    break
                else:
                    in_rev_ts = article_revisions_dict[in_rev_id]

        # last rein
        # if len(token.outbound) - len(token.inbound) == 0:
        if in_rev_id is not None:
            # no out for this in
            if from_ym <= in_rev_ts <= to_ym:
                rein_ym = in_rev_ts.date().replace(day=1)
                rein_editor = wikiwho.revisions[in_rev_id].editor
                editors_dict[rein_ym][rein_editor][4] += 1
                editors_dict[rein_ym][rein_editor][5] += 1
                editors_dict[rein_ym][rein_editor][7] += 1
                # stopword count for rein
                editors_stop[rein_ym][rein_editor][1].append(token.value)

    # if editors_dict[oadd_ym][oadd_editor][1] == 0 & editors_dict[oadd_ym][oadd_editor][0] == 0 :
    #     editors_stop[oadd_ym][oadd_editor][6] = 0
    # else:
    #     editors_stop[oadd_ym][oadd_editor][6] = editors_dict[oadd_ym][oadd_editor][1] / editors_dict[oadd_ym][oadd_editor][0]
    #
    # if editors_dict[rein_ym][rein_editor][5] == 0 & editors_dict[rein_ym][rein_editor][4] == 0 :
    #     editors_stop[rein_ym][rein_editor][7] = 0
    # else:
    #     editors_stop[rein_ym][rein_editor][7] = editors_dict[rein_ym][rein_editor][5] / editors_dict[rein_ym][rein_editor][4]
    #
    # if editors_dict[del_ym][del_editor][3] == 0 & editors_dict[del_ym][del_editor][2] == 0:
    #     editors_stop[del_ym][del_editor][8] = 0
    # else:
    #     editors_stop[del_ym][del_editor][8] = editors_dict[del_ym][del_editor][3] / editors_dict[del_ym][del_editor][2]

    p = join(dirname(realpath(__file__)), 'stop_word_list.txt')
    with open(p, 'r') as f:
        stopword_set = set(f.read().splitlines())

    # for ym, editor_data in editors_dict.items():
    #     for editor, data in editor_data.items():
    #         print(ym, editor)
    #         stopwords_oadds = []
    #         stopwords_reins = []
    #         stopwords_dels = []
    #         for t in editors_stop[ym][editor][0]:
    #             if t in stopword_set:
    #                 stopwords_oadds.append(t)
    #         for t in editors_stop[ym][editor][1]:
    #             if t in stopword_set:
    #                 stopwords_reins.append(t)
    #         for t in editors_stop[ym][editor][2]:
    #             if t in stopword_set:
    #                 stopwords_dels.append(t)
    #         print('stopwords oadds:', stopwords_oadds)
    #         print('stopwords reins:', stopwords_reins)
    #         print('stopwords dels:', stopwords_dels)

    EDITOR_MODEL[language][0].objects.bulk_create(
        [
            EDITOR_MODEL[language][0](
                article_id=wikiwho.page_id,
                editor_id=0 if editor.startswith(
                    '0|') or editor == '' else int(editor),
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
                adds_stopword_count=sum(
                    t in stopword_set for t in editors_stop[ym][editor][0]),
                reins_stopword_count=sum(
                    t in stopword_set for t in editors_stop[ym][editor][1]),
                dels_stopword_count=sum(
                    t in stopword_set for t in editors_stop[ym][editor][2]),
                # total_actions = (data[0] + data[2] + data[4]),
                # total_actions_surv_48h = (data[1] + data[3] + data[5]),
                # total_actions_stopword_count = ((len([t for t in editors_stop[oadd_ym][oadd_editor][0] if t in stopword_set]))+(len([t for t in editors_stop[rein_ym][rein_editor][1] if t in stopword_set]))+(len([t for t in editors_stop[del_ym][del_editor][2] if t in stopword_set]))),
                # adds_survived_ratio = editors_stop[oadd_ym][oadd_editor][6],
                # reins_survived_ratio = editors_stop[rein_ym][rein_editor][7],
                # dels_survived_ratio = editors_stop[del_ym][del_editor][8],
            )
            for ym, editor_data in editors_dict.items()
            for editor, data in editor_data.items()
        ],
        batch_size=1000000
    )


def fill_indexed_editor_tables(language, from_ym, to_ym, already_partitioned=False):
    master_table = "api_editor_{}".format(
        EDITOR_MODEL[language][1].__name__.lower())
    part_table = '{}{}'.format(master_table, from_ym.year)
    if from_ym.month == 1 and not already_partitioned:
        # new year
        with connection.cursor() as cursor:
            # create a new partition table for current new year
            new_table_query = """
            CREATE TABLE {} 
            (CHECK ( year_month >= DATE '{}-01-01' AND year_month <= DATE '{}-12-31' )) 
            INHERITS ({});
            """.format(part_table, from_ym.year, from_ym.year, master_table)
            cursor.execute(new_table_query)

            # create a trigger function
            x = "{} ( NEW.year_month >= DATE '{}-01-01' AND NEW.year_month <= DATE '{}-12-31' ) THEN INSERT INTO {} VALUES (NEW.*);"
            trigger_function_query = """
            CREATE OR REPLACE FUNCTION api_editor_editordata_{}_insert_trigger()
            RETURNS TRIGGER AS $$
            BEGIN
                {}
                ELSE
                   RAISE EXCEPTION 'Date out of range. Fix the api_editor_editordata_insert_trigger() function!';
                END IF;
                RETURN NULL;
            END;
            $$
            LANGUAGE plpgsql;
            """.format(language,
                       '\n'.join([x.format('IF' if year == from_ym.year else 'ELSIF', year, year,
                                           '{}{}'.format(master_table, year))
                                  for year in range(from_ym.year, 2000, -1)]))
            cursor.execute(trigger_function_query)
            # attach trigger query to the table, this has to be done only one time
            trigger_query = """
            CREATE TRIGGER insert_api_editor_editordata_{}_trigger
              BEFORE INSERT ON {}
              FOR EACH ROW EXECUTE PROCEDURE api_editor_editordata_{}_insert_trigger();
              """.format(language, master_table, language)
            try:
                cursor.execute(trigger_query)
            except ProgrammingError:
                pass

    with connection.cursor() as cursor:
        if from_ym.month != 1 or already_partitioned:
            # drop indexes in the last partition
            cursor.execute("DROP INDEX {}_article_id;".format(part_table))
            cursor.execute("DROP INDEX {}_year_month;".format(part_table))
            cursor.execute("DROP INDEX {}_editor_id_ym;".format(part_table))

        # fill data
        not_indexed_table = "api_editor_{}".format(
            EDITOR_MODEL[language][0].__name__.lower())
        insert_query = """
        INSERT INTO {} 
        (article_id, editor_id, year_month, editor_name, o_adds, o_adds_surv_48h, 
        dels, dels_surv_48h, reins, reins_surv_48h, persistent_o_adds, persistent_actions, 
        adds_stopword_count, reins_stopword_count, dels_stopword_count) 
        (
          SELECT 
            article_id, editor_id, year_month, editor_name, o_adds, o_adds_surv_48h, 
            dels, dels_surv_48h, reins, reins_surv_48h, persistent_o_adds, persistent_actions, 
            adds_stopword_count, reins_stopword_count, dels_stopword_count
          FROM {} 
        );
        """.format(master_table, not_indexed_table)
        cursor.execute(insert_query)

        # re-create indexes
        cursor.execute("CREATE INDEX {}_article_id ON {} USING btree (article_id);".format(
            part_table, part_table))
        cursor.execute("CREATE INDEX {}_year_month ON {} USING btree (year_month);".format(
            part_table, part_table))
        cursor.execute("CREATE INDEX {}_editor_id_ym ON {} USING btree (editor_id, year_month);".
                       format(part_table, part_table))


def empty_notindexed_editor_tables(language):
    EDITOR_MODEL[language][0].objects.all().delete()
