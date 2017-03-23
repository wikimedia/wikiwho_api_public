# -*- coding: utf-8 -*-
"""

:Authors:
    Maribel Acosta,
    Fabian Floeck,
    Kenan Erdogan
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from WikiWho.wikiwho import Wikiwho as BaseWikiwho
from WikiWho.utils import iter_rev_tokens


class Wikiwho(BaseWikiwho):

    def get_revision_content(self, revision_ids, parameters):
        """
        Return content of revision(s).

        :param revision_ids: List of revision ids. 2 revision ids mean a range.
        :param parameters: List of parameters ('o_rev_id', 'editor', 'token_id', 'in', 'out') to decide
        content of revision(s).
        :return: Content of revision in json format.
        """
        json_data = dict()
        json_data["article_title"] = self.title
        json_data["page_id"] = self.page_id
        json_data["success"] = True
        json_data["message"] = None

        # Check if given rev ids exits
        for rev_id in revision_ids:
            if rev_id not in self.revisions:
                return {'Error': 'Revision ID ({}) does not exist or is spam or deleted!'.format(rev_id)}

        if len(revision_ids) == 2:
            # Get range of revisions
            start_index = self.ordered_revisions.index(revision_ids[0])
            end_index = self.ordered_revisions.index(revision_ids[1])
            revision_ids = self.ordered_revisions[start_index:end_index]

        json_data['revisions'] = []
        for rev_id in revision_ids:
            # Prepare output revision content according to parameters
            revision = self.revisions[rev_id]
            tokens = []
            json_data['revisions'].append({rev_id: {"editor": revision.editor,
                                                    "time": revision.timestamp,
                                                    "tokens": tokens}})
            for word in iter_rev_tokens(revision):
                token = dict()
                token['str'] = word.value
                if 'o_rev_id' in parameters:
                    token['o_rev_id'] = word.origin_rev_id
                if 'editor' in parameters:
                    token['editor'] = self.revisions[word.origin_rev_id].editor
                if 'token_id' in parameters:
                    token['token_id'] = word.token_id
                if 'in' in parameters:
                    token['in'] = word.inbound
                if 'out' in parameters:
                    token['out'] = word.outbound
                tokens.append(token)
        return json_data

    def get_revision_min_content(self, revision_ids):
        """
        Return the revision content in minimum form (list of values).
        It behaves as all parameters are given.

        :param revision_ids: List of revision ids. 2 revision ids mean a range.
        :return: Content of the article in json format in min form.
        """
        json_data = dict()
        json_data["article_title"] = self.title
        json_data["page_id"] = self.page_id
        json_data["success"] = True
        json_data["message"] = None

        # Check if given rev ids exits
        for rev_id in revision_ids:
            if rev_id not in self.revisions:
                return {'Error': 'Revision ID ({}) does not exist or is spam or deleted!'.format(rev_id)}

        if len(revision_ids) == 2:
            # Get range of revisions
            start_index = self.ordered_revisions.index(revision_ids[0])
            end_index = self.ordered_revisions.index(revision_ids[1])
            revision_ids = self.ordered_revisions[start_index:end_index]

        json_data['revisions'] = []
        for rev_id in revision_ids:
            # Prepare output revision content
            revision = self.revisions[rev_id]
            values = []
            rev_ids = []
            editors = []
            token_ids = []
            outs = []
            ins = []
            json_data['revisions'].append({rev_id: {"editor": revision.editor,
                                                    "time": revision.timestamp,
                                                    "str": values,
                                                    "o_rev_ids": rev_ids,
                                                    "editors": editors,
                                                    "token_ids": token_ids,
                                                    "outs": outs,
                                                    "ins": ins,
                                                    }})
            for word in iter_rev_tokens(revision):
                values.append(word.value)
                rev_ids.append(word.origin_rev_id)
                editors.append(self.revisions[word.origin_rev_id].editor)
                token_ids.append(word.token_id)
                outs.append(word.outbound)
                ins.append(word.inbound)
        return json_data

    def get_deleted_content(self, parameters):
        """
        Return deleted content of this article.
        Deleted content is all tokens that are not present in last revision.

        :param parameters: List of parameters ('o_rev_id', 'editor', 'token_id', 'in', 'out', 'threshold').
        :return: Deleted content of the article in json format.
        """
        json_data = dict()
        json_data["article_title"] = self.title
        json_data["page_id"] = self.page_id
        json_data["success"] = True
        json_data["message"] = None

        threshold = parameters[-1]
        json_data["threshold"] = threshold
        last_rev_id = self.ordered_revisions[-1]
        json_data["revision_id"] = last_rev_id

        deleted_tokens = []
        json_data["deleted_tokens"] = deleted_tokens
        for word in self.tokens:
            if len(word.outbound) > threshold and word.last_rev_id != last_rev_id:
                token = dict()
                token['str'] = word.value
                if 'o_rev_id' in parameters:
                    token['o_rev_id'] = word.origin_rev_id
                if 'editor' in parameters:
                    token['editor'] = self.revisions[word.origin_rev_id].editor
                if 'token_id' in parameters:
                    token['token_id'] = word.token_id
                if 'in' in parameters:
                    token['in'] = word.inbound
                if 'out' in parameters:
                    token['out'] = word.outbound
                deleted_tokens.append(token)
        return json_data

    def get_all_content(self, parameters):
        """
        Return content (all tokens) of this article.

        :param parameters: List of parameters ('o_rev_id', 'editor', 'token_id', 'in', 'out').
        :return: Content of the article in json format.
        """
        json_data = dict()
        json_data["article_title"] = self.title
        json_data["page_id"] = self.page_id
        json_data["success"] = True
        json_data["message"] = None

        threshold = parameters[-1]
        json_data["threshold"] = threshold

        all_tokens = []
        json_data["all_tokens"] = all_tokens
        if threshold == 0:
            for word in self.tokens:
                token = dict()
                token['str'] = word.value
                if 'o_rev_id' in parameters:
                    token['o_rev_id'] = word.origin_rev_id
                if 'editor' in parameters:
                    token['editor'] = self.revisions[word.origin_rev_id].editor
                if 'token_id' in parameters:
                    token['token_id'] = word.token_id
                if 'in' in parameters:
                    token['in'] = word.inbound
                if 'out' in parameters:
                    token['out'] = word.outbound
                all_tokens.append(token)
        else:
            for word in self.tokens:
                if len(word.outbound) > threshold:
                    token = dict()
                    token['str'] = word.value
                    if 'o_rev_id' in parameters:
                        token['o_rev_id'] = word.origin_rev_id
                    if 'editor' in parameters:
                        token['editor'] = self.revisions[word.origin_rev_id].editor
                    if 'token_id' in parameters:
                        token['token_id'] = word.token_id
                    if 'in' in parameters:
                        token['in'] = word.inbound
                    if 'out' in parameters:
                        token['out'] = word.outbound
                    all_tokens.append(token)
        return json_data

    def get_all_min_content(self, parameters):
        """
        Return content (all tokens) of this article in minimum form (list of values).
        It behaves as all parameters are given.

        :param parameters: List of parameters ('rev_id', 'editor', 'token_id', 'inbound', 'outbound', 'threshold').
        :return: Content of the article in json format.
        """
        json_data = dict()
        json_data["article_title"] = self.title
        json_data["page_id"] = self.page_id
        json_data["success"] = True
        json_data["message"] = None

        threshold = parameters[-1]
        json_data["threshold"] = threshold
        # json_data["revision_id"] = self.ordered_revisions[-1]

        all_tokens = []
        json_data["all_tokens"] = all_tokens
        # TODO finish
        return json_data

    def get_revision_ids(self, parameters):
        """
        Return list of list of revision ids with optionally appending editor and timestamp information.

        :param parameters: List of parameters ('editor', 'timestamp').
        :return: List of revision ids of this article in json format.
        """
        json_data = dict()
        json_data["article_title"] = self.title
        json_data["page_id"] = self.page_id
        json_data["success"] = True
        json_data["message"] = None

        revisions = []
        json_data["revisions"] = revisions
        for rev_id in self.ordered_revisions:
            rev = {'id': rev_id}
            revision = self.revisions[rev_id]
            if 'editor' in parameters:
                rev['editor'] = revision.editor
            if 'timestamp' in parameters:
                rev['timestamp'] = revision.timestamp
            revisions.append(rev)
        return json_data

    def get_revision_text(self, revision_id):
        """
        :param revision_id:
        :return: List of token values and list of origin rev ids respectively.
        """
        revision = self.revisions[revision_id]
        text = []
        origin_rev_ids = []
        for word in iter_rev_tokens(revision):
            text.append(word.value)
            origin_rev_ids.append(word.origin_rev_id)
        return text, origin_rev_ids
