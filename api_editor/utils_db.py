import pytz
from datetime import datetime
from collections import defaultdict
from os.path import basename, join, dirname, realpath

from deployment.celery_config import long_task_soft_time_limit

from django.db import connection
from django.utils.dateparse import parse_datetime, datetime_re
from django.db.utils import ProgrammingError
from django.conf import settings

from api.handler import WPHandler, WPHandlerException
from api.utils_pickles import pickle_load, UnpicklingError
from api.tasks import save_long_failed_article
from api.utils import Timeout
from api_editor.utils import Timer

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
__ADDS_P__ = 2
__ADDS_SW__ = 3
__DELS__ = 4
__DELS_48__ = 5
__DELS_P__ = 6
__DELS_SW__ = 7
__REINS__ = 8
__REINS_48__ = 9
__REINS_P__ = 10
__REINS_SW__ = 11


def fill_notindexed_editor_tables(pickle_path, from_ym, to_ym, language, update=False):

    try:
        wikiwho = pickle_load(pickle_path)
        title = wikiwho.title
    except (EOFError,  UnpicklingError, FileNotFoundError) as e:
        title = None
        wikiwho = None
        update = True
        # TODO log correpted pickle and dont set upgrade flag
    if update:
        # update pickle until latest revision
        page_id = int(basename(pickle_path)[:-2])
        try:
            if (settings.DEBUG or settings.TESTING):
                timeout = 60 * 2
            else:
                timeout = long_task_soft_time_limit  # 6 hours
            with Timeout(seconds=timeout, error_message='Timeout {} seconds - page id {}'.format(timeout, page_id)):
                with WPHandler(title, page_id=page_id, wikiwho=wikiwho, language=language) as wp:
                    wp.handle(revision_ids=[],
                              is_api_call=False, timeout=timeout)
                    if wp.wikiwho is None:
                        raise Exception(
                            'Handler did not return any WikiWho object')
                    else:
                        wikiwho = wp.wikiwho
        except WPHandlerException as e:
            if wikiwho is None:
                raise e
        except TimeoutError as e:
            save_long_failed_article(wp, language)

    with open(join(dirname(realpath(__file__)), 'stop_word_list.txt'), 'r') as f:
        stopword_set = set(f.read().splitlines())

    # 48 hours
    seconds_limit = 172800

    # contains an integer representing year month
    article_revisions_yms = {}
    # contains the revision timestamp
    article_revisions_tss = {}
    # contain parsed information of the editor
    ed2edid = {}

    # The line below will stop the execution, and you can access the variables from here
    # import ipdb; ipdb.set_trace()

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
    editors_dict = {y + m:  defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
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
            else:
                # there is no outbound, additions is permanent
                editors_dict[oadd_ym][oadd_editor][__ADDS_48__] += 1
                editors_dict[oadd_ym][oadd_editor][__ADDS_P__] += 1

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
                            # it was not deleted again this month, so it is
                            # permanent
                            editors_dict[rein_ym][
                                rein_editor][__REINS_P__] += 1

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
                            # the deletion last until the end of the month
                            # (permanent)
                            editors_dict[del_ym][del_editor][__DELS_P__] += 1

                    if is_stop_word:
                        # stopword count for del
                        editors_dict[del_ym][del_editor][__DELS_SW__] += 1

                else:
                    # no in for this out, therefore is permament
                    editors_dict[del_ym][del_editor][__DELS__] += 1
                    editors_dict[del_ym][del_editor][__DELS_48__] += 1
                    editors_dict[del_ym][del_editor][__DELS_P__] += 1

                    if is_stop_word:
                        # stopword count for del
                        editors_dict[del_ym][del_editor][__DELS_SW__] += 1
                    # break the loop (nothing else happen to this token during
                    # this month)
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
                    # break the loop (nothing else happen to this token during
                    # this month)
                    break

        # last reinsertion
        # if len(token.outbound) - len(token.inbound) == 0:
        if in_rev_id is not None:
            # it is in between the dates
            if from_ym_ts <= in_rev_ts <= to_ym_ts:
                rein_editor = wikiwho.revisions[in_rev_id].editor
                editors_dict[rein_ym][rein_editor][__REINS__] += 1
                editors_dict[rein_ym][rein_editor][__REINS_48__] += 1
                editors_dict[rein_ym][rein_editor][__REINS_P__] += 1

                if is_stop_word:
                    # stopword count for rein
                    editors_dict[rein_ym][rein_editor][__REINS_SW__] += 1

    # map the ym to datetimes in order to do it only once
    ym2dt = {ym: datetime.strptime('{}-{:02}'.format(*divmod(ym, 100)), '%Y-%m').replace(
        tzinfo=pytz.UTC).date() for ym in editors_dict.keys()}

    with connection.cursor() as cursor:

        # create query
        insert_query = """
            INSERT INTO api_editor_{} 
                (page_id, editor_id, editor_name, year_month, 
                adds, adds_surv_48h, adds_persistent, adds_stopword_count, 
                dels, dels_surv_48h, dels_persistent, dels_stopword_count, 
                reins, reins_surv_48h, reins_persistent, reins_stopword_count) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
            """.format(EDITOR_MODEL[language][0].__name__.lower())

        # fill data
        cursor.executemany(insert_query,
                           ((wikiwho.page_id, ed2edid[editor]['id'], ed2edid[editor]['name'], ym2dt[ym],
                             data[__ADDS__], data[__ADDS_48__], data[
                                 __ADDS_P__], data[__ADDS_SW__],
                             data[__DELS__], data[__DELS_48__], data[
                                 __DELS_P__], data[__DELS_SW__],
                             data[__REINS__], data[__REINS_48__], data[
                                 __REINS_P__], data[__REINS_SW__]
                             ) for ym, editor_data in editors_dict.items()
                               for editor, data in editor_data.items()))


def fill_indexed_editor_tables(language, from_ym, to_ym):
    master_table = "api_editor_{}".format(
        EDITOR_MODEL[language][1].__name__.lower())
    not_indexed_table = "api_editor_{}".format(
        EDITOR_MODEL[language][0].__name__.lower())

    with connection.cursor() as cursor:

        # let's create an index on the non index table so the selects of the inserts
        # are faster
        index_notindexed = """
            CREATE INDEX IF NOT EXISTS {}_year_month 
            ON {} USING btree (year_month);
        """.format(not_indexed_table, not_indexed_table)

        cursor.execute(index_notindexed)

        for year in range(from_ym.year, to_ym.year + 1):

            part_table = '{}_y{}'.format(master_table, year)

            #  drop indexes in the last partition
            cursor.execute(
                "DROP INDEX IF EXISTS {}_page_id;".format(part_table))
            cursor.execute(
                "DROP INDEX IF EXISTS {}_year_month;".format(part_table))
            cursor.execute(
                "DROP INDEX IF EXISTS {}_editor_id_ym;".format(part_table))

            # create the table if not exists
            new_table_query = """
                CREATE TABLE IF NOT EXISTS {} 
                (CHECK ( year_month >= '{}-01-01'::DATE AND year_month <= '{}-12-31'::DATE )) 
                INHERITS ({});
                """.format(part_table, year, year, master_table)
            cursor.execute(new_table_query)

            # move the data to the partition tables
            insert_query = """
                INSERT INTO {} 
                (page_id, editor_id, year_month, editor_name, 
                    adds, adds_surv_48h, adds_persistent, adds_stopword_count, 
                    dels, dels_surv_48h, dels_persistent, dels_stopword_count, 
                    reins, reins_surv_48h, reins_persistent, reins_stopword_count) 
                (
                  SELECT 
                    page_id, editor_id, year_month, editor_name,
                    adds, adds_surv_48h, adds_persistent, adds_stopword_count, 
                    dels, dels_surv_48h, dels_persistent, dels_stopword_count, 
                    reins, reins_surv_48h, reins_persistent, reins_stopword_count
                  FROM {}
                  WHERE (year_month >= '{}-01-01'::DATE AND year_month <= '{}-12-31'::DATE )
                );
            """.format(part_table, not_indexed_table, year, year)
            cursor.execute(insert_query)

            part_table = '{}_y{}'.format(master_table, year)

            # re-create indexes
            cursor.execute("CREATE INDEX {}_page_id ON {} USING btree (page_id);".format(
                part_table, part_table))
            cursor.execute("CREATE INDEX {}_year_month ON {} USING btree (year_month);".format(
                part_table, part_table))
            cursor.execute("CREATE INDEX {}_editor_id_ym ON {} USING btree (editor_id, year_month);".
                           format(part_table, part_table))


def empty_notindexed_editor_tables(language):

    # delete all rows
    EDITOR_MODEL[language][0].objects.all().delete()

    # get the name of the table
    not_indexed_table = "api_editor_{}".format(
        EDITOR_MODEL[language][0].__name__.lower())

    with connection.cursor() as cursor:

        # remove index so inserts are fast, this index is created in the
        # fill_indexed_editor_tables so the selection to move to the index
        # table is fast
        cursor.execute(f"DROP INDEX IF EXISTS {not_indexed_table}_year_month")

        # vacuum table to free space up
        cursor.execute(f"VACUUM (VERBOSE,FULL,ANALYZE) {not_indexed_table};")
