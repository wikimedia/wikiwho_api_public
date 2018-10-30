import pytz
from datetime import datetime
from collections import defaultdict
from os.path import basename, join, dirname, realpath

from django.db import connection
from django.utils.dateparse import parse_datetime, datetime_re
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

__ADDS__ = 0
__ADDS_48__ = 1
__DELS__ = 2
__DELS_48__ = 3
__REINS__ = 4
__REINS_48__ = 5
__ADDS_P__ = 6
__ACTS_P__ = 7
__ADDS_SW__ = 8
__DELS_SW__ = 9
__REINS_SW__ = 10


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

    with open(join(dirname(realpath(__file__)), 'stop_word_list.txt'), 'r') as f:
        stopword_set = set(f.read().splitlines())

    # update or create the article
    article, created = Article.objects.update_or_create(page_id=wikiwho.page_id, language=language,
                                                        defaults={'title': wikiwho.title,
                                                                  'spam_ids': wikiwho.spam_ids,
                                                                  'rvcontinue': wikiwho.rvcontinue})
    # 48 hours
    seconds_limit = 172800  

    # contains an integer representing year month
    article_revisions_yms = {}
    # contains the revision timestamp
    article_revisions_tss = {}
    # contain parsed information of the editor
    ed2edid = {}

    for rev_id, rev in wikiwho.revisions.items():
        #dt = parse_datetime(rev.timestamp)
        dt = datetime(**{k: pytz.utc if v == 'Z' else int(v)
                         for k, v in datetime_re.match(rev.timestamp).groupdict().items() if v is not None})

        # store date as an integer
        article_revisions_yms[rev_id] = dt.year * 100 + dt.month
        article_revisions_tss[rev_id] = dt.timestamp()

        # fill up information of new found editors
        if rev.editor not in ed2edid:
            ed2edid[rev.editor] = {
                'id': 0,
                'name': rev.editor[2:],
            } if rev.editor.startswith('0|') else {
                'id': 0 if rev.editor == '' else int(rev.editor),
                'name': '',
            }

    # create a dictionary to store intermediate results
    editors_dict = {y + m:  defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                    for y in range(from_ym.year * 100, to_ym.year * 100 + 1, 100) for m in range(1, 13)}

    # use the date timestamps as it is faster
    from_ym_ts = from_ym.timestamp()
    to_ym_ts = to_ym.timestamp()

    for token in wikiwho.tokens:
        # flag if it is stop word
        is_stop_word = token.value in stopword_set

        # original additions
        oadd_rev_ts = article_revisions_tss[token.origin_rev_id]
        if from_ym_ts <= oadd_rev_ts <= to_ym_ts:
            # there is an addition

            oadd_ym = article_revisions_yms[token.origin_rev_id]
            oadd_editor = wikiwho.revisions[token.origin_rev_id].editor
            editors_dict[oadd_ym][oadd_editor][__ADDS__] += 1
            if token.outbound:
                first_out_ts = article_revisions_tss[token.outbound[0]]
                if first_out_ts - oadd_rev_ts >= seconds_limit:
                    # there is an outbund but survived 48 hours
                    editors_dict[oadd_ym][oadd_editor][__ADDS_48__] += 1

                    if oadd_ym != article_revisions_yms[token.outbound[0]]:
                        # it was not deleted in this month, so it is permanent
                        editors_dict[oadd_ym][oadd_editor][__ADDS_P__] += 1
                        editors_dict[oadd_ym][oadd_editor][__ACTS_P__] += 1
            else:
                # there is no outbound, additions is permanent
                editors_dict[oadd_ym][oadd_editor][__ADDS_48__] += 1
                editors_dict[oadd_ym][oadd_editor][__ADDS_P__] += 1
                editors_dict[oadd_ym][oadd_editor][__ACTS_P__] += 1

            if is_stop_word:
                # stopword count for oadd
                editors_dict[oadd_ym][oadd_editor][__ADDS_SW__] += 1

        # reinsertions and deleletions
        in_rev_id = None
        for i, out_rev_id in enumerate(token.outbound):
            # reinsertions
            if in_rev_id is not None:
                # there is a reinsertion

                if from_ym_ts <= in_rev_ts <= to_ym_ts:
                    # the reinsertion corresponds to this period

                    rein_editor = wikiwho.revisions[in_rev_id].editor
                    editors_dict[rein_ym][rein_editor][__REINS__] += 1

                    if article_revisions_tss[out_rev_id] - in_rev_ts >= seconds_limit:
                        # the reinsertion has survived 48 hours
                        editors_dict[rein_ym][rein_editor][__REINS_48__] += 1
                        if rein_ym != article_revisions_yms[out_rev_id]:
                            # it was not deleted again this month, so it is permanent
                            editors_dict[rein_ym][rein_editor][__ACTS_P__] += 1

                    if is_stop_word:
                        # stopword count for rein
                        editors_dict[rein_ym][rein_editor][__REINS_SW__] += 1
                elif in_rev_ts > to_ym_ts:
                    in_rev_id = None
                    break

            # deletions
            in_rev_id = None
            out_rev_ts = article_revisions_tss[out_rev_id]
            if from_ym_ts <= out_rev_ts <= to_ym_ts:
                # the deletion corresponds to the period

                del_ym = article_revisions_yms[out_rev_id]
                del_editor = wikiwho.revisions[out_rev_id].editor

                if i < len(token.inbound):
                    # there is an in for this out (reinsertion)
                    in_rev_id = token.inbound[i]
                    editors_dict[del_ym][del_editor][__DELS__] += 1
                    in_rev_ts = article_revisions_tss[in_rev_id]

                    # there is a reinsertion to be processed in the next loop
                    rein_ym = article_revisions_yms[in_rev_id]

                    if in_rev_ts - out_rev_ts >= seconds_limit:
                        # the deletion lasted at least 48 hours
                        editors_dict[del_ym][del_editor][__DELS_48__] += 1
                        if del_ym != article_revisions_yms[in_rev_id]:
                            # the deletion last until the end of the month (permanent)
                            editors_dict[del_ym][del_editor][__ACTS_P__] += 1

                    if is_stop_word:
                        # stopword count for del
                        editors_dict[del_ym][del_editor][__DELS_SW__] += 1

                else:
                    # no in for this out, therefore is permament
                    editors_dict[del_ym][del_editor][__DELS__] += 1
                    editors_dict[del_ym][del_editor][__DELS_48__] += 1
                    editors_dict[del_ym][del_editor][__ACTS_P__] += 1

                    if is_stop_word:
                        # stopword count for del
                        editors_dict[del_ym][del_editor][__DELS_SW__] += 1
                    # break the loop (nothing else happen to this token during this month)
                    break

            elif out_rev_ts > to_ym_ts:
                break
            else:
                if i < len(token.inbound):
                    # there is an in for this out (reinsertion)
                    in_rev_id = token.inbound[i]
                    in_rev_ts = article_revisions_tss[in_rev_id]

                    # there is a reinsertion to be processed in the next loop
                    rein_ym = article_revisions_yms[in_rev_id]
                else:
                    # break the loop (nothing else happen to this token during this month)
                    break

        # last reinsertion
        # if len(token.outbound) - len(token.inbound) == 0:
        if in_rev_id is not None:
            # it is in between the dates
            if from_ym_ts <= in_rev_ts <= to_ym_ts:
                rein_editor = wikiwho.revisions[in_rev_id].editor
                editors_dict[rein_ym][rein_editor][__REINS__] += 1
                editors_dict[rein_ym][rein_editor][__REINS_48__] += 1
                editors_dict[rein_ym][rein_editor][__ACTS_P__] += 1

                if is_stop_word:
                    # stopword count for rein
                    editors_dict[rein_ym][rein_editor][__REINS_SW__] += 1

    # map the ym to datetimes in order to do it only once
    ym2dt = {ym: datetime.strptime('{}-{:02}'.format(*divmod(ym, 100)), '%Y-%m').replace(
        tzinfo=pytz.UTC).date() for ym in editors_dict.keys()}

    # save to the database
    EDITOR_MODEL[language][0].objects.bulk_create(
        (
            EDITOR_MODEL[language][0](
                article_id=wikiwho.page_id,
                editor_id=ed2edid[editor]['id'],
                editor_name=ed2edid[editor]['name'],
                year_month=ym2dt[ym],
                o_adds=data[__ADDS__],
                o_adds_surv_48h=data[__ADDS_48__],
                dels=data[__DELS__],
                dels_surv_48h=data[__DELS_48__],
                reins=data[__REINS__],
                reins_surv_48h=data[__REINS_48__],
                persistent_o_adds=data[__ADDS_P__],
                persistent_actions=data[__ACTS_P__],
                adds_stopword_count=data[__ADDS_SW__],
                reins_stopword_count=data[__REINS_SW__],
                dels_stopword_count=data[__DELS_SW__],

            )
            for ym, editor_data in editors_dict.items()
            for editor, data in editor_data.items()
        ),
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
