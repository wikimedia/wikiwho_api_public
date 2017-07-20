# -*- coding: utf-8 -*-
from WhoColor.parser import WikiMarkupParser as WikiMarkupParserBase

from .utils import WikipediaUser


class WikiMarkupParser(WikiMarkupParserBase):

    def __set_present_editors(self):
        """
        First get names of editors from wp api.
        Sort editors who owns tokens in given revision according to percentage of owned tokens in decreasing order.
        """
        editor_ids = {e for e in self.present_editors if not e.startswith('0|')}
        wp_users_obj = WikipediaUser(editor_ids)
        editor_names_dict = wp_users_obj.get_editor_names()
        self.present_editors = tuple(
            (class_name, editor_names_dict.get(editor_id, editor_id), count*100.0/self.tokens_len)
            for editor_id, (class_name, count) in
            sorted(self.present_editors.items(), key=lambda x: x[1][1], reverse=True)
        )

        # # TODO calculate editor scores directly from token data?
        # editors = defaultdict(int)
        # for t in self.tokens:
        #     editors[t['editor']] += 1
        # editor_ids = {e for e in editors if not e.startswith('0|')}
        # wp_users_obj = WikipediaUser(editor_ids)
        # editor_names_dict = wp_users_obj.get_editor_names()
        # self.present_editors = tuple((e, editor_names_dict.get(e, e), c*100.0/self.tokens_len)
        #                              for e, c in sorted(editors.items(), key=lambda x: x[1], reverse=True))
