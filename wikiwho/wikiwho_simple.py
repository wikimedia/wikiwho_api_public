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
import argparse
import logging

from wikiwho.structures import Word, Sentence, Paragraph, Revision
from wikiwho.utils import calculateHash, splitIntoParagraphs, splitIntoSentences, splitIntoWords, computeAvgWordFreq


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
        self.revisions = {}
        self.rvcontinue = '0'
        self.article = article
        # Revisions to compare.
        self.revision_curr = Revision()
        # self.revision_prev = Revision()

        self.text_curr = ''
        self.token_id = 0

    def _clean(self):
        # empty attributes
        # self.revision_prev = None
        self.text_curr = ''
        self.token_id = 0

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

        # Add the information of 'deletion' to words
        # for unmatched_sentence in unmatched_sentences_prev:
        #            for word in unmatched_sentence.words:
        #                if not(word.matched):
        #                    word.deleted.append(self.revision_curr.wikipedia_id)

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
            hash_curr = calculateHash(paragraph)
            matched_curr = False

            # If the paragraph is in the previous revision,
            # update the authorship information and mark both paragraphs as matched (also in HT).
            for paragraph_prev in revision_prev.paragraphs.get(hash_curr, []):
                if not paragraph_prev.matched:
                    matched_curr = True
                    paragraph_prev.matched = True
                    matched_paragraphs_prev.append(paragraph_prev)

                    # TODO: added this (CHECK).
                    # Set all sentences and words of this paragraph as matched
                    for hash_sentence_prev in paragraph_prev.sentences:
                        for sentence_prev in paragraph_prev.sentences[hash_sentence_prev]:
                            sentence_prev.matched = True
                            for word_prev in sentence_prev.words:
                                # word_prev.freq = word_prev.freq + 1
                                # word_prev.freq.append(self.revision_curr.wikipedia_id)
                                word_prev.matched = True

                    # Add paragraph to current revision.
                    if hash_curr in self.revision_curr.paragraphs:
                        self.revision_curr.paragraphs[hash_curr].append(paragraph_prev)
                    else:
                        self.revision_curr.paragraphs.update({paragraph_prev.hash_value: [paragraph_prev]})
                    self.revision_curr.ordered_paragraphs.append(paragraph_prev.hash_value)
                    break

            # If the paragraph is not in the previous revision, but it is in an older revision
            # update the authorship information and mark both paragraphs as matched.
            if not matched_curr:
                for paragraph_prev in self.paragraphs_ht.get(hash_curr, []):
                    if not paragraph_prev.matched:
                        matched_curr = True
                        paragraph_prev.matched = True
                        matched_paragraphs_prev.append(paragraph_prev)

                        # TODO: added this (CHECK).
                        # Set all sentences and words of this paragraph as matched
                        for hash_sentence_prev in paragraph_prev.sentences:
                            for sentence_prev in paragraph_prev.sentences[hash_sentence_prev]:
                                sentence_prev.matched = True
                                for word_prev in sentence_prev.words:
                                    # word_prev.freq = word_prev.freq + 1
                                    # word_prev.freq.append(self.revision_curr.wikipedia_id)
                                    word_prev.matched = True

                        # Add paragraph to current revision.
                        if hash_curr in self.revision_curr.paragraphs:
                            self.revision_curr.paragraphs[hash_curr].append(paragraph_prev)
                        else:
                            self.revision_curr.paragraphs.update({paragraph_prev.hash_value: [paragraph_prev]})
                        self.revision_curr.ordered_paragraphs.append(paragraph_prev.hash_value)
                        break

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
            for paragraph_prev in revision_prev.paragraphs[paragraph_prev_hash]:
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

                                # TODO: CHECK this
                                for word_prev in sentence_prev.words:
                                    # word_prev.freq = word_prev.freq + 1
                                    # word_prev.freq.append(self.revision_curr.wikipedia_id)
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

                                # TODO: CHECK this
                                for word_prev in sentence_prev.words:
                                    # word_prev.freq.append(self.revision_curr.wikipedia_id)
                                    # word_prev.freq = word_prev.freq + 1
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
                for sentence_prev in paragraph_prev.sentences[sentence_prev_hash]:
                    if not sentence_prev.matched:
                        unmatched_sentences_prev.append(sentence_prev)
                        sentence_prev.matched = True  # TODO why?
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
                    word_curr.author_id = self.revision_curr.contributor_name
                    word_curr.author_name = self.revision_curr.contributor_name
                    word_curr.revision = self.revision_curr.wikipedia_id
                    word_curr.value = word
                    # word_curr.freq.append(self.revision_curr.wikipedia_id)
                    word_curr.internal_id = self.token_id
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
                                    # word_prev.freq = word_prev.freq + 1
                                    # word_prev.freq.append(self.revision_curr.wikipedia_id)
                                    word_prev.matched = True
                                    curr_matched = True
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
                                    # word_prev.deleted.append(self.revision_curr.wikipedia_id)
                                    matched_words_prev.append(word_prev)
                                    diff[pos] = ''
                                    break
                        elif word_diff[0] == '+':
                            # a new added word
                            curr_matched = True
                            word_curr = Word()
                            word_curr.value = word
                            word_curr.author_id = self.revision_curr.contributor_name
                            word_curr.author_name = self.revision_curr.contributor_name
                            word_curr.revision = self.revision_curr.wikipedia_id
                            word_curr.internal_id = self.token_id
                            # word_curr.freq.append(self.revision_curr.wikipedia_id)
                            sentence_curr.words.append(word_curr)
                            self.token_id += 1
                            diff[pos] = ''
                            pos = len(diff) + 1
                    pos += 1

                if not curr_matched:
                    # if diff returns a word as '? ...'
                    word_curr = Word()
                    word_curr.value = word
                    word_curr.author_id = self.revision_curr.contributor_name
                    word_curr.author_name = self.revision_curr.contributor_name
                    word_curr.revision = self.revision_curr.wikipedia_id
                    # word_curr.freq.append(self.revision_curr.wikipedia_id)
                    sentence_curr.words.append(word_curr)
                    word_curr.internal_id = self.token_id
                    self.token_id += 1

        return matched_words_prev, possible_vandalism

    def get_revision_json(self, revision_ids, parameters, format_="json"):
        response = dict()
        # response["success"] = "true"
        response["revisions"] = {}
        response["article"] = self.article

        for rev_id in self.revisions:
            if len(revision_ids) == 2:
                if rev_id < revision_ids[0] or rev_id > revision_ids[1]:
                    continue
            else:
                if rev_id != revision_ids[0]:
                    continue
            revision = self.revisions[rev_id]

            response["revisions"][rev_id] = {"author": revision.contributor_name,  # .encode("utf-8"),
                                             "time": revision.time,
                                             "tokens": []}
            dict_list = []
            for hash_paragraph in revision.ordered_paragraphs:
                # text = ''
                paragraph = revision.paragraphs[hash_paragraph][-1]
                for hash_sentence in paragraph.ordered_sentences:
                    sentence = paragraph.sentences[hash_sentence][-1]
                    for word in sentence.words:
                        if format_ == 'json':
                            dict_json = dict()
                            dict_json['str'] = word.value  # .encode('utf-8')
                            if 'revid' in parameters:
                                dict_json['revid'] = str(word.revision)
                            if 'author' in parameters:
                                dict_json['author'] = word.author_name  # .encode("utf-8"))
                            if 'tokenid' in parameters:
                                dict_json['tokenid'] = str(word.internal_id)
                            dict_list.append(dict_json)
            if format_ == 'json':
                response["revisions"][rev_id]["tokens"] = dict_list
        # response["message"] = None
        # with open('local/test.json', 'w') as f:
        #     f.write(json.dumps(response, indent=4, separators=(',', ': '), sort_keys=True))
        return response

    def print_revision(self, revision_ids, parameters):
        for rev_id in self.revisions:
            if len(revision_ids) == 2:
                if rev_id < revision_ids[0] or rev_id > revision_ids[1]:
                    continue
            else:
                if rev_id != revision_ids[0]:
                    continue
            revision = self.revisions[rev_id]

            print("Printing authorship for revision: {}".format(revision.wikipedia_id))
            text = []
            authors = []
            for hash_paragraph in revision.ordered_paragraphs:
                logging.debug(hash_paragraph)
                # text = ''
                paragraph = revision.paragraphs[hash_paragraph][-1]
                logging.debug(paragraph.value)
                logging.debug(len(paragraph.sentences))

                for hash_sentence in paragraph.ordered_sentences:
                    logging.debug(hash_sentence)
                    sentence = paragraph.sentences[hash_sentence][-1]
                    logging.debug(sentence.words)

                    for word in sentence.words:
                        logging.debug(word)
                        # text = text + ' ' + unicode(word.value,'utf-8') + "@@" + str(word.revision)
                        text.append(word.value)
                        authors.append(word.revision)
            print(text)
            print(authors)

    def get_revision_text(self, revision_id):
        revision = self.revisions[revision_id]
        text = []
        authors = []
        for hash_paragraph in revision.ordered_paragraphs:
            paragraph = revision.paragraphs[hash_paragraph][-1]
            for hash_sentence in paragraph.ordered_sentences:
                sentence = paragraph.sentences[hash_sentence][-1]
                for word in sentence.words:
                    text.append(word.value)
                    authors.append(word.revision)
        return text, authors


def get_args():
    parser = argparse.ArgumentParser(description='WikiWho: An algorithm for detecting attribution of authorship in '
                                                 'revisioned content.')
    # parser.add_argument('input_file', help='File to analyze')
    parser.add_argument('-i', '--ifile', help='File to analyze')
    parser.add_argument('-a', '--article', help='Article name to analyze')
    parser.add_argument('-rev', '--revision',  # type=int,
                        help='Revision to analyse. If not specified, all revisions are printed.')
    parser.add_argument('-d', '--debug', help='Run in debug mode', action='store_true')

    args = parser.parse_args()

    if not args.ifile and not args.article:
        parser.error("argument -i/--ifile or -a/--article is required")
    elif args.ifile and args.article:
        parser.error("only one of -i/--ifile or -a/--article is required")
    # check # given rev_ids
    revision_ids = args.revision
    if revision_ids:
        revision_ids = [int(x) for x in str(revision_ids).split('|')]
        if len(revision_ids) > 2:
            parser.error("Too many revision ids provided!")

    return args


def main():
    args = get_args()
    input_file = args.ifile
    article_name = args.article
    revision_ids = args.revision
    if args.debug:
        # logging.basicConfig(level=logging.DEBUG,  format='%(asctime)s - %(levelname)s - %(message)s')
        # BASIC_FORMAT = "%(levelname)s:%(name)s:%(message)s"
        logging.basicConfig(level=logging.DEBUG)

    if article_name:
        # from time import time
        # time1 = time()
        # TODO get results from ww_api, otherwise user must have a bot always.
        if revision_ids:
            revision_ids = [int(x) for x in str(revision_ids).split('|')]
            if len(revision_ids) == 2 and revision_ids[1] <= revision_ids[0]:
                revision_ids.reverse()
        from api.handler import WPHandler
        # TODO get output folder from cmd line
        pickle_folder = '' or 'local/test_pickles'
        with WPHandler(article_name, pickle_folder) as wp:
            wp.handle(revision_ids, 'json')
            wp.wikiwho.print_revision(wp.revision_ids, {'author'})
        # time2 = time()
        # print("Execution time: {}".format(time2-time1))
    elif input_file:
        print('Not implemented yet.')
        """
        from time import time
        print("Calculating authorship for: {}".format(input_file))

        time1 = time()
        wikiwho = Wikiwho()
        revisions, ordered_revisions = analyse_article(input_file)
        time2 = time()

        # pos = input_file.rfind("/")
        # print input_file[pos+1: len(input_file)-len(".xml")], time2-time1

        if revision_ids:
            print_revision(revisions[revision_ids])
        else:
            for (rev, vandalism) in ordered_revisions:
                if not vandalism:
                    print_revision(revisions[rev])
                else:
                    print("Revision {} was detected as vandalism.".format(rev))

        print("Execution time: {}".format(time2-time1))
        """

if __name__ == '__main__':
    main()
