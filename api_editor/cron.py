
from datetime import date, timedelta, datetime
import pytz

from base.utils_log import get_base_logger
from .management.commands.fill_notindexed_editor_tables import fill_notindexed_editor_tables_batch
from .management.commands.fill_indexed_editor_tables import fill_indexed_editor_tables_batch
from .management.commands.empty_notindexed_editor_tables import empty_notindexed_editor_tables_batch
from django.conf import settings
from os import mkdir
from os.path import join
import traceback


def update_actions_tables():

    # this try is important to avoid unknown erros from going to the limbo
    try:

        to_ym = datetime.today().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.UTC)
        from_ym = (to_ym - timedelta(days=1)).replace(day=1)

        logger = get_base_logger('update_actions_tables', settings.ACTIONS_LOG)

        logger.info("Filling NOT INDEXED editor tables")
        fill_notindexed_editor_tables_batch(
            from_ym=from_ym,
            to_ym=to_ym,
            languages=settings.ACTIONS_LANGUAGES,
            max_workers=settings.ACTIONS_MAX_WORKERS,
            log_folder=settings.ACTIONS_LOG,
            json_file=None,
            update=False)
        logger.info("NOT INDEXED editor tables were filled")

        logger.info("Filling INDEXED editor tables")
        fill_indexed_editor_tables_batch(
            from_ym=from_ym,
            to_ym=to_ym,
            languages=settings.ACTIONS_LANGUAGES,
            max_workers=settings.ACTIONS_MAX_WORKERS,
            log_folder=settings.ACTIONS_LOG)
        logger.info("Indexed editor tables were filled")

        logger.info("Emptying NOT INDEXED editor tables")
        empty_notindexed_editor_tables_batch(
            languages=settings.ACTIONS_LANGUAGES,
            max_workers=settings.ACTIONS_MAX_WORKERS,
            log_folder=settings.ACTIONS_LOG)
        logger.info("NOT INDEXED editor tables were emptied")

    except Exception as e:
        logger.error(traceback.format_exc())
