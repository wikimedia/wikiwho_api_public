# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py generate_articles_from_wp_xmls -p '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/' -t 30 -m 24
python manage.py generate_articles_from_wp_xmls -p '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/' -j '' -m 24 --check_exists
"""
from os import mkdir, listdir
from os.path import basename, exists
import logging
from time import strftime, sleep

from concurrent.futures import ProcessPoolExecutor, as_completed  # , ThreadPoolExecutor, TimeoutError, CancelledError
from mwxml import Dump
from mwtypes.files import reader

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError, DatabaseError
from django.conf import settings

from api.handler import WPHandler
from base.utils import is_db_running


def generate_articles_postgres(xml_file_path, page_ids, log_folder, format_, check_exists_in_db=False, timeout=None):
    xml_file_name = basename(xml_file_path)
    logger = logging.getLogger(xml_file_name[:-3].split('-')[-1])
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                xml_file_name,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    parsing_pattern = settings.LOG_PARSING_PATTERN

    print('Start: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
    try:
        dump = Dump.from_file(reader(xml_file_path))
        # dump = iteration.Iterator.from_file(open('decompressed file path'))
        # import itertools
        # dump = itertools.islice(dump, 2)
    except Exception as e:
        logger.exception('{}--------{}'.format(xml_file_name, parsing_pattern))
    else:
        for page in dump:
            try:
                if page.namespace == 0 and not page.redirect and (not page_ids or int(page.id) in page_ids):
                    with WPHandler(page.title, page_id=page.id, save_into_db=True, check_exists_in_db=check_exists_in_db, is_xml=True) as wp:
                        # print(wp.article_title)
                        wp.handle_from_xml(page, timeout)
            except (OperationalError, DatabaseError):
                while not is_db_running():
                    sleep(60*5)
                logger.exception('{}-({})--------{}-DBError'.format(page.title, page.id, parsing_pattern))
            except Exception as e:
                logger.exception('{}-({})--------{}'.format(page.title, page.id, parsing_pattern))
    print('Done: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
    return True


class Command(BaseCommand):
    help = 'Generates articles in xml file in given path from data in xml. Skips redirect articles and ' \
           'pages which does not have namespace as 0. This command processes files concurrently.'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path', help='Path of xml folder where compressed dumps take place.',
                            required=True)
        parser.add_argument('-j', '--json', help='Path of json folder.', required=False)
        parser.add_argument('-l', '--log_folder', help='Folder where to write logs. Default is folder of xml folder',
                            required=False)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. '
                                                                  'Default is # compressed files in given folder path.',
                            required=False)
        parser.add_argument('-t', '--timeout', type=float, required=False,
                            help='Timeout value for each processor for analyzing articles [minutes]')
        parser.add_argument('-tpe', '--thread_pool_executor', action='store_true',
                            help='Use ThreadPoolExecutor, default is ProcessPoolExecutor', default=False,
                            required=False)
        parser.add_argument('-c', '--check_exists', action='store_true',
                            help='Check if an article exists in db before creating it.'
                                 ' If yes, go to the next article. If not, process article. '
                                 'Be careful that if yes, this costs 1 extra db query for each article!',
                            default=False, required=False)

    def handle(self, *args, **options):
        xml_folder = options['path']
        xml_folder = xml_folder[:-1] if xml_folder.endswith('/') else xml_folder

        check_exists_in_db = options['check_exists']
        json_folder = options['json']
        xml_files = []
        if json_folder and check_exists_in_db:
            import json
            json_folder = json_folder[:-1] if json_folder.endswith('/') else json_folder
            json_files = ['{}/{}'.format(json_folder, j) for j in listdir(json_folder) if j.endswith('.json')]
            for json_file in json_files:
                with open(json_file, 'r') as f:
                    json_data = json.loads(f.read())
                    for xml_file in json_data:
                        title_ids = json_data[xml_file]['timeouts']
                        if check_exists_in_db:
                            title_ids += json_data[xml_file]['operationals']
                        # print(title_ids)
                        page_ids = [int(ti[1]) for ti in title_ids]
                        if page_ids:
                            xml_files.append(['{}/{}'.format(xml_folder, xml_file), page_ids])
        elif not json_folder:
            xml_files = [['{}/{}'.format(xml_folder, x), []] for x in listdir(xml_folder) if x.endswith('.7z')]

        if not xml_files:
            raise CommandError('In given folder ({}), there are no 7z files.'.format(xml_folder))
        log_folder = options['log_folder']
        log_folder = log_folder[:-1] if log_folder and log_folder.endswith('/') else log_folder
        log_folder = '{}/{}'.format(log_folder or xml_folder, 'logs')
        if not exists(log_folder):
            mkdir(log_folder)

        max_workers = options['max_workers'] or len(xml_files)
        is_ppe = not options['thread_pool_executor']
        timeout = int(options['timeout'] * 60) if options['timeout'] else None  # convert into seconds

        if is_ppe:
            Executor = ProcessPoolExecutor
            format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
        else:
            raise NotImplemented  # Not used/tested
            # Executor = ThreadPoolExecutor
            # format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'

        # for xml_file_path in xml_files:
        #     generate_articles_postgres(xml_file_path, log_folder, format_, check_exists_in_db, timeout)

        logger = logging.getLogger('future_log')
        file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                    xml_folder.split('/')[-1],
                                                                    strftime("%Y-%m-%d-%H:%M:%S")))
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(format_)
        file_handler.setFormatter(formatter)
        logger.handlers = [file_handler]
        # logger.addHandler(file_handler)

        print(max_workers)
        # print(xml_files)
        with Executor(max_workers=max_workers) as executor:
            jobs = {}
            files_left = len(xml_files)
            files_iter = iter(xml_files)

            while files_left:
                for xml_file_path, page_ids in files_iter:
                    job = executor.submit(generate_articles_postgres, xml_file_path, page_ids, log_folder,
                                          format_, check_exists_in_db, timeout)
                    jobs[job] = basename(xml_file_path)
                    if len(jobs) == max_workers:  # limit # jobs with max_workers
                        break

                for job in as_completed(jobs):
                    files_left -= 1
                    xml_file_name = jobs[job]
                    try:
                        data = job.result()
                    except Exception as exc:
                        logger.exception(xml_file_name)

                    del jobs[job]
                    break  # to add a new job, if there is any
        print('Done: {} at {}'.format(xml_folder, strftime("%H:%M:%S %d-%m-%Y")))
