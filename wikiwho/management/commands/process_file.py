# -*- coding: utf-8 -*-
"""
Process one wikipedia file (update pickle, and index chobs)

Example usage:
python manage.py process_file -lang 'en' -t 6187
"""


from os.path import join
from django.core.management.base import BaseCommand
from api.utils_pickles import get_pickle_folder
from api_editor.utils_db import fill_notindexed_editor_tables
from api.tasks import process_article


class Command(BaseCommand):
    help = 'Generates editor data and fills the editor database per ym, editor, article.'

    def add_arguments(self, parser):
        parser.add_argument('-lang', '--language',
                            help="Wikipedia language. Ex: 'en'", required=True)
        parser.add_argument('-t', '--title', 
                            help='Wikipedia Page title that will be analized.',
                            default='Bioglass')
        parser.add_argument('--celeryed', help='Process with celery', action='store_true')


    def handle(self, *args, **options):
        language = options['language']
        title = options['title']

        if options['celeryed']:
            process_article.delay(language, title)
        else:
            process_article(language, title)
