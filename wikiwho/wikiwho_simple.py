# -*- coding: utf-8 -*-
"""
Created on Feb 20, 2013

@author: Maribel Acosta 
@author: Fabian Floeck 
@author: Andriy Rodchenko
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from copy import deepcopy
from difflib import Differ

from .structures import Word, Sentence, Paragraph, Revision
from .utils import calculateHash, splitIntoParagraphs, splitIntoSentences, splitIntoWords, computeAvgWordFreq


# spam detection variables.
CHANGE_PERCENTAGE = -0.40
PREVIOUS_LENGTH = 1000
CURR_LENGTH = 1000
FLAG = "move"
UNMATCHED_PARAGRAPH = 0.0
WORD_DENSITY = 10
# WORD_DENSITY = 12
WORD_LEN = 100


class Wikiwho:
    def __init__(self, article):
        # Hash tables.
        self.paragraphs_ht = {}
        self.sentences_ht = {}

        self.spam = []
        self.revisions = {}  # {rev_id : rev_obj, ...}
        self.rvcontinue = '0'
        self.article = article
        self.page_id = None
        # Revisions to compare.
        self.revision_curr = Revision()
        # self.revision_prev = Revision()

        self.text_curr = ''
        self.token_id = 0
        self.temp = []

    def _clean(self):
        # empty attributes
        # self.revision_prev = None
        self.text_curr = ''
        self.temp = []

    def analyse_article(self, revisions):
        i = 1
        # Iterate over revisions of the article.
        for revision in revisions:
            if 'texthidden' in revision:
                continue
            if 'textmissing' in revision:
                continue

            vandalism = False
            # Update the information about the previous revision.
            revision_prev = self.revision_curr

            text = revision['*']
            if revision['sha1'] == "":
                revision['sha1'] = calculateHash(text)  # .encode("utf-8"))
            rev_id = int(revision['revid'])
            if rev_id in self.spam:
                vandalism = True

            # TODO: spam detection: DELETION
            text_len = len(text)
            try:
                if revision['comment'] != '' and 'minor' in revision:
                # if revision['comment'] != '' and FLAG in revision:
                    pass
                else:
                    # if content is not moved (flag) to different article in good faith, check for vandalism
                    # if revisions have reached a certain size
                    if revision_prev.length > PREVIOUS_LENGTH and \
                       text_len < CURR_LENGTH and \
                       ((text_len-revision_prev.length) / revision_prev.length) <= CHANGE_PERCENTAGE:
                        # VANDALISM: CHANGE PERCENTAGE
                        vandalism = True
            except:
                pass

            if vandalism:
                # print("---------------------------- FLAG 1")
                # print(revision.id)
                # print(self.text_curr)
                self.revision_curr = revision_prev
                self.spam.append(rev_id)  # skip revision with vandalism in history
            else:
                # Information about the current revision.
                self.revision_curr = Revision()
                self.revision_curr.id = i
                self.revision_curr.wikipedia_id = rev_id
                self.revision_curr.length = text_len
                self.revision_curr.time = revision['timestamp']

                # Some revisions don't have contributor.
                self.revision_curr.contributor_id = revision.get('userid', '')  # Not Available
                self.revision_curr.contributor_name = revision.get('user', '')

                # Content within the revision.
                # Software should only work with Unicode strings internally, converting to a particular encoding on
                # output.
                # https://docs.python.org/2/howto/unicode.html#tips-for-writing-unicode-aware-programs
                # https://pythonhosted.org/kitchen/unicode-frustrations.html
                self.text_curr = text.lower()  # .encode("utf-8")

                # Perform comparison.
                vandalism = self.determine_authorship(revision_prev)

                if vandalism:
                    # print "---------------------------- FLAG 2"
                    # print revision.getId()
                    # print revision.getText()
                    # print
                    self.revision_curr = revision_prev  # skip revision with vandalism in history
                    self.spam.append(rev_id)
                else:
                    # Add the current revision with all the information.
                    self.revisions.update({self.revision_curr.wikipedia_id: self.revision_curr})
                    # Update the fake revision id.
                    i += 1
            self.temp = []

        self._clean()

    def determine_authorship(self, revision_prev):
        # Containers for unmatched paragraphs and sentences in both revisions.
        unmatched_sentences_curr = []
        unmatched_sentences_prev = []
        matched_sentences_prev = []
        matched_words_prev = []
        possible_vandalism = False
        vandalism = False

        # Analysis of the paragraphs in the current revision.
        unmatched_paragraphs_curr, unmatched_paragraphs_prev, matched_paragraphs_prev = \
            self.analyse_paragraphs_in_revision(revision_prev)

        # Analysis of the sentences in the unmatched paragraphs of the current revision.
        if unmatched_paragraphs_curr:
            unmatched_sentences_curr, unmatched_sentences_prev, matched_sentences_prev, total_sentences = \
                self.analyse_sentences_in_paragraphs(unmatched_paragraphs_curr, unmatched_paragraphs_prev,
                                                     revision_prev)

            # TODO: spam detection
            if len(unmatched_paragraphs_curr) / len(self.revision_curr.ordered_paragraphs) > UNMATCHED_PARAGRAPH:
                # will be used to detect copy-paste vandalism - token density
                possible_vandalism = True

            # Analysis of words in unmatched sentences (diff of both texts).
            if unmatched_sentences_curr:
                matched_words_prev, vandalism = self.analyse_words_in_sentences(unmatched_sentences_curr,
                                                                                unmatched_sentences_prev,
                                                                                possible_vandalism)

        # Add the information of 'deletion' to words
        for unmatched_sentence in unmatched_sentences_prev:
            for word in unmatched_sentence.words:
                if not word.matched:
                    word.outbound.append(self.revision_curr.wikipedia_id)
                    # print('outbound:', word.value, self.revision_curr.wikipedia_id)
        if not unmatched_sentences_prev:
            # if all current paragraphs are matched
            for unmatched_paragraph in unmatched_paragraphs_prev:
                for sentence_hash in unmatched_paragraph.sentences:
                    for sentence in unmatched_paragraph.sentences[sentence_hash]:
                        for word in sentence.words:
                            if not word.matched:
                                word.outbound.append(self.revision_curr.wikipedia_id)

        # Reset matched structures from old revisions.
        for matched_paragraph in matched_paragraphs_prev:
            matched_paragraph.matched = False
            for sentence_hash in matched_paragraph.sentences:
                for sentence in matched_paragraph.sentences[sentence_hash]:
                    sentence.matched = False
                    for word in sentence.words:
                        word.matched = False

        for matched_sentence in matched_sentences_prev:
            matched_sentence.matched = False
            for word in matched_sentence.words:
                word.matched = False

        for matched_word in matched_words_prev:
            matched_word.matched = False

        if not vandalism:
            # Add the new paragraphs to hash table of paragraphs.
            for unmatched_paragraph in unmatched_paragraphs_curr:
                if unmatched_paragraph.hash_value in self.paragraphs_ht:
                    self.paragraphs_ht[unmatched_paragraph.hash_value].append(unmatched_paragraph)
                else:
                    self.paragraphs_ht.update({unmatched_paragraph.hash_value: [unmatched_paragraph]})

            # Add the new sentences to hash table of sentences.
            for unmatched_sentence in unmatched_sentences_curr:
                if unmatched_sentence.hash_value in self.sentences_ht:
                    self.sentences_ht[unmatched_sentence.hash_value].append(unmatched_sentence)
                else:
                    self.sentences_ht.update({unmatched_sentence.hash_value: [unmatched_sentence]})

        return vandalism

    def analyse_paragraphs_in_revision(self, revision_prev):
        # Containers for unmatched and matched paragraphs.
        unmatched_paragraphs_curr = []
        unmatched_paragraphs_prev = []
        matched_paragraphs_prev = []

        # Split the text of the current into paragraphs.
        paragraphs = splitIntoParagraphs(self.text_curr)

        # Iterate over the paragraphs of the current version.
        for paragraph in paragraphs:
            # Build Paragraph structure and calculate hash value.
            paragraph = paragraph.strip()
            if not paragraph:
                # dont track empty lines
                continue
            hash_curr = calculateHash(paragraph)
            matched_curr = False

            # If the paragraph is in the previous revision,
            # update the authorship information and mark both paragraphs as matched (also in HT).
            for paragraph_prev in revision_prev.paragraphs.get(hash_curr, []):
                if not paragraph_prev.matched:
                    matched_one = False
                    matched_all = True
                    for h in paragraph_prev.sentences:
                        for s_prev in paragraph_prev.sentences[h]:
                            for w_prev in s_prev.words:
                                if w_prev.matched:
                                    matched_one = True
                                else:
                                    matched_all = False

                    if not matched_one:
                        # if there is not any already matched prev word, so set them all as matched
                        matched_curr = True
                        paragraph_prev.matched = True
                        matched_paragraphs_prev.append(paragraph_prev)

                        # Set all sentences and words of this paragraph as matched
                        for hash_sentence_prev in paragraph_prev.sentences:
                            for sentence_prev in paragraph_prev.sentences[hash_sentence_prev]:
                                sentence_prev.matched = True
                                for word_prev in sentence_prev.words:
                                    word_prev.matched = True
                                    word_prev.last_used = self.revision_curr.wikipedia_id

                        # Add paragraph to current revision.
                        if hash_curr in self.revision_curr.paragraphs:
                            self.revision_curr.paragraphs[hash_curr].append(paragraph_prev)
                        else:
                            self.revision_curr.paragraphs.update({paragraph_prev.hash_value: [paragraph_prev]})
                        self.revision_curr.ordered_paragraphs.append(paragraph_prev.hash_value)
                        break
                    elif matched_all:
                        # if all prev words in this paragraph are already matched
                        paragraph_prev.matched = True
                        matched_paragraphs_prev.append(paragraph_prev)

            # If the paragraph is not in the previous revision, but it is in an older revision
            # update the authorship information and mark both paragraphs as matched.
            if not matched_curr:
                for paragraph_prev in self.paragraphs_ht.get(hash_curr, []):
                    if not paragraph_prev.matched:
                        matched_one = False
                        matched_all = True
                        for h in paragraph_prev.sentences:
                            for s_prev in paragraph_prev.sentences[h]:
                                for w_prev in s_prev.words:
                                    if w_prev.matched:
                                        matched_one = True
                                    else:
                                        matched_all = False

                        if not matched_one:
                            # if there is not any already matched prev word, so set them all as matched
                            matched_curr = True
                            paragraph_prev.matched = True
                            matched_paragraphs_prev.append(paragraph_prev)

                            # Set all sentences and words of this paragraph as matched
                            for hash_sentence_prev in paragraph_prev.sentences:
                                for sentence_prev in paragraph_prev.sentences[hash_sentence_prev]:
                                    sentence_prev.matched = True
                                    for word_prev in sentence_prev.words:
                                        word_prev.matched = True
                                        if revision_prev.wikipedia_id != word_prev.last_used:
                                            word_prev.inbound.append(self.revision_curr.wikipedia_id)
                                            # print('inbound:', word_prev.value, self.revision_curr.wikipedia_id)
                                        word_prev.last_used = self.revision_curr.wikipedia_id

                            # Add paragraph to current revision.
                            if hash_curr in self.revision_curr.paragraphs:
                                self.revision_curr.paragraphs[hash_curr].append(paragraph_prev)
                            else:
                                self.revision_curr.paragraphs.update({paragraph_prev.hash_value: [paragraph_prev]})
                            self.revision_curr.ordered_paragraphs.append(paragraph_prev.hash_value)
                            break
                        elif matched_all:
                            # if all prev words in this paragraph are already matched
                            paragraph_prev.matched = True
                            matched_paragraphs_prev.append(paragraph_prev)

            # If the paragraph did not match with previous revisions,
            # add to container of unmatched paragraphs for further analysis.
            if not matched_curr:
                paragraph_curr = Paragraph()
                paragraph_curr.hash_value = hash_curr
                paragraph_curr.value = paragraph
                if hash_curr in self.revision_curr.paragraphs:
                    self.revision_curr.paragraphs[hash_curr].append(paragraph_curr)
                else:
                    self.revision_curr.paragraphs.update({paragraph_curr.hash_value: [paragraph_curr]})
                self.revision_curr.ordered_paragraphs.append(paragraph_curr.hash_value)
                unmatched_paragraphs_curr.append(paragraph_curr)

        # Identify unmatched paragraphs in previous revision for further analysis.
        for paragraph_prev_hash in revision_prev.ordered_paragraphs:
            if len(revision_prev.paragraphs[paragraph_prev_hash]) > 1:
                s = 'p-{}-{}'.format(revision_prev, paragraph_prev_hash)
                self.temp.append(s)
                count = self.temp.count(s)
                paragraph_prev = revision_prev.paragraphs[paragraph_prev_hash][count - 1]
            else:
                paragraph_prev = revision_prev.paragraphs[paragraph_prev_hash][0]
            if not paragraph_prev.matched:
                unmatched_paragraphs_prev.append(paragraph_prev)

        return unmatched_paragraphs_curr, unmatched_paragraphs_prev, matched_paragraphs_prev

    def analyse_sentences_in_paragraphs(self, unmatched_paragraphs_curr, unmatched_paragraphs_prev, revision_prev):
        # Containers for unmatched and matched sentences.
        unmatched_sentences_curr = []
        unmatched_sentences_prev = []
        matched_sentences_prev = []
        total_sentences = 0

        # Iterate over the unmatched paragraphs of the current revision.
        for paragraph_curr in unmatched_paragraphs_curr:
            # Split the current paragraph into sentences.
            sentences = splitIntoSentences(paragraph_curr.value)
            # Iterate over the sentences of the current paragraph
            for sentence in sentences:
                # Create the Sentence structure.
                sentence = sentence.strip()
                if not sentence:
                    # dont track empty lines
                    continue
                sentence = ' '.join(splitIntoWords(sentence))
                hash_curr = calculateHash(sentence)
                matched_curr = False
                total_sentences += 1

                # Iterate over the unmatched paragraphs from the previous revision.
                for paragraph_prev in unmatched_paragraphs_prev:
                    for sentence_prev in paragraph_prev.sentences.get(hash_curr, []):
                        if not sentence_prev.matched:
                            matched_one = False
                            matched_all = True
                            for word_prev in sentence_prev.words:
                                if word_prev.matched:
                                    matched_one = True
                                else:
                                    matched_all = False

                            if not matched_one:
                                # if there is not any already matched prev word, so set them all as matched
                                sentence_prev.matched = True
                                matched_curr = True
                                matched_sentences_prev.append(sentence_prev)

                                for word_prev in sentence_prev.words:
                                    word_prev.matched = True
                                    word_prev.last_used = self.revision_curr.wikipedia_id

                                # Add the sentence information to the paragraph.
                                if hash_curr in paragraph_curr.sentences:
                                    paragraph_curr.sentences[hash_curr].append(sentence_prev)
                                else:
                                    paragraph_curr.sentences.update({sentence_prev.hash_value: [sentence_prev]})
                                paragraph_curr.ordered_sentences.append(sentence_prev.hash_value)
                                break
                            elif matched_all:
                                # if all prev words in this sentence are already matched
                                sentence_prev.matched = True
                                matched_sentences_prev.append(sentence_prev)
                    if matched_curr:
                        break

                # Iterate over the hash table of sentences from old revisions.
                if not matched_curr:
                    for sentence_prev in self.sentences_ht.get(hash_curr, []):
                        if not sentence_prev.matched:
                            matched_one = False
                            matched_all = True
                            for word_prev in sentence_prev.words:
                                if word_prev.matched:
                                    matched_one = True
                                else:
                                    matched_all = False

                            if not matched_one:
                                # if there is not any already matched prev word, so set them all as matched
                                sentence_prev.matched = True
                                matched_curr = True
                                matched_sentences_prev.append(sentence_prev)

                                for word_prev in sentence_prev.words:
                                    word_prev.matched = True
                                    if revision_prev.wikipedia_id != word_prev.last_used:
                                        word_prev.inbound.append(self.revision_curr.wikipedia_id)
                                        # print('inbound:', word_prev.value, self.revision_curr.wikipedia_id)
                                    word_prev.last_used = self.revision_curr.wikipedia_id

                                # Add the sentence information to the paragraph.
                                if hash_curr in paragraph_curr.sentences:
                                    paragraph_curr.sentences[hash_curr].append(sentence_prev)
                                else:
                                    paragraph_curr.sentences.update({sentence_prev.hash_value: [sentence_prev]})
                                paragraph_curr.ordered_sentences.append(sentence_prev.hash_value)
                                break
                            elif matched_all:
                                # if all prev words in this sentence are already matched
                                sentence_prev.matched = True
                                matched_sentences_prev.append(sentence_prev)

                # If the sentence did not match,
                # then include in the container of unmatched sentences for further analysis.
                if not matched_curr:
                    sentence_curr = Sentence()
                    sentence_curr.value = sentence
                    sentence_curr.hash_value = hash_curr

                    if hash_curr in paragraph_curr.sentences:
                        paragraph_curr.sentences[hash_curr].append(sentence_curr)
                    else:
                        paragraph_curr.sentences.update({sentence_curr.hash_value: [sentence_curr]})
                    paragraph_curr.ordered_sentences.append(sentence_curr.hash_value)
                    unmatched_sentences_curr.append(sentence_curr)

        # Identify the unmatched sentences in the previous paragraph revision.
        for paragraph_prev in unmatched_paragraphs_prev:
            for sentence_prev_hash in paragraph_prev.ordered_sentences:
                if len(paragraph_prev.sentences[sentence_prev_hash]) > 1:
                    s = 's-{}-{}'.format(paragraph_prev, sentence_prev_hash)
                    self.temp.append(s)
                    count = self.temp.count(s)
                    sentence_prev = paragraph_prev.sentences[sentence_prev_hash][count - 1]
                else:
                    sentence_prev = paragraph_prev.sentences[sentence_prev_hash][0]
                if not sentence_prev.matched:
                    unmatched_sentences_prev.append(sentence_prev)
                    sentence_prev.matched = True  # to reset them correctly in determine_authorship
                    matched_sentences_prev.append(sentence_prev)

        return unmatched_sentences_curr, unmatched_sentences_prev, matched_sentences_prev, total_sentences

    def analyse_words_in_sentences(self, unmatched_sentences_curr, unmatched_sentences_prev, possible_vandalism):
        matched_words_prev = []
        unmatched_words_prev = []

        # Split sentences into words.
        text_prev = []
        for sentence_prev in unmatched_sentences_prev:
            for word_prev in sentence_prev.words:
                if not word_prev.matched:
                    text_prev.append(word_prev.value)
                    unmatched_words_prev.append(word_prev)

        text_curr = []
        for sentence_curr in unmatched_sentences_curr:
            words = splitIntoWords(sentence_curr.value)
            text_curr.extend(words)
            sentence_curr.splitted.extend(words)

        # Edit consists of removing sentences, not adding new content.
        if not text_curr:
            return matched_words_prev, False

        # spam detection.
        if possible_vandalism:
            token_density = computeAvgWordFreq(text_curr, self.revision_curr.wikipedia_id)
            if token_density > WORD_DENSITY:
                return matched_words_prev, possible_vandalism
            else:
                possible_vandalism = False

        # Edit consists of adding new content, not changing content ?
        if not text_prev:
            for sentence_curr in unmatched_sentences_curr:
                for word in sentence_curr.splitted:
                    word_curr = Word()
                    word_curr.value = word
                    word_curr.internal_id = self.token_id
                    word_curr.author_id = self.revision_curr.contributor_id
                    word_curr.author_name = self.revision_curr.contributor_name
                    word_curr.revision = self.revision_curr.wikipedia_id
                    word_curr.last_used = self.revision_curr.wikipedia_id
                    sentence_curr.words.append(word_curr)
                    self.token_id += 1
            return matched_words_prev, possible_vandalism

        d = Differ()
        diff = list(d.compare(text_prev, text_curr))
        for sentence_curr in unmatched_sentences_curr:
            for word in sentence_curr.splitted:
                curr_matched = False
                pos = 0
                # next_word = False
                while pos < len(diff):
                    word_diff = diff[pos]
                    if word == word_diff[2:]:
                        if word_diff[0] == ' ':
                            # match
                            for word_prev in unmatched_words_prev:
                                if not word_prev.matched and word_prev.value == word:
                                    word_prev.matched = True
                                    curr_matched = True
                                    word_prev.last_used = self.revision_curr.wikipedia_id
                                    sentence_curr.words.append(word_prev)
                                    matched_words_prev.append(word_prev)
                                    diff[pos] = ''
                                    pos = len(diff) + 1
                                    break
                        elif word_diff[0] == '-':
                            # deleted / reintroduced ??
                            for word_prev in unmatched_words_prev:
                                if not word_prev.matched and word_prev.value == word:
                                    word_prev.matched = True
                                    word_prev.outbound.append(self.revision_curr.wikipedia_id)
                                    # print('outbound:', word_prev.value, self.revision_curr.wikipedia_id)
                                    matched_words_prev.append(word_prev)
                                    diff[pos] = ''
                                    break
                        elif word_diff[0] == '+':
                            # a new added word
                            curr_matched = True
                            word_curr = Word()
                            word_curr.value = word
                            word_curr.internal_id = self.token_id
                            word_curr.author_id = self.revision_curr.contributor_id
                            word_curr.author_name = self.revision_curr.contributor_name
                            word_curr.revision = self.revision_curr.wikipedia_id
                            word_curr.last_used = self.revision_curr.wikipedia_id
                            sentence_curr.words.append(word_curr)
                            self.token_id += 1
                            diff[pos] = ''
                            pos = len(diff) + 1
                    pos += 1

                if not curr_matched:
                    # if diff returns a word as '? ...'
                    word_curr = Word()
                    word_curr.value = word
                    word_curr.internal_id = self.token_id
                    word_curr.author_id = self.revision_curr.contributor_id
                    word_curr.author_name = self.revision_curr.contributor_name
                    word_curr.revision = self.revision_curr.wikipedia_id
                    word_curr.last_used = self.revision_curr.wikipedia_id
                    sentence_curr.words.append(word_curr)
                    self.token_id += 1

        return matched_words_prev, possible_vandalism

    def get_revision_json(self, revision_ids, parameters, format_="json"):
        response = dict()
        response["success"] = "true"
        revisions = []
        response["article"] = self.article

        for rev_id in revision_ids:
            if rev_id not in self.revisions:
                return {'Error': 'Revision ID ({}) does not exist or is spam or deleted!'.format(rev_id)}

        for rev_id, revision in self.revisions.items():
            if len(revision_ids) == 2:
                if rev_id < revision_ids[0] or rev_id > revision_ids[1]:
                    continue
            else:
                if rev_id != revision_ids[0]:
                    continue

            revisions.append({rev_id: {"author": revision.contributor_name,  # .encode("utf-8"),
                                       "time": revision.time,
                                       "tokens": []}})
            dict_list = []
            ps_copy = deepcopy(revision.paragraphs)
            for hash_paragraph in revision.ordered_paragraphs:
                # text = ''
                paragraph = ps_copy[hash_paragraph].pop(0)
                for hash_sentence in paragraph.ordered_sentences:
                    sentence = paragraph.sentences[hash_sentence].pop(0)
                    for word in sentence.words:
                        if format_ == 'json':
                            dict_json = dict()
                            dict_json['str'] = word.value
                            if 'rev_id' in parameters:
                                dict_json['rev_id'] = word.revision
                            if 'author_id' in parameters:
                                dict_json['author_id'] = word.author_id
                            if 'token_id' in parameters:
                                dict_json['token_id'] = word.internal_id
                            if 'inbound' in parameters:
                                dict_json['inbound'] = word.inbound
                            if 'outbound' in parameters:
                                dict_json['outbound'] = word.outbound
                            dict_list.append(dict_json)
            if format_ == 'json':
                revisions[-1][rev_id]["tokens"] = dict_list
        response["revisions"] = sorted(revisions, key=lambda x: sorted(x.keys())) \
            if len(revision_ids) > 1 else revisions
        response["message"] = None
        # import json
        # with open('tmp_pickles/{}_{}.json'.format(self.article, revision_ids[0]), 'w') as f:
        #     f.write(json.dumps(response, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        return response

    def get_deleted_tokens(self, parameters):
        response = dict()
        response["success"] = "true"
        response["article"] = self.article

        threshold = parameters[-1]
        deleted_tokens = []
        deleted_token_keys = []
        from datetime import datetime
        revisions = [(datetime.strptime(rev.time, '%Y-%m-%dT%H:%M:%SZ'), rev) for rev in self.revisions.values()]
        revisions = [rev_id for time, rev_id in sorted(revisions, key=lambda x: x[0])]
        last_rev_id = revisions[-1].wikipedia_id
        for revision in revisions[:-1]:
            ps_copy = deepcopy(revision.paragraphs)
            for hash_paragraph in revision.ordered_paragraphs:
                paragraph = ps_copy[hash_paragraph].pop(0)
                for hash_sentence in paragraph.ordered_sentences:
                    sentence = paragraph.sentences[hash_sentence].pop(0)
                    for word in sentence.words:
                        if len(word.outbound) > threshold and word.last_used != last_rev_id:
                            token = dict()
                            token['str'] = word.value
                            if 'rev_id' in parameters:
                                token['rev_id'] = word.revision
                            if 'author_id' in parameters:
                                token['author_id'] = word.author_id
                            if 'token_id' in parameters:
                                token['token_id'] = word.internal_id
                            if 'inbound' in parameters:
                                token['inbound'] = word.inbound
                            if 'outbound' in parameters:
                                token['outbound'] = word.outbound
                            key = '{}-{}'.format(word.revision, word.internal_id)
                            if key not in deleted_token_keys:
                                deleted_token_keys.append(key)
                                deleted_tokens.append(token)
        response["deleted_tokens"] = deleted_tokens

        response["threshold"] = threshold
        response["revision_id"] = last_rev_id
        response["message"] = None
        return response

    def get_revision_ids(self):
        response = dict()
        response["success"] = "true"
        revisions = []
        response["article"] = self.article
        from datetime import datetime
        for rev_id, rev in self.revisions.items():
            revisions.append((datetime.strptime(rev.time, '%Y-%m-%dT%H:%M:%SZ'), rev_id))
        response["revisions"] = [rev_id for time, rev_id in sorted(revisions, key=lambda x: x[0])]
        response["message"] = None
        return response

    def get_revision_text(self, revision_id):
        revision = self.revisions[revision_id]
        text = []
        label_rev_ids = []
        ps_copy = deepcopy(revision.paragraphs)
        for hash_paragraph in revision.ordered_paragraphs:
            paragraph = ps_copy[hash_paragraph].pop(0)
            for hash_sentence in paragraph.ordered_sentences:
                sentence = paragraph.sentences[hash_sentence].pop(0)
                for word in sentence.words:
                    text.append(word.value)
                    label_rev_ids.append(word.revision)
        return text, label_rev_ids
