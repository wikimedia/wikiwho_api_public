# -*- coding: utf-8 -*-
"""

:Authors:
    Kenan Erdogan
"""
import os
import hashlib

from django.conf import settings

from api.utils_pickles import pickle_load
from WhoColor.parser import WikiMarkupParser
from .utils import WikipediaRevText, WikipediaUser


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
        # self.wiki_text = ''
        # self.tokens = []
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
        if data is None:
            raise WhoColorException('The revision ({}) you are trying to request does not exist!'.
                                    format(self.rev_id), '03')
        if 'error' in data:
            raise WhoColorException('Wikipedia API returned the following error:' + str(data['error']), '11')
        if "-1" in data:
            raise WhoColorException('The article ({}) you are trying to request does not exist!'.
                                    format(self.page_title or self.page_id), '00')
        self.page_id = data['page_id']
        self.rev_id = data['rev_id']
        wiki_text = data['rev_text']
        if data['namespace'] != 0:
            raise WhoColorException('Only articles! Namespace {} is not accepted.'.format(data['namespace']), '02')

        # get authorship data directly from pickles
        pickle_path = "{}/{}.p".format(self.pickle_folder, self.page_id)
        already_exists = os.path.exists(pickle_path)
        if not already_exists:
            # requested page is not processed by WikiWho yet
            if not settings.ONLY_READ_ALLOWED:
                return None, None, None
            else:
                raise WhoColorException('Only read is allowed for now.', '21')
        else:
            wikiwho = pickle_load(pickle_path)
            if self.rev_id not in wikiwho.revisions:
                # requested rev id is not processed by WikiWho yet or it is in spams
                if self.rev_id in wikiwho.spam_ids:
                    return False, False, False
                if not settings.ONLY_READ_ALLOWED:
                    return None, None, None
                else:
                    raise WhoColorException('Only read is allowed for now.', '21')
            whocolor_data = wikiwho.get_whocolor_data(self.rev_id)

            # get editor names from wp api
            editor_ids = {v[2] for k, v in whocolor_data['revisions'].items() if not v[2].startswith('0|')}
            wp_users_obj = WikipediaUser(editor_ids)
            editor_names_dict = wp_users_obj.get_editor_names()

            # set editor and class names for each token
            for token in whocolor_data['tokens']:
                token['editor_name'] = editor_names_dict.get(token['editor'], token['editor'])
                if token['editor'].startswith('0|'):
                    token['class_name'] = hashlib.md5(token['editor'].encode('utf-8')).hexdigest()
                else:
                    token['class_name'] = token['editor']

            # annotate authorship data to wiki text
            # if registered user, class name is editor id
            parser = WikiMarkupParser(wiki_text, whocolor_data['tokens'])  # , self.revisions)
            parser.generate_extended_wiki_markup()
            extended_html = wp_rev_text_obj.convert_wiki_text_to_html(parser.extended_wiki_text)

            # exclude unnecessary token data
            # [[conflict_score, str, o_rev_id, in, out, editor/class_name]]
            tokens = [[token['conflict_score'], token['str'], token['o_rev_id'],
                       token['in'], token['out'], token['class_name']]
                      for token in whocolor_data['tokens']]

            # append editor names into revisions
            # {rev_id: [timestamp, parent_id, class_name/editor, editor_name]}
            for rev_id, rev_data in whocolor_data['revisions'].items():
                rev_data.append(editor_names_dict.get(rev_data[2], rev_data[2]))
                if rev_data[2].startswith('0|'):
                    rev_data[2] = hashlib.md5(rev_data[2].encode('utf-8')).hexdigest()

            whocolor_data['tokens'] = tokens
            return extended_html, parser.present_editors, whocolor_data

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
