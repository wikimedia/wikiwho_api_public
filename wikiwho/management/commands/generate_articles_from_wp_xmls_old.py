# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py generate_articles_from_wp_xmls -p '../enwiki-20161101-pages-meta-history1.xml-p000000010p000002289' -m 90 -t 300
"""
from os import mkdir
from os.path import basename, dirname, exists
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed  # , TimeoutError, CancelledError
import logging
from time import strftime
from mw.xml_dump import Iterator

from django.core.management.base import BaseCommand, CommandError

from api.handler import WPHandler


def generate_article(xml_file_path, page_id, check_exists_in_db=False):
    dump = Iterator.from_file(open(xml_file_path))
    for page in dump:
        if page_id == page.id:
            article_title = page.title
            break
    del dump
    with WPHandler(article_title, check_exists_in_db=check_exists_in_db, is_xml=True) as wp:
        wp.handle_from_xml(page)
        # del revisions
    return True


def convert_page_into_pickable(page):
    pickable = {
        'title': page.title,
        'id': page.id,
        'revisions': []
    }
    for revision in page:
        text = str(revision.text)
        if not text and (revision.sha1 == '' or revision.sha1 == 'None'):
            # texthidden / textmissing
            data = {'texthidden': '', 'textmissing': ''}
        else:
            data = {
                '*': text,
                'revid': revision.id,
                'comment': str(revision.comment),
                'timestamp': revision.timestamp.long_format(),
                'user': revision.contributor.user_text or '',
            }
            if revision.minor:
                data['minor'] = ''
            if revision.contributor.id is None and data['user']:
                data['userid'] = 0
            else:
                data['userid'] = revision.contributor.id or ''
        pickable['revisions'].append(data)
    return pickable


class Command(BaseCommand):
    help = 'Generates articles in xml file in given path from data in xml. Skips redirect articles. ' \
           'This command processes articles in file concurrently'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path', help='Path of xml file', required=True)
        parser.add_argument('-l', '--log_folder', help='Folder where to write logs. Default is folder of xml file',
                            required=False)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of threads/processors to run parallel.',
                            required=True)
        parser.add_argument('-t', '--timeout', type=float, required=False,
                            help='This feature does not work for now. Timeout value for each worker [minutes]')
        parser.add_argument('-tpe', '--thread_pool_executor', action='store_true',
                            help='Use ThreadPoolExecutor, default is ProcessPoolExecutor', default=False,
                            required=False)
        parser.add_argument('-s', '--start', type=int, help='From range', required=False)
        parser.add_argument('-e', '--end', type=int, help='To range', required=False)
        parser.add_argument('-c', '--check_exists', action='store_true',
                            help='Check if an article exists in db before creating it. If yes, go to the next article. '
                                 'If not, process article. '
                                 'Be careful that if yes, this costs 1 extra db query for each article!',
                            default=False, required=False)

    def handle(self, *args, **options):
        # TODO read from uncompressed file (7z), not from compressed file.
        xml_file_path = options['path']
        xml_file_name = basename(xml_file_path)
        log_folder = '{}/{}'.format(options['log_folder'] or dirname(xml_file_path), 'logs')
        if not exists(log_folder):
            mkdir(log_folder)
        max_workers = options['max_workers']
        is_ppe = not options['thread_pool_executor']
        start = options['start']
        end = options['end']
        check_exists_in_db = options['check_exists']
        timeout = options['timeout'] * 60 if options['timeout'] else None  # convert into seconds
        # if start > end:
        #     raise CommandError('start ({}) must be >= end ({})'.format(start, end))

        parsing_pattern = '#######*******#######'
        if is_ppe:
            Executor = ProcessPoolExecutor
            format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
        else:
            Executor = ThreadPoolExecutor
            format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'

        # logger_timeout = logging.getLogger('timeout')
        # file_handler = logging.FileHandler('{}/logs/timeouts_{}_at_{}.log'.format(path,
        #                                                                           '_'.join([str(start), str(end)]),
        #                                                                           strftime("%Y-%m-%d-%H:%M:%S")))
        # file_handler.setLevel(logging.ERROR)
        # formatter = logging.Formatter('%(message)s')
        # file_handler.setFormatter(formatter)
        # logger_timeout.addHandler(file_handler)
        logger = logging.getLogger('')
        # logger = logging.getLogger('error')
        file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                    xml_file_name,
                                                                    strftime("%Y-%m-%d-%H:%M:%S")))
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(format_)
        file_handler.setFormatter(formatter)
        logger.handlers = [file_handler]
        # logger.addHandler(file_handler)

        dump = Iterator.from_file(open(xml_file_path))
        # import itertools
        # dump = itertools.islice(dump, 3)
        # for page in dump:
        #     try:
        #         generate_article(xml_file_path, page.id, check_exists_in_db)
        #     except Exception as exc:
        #         logger.exception('{}--------{}'.format(page.title, parsing_pattern))

        timeout = None
        print('Start: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
        # We can use a with statement to ensure threads are cleaned up promptly
        with Executor(max_workers=max_workers) as executor:
            # Start the load operations and mark each future with its article
            future_to_article = {executor.submit(generate_article, xml_file_path, page.id, check_exists_in_db):
                                 page.title
                                 for page in dump if not page.redirect}
            # for page in dump:
            #     if not page.redirect:
            #         result = executor.submit(generate_article, convert_page_into_pickable(page), check_exists_in_db)
            #         break
            # print(result.result())

            for future in as_completed(future_to_article):
                article_name = future_to_article[future]
            # for future, article_name in future_to_article.items():
                try:
                    data = future.result(timeout=timeout)
                # except (TimeoutError, CancelledError) as e:
                #     logger_timeout.error(article_name)
                except Exception as exc:
                    logger.exception('{}--------{}'.format(article_name, parsing_pattern))
                    # else:
                    #     print('Success: {}'.format(article_name))
        print('Done: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))

        # from pathos.multiprocessing import ProcessingPool as Pool
        # p = Pool(4)
        # results = p.map(page for page in dump if not page.redirect)
        # print(results)