# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py generate_articles_from_wp_xmls -p '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/local/xmls/'
"""
from os import mkdir, listdir
from os.path import basename, exists
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor  # , as_completed, TimeoutError, CancelledError
import logging
from time import strftime
from mwxml import Dump
from mwtypes.files import reader
import csv

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from api.handler import WPHandler


def generate_articles_postgres(xml_file_path, log_folder, format_, check_exists_in_db=False, timeout=None):
    logger = logging.getLogger('generate_article')
    xml_file_name = basename(xml_file_path)
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                xml_file_name,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]
    logger.addHandler(file_handler)

    parsing_pattern = '#######*******#######'

    print('Start: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
    try:
        dump = Dump.from_file(reader(xml_file_path))
        # dump = iteration.Iterator.from_file(open('uncompressed file path'))
        # import itertools
        # dump = itertools.islice(dump, 2)
    except Exception as e:
        logger.exception('{}--------{}'.format(xml_file_name, parsing_pattern))
    else:
        for page in dump:
            try:
                if not page.redirect:
                    with WPHandler(page.title, save_into_db=True, check_exists_in_db=check_exists_in_db, is_xml=True) as wp:
                        # print(wp.article_title)
                        wp.handle_from_xml(page, timeout)
            except Exception as e:
                logger.exception('{}-({})--------{}'.format(page.title, page.id, parsing_pattern))
    print('Done: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
    return True


def generate_articles_csv(xml_file_path, csv_folder, log_folder, format_, check_exists_in_db=False):
    logger = logging.getLogger('generate_article')
    xml_file_name = basename(xml_file_path)
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                xml_file_name,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]
    logger.addHandler(file_handler)

    parsing_pattern = '#######*******#######'

    print('Start: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
    try:
        dump = Dump.from_file(reader(xml_file_path))
    except Exception as e:
        logger.exception('{}--------{}'.format(xml_file_name, parsing_pattern))
    else:
        csv_file_name = xml_file_name
        csv_file_path = '{}/{}'.format(csv_folder, csv_file_name)
        articles_csv = csv_file_path + '_articles.csv'
        with open(articles_csv, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['ID', 'TITLE', 'RVCONTINUE', 'SPAM'])
        revs_csv = csv_file_path + '_revs.csv'
        with open(revs_csv, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['ID', 'ARTICLE_ID', 'EDITOR', 'TIMESTAMP', 'LENGTH', 'CREATED'])
        rps_csv = csv_file_path + '_rps.csv'
        with open(rps_csv, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['REVISION_ID', 'PARAGRAPH_ID', 'POSITION'])
        paras_csv = csv_file_path + '_paras.csv'
        with open(paras_csv, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['ID', 'HASH_VALUE'])
        pss_csv = csv_file_path + '_pss.csv'
        with open(pss_csv, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['PARAGRAPH_ID', 'SENTENCE_ID', 'POSITION'])
        sents_csv = csv_file_path + '_sents.csv'
        with open(sents_csv, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['ID', 'HASH_VALUE'])
        sts_csv = csv_file_path + '_sts.csv'
        with open(sts_csv, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['SENTENCE_ID', 'TOKEN_ID', 'POSITION'])
        tokens_csv = csv_file_path + '_tokens.csv'
        with open(tokens_csv, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['ID', 'VALUE', 'LAST_USED', 'INBOUND', 'OUTBOUND', 'LABEL_REVISION_ID', 'TOKEN_ID'])
        # import itertools
        # dump = itertools.islice(dump, 2)
        for page in dump:
            if not page.redirect:
                try:
                    with WPHandler(page.title, save_into_db=False, check_exists_in_db=check_exists_in_db, is_xml=True) as wp:
                        wp.handle_from_xml(page)
                        ww = wp.wikiwho
                    with open(articles_csv, 'a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csv_writer.writerow([ww.page_id,
                                             ww.article_title,
                                             str(ww.rvcontinue),
                                             str({s for s in ww.spam}) if ww.spam else '{}'])
                    revs = []
                    rps = []
                    paras = {}
                    pss = []
                    sents = {}
                    sts = []
                    tokens = {}
                    temp = []
                    for rev_id, rev in ww.revisions.items():
                        editor = rev.contributor_id
                        editor = str(editor) if editor != 0 else '0|{}'.format(rev.contributor_name)
                        revs.append([
                            rev.wikipedia_id,
                            ww.page_id,
                            editor,
                            rev.time,  # parse_datetime(self.revision_curr.time)
                            rev.length,
                            timezone.now()
                        ])
                        # ps_copy = deepcopy(rev.paragraphs)
                        paragraph_position = 0
                        for hash_paragraph in rev.ordered_paragraphs:
                            if len(rev.paragraphs[hash_paragraph]) > 1:
                                s = 'p-{}-{}'.format(rev, hash_paragraph)
                                temp.append(s)
                                count = temp.count(s)
                                paragraph = rev.paragraphs[hash_paragraph][count - 1]
                            else:
                                paragraph = rev.paragraphs[hash_paragraph][0]
                            # paragraph = rev.paragraphs[hash_paragraph].pop(0)
                            rps.append([
                                rev.wikipedia_id,
                                paragraph.id,
                                paragraph_position
                            ])
                            if paragraph.id not in paras:
                                paras[paragraph.id] = [
                                    paragraph.id,
                                    paragraph.hash_value
                                ]
                            sentence_position = 0
                            for hash_sentence in paragraph.ordered_sentences:
                                if len(paragraph.sentences[hash_sentence]) > 1:
                                    s = 's-{}-{}'.format(paragraph, hash_sentence)
                                    temp.append(s)
                                    count = temp.count(s)
                                    sentence = paragraph.sentences[hash_sentence][count - 1]
                                else:
                                    sentence = paragraph.sentences[hash_sentence][0]
                                # sentence = paragraph.sentences[hash_sentence].pop(0)
                                pss.append([
                                    paragraph.id,
                                    sentence.id,
                                    sentence_position
                                ])
                                if sentence.id not in sents:
                                    sents[sentence.id] = [
                                        sentence.id,
                                        sentence.hash_value
                                    ]
                                token_position = 0
                                for word in sentence.words:
                                    # TODO
                                    # if len(paragraph.sentences[hash_sentence]) > 1:
                                    #     s = 's-{}-{}'.format(paragraph, hash_sentence)
                                    #     temp.append(s)
                                    #     count = temp.count(s)
                                    #     word = sentence.words[hash_sentence][count - 1]
                                    # else:
                                    #     word = sentence.words[hash_sentence][0]
                                    sts.append([
                                        sentence.id,
                                        word.id,
                                        token_position
                                    ])
                                    if word.id not in tokens:
                                        tokens[word.id] = [
                                            word.id,
                                            word.value,
                                            word.last_used,
                                            str({ib for ib in word.inbound}) if word.inbound else '{}',
                                            str({ob for ob in word.outbound}) if word.outbound else '{}',
                                            word.revision,
                                            word.token_id
                                        ]
                                    token_position += 1
                                sentence_position += 1
                            paragraph_position += 1
                        temp = []

                    with open(revs_csv, 'a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csv_writer.writerows(revs)
                    with open(rps_csv, 'a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csv_writer.writerows(rps)
                    with open(paras_csv, 'a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csv_writer.writerows(paras.values())
                    with open(pss_csv, 'a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csv_writer.writerows(pss)
                    with open(sents_csv, 'a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csv_writer.writerows(sents.values())
                    with open(sts_csv, 'a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csv_writer.writerows(sts)
                    with open(tokens_csv, 'a', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        csv_writer.writerows(tokens.values())
                    del wp
                    del ww
                except Exception as e:
                    logger.exception('{}--------{}'.format(page.title, parsing_pattern))
                # finally:

        try:
            # TODO comment here. This is only example to show how to use CopyMapping
            from postgres_copy import CopyMapping
            from wikiwho.models import Article, Revision, RevisionParagraph, Paragraph, ParagraphSentence, \
                Sentence, SentenceToken, Token
            c = CopyMapping(Article,
                            articles_csv,
                            dict(id='ID', title='TITLE', rvcontinue='RVCONTINUE', spam='SPAM'), delimiter=';',
                            encoding='utf-8')
            c.save()
            c = CopyMapping(Revision,
                            revs_csv,
                            dict(id='ID', article_id='ARTICLE_ID', editor='EDITOR', timestamp='TIMESTAMP',
                                 length='LENGTH', created='CREATED'), delimiter=';', encoding='utf-8')
            c.save()
            c = CopyMapping(RevisionParagraph,
                            rps_csv,
                            dict(revision_id='REVISION_ID', paragraph_id='PARAGRAPH_ID', position='POSITION'),
                            delimiter=';', encoding='utf-8')
            c.save()
            c = CopyMapping(Paragraph,
                            paras_csv,
                            dict(id='ID', hash_value='HASH_VALUE'), delimiter=';', encoding='utf-8')
            c.save()
            c = CopyMapping(ParagraphSentence,
                            pss_csv,
                            dict(sentence_id='SENTENCE_ID', paragraph_id='PARAGRAPH_ID', position='POSITION'),
                            delimiter=';', encoding='utf-8')
            c.save()
            c = CopyMapping(Sentence,
                            sents_csv,
                            dict(id='ID', hash_value='HASH_VALUE'), delimiter=';', encoding='utf-8')
            c.save()
            c = CopyMapping(SentenceToken,
                            sts_csv,
                            dict(sentence_id='SENTENCE_ID', token_id='TOKEN_ID', position='POSITION'),
                            delimiter=';', encoding='utf-8')
            c.save()
            c = CopyMapping(Token,
                            tokens_csv,
                            dict(id='ID', value='VALUE', last_used='LAST_USED', inbound='INBOUND',
                                 outbound='OUTBOUND', label_revision_id='LABEL_REVISION_ID',
                                 token_id='TOKEN_ID'), delimiter=';', encoding='utf-8')
            c.save()
        except Exception as e:
            logger.exception('{}--------{}'.format(xml_file_name, parsing_pattern))

    print('Done: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
    return True


class Command(BaseCommand):
    help = 'Generates articles in xml file in given path from data in xml. Skips redirect articles. ' \
           'This command processes files concurrently.'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path', help='Path of xml folder where compressed dumps take place.',
                            required=True)
        parser.add_argument('-l', '--log_folder', help='Folder where to write logs. Default is folder of xml folder',
                            required=False)
        parser.add_argument('-f', '--csv_folder', help='Folder where to write csvs. Default is folder of xml folder',
                            required=False)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. '
                                                                  'Default is # compressed files in given folder path.',
                            required=False)
        parser.add_argument('-t', '--timeout', type=float, required=False,
                            help='Timeout value for each processor for analyzing articles [minutes]')
        parser.add_argument('-tpe', '--thread_pool_executor', action='store_true',
                            help='Use ThreadPoolExecutor, default is ProcessPoolExecutor', default=False,
                            required=False)
        parser.add_argument('-uc', '--use_copy', action='store_true',
                            help='Use copy command to save into db. Default is False.', default=False,
                            required=False)
        parser.add_argument('-c', '--check_exists', action='store_true',
                            help='Check if an article exists in db before creating it.'
                                 ' If yes, go to the next article. If not, process article. '
                                 'Be careful that if yes, this costs 1 extra db query for each article!',
                            default=False, required=False)

    def handle(self, *args, **options):
        xml_folder = options['path']
        xml_folder = xml_folder[:-1] if xml_folder.endswith('/') else xml_folder
        xml_files = sorted(['{}/{}'.format(xml_folder, x)
                            for x in listdir(xml_folder)
                            if x.endswith('.7z')])
                            # if '.xml-' in x and not x.endswith('.7z')])
        if not xml_files:
            raise CommandError('In given folder ({}), there are no 7z files.'.format(xml_folder))
        log_folder = options['log_folder']
        log_folder = log_folder[:-1] if log_folder and log_folder.endswith('/') else log_folder
        log_folder = '{}/{}'.format(log_folder or xml_folder, 'logs')
        if not exists(log_folder):
            mkdir(log_folder)

        use_copy = options['use_copy']
        if use_copy:
            csv_folder = options['csv_folder']
            csv_folder = csv_folder[:-1] if csv_folder and csv_folder.endswith('/') else csv_folder
            csv_folder = '{}/{}'.format(csv_folder or xml_folder, 'csvs')
            if not exists(csv_folder):
                mkdir(csv_folder)
        max_workers = options['max_workers'] or len(xml_files)
        is_ppe = not options['thread_pool_executor']
        check_exists_in_db = options['check_exists']
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

        print(max_workers)
        # print(xml_files)
        # print('Start: {} with --use_copy={} at {}'.format(xml_folder, use_copy, strftime("%H:%M:%S %d-%m-%Y")))
        with Executor(max_workers=max_workers) as executor:
            for xml_file_path in xml_files:
                if not use_copy:
                    executor.submit(generate_articles_postgres, xml_file_path, log_folder, format_,
                                    check_exists_in_db, timeout)
                else:
                    raise NotImplementedError
                    # FIXME known error: PS and ST token creation. maybe there are more errors.
                    # executor.submit(generate_articles_csv, xml_file_path, csv_folder, log_folder, format_, check_exists_in_db)
        print('Done: {} at {}'.format(xml_folder, strftime("%H:%M:%S %d-%m-%Y")))
