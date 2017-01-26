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

from difflib import Differ

from .structures import Word, Sentence, Paragraph, Revision
from .utils import calculateHash, splitIntoParagraphs, splitIntoSentences, splitIntoWords, computeAvgWordFreq, \
    iter_rev_tokens


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
    def __init__(self, article_title):
        # Hash tables.
        self.paragraphs_ht = {}
        self.sentences_ht = {}

        self.spam_ids = []
        self.spam_hashes = []
        self.revisions = {}  # {rev_id : rev_obj, ...}
        self.rvcontinue = '0'
        self.title = article_title
        self.page_id = None  # article id
        self.token_id = 0  # sequential id for words in article. unique per article
        # Revisions to compare.
        self.revision_curr = Revision()
        self.revision_prev = Revision()

        self.continue_rev_ts = None  # to detect updated previous tokens
        self.updated_prev_tokens = []  # [token_id, ..]
        self.text_curr = ''
        self.temp = []

    def clean_attributes(self):
        # empty attributes
        self.revision_prev = None

        self.updated_prev_tokens = []
        self.text_curr = ''
        self.temp = []

    def analyse_article_xml(self, page):
        position = self.revision_prev.position + 1
        # Iterate over revisions of the article.
        for revision in page:
            text = revision.text or ''
            if not text and (revision.deleted.text or revision.deleted.restricted):
            # if not text or revision.deleted.text or revision.deleted.restricted:  # or revision.deleted.comment or revision.deleted.user
                # equivalent of "'texthidden' in revision or 'textmissing' in revision" in analyse_article
                continue

            vandalism = False
            # Update the information about the previous revision.
            self.revision_prev = self.revision_curr

            rev_id = revision.id
            rev_hash = revision.sha1 or calculateHash(text)
            if rev_hash in self.spam_hashes:
                vandalism = True

            # TODO: spam detection: DELETION
            text_len = len(text)
            if not vandalism and not(revision.comment and revision.minor):
                # if content is not moved (flag) to different article in good faith, check for vandalism
                # if revisions have reached a certain size
                if self.revision_prev.length > PREVIOUS_LENGTH and \
                   text_len < CURR_LENGTH and \
                   ((text_len-self.revision_prev.length) / self.revision_prev.length) <= CHANGE_PERCENTAGE:
                    # VANDALISM: CHANGE PERCENTAGE - DELETION
                    vandalism = True

            if vandalism:
                # print("---------------------------- FLAG 1")
                # print(revision.position)
                # print(self.text_curr)
                self.revision_curr = self.revision_prev
                self.spam_ids.append(rev_id)
                self.spam_hashes.append(rev_hash)
            else:
                # Information about the current revision.
                self.revision_curr = Revision()
                self.revision_curr.position = position
                self.revision_curr.id = rev_id
                self.revision_curr.length = text_len
                self.revision_curr.timestamp = revision.timestamp.long_format()

                # Some revisions don't have contributor.
                if revision.user:
                    contributor_name = revision.user.text or ''  # Not Available
                    if revision.user.id is None and contributor_name or revision.user.id == 0:
                        contributor_id = 0
                    else:
                        contributor_id = revision.user.id or ''
                else:
                    contributor_name = ''
                    contributor_id = ''
                editor = contributor_id
                editor = str(editor) if editor != 0 else '0|{}'.format(contributor_name)
                self.revision_curr.editor = editor

                # Content within the revision.
                # Software should only work with Unicode strings internally, converting to a particular encoding on
                # output.
                # https://docs.python.org/2/howto/unicode.html#tips-for-writing-unicode-aware-programs
                # https://pythonhosted.org/kitchen/unicode-frustrations.html
                self.text_curr = text.lower()  # .encode("utf-8")

                # Perform comparison.
                vandalism = self.determine_authorship()

                if vandalism:
                    # print "---------------------------- FLAG 2"
                    self.revision_curr = self.revision_prev  # skip revision with vandalism in history
                    self.spam_ids.append(rev_id)
                    self.spam_hashes.append(rev_hash)
                else:
                    # Add the current revision with all the information.
                    self.revisions.update({self.revision_curr.id: self.revision_curr})
                    # Update the fake revision id (position in article).
                    position += 1
            self.temp = []

    def analyse_article(self, revisions):
        position = self.revision_prev.position + 1
        # Iterate over revisions of the article.
        for revision in revisions:
            if 'texthidden' in revision or 'textmissing' in revision:
                continue

            vandalism = False
            # Update the information about the previous revision.
            self.revision_prev = self.revision_curr

            text = revision.get('*', '')
            rev_id = int(revision['revid'])
            rev_hash = revision.get('sha1', calculateHash(text))
            if rev_hash in self.spam_hashes:
                vandalism = True

            # TODO: spam detection: DELETION
            text_len = len(text)
            if not vandalism and not(revision.get('comment') and 'minor' in revision):
                # if content is not moved (flag) to different article in good faith, check for vandalism
                # if revisions have reached a certain size
                if self.revision_prev.length > PREVIOUS_LENGTH and \
                   text_len < CURR_LENGTH and \
                   ((text_len-self.revision_prev.length) / self.revision_prev.length) <= CHANGE_PERCENTAGE:
                    # VANDALISM: CHANGE PERCENTAGE - DELETION
                    vandalism = True

            if vandalism:
                # print("---------------------------- FLAG 1")
                # print(revision.position)
                # print(self.text_curr)
                self.revision_curr = self.revision_prev
                self.spam_ids.append(rev_id)
                self.spam_hashes.append(rev_hash)
            else:
                # Information about the current revision.
                self.revision_curr = Revision()
                self.revision_curr.position = position
                self.revision_curr.id = rev_id
                self.revision_curr.length = text_len
                self.revision_curr.timestamp = revision['timestamp']

                # Some revisions don't have contributor.
                contributor_id = revision.get('userid', '')  # Not Available
                contributor_name = revision.get('user', '')
                editor = contributor_id
                editor = str(editor) if editor != 0 else '0|{}'.format(contributor_name)
                self.revision_curr.editor = editor

                # Content within the revision.
                # Software should only work with Unicode strings internally, converting to a particular encoding on
                # output.
                # https://docs.python.org/2/howto/unicode.html#tips-for-writing-unicode-aware-programs
                # https://pythonhosted.org/kitchen/unicode-frustrations.html
                self.text_curr = text.lower()  # .encode("utf-8")

                # Perform comparison.
                vandalism = self.determine_authorship()

                if vandalism:
                    # print "---------------------------- FLAG 2"
                    # print revision.getId()
                    # print revision.getText()
                    # print
                    self.revision_curr = self.revision_prev  # skip revision with vandalism in history
                    self.spam_ids.append(rev_id)
                    self.spam_hashes.append(rev_hash)
                else:
                    # Add the current revision with all the information.
                    self.revisions.update({self.revision_curr.id: self.revision_curr})
                    # Update the fake revision id (position in article).
                    position += 1
            self.temp = []

    def determine_authorship(self):
        # Containers for unmatched paragraphs and sentences in both revisions.
        unmatched_sentences_curr = []
        unmatched_sentences_prev = []
        matched_sentences_prev = []
        matched_words_prev = []
        possible_vandalism = False
        vandalism = False

        # Analysis of the paragraphs in the current revision.
        unmatched_paragraphs_curr, unmatched_paragraphs_prev, matched_paragraphs_prev = \
            self.analyse_paragraphs_in_revision()

        # Analysis of the sentences in the unmatched paragraphs of the current revision.
        if unmatched_paragraphs_curr:
            unmatched_sentences_curr, unmatched_sentences_prev, matched_sentences_prev, total_sentences = \
                self.analyse_sentences_in_paragraphs(unmatched_paragraphs_curr, unmatched_paragraphs_prev)

            # TODO: spam detection
            if len(unmatched_paragraphs_curr) / len(self.revision_curr.ordered_paragraphs) > UNMATCHED_PARAGRAPH:
                # will be used to detect copy-paste vandalism - token density
                possible_vandalism = True

            # Analysis of words in unmatched sentences (diff of both texts).
            if unmatched_sentences_curr:
                matched_words_prev, vandalism = self.analyse_words_in_sentences(unmatched_sentences_curr,
                                                                                unmatched_sentences_prev,
                                                                                possible_vandalism)

        if not vandalism:
            # Add the information of 'deletion' to words
            for unmatched_sentence in unmatched_sentences_prev:
                for word_prev in unmatched_sentence.words:
                    if not word_prev.matched:
                        word_prev.outbound.append(self.revision_curr.id)
                        if self.continue_rev_ts and self.continue_rev_ts >= word_prev.timestamp:
                        # if self.continue_rev_id and self.continue_rev_id >= word_prev.origin_rev_id:
                            self.updated_prev_tokens.append(word_prev.token_id)
            if not unmatched_sentences_prev:
                # if all current paragraphs are matched
                for unmatched_paragraph in unmatched_paragraphs_prev:
                    for sentence_hash in unmatched_paragraph.sentences:
                        for sentence in unmatched_paragraph.sentences[sentence_hash]:
                            for word_prev in sentence.words:
                                if not word_prev.matched:
                                    word_prev.outbound.append(self.revision_curr.id)
                                    if self.continue_rev_ts and self.continue_rev_ts >= word_prev.timestamp:
                                        self.updated_prev_tokens.append(word_prev.token_id)

        # Reset matched structures from old revisions.
        for matched_paragraph in matched_paragraphs_prev:
            matched_paragraph.matched = False
            for sentence_hash in matched_paragraph.sentences:
                for sentence in matched_paragraph.sentences[sentence_hash]:
                    sentence.matched = False
                    for word_prev in sentence.words:
                        # first update inbound and last used info of matched words of all previous revisions
                        if not vandalism and word_prev.matched and \
                                word_prev.outbound and word_prev.outbound[-1] != self.revision_curr.id:
                            if word_prev.last_rev_id != self.revision_prev.id:
                                word_prev.inbound.append(self.revision_curr.id)
                            word_prev.last_rev_id = self.revision_curr.id
                            if self.continue_rev_ts and self.continue_rev_ts >= word_prev.timestamp:
                                self.updated_prev_tokens.append(word_prev.token_id)
                        # reset
                        word_prev.matched = False

        for matched_sentence in matched_sentences_prev:
            matched_sentence.matched = False
            for word_prev in matched_sentence.words:
                # first update inbound and last used info of matched words of all previous revisions
                if not vandalism and word_prev.matched and \
                        word_prev.outbound and word_prev.outbound[-1] != self.revision_curr.id:
                    if word_prev.last_rev_id != self.revision_prev.id:
                        word_prev.inbound.append(self.revision_curr.id)
                    word_prev.last_rev_id = self.revision_curr.id
                    if self.continue_rev_ts and self.continue_rev_ts >= word_prev.timestamp:
                        self.updated_prev_tokens.append(word_prev.token_id)
                # reset
                word_prev.matched = False

        for matched_word in matched_words_prev:
            # first update last used info of matched prev words
            # there is no inbound chance because we only diff with words of previous revision
            if not vandalism and word_prev.matched:
                if word_prev.outbound and word_prev.outbound[-1] != self.revision_curr.id:
                    word_prev.last_rev_id = self.revision_curr.id
                if self.continue_rev_ts and self.continue_rev_ts >= word_prev.timestamp:
                    self.updated_prev_tokens.append(word_prev.token_id)
            # reset
            matched_word.matched = False

        if not vandalism:
            # Add the new paragraphs to hash table of paragraphs.
            for unmatched_paragraph in unmatched_paragraphs_curr:
                if unmatched_paragraph.hash_value in self.paragraphs_ht:
                    self.paragraphs_ht[unmatched_paragraph.hash_value].append(unmatched_paragraph)
                else:
                    self.paragraphs_ht.update({unmatched_paragraph.hash_value: [unmatched_paragraph]})
                unmatched_paragraph.value = ''  # hash value is used for next rev analysis

            # Add the new sentences to hash table of sentences.
            for unmatched_sentence in unmatched_sentences_curr:
                if unmatched_sentence.hash_value in self.sentences_ht:
                    self.sentences_ht[unmatched_sentence.hash_value].append(unmatched_sentence)
                else:
                    self.sentences_ht.update({unmatched_sentence.hash_value: [unmatched_sentence]})
                unmatched_sentence.value = ''  # hash value is used for next rev analysis

        return vandalism

    def analyse_paragraphs_in_revision(self):
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
            for paragraph_prev in self.revision_prev.paragraphs.get(hash_curr, []):
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
                        # for hash_sentence_prev in paragraph_prev.sentences:
                        #     for sentence_prev in paragraph_prev.sentences[hash_sentence_prev]:
                        #         sentence_prev.matched = True
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
                            # for hash_sentence_prev in paragraph_prev.sentences:
                            #     for sentence_prev in paragraph_prev.sentences[hash_sentence_prev]:
                            #         sentence_prev.matched = True
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
        for paragraph_prev_hash in self.revision_prev.ordered_paragraphs:
            if len(self.revision_prev.paragraphs[paragraph_prev_hash]) > 1:
                s = 'p-{}-{}'.format(self.revision_prev, paragraph_prev_hash)
                self.temp.append(s)
                count = self.temp.count(s)
                paragraph_prev = self.revision_prev.paragraphs[paragraph_prev_hash][count - 1]
            else:
                paragraph_prev = self.revision_prev.paragraphs[paragraph_prev_hash][0]
            if not paragraph_prev.matched:
                unmatched_paragraphs_prev.append(paragraph_prev)

        return unmatched_paragraphs_curr, unmatched_paragraphs_prev, matched_paragraphs_prev

    def analyse_sentences_in_paragraphs(self, unmatched_paragraphs_curr, unmatched_paragraphs_prev):
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
                    # to reset 'matched words in analyse_words_in_sentences' of unmatched paragraphs and sentences
                    sentence_prev.matched = True
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
            token_density = computeAvgWordFreq(text_curr, self.revision_curr.id)
            if token_density > WORD_DENSITY:
                return matched_words_prev, possible_vandalism
            else:
                possible_vandalism = False

        # Edit consists of adding new content, not changing/removing content
        if not text_prev:
            for sentence_curr in unmatched_sentences_curr:
                for word in sentence_curr.splitted:
                    word_curr = Word()
                    word_curr.value = word
                    word_curr.token_id = self.token_id
                    word_curr.editor = self.revision_curr.editor
                    word_curr.origin_rev_id = self.revision_curr.id
                    word_curr.origin_ts = self.revision_curr.timestamp
                    word_curr.last_rev_id = self.revision_curr.id

                    sentence_curr.words.append(word_curr)
                    self.token_id += 1
                    self.revision_curr.original_adds += 1
            return matched_words_prev, possible_vandalism

        d = Differ()
        diff = list(d.compare(text_prev, text_curr))
        for sentence_curr in unmatched_sentences_curr:
            for word in sentence_curr.splitted:
                curr_matched = False
                pos = 0
                while pos < len(diff):
                    word_diff = diff[pos]
                    if word == word_diff[2:]:
                        if word_diff[0] == ' ':
                            # match
                            for word_prev in unmatched_words_prev:
                                if not word_prev.matched and word_prev.value == word:

                                    word_prev.matched = True
                                    curr_matched = True
                                    sentence_curr.words.append(word_prev)
                                    matched_words_prev.append(word_prev)
                                    diff[pos] = ''
                                    pos = len(diff) + 1
                                    break
                        elif word_diff[0] == '-':
                            # deleted
                            for word_prev in unmatched_words_prev:
                                if not word_prev.matched and word_prev.value == word:
                                    word_prev.matched = True
                                    word_prev.outbound.append(self.revision_curr.id)
                                    matched_words_prev.append(word_prev)
                                    diff[pos] = ''
                                    break
                        elif word_diff[0] == '+':
                            # a new added word
                            curr_matched = True
                            word_curr = Word()
                            word_curr.value = word
                            word_curr.token_id = self.token_id
                            word_curr.editor = self.revision_curr.editor
                            word_curr.origin_rev_id = self.revision_curr.id
                            word_curr.origin_ts = self.revision_curr.timestamp
                            word_curr.last_rev_id = self.revision_curr.id

                            sentence_curr.words.append(word_curr)
                            self.token_id += 1
                            self.revision_curr.original_adds += 1
                            diff[pos] = ''
                            pos = len(diff) + 1
                    pos += 1

                if not curr_matched:
                    # if diff returns a word as '? ...'
                    word_curr = Word()
                    word_curr.value = word
                    word_curr.token_id = self.token_id
                    word_curr.editor = self.revision_curr.editor
                    word_curr.origin_rev_id = self.revision_curr.id
                    word_curr.origin_ts = self.revision_curr.timestamp
                    word_curr.last_rev_id = self.revision_curr.id
                    sentence_curr.words.append(word_curr)

                    self.token_id += 1
                    self.revision_curr.original_adds += 1

        return matched_words_prev, possible_vandalism

    def get_revision_json(self, revision_ids, parameters, only_last_valid_revision=False, minimal=False):
        json_data = dict()
        json_data["article"] = self.title
        if not minimal:
            json_data["success"] = True
            json_data["message"] = None

        revisions = []
        positions = []
        for rev_id in revision_ids:
            if rev_id not in self.revisions:
                return {'Error': 'Revision ID ({}) does not exist or is spam or deleted!'.format(rev_id)}

        for rev_id, revision in self.revisions.items():
            if len(revision_ids) == 2:
                # FIXME revision ids are not ordered
                if rev_id < revision_ids[0] or rev_id > revision_ids[1]:
                    continue
            else:
                if rev_id != revision_ids[0]:
                    continue

            positions.append(revision.position)
            tokens = []
            revisions.append({rev_id: {"editor": revision.editor,
                                       "time": revision.timestamp,
                                       "tokens": tokens}})

            for word in iter_rev_tokens(revision):
                token = dict()
                token['str'] = word.value
                if 'rev_id' in parameters:
                    token['rev_id'] = word.origin_rev_id
                if 'editor' in parameters:
                    token['editor'] = word.editor
                if 'token_id' in parameters:
                    token['token_id'] = word.token_id
                if 'inbound' in parameters:
                    token['inbound'] = word.inbound
                if 'outbound' in parameters:
                    token['outbound'] = word.outbound
                tokens.append(token)

        json_data['revisions'] = [rs for (p, rs) in sorted(zip(positions, revisions), key=lambda pair: pair[0])] \
            if len(revision_ids) > 1 else revisions

        # import json
        # with open('tmp_pickles/{}.json'.format(self.title), 'w') as f:
        #     f.write(json.dumps(json_data, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        return json_data

    def get_deleted_tokens(self, parameters):
        response = dict()
        response["success"] = "true"
        response["article"] = self.title

        threshold = parameters[-1]
        deleted_tokens = []
        deleted_token_keys = []
        from datetime import datetime
        revisions = [(datetime.strptime(rev.timestamp, '%Y-%m-%dT%H:%M:%SZ'), rev) for rev in self.revisions.values()]
        revisions = [rev_id for time, rev_id in sorted(revisions, key=lambda x: x[0])]
        last_rev_id = revisions[-1].id
        for revision in revisions[:-1]:
            # ps_copy = deepcopy(revision.paragraphs)
            for hash_paragraph in revision.ordered_paragraphs:
                # paragraph = ps_copy[hash_paragraph].pop(0)
                paragraph = revision.paragraphs[hash_paragraph].pop(0)
                for hash_sentence in paragraph.ordered_sentences:
                    sentence = paragraph.sentences[hash_sentence].pop(0)
                    for word in sentence.words:
                        if len(word.outbound) > threshold and word.last_rev_id != last_rev_id:
                            token = dict()
                            token['str'] = word.value
                            if 'rev_id' in parameters:
                                token['rev_id'] = word.origin_rev_id
                            if 'editor' in parameters:
                                token['editor'] = word.editor
                            if 'token_id' in parameters:
                                token['token_id'] = word.token_id
                            if 'inbound' in parameters:
                                token['inbound'] = word.inbound
                            if 'outbound' in parameters:
                                token['outbound'] = word.outbound
                            key = '{}-{}'.format(word.origin_rev_id, word.token_id)
                            if key not in deleted_token_keys:
                                deleted_token_keys.append(key)
                                deleted_tokens.append(token)
        response["deleted_tokens"] = deleted_tokens

        response["threshold"] = threshold
        response["revision_id"] = last_rev_id
        response["message"] = None
        # import json
        # with open('tmp_pickles/{}_deleted_tokens.json'.format(self.title), 'w') as f:
        #     f.write(json.dumps(response, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        return response

    def get_revision_ids(self):
        response = dict()
        response["success"] = "true"
        revisions = []
        response["article"] = self.title
        from datetime import datetime
        for rev_id, rev in self.revisions.items():
            revisions.append((datetime.strptime(rev.timestamp, '%Y-%m-%dT%H:%M:%SZ'), rev_id))
        response["revisions"] = [rev_id for time, rev_id in sorted(revisions, key=lambda x: x[0])]
        response["message"] = None
        return response

    def get_revision_text(self, revision_id):
        revision = self.revisions[revision_id]
        text = []
        label_rev_ids = []
        # ps_copy = deepcopy(revision.paragraphs)
        ps_copy = revision.paragraphs(revision.paragraphs)
        for hash_paragraph in revision.ordered_paragraphs:
            paragraph = ps_copy[hash_paragraph].pop(0)
            for hash_sentence in paragraph.ordered_sentences:
                sentence = paragraph.sentences[hash_sentence].pop(0)
                for word in sentence.words:
                    text.append(word.value)
                    label_rev_ids.append(word.origin_rev_id)
        return text, label_rev_ids
