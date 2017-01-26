# -*- coding: utf-8 -*-
"""
Created on Feb 20, 2013

@author: maribelacosta
"""
from __future__ import division
from __future__ import unicode_literals
import hashlib


def calculateHash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def splitIntoParagraphs(text):
    paragraphs = text.replace('\r\n', '\n').replace('\r', '\n').split("\n\n")
    return paragraphs


def splitIntoSentences(p):
    p = p.replace('. ', '.@@@@')
    p = p.replace('\n', '\n@@@@')
    p = p.replace('; ', ';@@@@')
    p = p.replace('? ', '?@@@@')
    p = p.replace('! ', '!@@@@')
    # p = p.replace('.{', '.||{')
    # p = p.replace('!{', '!||{')
    # p = p.replace('?{', '?||{')
    p = p.replace('>{', '>@@@@{')
    p = p.replace('}<', '}@@@@<')
    # p = p.replace('.[', '.||[')
    # p = p.replace('.]]', '.]]||')
    # p = p.replace('![', '!||[')
    # p = p.replace('?[', '?||[')
    p = p.replace('<ref', '@@@@<ref')
    p = p.replace('/ref>', '/ref>@@@@')

    while '@@@@@@@@' in p:
        p = p.replace('@@@@@@@@', '@@@@')

    sentences = p.split('@@@@')
    return sentences


def splitIntoWords(p):
    p = p.replace('|', '||@||')

    p = p.replace('<', '||<').replace('>', '>||')
    p = p.replace('?', '?||').replace('!', '!||').replace('.[[', '.||[[').replace('\n', '||')

    p = p.replace('.', '||.||').replace(',', '||,||').replace(';', '||;||').replace(':', '||:||').replace('?', '||?||').replace('!', '||!||')
    p = p.replace('-', '||-||').replace('/', '||/||').replace('\\', '||\\||').replace('\'\'\'', '||\'\'\'||')
    p = p.replace('(', '||(||').replace(')', '||)||')
    p = p.replace('[', '||[||').replace(']', '||]||')
    p = p.replace('{', '||{||').replace('}', '||}||')
    p = p.replace('*', '||*||').replace('#', '||#||').replace('@', '||@||').replace('&', '||&||')
    p = p.replace('=', '||=||').replace('+', '||+||').replace('_', '||_||').replace('%', '||%||')
    p = p.replace('~', '||~||')
    p = p.replace('$', '||$||')
    p = p.replace('^', '||^||')

    p = p.replace('<', '||<||').replace('>', '||>||')
    p = p.replace('[||||[', '[[').replace(']||||]', ']]')
    p = p.replace('{||||{', '{{').replace('}||||}', '}}')
    p = p.replace('||.||||.||||.||', '...').replace('/||||>', '/>').replace('<||||/', '</')
    p = p.replace('-||||-', '--')

    p = p.replace('<||||!||||--||', '||<!--||').replace('||--||||>', '||-->||')
    p = p.replace(' ', '||')

    while '||||' in p:
        p = p.replace('||||', '||')

    words = filter(lambda a: a != '', p.split('||'))
    words = ['|' if w == '@' else w for w in words]

    return words


def computeAvgWordFreq(text_list, revision_id=0):
    d = {}

    for elem in text_list:
        if elem not in d:
            d.update({elem: text_list.count(elem)})

    if '<' in d:
        del d['<']

    if '>' in d:
        del d['>']

    if 'tr' in d:
        del d['tr']

    if 'td' in d:
        del d['td']

    # if '(' in d:
    #     del d['(']
    #
    # if ')' in d:
    #     del d[')']

    if '[' in d:
        del d['[']

    if ']' in d:
        del d[']']

    if '"' in d:
        del d['"']

    # if '|' in d:
    #     del d['|']

    if '*' in d:
        del d['*']

    if '==' in d:
        del d['==']

    if d:
        return sum(d.values()) / len(d)
    else:
        return 0


def iter_rev_tokens(revision):
    # x = []
    # from copy import deepcopy
    # ps_copy = deepcopy(revision.paragraphs)
    tmp = {'p': [], 's': []}
    for hash_paragraph in revision.ordered_paragraphs:
        # paragraph = ps_copy[hash_paragraph].pop(0)
        if len(revision.paragraphs[hash_paragraph]) > 1:
            tmp['p'].append(hash_paragraph)
            paragraph = revision.paragraphs[hash_paragraph][tmp['p'].count(hash_paragraph)-1]
        else:
            paragraph = revision.paragraphs[hash_paragraph][0]
        # paragraph = revision.paragraphs[hash_paragraph].pop(0)
        tmp['s'][:] = []
        for hash_sentence in paragraph.ordered_sentences:
            if len(paragraph.sentences[hash_sentence]) > 1:
                # tmp['s'].append('{}-{}'.format(hash_paragraph, hash_sentence))  # and dont do tmp['s'][:] = []
                tmp['s'].append(hash_sentence)
                sentence = paragraph.sentences[hash_sentence][tmp['s'].count(hash_sentence)-1]
            else:
                sentence = paragraph.sentences[hash_sentence][0]
            # sentence = paragraph.sentences[hash_sentence].pop(0)
            for word in sentence.words:
                # TODO decide generator or list
                # x.append(word)
                yield word
    # return x
