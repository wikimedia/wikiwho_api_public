# -*- coding: utf-8 -*-
"""
Created on Feb 20, 2013

@author: maribelacosta
@author: Andriy Rodchenko
"""


class Word(object):
    """
    Implementation of the structure "Word", which includes the authorship information.
    """
    def __init__(self):
        self.author_id = 0  # Identificator of the author of the word.
        self.author_name = ''  # Username of the author of the word.
        self.revision = 0  # Revision where the word was included.
        self.value = ''  # The word (simple text).
        self.matched = False
        # self.length = 0
        # self.freq = []
        # self.deleted = []
        self.internal_id = 0
        # self.used = []

    def __repr__(self):
        return str(id(self))

    def to_dict(self):
        word = {}
        # word.update({'author' : {'id': self.author_id, 'username': self.author_name}})
        word.update({str(self.revision) : self.value})
        return word


class Sentence(object):
    """
    classdocs
    """
    def __init__(self):
        self.hash_value = ''  # The hash value of the sentence.
        self.value = ''  # The sentence (simple text).
        self.splitted = []  # List of strings composing the sentence.
        self.words = []  # List of words in the sentence. It is an array of Word.
        self.matched = False  # Flag.

    def __repr__(self):
        return str(id(self))

    def to_dict(self):
        sentence = {}
        sentence.update({'hash': self.hash_value})

        obj_words = []
        for word in self.words:
            obj_words.append(repr(word))

        sentence.update({'obj': obj_words})
        return sentence


class Paragraph(object):
    """
    classdocs
    """
    def __init__(self):
        self.hash_value = ''  # The hash value of the paragraph.
        self.value = ''  # The text of the paragraph.
        self.sentences = {}  # Dictionary of sentences in the paragraph. It is a dictionary of the form {sentence_hash : Sentence}
        self.ordered_sentences = []  # List with the hash of the sentences, ordered by hash appeareances.
        self.matched = False  # Flag.

    def __repr__(self):
        return str(id(self))

    def to_dict(self):
        paragraph = {}
        paragraph.update({'hash': self.hash_value})
        # paragraph.update({'sentences' : self.ordered_sentences})

        obj_sentences = []
        for sentence_hash in self.ordered_sentences:
            s = []
            for sentence in self.sentences[sentence_hash]:
                s.append(repr(sentence))
            obj_sentences.append(s)

        paragraph.update({'obj' : obj_sentences})

        return paragraph
        # str(hex(id(self)))
        # return "<'{0}'.'{1}' object at '{2}'>".format(self.__class__.__module__, self.__class__.__name__, hex(id(self)))


class Revision(object):
    """
    classdocs
    """

    def __init__(self):
        self.id = 0  # Fake sequential id. Starts in 0.
        self.wikipedia_id = 0  # Wikipedia revision id.
        self.contributor_id = 0  # Id of the contributor who performed the revision.
        self.contributor_name = ''  # Name of the contributor who performed the revision.
        self.contributor_ip = ''  # Name of the contributor who performed the revision.
        self.paragraphs = {}  # Dictionary of paragraphs. It is of the form {paragraph_hash : [Paragraph]}.
        self.ordered_paragraphs = []  # Ordered list of paragraph hashes.
        self.length = 0  # Content length (bytes).
        # self.content = ''  # TODO: this should be removed. Just for debugging process.
        # self.ordered_content = []  # TODO: this should be removed. Just for debugging process.
        # self.total_tokens = 0  # Number of tokens in the revision.
        self.time = 0

    def __repr__(self):
        return str(id(self))

    def to_dict(self):
        revision = {}
        # json_revision.update({'id' : revisions[revision].wikipedia_id})
        # revision.update({'author' : {'id' : self.contributor_id, 'name' : self.contributor_name}})
        # json_revision.update({'length' : revisions[revision].length})
        # json_revision.update({'paragraphs' : revisions[revision].ordered_paragraphs})
        revision.update({'obj': []})
        for paragraph_hash in self.ordered_paragraphs:
            p = []
            for paragraph in self.paragraphs[paragraph_hash]:
                p.append(repr(paragraph))
            revision['obj'].append(p)

        return revision
