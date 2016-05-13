'''
Created on Feb 20, 2013

@author: Maribel Acosta 
@author: Fabian Floeck 
@author: Andriy Rodchenko 
'''

from wmf import dump
from difflib import Differ
from time import time

from structuresML.Revision import Revision
from structuresML.Paragraph import Paragraph
from structuresML.Sentence import Sentence
from structuresML.Word import Word
from structuresML import Text

import simplejson

import urllib, urllib2
import sys
from sys import argv,exit
import getopt
import os
import time

from copy import deepcopy

import dateutil.parser
import datetime

# self.spam detection variables.
CHANGE_PERCENTAGE = -0.40
PREVIOUS_LENGTH = 1000
CURR_LENGTH = 1000
FLAG = "move"   
UNMATCHED_PARAGRAPH = 0.0
WORD_DENSITY = 10
WORD_LEN = 100

GLOBAL_ID = 0

class Wikiwho:

    def __init__(self, article):

        # Hash tables.
        self.paragraphs_ht = {}
        self.sentences_ht = {}
        self.spam = []
        self.revisions = {}

        #self.lastrev_date = dateutil.parser.parse('1900-01-01T00:00:00')
        #self.lastrev = 0

        self.rvcontinue = '0'

        self.article = article

        self.revision_curr = Revision()
        self.revision_prev = Revision()

    def analyseArticle(self, revisions):

        # Container of revisions.


        # Revisions to compare.
        revision_curr = self.revision_curr
        revision_prev = self.revision_prev
        text_curr = None

        i = 1

        # Iterate over revisions of the article.
        for revision in revisions:
	    
            if 'texthidden' in revision:
                continue
            if 'textmissing' in revision:
                continue
            #revid = revision.getId()
            timestamp = revision['timestamp']

            #timestamp_iso = dateutil.parser.parse(datetime.datetime.utcfromtimestamp(timestamp).isoformat())

            # if timestamp_iso > self.lastrev_date:
            # #print timestamp_iso, self.lastrev_date
            #     revid = revision.getId()
            #     self.lastrev_date = timestamp_iso
            #     self.lastrev = revid

            vandalism = False

            # Update the information about the previous revision.
            revision_prev = revision_curr
            #print "----"
            #print revision
            text = revision['*']

            # if text == None:
            #     text = ''

            if (revision['sha1'] == ""):
                revision['sha1'] = Text.calculateHash(text.encode("utf-8"))

            if (revision['sha1'] in self.spam):
                vandalism = True

            #TODO: self.spam detection: DELETION
            text_len = len(text)

       	    try:
                if (revision['comment'] != '' and 'minor' in revision):
                    pass
            	else:
                    if (revision_prev.length > PREVIOUS_LENGTH) and (text_len < CURR_LENGTH) and (((text_len-revision_prev.length)/float(revision_prev.length)) <= CHANGE_PERCENTAGE):
                        vandalism = True
                        revision_curr = revision_prev
            except:
                pass

            #if (vandalism):
                #print "---------------------------- FLAG 1"
                #print revision.getId()
                #print revision.getText()
                #print

            if (not vandalism):
                # Information about the current revision.
                revision_curr = Revision()
                revision_curr.id = i
                revision_curr.wikipedia_id = int(revision['revid'])
                revision_curr.length = text_len
                revision_curr.time = revision['timestamp']
                    #datetime.datetime.utcfromtimestamp(revision['timestamp']).isoformat()

                # Some revisions don't have contributor.
                #if (revision.getContributor() != None):
                try:
                    revision_curr.contributor_id = revision['userid']
                except:
                    revision_curr.contributor_id = ""
                try:
                    revision_curr.contributor_name = revision['user']
                except:
                    revision_curr.contributor_name = ""
                #else:
                #revision_curr.contributor_id = 'Not Available'
                #revision_curr.contribur_name = 'Not Available'

                # Content within the revision.
                text_curr = text.encode('utf-8')
                text_curr = text_curr.lower()
                #revision_curr.content = text_curr

                # Perform comparison.
                vandalism = self.determineAuthorship(revision_curr, revision_prev, text_curr)


                if (not vandalism):
                    # Add the current revision with all the information.
                    self.revisions.update({revision_curr.wikipedia_id : revision_curr})
                    # Update the fake revision id.
                    i = i+1

                else:
                    #print "---------------------------- FLAG 2"
                    #print revision.getId()
                    #print revision.getText()
                    #print
                    revision_curr = revision_prev
                    self.spam.append(revision['sha1'])

        self.revision_prev = revision_prev
        self.revision_curr = revision_curr


    def determineAuthorship(self, revision_curr, revision_prev, text_curr):

        # Containers for unmatched paragraphs and sentences in both revisions.
        unmatched_sentences_curr = []
        unmatched_sentences_prev = []
        matched_sentences_prev = []
        matched_words_prev = []
        possible_vandalism = False
        vandalism = False

        # Analysis of the paragraphs in the current revision.
        (unmatched_paragraphs_curr, unmatched_paragraphs_prev, matched_paragraphs_prev) = self.analyseParagraphsInRevision(revision_curr, revision_prev, text_curr)

        # Analysis of the sentences in the unmatched paragraphs of the current revision.
        if (len(unmatched_paragraphs_curr)>0):
            (unmatched_sentences_curr, unmatched_sentences_prev, matched_sentences_prev, _) = self.analyseSentencesInParagraphs(unmatched_paragraphs_curr, unmatched_paragraphs_prev, revision_curr)

            #TODO: self.spam detection
            if (len(unmatched_paragraphs_curr)/float(len(revision_curr.ordered_paragraphs)) > UNMATCHED_PARAGRAPH):
                possible_vandalism = True

            # Analysis of words in unmatched sentences (diff of both texts).
            if (len(unmatched_sentences_curr)>0):
                (matched_words_prev, vandalism) = self.analyseWordsInSentences(unmatched_sentences_curr, unmatched_sentences_prev, revision_curr, possible_vandalism)

        # Add the information of 'deletion' to words
        #for unmatched_sentence in unmatched_sentences_prev:
        #            for word in unmatched_sentence.words:
        #                if not(word.matched):
        #                    word.deleted.append(revision_curr.wikipedia_id)

        # Reset matched structures from old revisions.
        for matched_paragraph in matched_paragraphs_prev:
            matched_paragraph.matched = False
            for sentence_hash in matched_paragraph.sentences.keys():
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




        if (not vandalism):
            # Add the new paragraphs to hash table of paragraphs.
            for unmatched_paragraph in unmatched_paragraphs_curr:
                if (unmatched_paragraph.hash_value in self.paragraphs_ht.keys()):
                    self.paragraphs_ht[unmatched_paragraph.hash_value].append(unmatched_paragraph)
                else:
                    self.paragraphs_ht.update({unmatched_paragraph.hash_value : [unmatched_paragraph]})

                # Add the new sentences to hash table of sentences.
            for unmatched_sentence in unmatched_sentences_curr:
                if (unmatched_sentence.hash_value in self.sentences_ht.keys()):
                    self.sentences_ht[unmatched_sentence.hash_value].append(unmatched_sentence)
                else:
                    self.sentences_ht.update({unmatched_sentence.hash_value : [unmatched_sentence]})

        return vandalism

    def analyseParagraphsInRevision(self, revision_curr, revision_prev, text_curr):

        # Containers for unmatched and matched paragraphs.
        unmatched_paragraphs_curr = []
        unmatched_paragraphs_prev = []
        matched_paragraphs_prev = []

        # Split the text of the current into paragraphs.
        paragraphs = Text.splitIntoParagraphs(text_curr)

        # Iterate over the paragraphs of the current version.
        for paragraph in paragraphs:

            # Build Paragraph structure and calculate hash value.
            paragraph = paragraph.strip()
            hash_curr = Text.calculateHash(paragraph)
            matched_curr = False

            # If the paragraph is in the previous revision,
            # update the authorship information and mark both paragraphs as matched (also in HT).
            if (hash_curr in revision_prev.ordered_paragraphs):

                for paragraph_prev in revision_prev.paragraphs[hash_curr]:
                    if (not paragraph_prev.matched):
                        matched_curr = True
                        paragraph_prev.matched = True
                        matched_paragraphs_prev.append(paragraph_prev)

                        # TODO: added this (CHECK).
                        for hash_sentence_prev in paragraph_prev.sentences.keys():
                            for sentence_prev in paragraph_prev.sentences[hash_sentence_prev]:
                                sentence_prev.matched = True
                                for word_prev in sentence_prev.words:
                                    #word_prev.freq = word_prev.freq + 1
                                    #word_prev.freq.append(revision_curr.wikipedia_id)
                                    word_prev.matched = True

                        # Add paragraph to current revision.
                        if (hash_curr in revision_curr.paragraphs.keys()):
                            revision_curr.paragraphs[paragraph_prev.hash_value].append(paragraph_prev)
                            revision_curr.ordered_paragraphs.append(paragraph_prev.hash_value)
                        else:
                            revision_curr.paragraphs.update({paragraph_prev.hash_value : [paragraph_prev]})
                            revision_curr.ordered_paragraphs.append(paragraph_prev.hash_value)

                        break


            # If the paragraph is not in the previous revision, but it is in an older revision
            # update the authorship information and mark both paragraphs as matched.
            if ((not matched_curr) and (hash_curr in self.paragraphs_ht)):
                for paragraph_prev in self.paragraphs_ht[hash_curr]:
                    if (not paragraph_prev.matched):
                        matched_curr = True
                        paragraph_prev.matched = True
                        matched_paragraphs_prev.append(paragraph_prev)

                        # TODO: added this (CHECK).
                        for hash_sentence_prev in paragraph_prev.sentences.keys():
                            for sentence_prev in paragraph_prev.sentences[hash_sentence_prev]:
                                sentence_prev.matched = True
                                for word_prev in sentence_prev.words:
                                    #word_prev.freq = word_prev.freq + 1
                                    #word_prev.freq.append(revision_curr.wikipedia_id)
                                    word_prev.matched = True


                        # Add paragraph to current revision.
                        if (hash_curr in revision_curr.paragraphs.keys()):
                            revision_curr.paragraphs[paragraph_prev.hash_value].append(paragraph_prev)
                            revision_curr.ordered_paragraphs.append(paragraph_prev.hash_value)
                        else:
                            revision_curr.paragraphs.update({paragraph_prev.hash_value : [paragraph_prev]})
                            revision_curr.ordered_paragraphs.append(paragraph_prev.hash_value)

                        break

            # If the paragraph did not match with previous revisions,
            # add to container of unmatched paragraphs for further analysis.
            if (not matched_curr):
                paragraph_curr = Paragraph()
                paragraph_curr.hash_value = Text.calculateHash(paragraph)
                paragraph_curr.value = paragraph

                revision_curr.ordered_paragraphs.append(paragraph_curr.hash_value)

                if (paragraph_curr.hash_value in revision_curr.paragraphs.keys()):
                    revision_curr.paragraphs[paragraph_curr.hash_value].append(paragraph_curr)
                else:
                    revision_curr.paragraphs.update({paragraph_curr.hash_value : [paragraph_curr]})

                unmatched_paragraphs_curr.append(paragraph_curr)


        # Identify unmatched paragraphs in previous revision for further analysis.
        for paragraph_prev_hash in revision_prev.ordered_paragraphs:
            for paragraph_prev in revision_prev.paragraphs[paragraph_prev_hash]:
                if (not paragraph_prev.matched):
                    unmatched_paragraphs_prev.append(paragraph_prev)

        return (unmatched_paragraphs_curr, unmatched_paragraphs_prev, matched_paragraphs_prev)


    def analyseSentencesInParagraphs(self,unmatched_paragraphs_curr, unmatched_paragraphs_prev, revision_curr):

        # Containers for unmatched and matched sentences.
        unmatched_sentences_curr = []
        unmatched_sentences_prev = []
        matched_sentences_prev = []
        total_sentences = 0


        # Iterate over the unmatched paragraphs of the current revision.
        for paragraph_curr in unmatched_paragraphs_curr:

            # Split the current paragraph into sentences.
            sentences = Text.splitIntoSentences(paragraph_curr.value)

            # Iterate over the sentences of the current paragraph
            for sentence in sentences:

                # Create the Sentence structure.
                sentence = sentence.strip()
                sentence = ' '.join(Text.splitIntoWords(sentence))
                hash_curr = Text.calculateHash(sentence)
                matched_curr = False
                total_sentences = total_sentences + 1


                # Iterate over the unmatched paragraphs from the previous revision.
                for paragraph_prev in unmatched_paragraphs_prev:
                    if (hash_curr in paragraph_prev.sentences.keys()):
                        for sentence_prev in paragraph_prev.sentences[hash_curr]:

                            if (not sentence_prev.matched):

                                matched_one = False
                                matched_all = True
                                for word_prev in sentence_prev.words:
                                    if (word_prev.matched):
                                        matched_one = True
                                    else:
                                        matched_all = False

                                if not(matched_one):
                                    sentence_prev.matched = True
                                    matched_curr = True
                                    matched_sentences_prev.append(sentence_prev)

                                    # TODO: CHECK this
                                    for word_prev in sentence_prev.words:
                                        #word_prev.freq = word_prev.freq + 1
                                        #word_prev.freq.append(revision_curr.wikipedia_id)
                                        word_prev.matched = True

                                    # Add the sentence information to the paragraph.
                                    if (hash_curr in paragraph_curr.sentences.keys()):
                                        paragraph_curr.sentences[hash_curr].append(sentence_prev)
                                        paragraph_curr.ordered_sentences.append(sentence_prev.hash_value)
                                    else:
                                        paragraph_curr.sentences.update({sentence_prev.hash_value : [sentence_prev]})
                                        paragraph_curr.ordered_sentences.append(sentence_prev.hash_value)
                                    break
                                elif (matched_all):
                                    sentence_prev.matched = True
                                    matched_sentences_prev.append(sentence_prev)

                        if (matched_curr):
                            break


                # Iterate over the hash table of sentences from old revisions.
                if ((not matched_curr) and (hash_curr in self.sentences_ht.keys())):
                    for sentence_prev in self.sentences_ht[hash_curr]:
                        if (not sentence_prev.matched):
                            matched_one = False
                            matched_all = True
                            for word_prev in sentence_prev.words:
                                if (word_prev.matched):
                                    matched_one = True
                                else:
                                    matched_all = False

                            if not(matched_one):

                                sentence_prev.matched = True
                                matched_curr = True
                                matched_sentences_prev.append(sentence_prev)

                                # TODO: CHECK this
                                for word_prev in sentence_prev.words:
                                    #word_prev.freq.append(revision_curr.wikipedia_id)
                                    #word_prev.freq = word_prev.freq + 1
                                    word_prev.matched = True

                                # Add the sentence information to the paragraph.
                                if (hash_curr in paragraph_curr.sentences.keys()):
                                    paragraph_curr.sentences[hash_curr].append(sentence_prev)
                                    paragraph_curr.ordered_sentences.append(sentence_prev.hash_value)
                                else:
                                    paragraph_curr.sentences.update({sentence_prev.hash_value : [sentence_prev]})
                                    paragraph_curr.ordered_sentences.append(sentence_prev.hash_value)
                                break
                            elif (matched_all):
                                sentence_prev.matched = True
                                matched_sentences_prev.append(sentence_prev)


                # If the sentence did not match, then include in the container of unmatched sentences for further analysis.
                if (not matched_curr):
                    sentence_curr = Sentence()
                    sentence_curr.value = sentence
                    sentence_curr.hash_value = hash_curr

                    paragraph_curr.ordered_sentences.append(sentence_curr.hash_value)
                    if (sentence_curr.hash_value in paragraph_curr.sentences.keys()):
                        paragraph_curr.sentences[sentence_curr.hash_value].append(sentence_curr)
                    else:
                        paragraph_curr.sentences.update({sentence_curr.hash_value : [sentence_curr]})

                    unmatched_sentences_curr.append(sentence_curr)


        # Identify the unmatched sentences in the previous paragraph revision.
        for paragraph_prev in unmatched_paragraphs_prev:
            for sentence_prev_hash in paragraph_prev.ordered_sentences:
                for sentence_prev in paragraph_prev.sentences[sentence_prev_hash]:
                    if (not sentence_prev.matched):
                        unmatched_sentences_prev.append(sentence_prev)
                        sentence_prev.matched = True
                        matched_sentences_prev.append(sentence_prev)


        return (unmatched_sentences_curr, unmatched_sentences_prev, matched_sentences_prev, total_sentences)


    def analyseWordsInSentences(self, unmatched_sentences_curr, unmatched_sentences_prev, revision_curr, possible_vandalism):

        global GLOBAL_ID

        matched_words_prev = []
        unmatched_words_prev = []

        # Split sentences into words.
        text_prev = []
        for sentence_prev in unmatched_sentences_prev:
            for word_prev in sentence_prev.words:
                if (not word_prev.matched):
                    text_prev.append(word_prev.value)
                    unmatched_words_prev.append(word_prev)

        text_curr = []
        for sentence_curr in unmatched_sentences_curr:
            splitted = Text.splitIntoWords(sentence_curr.value)
            text_curr.extend(splitted)
            sentence_curr.splitted.extend(splitted)

        # Edit consists of removing sentences, not adding new content.
        if (len(text_curr) == 0):
            return (matched_words_prev, False)

        # self.spam detection.
        if (possible_vandalism):

            density = Text.computeAvgWordFreq(text_curr, revision_curr.wikipedia_id)

            if (density > WORD_DENSITY):
                return (matched_words_prev, possible_vandalism)
            else:
                possible_vandalism = False

        if (len(text_prev) == 0):
            for sentence_curr in unmatched_sentences_curr:
                for word in sentence_curr.splitted:
                    word_curr = Word()
                    word_curr.author_id = revision_curr.contributor_name
                    word_curr.author_name = revision_curr.contributor_name
                    word_curr.revision = revision_curr.wikipedia_id
                    word_curr.value = word
                    #word_curr.freq.append(revision_curr.wikipedia_id)
                    word_curr.internal_id = GLOBAL_ID
                    sentence_curr.words.append(word_curr)
                    GLOBAL_ID = GLOBAL_ID + 1


            return (matched_words_prev, possible_vandalism)

        d = Differ()
        diff = list(d.compare(text_prev, text_curr))


        for sentence_curr in unmatched_sentences_curr:

            for word in sentence_curr.splitted:
                curr_matched = False
                pos = 0

                while (pos < len(diff)):

                    word_diff = diff[pos]

                    if (word == word_diff[2:]):

                        if (word_diff[0] == ' '):
                            for word_prev in unmatched_words_prev:
                                if ((not word_prev.matched) and (word_prev.value == word)):
                                    #word_prev.freq = word_prev.freq + 1
                                    #word_prev.freq.append(revision_curr.wikipedia_id)
                                    word_prev.matched = True
                                    curr_matched = True
                                    sentence_curr.words.append(word_prev)
                                    matched_words_prev.append(word_prev)
                                    diff[pos] = ''
                                    pos = len(diff)+1
                                    break

                        elif (word_diff[0] == '-'):
                            for word_prev in unmatched_words_prev:
                                if ((not word_prev.matched) and (word_prev.value == word)):
                                    word_prev.matched = True
                                    #word_prev.deleted.append(revision_curr.wikipedia_id)
                                    matched_words_prev.append(word_prev)
                                    diff[pos] = ''
                                    break

                        elif (word_diff[0] == '+'):
                            curr_matched = True
                            word_curr = Word()
                            word_curr.value = word
                            word_curr.author_id = revision_curr.contributor_name
                            word_curr.author_name = revision_curr.contributor_name
                            word_curr.revision = revision_curr.wikipedia_id
                            word_curr.internal_id = GLOBAL_ID
                            #word_curr.freq.append(revision_curr.wikipedia_id)
                            sentence_curr.words.append(word_curr)
                            GLOBAL_ID = GLOBAL_ID + 1

                            diff[pos] = ''
                            pos = len(diff)+1

                    pos = pos + 1

                if not(curr_matched):
                    word_curr = Word()
                    word_curr.value = word
                    word_curr.author_id = revision_curr.contributor_name
                    word_curr.author_name = revision_curr.contributor_name
                    word_curr.revision = revision_curr.wikipedia_id
                    #word_curr.freq.append(revision_curr.wikipedia_id)
                    sentence_curr.words.append(word_curr)
                    word_curr.internal_id = GLOBAL_ID
                    GLOBAL_ID = GLOBAL_ID + 1

        return (matched_words_prev, possible_vandalism)

    @staticmethod
    def printFail(message = None, format ="json"):
        import os
        response = {}
        response["success"] = "false"
        response["revisions"] = None
        response["article"] = None
        #dict_list = None

        if format == 'json':
            #response["tokens"] = dict_list
            response["message"] = message
            print simplejson.dumps(response)
        sys.exit()
        #os._exit(1)

    def printRevision(self, revisions, params, format = "json"):


        response = {}
        response["success"] = "true"

        response["revisions"] = {}
        response["article"] = self.article
        for revid in self.revisions:

            if len(revisions) == 2:
                if revid < revisions[0] or revid > revisions[1]:
                    continue
            else:
                if revid != revisions[0]:
                    continue


            revision = self.revisions[revid]

            response["revisions"][revid] = {"author":revision.contributor_name.encode("utf-8"), "time":revision.time, "tokens":[]}
            dict_list =[]
            #print "format :"
            #print format
            for hash_paragraph in revision.ordered_paragraphs:

                text = ''

                #p_copy = deepcopy(revision.paragraphs[hash_paragraph])
                #paragraph = p_copy.pop(0) # "paragraph" will contain the hash for the paragraph.

                para = revision.paragraphs[hash_paragraph]
                paragraph = para[-1]

                for hash_sentence in paragraph.ordered_sentences:
                    sentence = paragraph.sentences[hash_sentence][-1]
                    #sentence = paragraph.sentences[hash_sentence].pop(0) #"sentence" will contain the hash for the sentence.
                    for word in sentence.words:
                        # if format == 'normal':
                        #    if (word.revision == lst_revision):
                        #        text = text + ' ' + unicode(word.value,'utf-8')
                        #    else:
                        #        text = text + ' ' + "@@@@" + str(word.revision) +',' + word.author_name + "@@@@" + unicode(word.value,'utf-8')
                        #    lst_revision = word.revision
                        #    authors.append(word.revision)
                        if format == 'json':
                            dict_json = {}
                            #ss = unicode(word.value,'utf-8')
                            ss = word.value
                            dict_json['str'] = ss#.encode('utf-8')
                            dict_json['revid'] = str(word.revision)
                            if 'author' in params:
                                dict_json['author'] = str(word.author_name.encode("utf-8"))
                            if 'tokenid' in params:
                                dict_json['tokenid'] = str(word.internal_id)
                            dict_list.append(dict_json)
            # if format == 'normal':
            #     print text.encode('utf-8')
            if format == 'json':
                response["revisions"][revid]["tokens"] = dict_list
        response["message"] = None
        print simplejson.dumps(response)


    # def printRevision(self,revision):
    #
    #     print "Printing authorhship for revision: ", revision.wikipedia_id
    #     text = []
    #     authors = []
    #     ids = []
    #     freqs = []
    #     authors_id = []
    #     len_paragraph = []
    #     len_sentence = []
    #     deletions = []
    #
    #     for hash_paragraph in revision.ordered_paragraphs:
    #         #print hash_paragraph
    #         #text = ''
    #
    #         p_copy = deepcopy(revision.paragraphs[hash_paragraph])
    #         paragraph = p_copy.pop(0)
    #
    #         p_len = 0
    #
    #         for p in paragraph.sentences.keys():
    #             p_len = p_len + len(paragraph.sentences[p][0].words)
    #             #print "p", p
    #         #print "p", p_len
    #
    #         #print paragraph.value
    #         #print len(paragraph.sentences)
    #         for hash_sentence in paragraph.ordered_sentences:
    #             #print hash_sentence
    #             sentence = paragraph.sentences[hash_sentence].pop(0)
    #             #print sentence.words
    #
    #             for word in sentence.words:
    #                 #print word
    #                 #text = text + ' ' + unicode(word.value,'utf-8') + "@@" + str(word.revision)
    #                 text.append(word.value)
    #                 authors.append(word.revision)
    #                 authors_id.append(word.author_id)
    #                 ids.append(word.internal_id)
    #                 i = 0
    #                 while i < len(word.freq):
    #                     if word.freq[i] > revision.wikipedia_id:
    #                         break
    #                     i = i+1
    #                 freqs.append(i)
    #                 len_paragraph.append(p_len)
    #                 len_sentence.append(len(sentence.words))
    #                 deletions.append(word.deleted)
    #
    #     print text
    #     print authors
    #     print authors_id
    #     print ids
    #     print freqs
    #     print len_paragraph
    #     print len_sentence
    #     print deletions



def main(my_argv):
    inputfile = ''
    revision = None
    
    if (len(my_argv) <= 3):
        try:
            opts, args = getopt.getopt(my_argv,"i:",["ifile="])
        except getopt.GetoptError:
            print 'Usage: Wikiwho_simple.py -i <inputfile> [-rev <revision_id>]'
            exit(2)
    else:
        try:
            opts, args = getopt.getopt(my_argv,"i:r:",["ifile=","revision="])
        except getopt.GetoptError:
            print 'Usage: Wikiwho_simple.py -i <inputfile> [-rev <revision_id>]'
            exit(2)
    
    for opt, arg in opts:
    
	if opt in ('-h', "--help"):
            print "WikiWho: An algorithm for detecting attribution of authorship in revisioned content"
            print
            print 'Usage: Wikiwho_simple.py -i <inputfile> [-rev <revision_id>]'
            print "-i --ifile File to analyze"
            print "-r --revision Revision to analyse. If not specified, the last revision is printed."
            print "-h --help This help."
            exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-r", "--revision"):
            revision = arg
         
    return (inputfile,revision)
   
if __name__ == '__main__':
    print "wo"
    ##main(sys.argv)
    #file_name = "Hermann_Beitzke"

    #rev = 620303041

    wikiwho = Wikiwho("Gamergate")

    #url ='http://en.wikipedia.org/w/index.php?title=Special:Export'
    #	timestamp = '2004-04-20T11:56:34Z'
    #TODO: the timestamp thing doesnt seem right here -- as it is a function
    #timestamp = '2014-04-12T07:50:44Z'
    #timestamp = '1900-00-00T00:00:00'
    #enc = {'pages':"Hermann_Beitzke",'offset':timestamp,'action':'submit'}

    #	enc = {'pages':art,'limit':'47','action':'submit'}
    #TODO: the code needs some error handling ... what happens if the request cant be finished?
    #data = urllib.urlencode(enc)
    #req = urllib2.Request(url,data)
    #response = urllib2.urlopen(req)


    #revisions = wikiwho.analyseArticle(response)

    #wikiwho.printRevision(revisions[rev])

    #print wikiwho.lastrev_date

    #(file_name, revision) = main(sys.argv[1:])
    #
    # print "Calculating authorship for:", file_name
    # time1 = time()
    
    print sys.argv[1]

    revisions = wikiwho.analyseArticle(open(sys.argv[1]))
    # time2 = time()
    #
    # if (revision != None and revision!='all'):
    #     printRevision(revisions[int(revision)])
    # elif (revision != None and revision=='all'):
    #     ordered = revisions.keys()
    #     ordered.sort()
    #     for rev in ordered:
    #         printRevision(revisions[rev])
    # else:
    #     rev_ids = revisions.keys()
    #     printRevision(revisions[max(rev_ids)])
    #
    #
    # print "Execution time:", time2-time1
    
    

    
