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

from dateutil import parser
from datetime import datetime


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

    def get_all_content_as_graph(self):
        json_data = dict()
        json_data['page_id'] = self.page_id
        json_data['revisions'] = []
        all_paragraphs_dict = dict()  # {ref_object: ref, }
        all_sentences_dict = dict()  # {ref_object: ref, }
        all_tokens_dict = dict()  # {toke_id: ref, }
        for i, rev_id in enumerate(self.ordered_revisions):
            paragraphs = []
            rev_dict = {
                'pos': i,
                'rev_id': rev_id,
                'paragraphs': paragraphs
            }
            json_data['revisions'].append(rev_dict)
            rev = self.revisions[rev_id]
            tmp = {'p': [], 's': []}
            for j, hash_paragraph in enumerate(rev.ordered_paragraphs):
                if len(rev.paragraphs[hash_paragraph]) > 1:
                    tmp['p'].append(hash_paragraph)
                    paragraph = rev.paragraphs[hash_paragraph][tmp['p'].count(hash_paragraph) - 1]
                else:
                    paragraph = rev.paragraphs[hash_paragraph][0]

                ref_paragraph = paragraph.__str__()  # object reference of paragraph
                if ref_paragraph in all_paragraphs_dict:
                    p_dict = {
                        'pos': j,
                        'ref': all_paragraphs_dict[ref_paragraph]['ref']
                    }
                    paragraphs.append(p_dict)
                    continue
                all_paragraphs_dict[ref_paragraph] = {'ref': '{}:{}:{}'.format(rev_id, hash_paragraph, j)}
                sentences = []
                p_dict = {
                    'pos': j,
                    'hash': hash_paragraph,
                    'sentences': sentences
                    }
                paragraphs.append(p_dict)

                tmp['s'][:] = []
                for k, hash_sentence in enumerate(paragraph.ordered_sentences):
                    if len(paragraph.sentences[hash_sentence]) > 1:
                        tmp['s'].append(hash_sentence)
                        sentence = paragraph.sentences[hash_sentence][tmp['s'].count(hash_sentence) - 1]
                    else:
                        sentence = paragraph.sentences[hash_sentence][0]

                    ref_sentence = sentence.__str__()  # object reference of sentence
                    if ref_sentence in all_sentences_dict:
                        s_dict = {
                            'pos': k,
                            'ref': all_sentences_dict[ref_sentence]['ref']
                        }
                        sentences.append(s_dict)
                        continue
                    all_sentences_dict[ref_sentence] = {
                        'ref': '{}:{}:{}:{}:{}'.format(rev_id, hash_paragraph, j, hash_sentence, k)
                    }
                    tokens = []
                    s_dict = {
                        'pos': k,
                        'hash': hash_sentence,
                        'tokens': tokens
                    }
                    sentences.append(s_dict)
                    for m, word in enumerate(sentence.words):
                        if word.token_id in all_tokens_dict:
                            t_dict = {
                                'pos': m,
                                'ref': all_tokens_dict[word.token_id]['ref']
                            }
                        else:
                            t_dict = {
                                'pos': m,
                                'token_id': word.token_id,
                                'str': word.value
                            }
                            all_tokens_dict[word.token_id] = {
                                'ref': '{}:{}:{}:{}:{}:{}'.format(rev_id, hash_paragraph, j, hash_sentence, k,
                                                                  word.token_id)
                            }
                        tokens.append(t_dict)
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

    def get_whocolor_data(self, revision_id):
        tokens = []  # {[{'o_rev_id': , 'str': , 'in': , 'out': , 'editor': , 'conflict_score': , 'age': }]}
        revision = self.revisions[revision_id]
        biggest_conflict_score = 0
        for token in iter_rev_tokens(revision):
            o_rev_id = token.origin_rev_id
            # calculate age
            o_rev_ts = parser.parse(self.revisions[o_rev_id].timestamp)
            age = datetime.now(o_rev_ts.tzinfo) - o_rev_ts
            # calculate conflict score
            editor_in_prev = None
            conflict_score = 0
            for i, out_ in enumerate(token.outbound):
                editor_out = self.revisions[out_].editor
                if editor_in_prev is not None and editor_in_prev != editor_out:
                    # exclude first deletions and self reverts (undo actions)
                    conflict_score += 1
                try:
                    in_ = token.inbound[i]
                except IndexError:
                    # no in for this out. end of loop.
                    pass
                else:
                    editor_in = self.revisions[in_].editor
                    if editor_out != editor_in:
                        # exclude self reverts (undo actions)
                        conflict_score += 1
                    editor_in_prev = editor_in
            tokens.append({
                'o_rev_id': o_rev_id,
                'str': token.value,
                'in': token.inbound,
                'out': token.outbound,
                'editor': self.revisions[token.origin_rev_id].editor,
                'conflict_score': conflict_score,
                'age': age.total_seconds()
            })
            if conflict_score > biggest_conflict_score:
                biggest_conflict_score = conflict_score
        # for token in tokens:
        #     token['conflict_score'] /= float(biggest_conflict_score)

        # {rev_id: [timestamp, parent_id, editor]}
        revisions = {self.ordered_revisions[0]: [self.revisions[self.ordered_revisions[0]].timestamp,
                                                 0,
                                                 self.revisions[self.ordered_revisions[0]].editor]}
        for i, rev_id in enumerate(self.ordered_revisions[1:]):
            revisions[rev_id] = [self.revisions[rev_id].timestamp,
                                 self.ordered_revisions[i],  # parent = previous rev id
                                 self.revisions[rev_id].editor]
        return {'tokens': tokens,
                'revisions': revisions,
                'biggest_conflict_score': biggest_conflict_score}
