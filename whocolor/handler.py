# -*- coding: utf-8 -*-
"""

:Authors:
    Kenan Erdogan
"""
import os

from django.conf import settings

from api.utils_pickles import pickle_load
from .utils import WikipediaRevText
from .parser import WikiMarkupParser


class WhoColorException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code

    def __str__(self):
        return repr(self.message)


class WhoColorHandler(object):
    def __init__(self, page_id=None, page_title=None, revision_id=None, pickle_folder='', *args, **kwargs):
        self.page_id = page_id
        self.page_title = page_title
        self.rev_id = revision_id
        self.pickle_folder = pickle_folder
        self.wiki_text = ''
        self.tokens = []
        # self.revisions = []
        # self.extended_wiki_text = ''

    def __enter__(self):
        # check if given page_id valid
        if self.page_id is not None:
            self.page_id = int(self.page_id)
            if not 0 < self.page_id < 2147483647:
                raise WhoColorException('Please enter a valid page id ({}).'.format(self.page_id), '01')

        self.pickle_folder = self.pickle_folder or settings.PICKLE_FOLDER
        return self

    def handle(self):
        # get rev wiki text from wp
        wp_rev_text_obj = WikipediaRevText(self.page_title, self.page_id, self.rev_id)
        data = wp_rev_text_obj.get_rev_wiki_text()
        if 'error' in data:
            raise WhoColorException('Wikipedia API returned the following error:' + str(data['error']), '11')
        if "-1" in data:
            raise WhoColorException('The article ({}) you are trying to request does not exist!'.
                                    format(self.page_title or self.page_id), '00')
        self.page_id = data['page_id']
        self.rev_id = data['rev_id']
        self.wiki_text = data['rev_text']
        if data['namespace'] != 0:
            raise WhoColorException('Only articles! Namespace {} is not accepted.'.format(data['namespace']), '02')

        # get authorship data directly from pickles
        pickle_path = "{}/{}.p".format(self.pickle_folder, self.page_id)
        already_exists = os.path.exists(pickle_path)
        if not already_exists:
            if not settings.ONLY_READ_ALLOWED:
                # TODO start a celery task and return info message
                return None, None
            else:
                raise WhoColorException('Only read is allowed for now.', '21')
        else:
            wikiwho = pickle_load(pickle_path)
            if self.rev_id not in wikiwho.revisions:
                if not settings.ONLY_READ_ALLOWED:
                    # TODO start a celery task and return info message
                    return None, None
                else:
                    raise WhoColorException('Only read is allowed for now.', '21')
            self.tokens = wikiwho.get_whocolor_content(self.rev_id)

            # annotate authorship data to wiki text
            parser = WikiMarkupParser(self.wiki_text, self.tokens)  # , self.revisions)
            parser.generate_extended_wiki_markup()
            extended_html = wp_rev_text_obj.convert_wiki_text_to_html(parser.extended_wiki_text)
            return extended_html, parser.present_editors

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
