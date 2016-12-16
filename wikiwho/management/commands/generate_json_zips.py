# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py generate_json_zips -o '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/jsons' -m 4
"""
import json
from os import mkdir, rename
from os.path import exists, getsize
import logging
import math
from time import strftime
from zipfile import ZipFile, ZIP_LZMA
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed  # , TimeoutError, CancelledError

from django.core.management.base import BaseCommand
from django.conf import settings

from wikiwho.models import Article
from api.views import WikiwhoView


def generate_jsons(f, t, output_folder, log_folder, format_, max_size):
    from_to = 'from_{}_to_{}'.format(f, t)

    logger = logging.getLogger(from_to)
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                from_to,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]

    print('Start: {} at {}'.format(from_to, strftime("%H:%M:%S %d-%m-%Y")))
    title = ''
    zip_name = '{}/{}.zip'.format(output_folder, from_to)
    for article in Article.objects.order_by('id')[f:t].iterator():
        if not title:
            from_page_id = article.id
        title = '{}_({})'.format(article.title, article.id)
        try:
            v = WikiwhoView(article)
            parameters = v.get_parameters()
            parameters[-1] = 0  # threshold.
            last_revision_json = v.get_revision_json([], parameters, only_last_valid_revision=True, minimal=True)
            # if not last_revision_json.get('no_revisions') and last_revision_json['revisions']:
            if last_revision_json['revisions']:
                last_rev_id = list(last_revision_json['revisions'][0].keys())[0]
                # test = last_revision_json['revisions'][0][last_rev_id]['tokens'][0]  # test for corrupted articles
                last_rev_id = int(last_rev_id)
            else:
                last_rev_id = None
            deleted_tokens_json = v.get_deleted_tokens(parameters, minimal=True, last_rev_id=last_rev_id)
            revision_ids_json = v.get_revision_ids(minimal=True)
            with ZipFile(zip_name, 'a', compression=ZIP_LZMA) as zip_:
                zip_.writestr('{}_content.json'.format(title),
                              json.dumps(last_revision_json, ensure_ascii=False))
                # json.dumps(last_revision_json, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False)
                zip_.writestr('{}_deleted_content.json'.format(title),
                              json.dumps(deleted_tokens_json, ensure_ascii=False))
                zip_.writestr('{}_revision_ids.json'.format(title),
                              json.dumps(revision_ids_json, ensure_ascii=False))
            if getsize(zip_name) >> 20 > max_size:  # size > max_size [MB]
                to_page_id = article.id
                rename(zip_name, '{}/wikiwho-{}-{}-{}.zip'.format(output_folder,
                                                                  strftime("%Y%m%d"), from_page_id, to_page_id))
                title = ''
        except Exception as e:
            logger.exception('{}--------{}'.format(title, settings.LOG_PARSING_PATTERN))
    if title:
        to_page_id = article.id
        rename(zip_name, '{}/wikiwho-{}-{}-{}.zip'.format(output_folder,
                                                          strftime("%Y%m%d"), from_page_id, to_page_id))
    print('Done: {} at {}'.format(from_to, strftime("%H:%M:%S %d-%m-%Y")))
    return True


class Command(BaseCommand):
    help = 'Generates json data set zips by using LZMA compression.'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--output', help='Folder to output jsons.', required=True)
        parser.add_argument('-l', '--limit', type=int, help='Queryset limit. '
                                                            'Default is total number of articles in db.',
                            required=False)
        parser.add_argument('-f', '--offset', type=int, help='Offset to start process. Default is 0.', required=False)
        parser.add_argument('-s', '--max_size', type=int, help='Max size of each zip file. Default is 900 MB. [MB]',
                            required=False)
        parser.add_argument('-ppe', '--process_pool_executor', action='store_true',
                            help='Use ProcessPoolExecutor, default is ThreadPoolExecutor', default=False,
                            required=False)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of threads/processors to run parallel.',
                            required=True)

    def handle(self, *args, **options):
        output_folder = options['output']
        output_folder = output_folder[:-1] if output_folder.endswith('/') else output_folder
        if not exists(output_folder):
            mkdir(output_folder)
        log_folder = '{}/{}'.format(output_folder, 'logs')
        if not exists(log_folder):
            mkdir(log_folder)
        is_ppe = options['process_pool_executor']
        max_workers = options['max_workers']
        max_size = options['max_size'] or 900

        if is_ppe:
            Executor = ProcessPoolExecutor
            format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
        else:
            Executor = ThreadPoolExecutor
            format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'

        logger = logging.getLogger('future_log')
        file_handler = logging.FileHandler('{}/future_log_at_{}.log'.format(log_folder, strftime("%Y-%m-%d-%H:%M:%S")))
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(format_)
        file_handler.setFormatter(formatter)
        logger.handlers = [file_handler]

        articles_count = options['limit'] or Article.objects.count()
        batch_size = math.ceil(articles_count / max_workers)
        offset = options['offset'] or 0
        f = offset - batch_size
        t = offset
        batches = []
        while True:
            f += batch_size
            t += batch_size
            batches.append((f, t))
            if t >= articles_count:
                break

        print(max_workers, len(batches))
        print('Start: json data set at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
        with Executor(max_workers=max_workers) as executor:
            future_to_article = {executor.submit(generate_jsons, batch[0], batch[1],
                                                 output_folder, log_folder, format_, max_size): batch
                                 for batch in batches}

            for future in as_completed(future_to_article):
                f, t = future_to_article[future]
                try:
                    data = future.result()
                except Exception as exc:
                    logger.exception('{}-{}--------{}'.format(f, t, settings.LOG_PARSING_PATTERN))
        print('Done: json data set at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
