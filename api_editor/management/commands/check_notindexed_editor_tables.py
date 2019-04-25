# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py fill_notindexed_editor_tables -from 2001-01 -to 2002-01 -m 6 -log '' -lang 'en,de,eu'

Check wikiwho_api/cron/manage_editor_data.sh for more information how we use 3 editor data scripts each month.
"""

import pytz
import sys
from os.path import join
from datetime import datetime, timedelta, date

from django.core.management.base import BaseCommand
from django.conf import settings

from api.utils_pickles import get_pickle_folder
from api_editor.utils_db import fill_notindexed_editor_tables


class Command(BaseCommand):
    help = 'Generates editor data and fills the editor database per ym, editor, article.'

    def add_arguments(self, parser):
        parser.add_argument('-from', '--from_ym', required=True,
                            help='Year-month to create data from [YYYY-MM]. Included.')
        parser.add_argument('-to', '--to_ym', required=True,
                            help='Year-month to create data until [YYYY-MM]. Not included.')
        parser.add_argument('-lang', '--language',
                            help="Wikipedia language. Ex: 'en'", required=True)
        parser.add_argument('-pid', '--page_id', type=int,
                            help='Wikipedia Page ID that will be analized.',
                            default=2161298)

    def handle(self, *args, **options):

        from_ym = options['from_ym']
        from_ym = datetime.strptime(from_ym, '%Y-%m').replace(tzinfo=pytz.UTC)
        to_ym = options['to_ym']
        to_ym = datetime.strptime(
            to_ym, '%Y-%m').replace(tzinfo=pytz.UTC) - timedelta(seconds=1)
        language = options['language']
        pageid = options['page_id']

        pickle_path = join(get_pickle_folder(language), f'{pageid}.p')

        fill_notindexed_editor_tables(pickle_path, from_ym, to_ym, language, False)

