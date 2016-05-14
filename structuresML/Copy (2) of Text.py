'''
Created on Feb 20, 2013

@author: maribelacosta
'''

import hashlib

def calculateHash(text):
    return hashlib.md5(text).hexdigest()


def splitIntoParagraphs(text):
    paragraphs = text.split("\n\n")

    return paragraphs

    
def splitIntoSentences(text):
    p = text

    p = p.replace('.', '.@@@@')
    p = p.replace('\n', '\n@@@@')
    p = p.replace(';', ';@@@@')
    p = p.replace('?', '?@@@@')
    p = p.replace('!', '!@@@@')
    #p = p.replace('.{', '.||{')
    #p = p.replace('!{', '!||{')
    #p = p.replace('?{', '?||{')
    p = p.replace('>{', '>@@@@{')
    p = p.replace('}<', '}@@@@<')
    #p = p.replace('.[', '.||[')
    #p = p.replace('.]]', '.]]||')
    #p = p.replace('![', '!||[')
    #p = p.replace('?[', '?||[')
    p = p.replace('<ref', '@@@@<ref')
    p = p.replace('/ref>', '/ref>@@@@')
    
    
    while '@@@@@@@@' in p :
        p = p.replace('@@@@@@@@', '@@@@')

    sentences = p.split('@@@@')
        
    return sentences


def splitIntoWords(text):
    p = text
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

    while '||||' in p :
        p = p.replace('||||', '||')

    words = filter(lambda a : a != '', p.split('||'))
    words = ['|' if w == '@' else w for w in words]
        
    return words
    

def computeAvgWordFreq(text_list):
    
    d = {}
    
    for elem in text_list:
        if not (d.has_key(elem)):
            d.update({elem : text_list.count(elem)})
                     
    return sum(d.values())/float(len(d))
    
