# -*- coding: utf-8 -*-
"""
Example usage:

"""
import glob
import pytz
import sys
import json
from os.path import join, basename, exists
from os import mkdir
from time import strftime, sleep
from datetime import datetime, timedelta
from simplejson import JSONDecodeError
from django.utils.dateparse import parse_datetime

from concurrent.futures import ProcessPoolExecutor, as_completed

from django.core.management.base import BaseCommand

from api.utils_pickles import get_pickle_folder, pickle_load
from api.handler import WPHandlerException
from base.utils_log import get_logger
from wikiwho.utils_db import fill_editor_tables
from difflib import SequenceMatcher


def words(s):
    return [w.value for w in s.words]


def generate_sentence_data(pickle_path, language):
    retries = 6
    while retries:
        retries -= 1
        try:
            wikiwho = pickle_load(pickle_path)
        except (UnboundLocalError, JSONDecodeError):
            sleep(30)
            if not retries:
                raise
    # refs = {}
    id_ = 0  # sentence id
    prev_rev_id = None
    all_sentences = {}  # {sentence_id: sentence_obj}
    rev_prev_sentence_ids = None  # used to find out deleted sentences
    for rev_id in wikiwho.ordered_revisions:
        rev = wikiwho.revisions[rev_id]
        rev.timestamp = parse_datetime(rev.timestamp)
        rev_sentences = []
        rev_sentence_ids = []
        rev_adds = []
        tmp = {'p': [], 's': []}  # this is used to get sentences in correct order
        for p_hash in rev.ordered_paragraphs:
            if len(rev.paragraphs[p_hash]) > 1:
                tmp['p'].append(p_hash)
                paragraph = rev.paragraphs[p_hash][tmp['p'].count(p_hash)-1]
            else:
                paragraph = rev.paragraphs[p_hash][0]
            tmp['s'][:] = []
            for s_hash in paragraph.ordered_sentences:
                if len(paragraph.sentences[s_hash]) > 1:
                    tmp['s'].append(s_hash)
                    sentence = paragraph.sentences[s_hash][tmp['s'].count(s_hash)-1]
                else:
                    sentence = paragraph.sentences[s_hash][0]
                # TODO (later) filter sentecse, e.g. <ref ... /fev>
                if not hasattr(sentence, 'ins'):
                    # this is a new added sentence
                    sentence.id_ = id_
                    # sentence.ins = [[rev_id, parse_datetime(rev.timestamp)]]
                    sentence.ins = [rev_id]
                    sentence.outs = []
                    # sentence.deleted_matched = False
                    # sentence.added_matched = False
                    # adds.append([sentence.hash_value, sentence])
                    rev_adds.append(sentence.id_)
                    assert id_ not in all_sentences
                    all_sentences.update({id_: sentence})
                    id_ += 1
                    # TODO what if ref is 1 tag: <ref alfklk> ?? ref name
                    # text = ''.join(words(sentence))
                    # is_ref = False
                    # if text.startswith('<ref') and text.endswith('>'):
                    #     is_ref = True
                    #     is_ref_prev = False
                    # if text.startswith('<ref') or text.endswith('ref>'):
                    #     is_ref = True
                    #     is_ref_prev = True
                    # if text.endswith('ref>'):
                    #     is_ref_prev = False
                    # if is_ref or is_ref_prev:
                    #     print(sentence.id_, text, sentence.ins, sentence.outs)
                    #     if s_hash in refs:
                    #         refs[s_hash].append(sentence)
                    #     else:
                    #         refs[s_hash] = [sentence]
                else:
                    if sentence.last_rev_id != prev_rev_id:
                        # sentence is re-added
                        sentence.ins.append(rev_id)
                        rev_adds.append(sentence.id_)
                sentence.last_rev_id = rev_id
                rev_sentences.append(sentence)
                rev_sentence_ids.append(sentence.id_)
        rev.sentences = rev_sentences
        rev.sentence_ids = rev_sentence_ids
        rev.adds = rev_adds
        if rev_prev_sentence_ids is not None:
            rev.deletes = list(set(rev_prev_sentence_ids) - set(rev_sentence_ids))
        else:
            rev.deletes = []
        for s_id in rev.deletes:
            all_sentences[s_id].outs.append(rev_id)
        rev_prev_sentence_ids = rev_sentence_ids[:]
        prev_rev_id = rev_id
    wikiwho.all_sentences = all_sentences
    # wikiwho.refs = refs
    return wikiwho


def calculate_similarity(list1, list2):
    return SequenceMatcher(None, list1, list2).ratio()


def get_sentence_data_(pickle_path, language):
    ww = generate_sentence_data(pickle_path, language)
    output = {}
    seconds_limit = 48 * 3600  # hours
    for s_id in range(len(ww.all_sentences)):
        sentence = ww.all_sentences[s_id]
        for i, out_rev_id in enumerate(sentence.outs):
            out_ts = ww.revisions[out_rev_id].timestamp
            in_ts = ww.revisions[sentence.ins[i]].timestamp
            successful_add = (out_ts - in_ts).total_seconds() >= seconds_limit
            # check adds of rev where this sentence is deleted
            for added_s_id in ww.revisions[out_rev_id].adds:
                added_sentence = ww.all_sentences[added_s_id]
                # TODO how to decide if this sentence already matched in the same revision edit?!
                if calculate_similarity(sentence.words, added_sentence.words) >= 0.8:
                    x = added_sentence.ins.index(out_rev_id)
                    try:
                        added_out_rev_id = added_sentence.outs[x+1]
                    except IndexError:
                        pass
                    else:
                        in_ts = out_ts
                        out_ts = ww.revisions[added_out_rev_id].timestamp
                        added_successful_add = (out_ts - in_ts).total_seconds() >= seconds_limit
                        print('###########################')
                        if successful_add and not added_successful_add:
                            print('### successful deleted by unsuccessful')
                            if s_id not in output:
                                output[s_id] = {}
                            assert out_rev_id not in output[s_id]
                            output[s_id][out_rev_id] = ['s', added_s_id, added_out_rev_id]
                            print(out_rev_id, added_out_rev_id, sentence.id_, added_sentence.id_, successful_add, added_successful_add)
                            print(words(sentence))
                            print(words(added_sentence))
                        elif not successful_add and added_successful_add:
                            print('### unsuccessful deleted by successful')
                            if s_id not in output:
                                output[s_id] = {}
                            assert out_rev_id not in output[s_id]
                            output[s_id][out_rev_id] = ['u', added_s_id, added_out_rev_id]
                            print(out_rev_id, added_out_rev_id, sentence.id_, added_sentence.id_, successful_add, added_successful_add)
                            print(words(sentence))
                            print(words(added_sentence))
                    break
        # sentence.matched = True  # processed
    ww.output = output
    return ww


def get_sentence_data(pickle_path, language):
    ww = generate_sentence_data(pickle_path, language)
    output = {}
    seconds_limit = 48 * 3600  # hours
    for s_id in range(len(ww.all_sentences)):
        sentence = ww.all_sentences[s_id]
        for i, out_rev_id in enumerate(sentence.outs):
            out_ts = ww.revisions[out_rev_id].timestamp
            in_ts = ww.revisions[sentence.ins[i]].timestamp
            if (out_ts - in_ts).total_seconds() < seconds_limit:
                continue
            # check adds of rev where this sentence is deleted
            for added_s_id in ww.revisions[out_rev_id].adds:
                added_sentence = ww.all_sentences[added_s_id]
                # TODO how to decide if this sentence already matched in the same revision edit?
                if calculate_similarity(sentence.words, added_sentence.words) >= 0.8:
                    x = added_sentence.ins.index(out_rev_id)
                    try:
                        added_out_rev_id = added_sentence.outs[x+1]
                    except IndexError:
                        pass
                    else:
                        in_ts = out_ts
                        out_ts = ww.revisions[added_out_rev_id].timestamp
                        if (out_ts - in_ts).total_seconds() >= seconds_limit:
                            break
                        for added_s_id_2 in ww.revisions[added_out_rev_id].adds:
                            added_sentence_2 = ww.all_sentences[added_s_id_2]
                            if calculate_similarity(added_sentence.words, added_sentence_2.words) >= 0.8:
                                x = added_sentence_2.ins.index(added_out_rev_id)
                                try:
                                    added_out_rev_id_2 = added_sentence_2.outs[x+1]
                                except IndexError:
                                    pass
                                else:
                                    in_ts = out_ts
                                    out_ts = ww.revisions[added_out_rev_id_2].timestamp
                                    if (out_ts - in_ts).total_seconds() >= seconds_limit:
                                        output[s_id] = [out_rev_id, added_s_id, added_out_rev_id, added_s_id_2, added_out_rev_id_2]

                    break
        # sentence.matched = True  # processed
    ww.output = output
    return ww


def x():
    from wikiwho.management.commands.fill_editor_tables import get_sentence_data, words
    # ww = get_sentence_data('/home/kenan/PycharmProjects/wikiwho_api/tmp_pickles/en/46966.p', '')  # Sleep_disorder
    # ww = get_sentence_data('/home/kenan/PycharmProjects/wikiwho_api/tmp_pickles/en/1503977.p', '')  # Honors_at_Dawn
    # ww = get_sentence_data('/home/kenan/PycharmProjects/wikiwho_api/tmp_pickles/en/2161298.p', '')  # Bioglass
    ww = get_sentence_data('/home/kenan/PycharmProjects/wikiwho_api/tmp_pickles/en/10577.p', '')  # Finland
    print(len(ww.all_sentences), len(ww.sentences_ht))
    assert len(ww.all_sentences) == len([y for x in ww.sentences_ht.values() for y in x])
    assert len(list(ww.all_sentences.keys())) == len(set(ww.all_sentences.keys()))
    # s_ids = sorted(list(ww.all_sentences.keys()))
    for r_id in ww.ordered_revisions:
        print(r_id)
        r = ww.revisions[r_id]
        print(r.adds)
        print(r.deletes)
        for s in r.sentences:
            assert hasattr(s, 'ins')
            assert hasattr(s, 'outs')
            assert hasattr(s, 'last_rev_id')
            print(s.id_, words(s), hasattr(s, 'ins'), hasattr(s, 'outs'), hasattr(s, 'last_rev_id'))
            print(s.ins)
            print(s.outs)
        print('#####################################################')


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        # parser.add_argument('-f', '--file', required=False,
        #                     help='Pickles json file {"en": [list of page ids], "de" [], }. '
        #                          'If not given, list is taken from relevant pickle folder for each language.')
        # parser.add_argument('-from', '--from_ym', required=True,
        #                     help='Year-month to create data from [YYYY-MM]. Included.')
        # parser.add_argument('-to', '--to_ym', required=True,
        #                     help='Year-month to create data until [YYYY-MM]. Not included.')
        parser.add_argument('-lang', '--language', help="Wikipedia language. Ex: 'en' or 'en,eu,de'", required=True)
        parser.add_argument('-log', '--log_folder', help='Folder where to write logs.', required=True)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. ',
                            required=True)
        # parser.add_argument('-u', '--update', action='store_true',
        #                     help='Update pickles from WP api before generating editor data. Default is False.',
        #                     default=False, required=False)
        # parser.add_argument('-t', '--timeout', type=float, required=False,
        #                     help='Timeout value for each processor for analyzing articles [minutes]')
        # parser.add_argument('-c', '--check_exists', action='store_true', help='', default=False, required=False)

    def get_parameters(self, options):
        # json_file = options['file'] or None
        # from_ym = options['from_ym']
        # from_ym = datetime.strptime(from_ym, '%Y-%m').replace(tzinfo=pytz.UTC)
        # to_ym = options['to_ym']
        # to_ym = datetime.strptime(to_ym, '%Y-%m').replace(tzinfo=pytz.UTC) - timedelta(seconds=1)
        languages = options['language'].split(',')
        max_workers = options['max_workers']
        # update = options['update']
        return languages, max_workers

    def handle(self, *args, **options):
        languages, max_workers = self.get_parameters(options)

        print('Start at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
        print(max_workers, languages)
        # Concurrent process of pickles of each language to generate editor data
        for language in languages:
            # set logging
            log_folder = options['log_folder']
            if not exists(log_folder):
                mkdir(log_folder)
            logger = get_logger('fill_editor_tables_{}'.format(language),
                                log_folder, is_process=True, is_set=True, language=language)
            pickle_folder = get_pickle_folder(language)
            print('Start: {} - {} at {}'.format(language, pickle_folder, strftime('%H:%M:%S %d-%m-%Y')))

            pickles_list = list(glob.iglob(join(pickle_folder, '*.p')))
            pickles_all = len(pickles_list)
            pickles_left = pickles_all
            pickles_iter = iter(pickles_list)
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                jobs = {}
                while pickles_left:
                    for pickle_path in pickles_iter:
                        page_id = basename(pickle_path)[:-2]
                        job = executor.submit(get_sentence_data, pickle_path, language)
                        jobs[job] = page_id
                        if len(jobs) == max_workers:  # limit # jobs with max_workers
                            break

                    for job in as_completed(jobs):
                        pickles_left -= 1
                        page_id_ = jobs[job]
                        try:
                            data = job.result()
                        except Exception as exc:
                            logger.exception('{}-{}'.format(page_id_, language))

                        del jobs[job]
                        sys.stdout.write('\rPickles left: {} - Pickles processed: {:.3f}%'.
                                         format(pickles_left, ((pickles_all - pickles_left) * 100) / pickles_all))
                        break  # to add a new job, if there is any
            print('\nDone: {} - {} at {}'.format(language, pickle_folder, strftime('%H:%M:%S %d-%m-%Y')))
        print('Done at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
