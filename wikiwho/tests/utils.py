"""
Utils for wikiwho tests.
"""

article_zips = {
    'Amstrad_CPC': 'enwiki-20161101-pages-meta-history1.xml-p000000010p000002289.7z',
    'Antarctica': 'enwiki-20161101-pages-meta-history20.xml-p018754736p018984527.7z',
    'Apollo_11': 'enwiki-20161101-pages-meta-history1.xml-p000000010p000002289.7z',
    'Armenian_Genocide': 'enwiki-20161101-pages-meta-history3.xml-p000118475p000143283.7z',
    'Barack_Obama': 'enwiki-20161101-pages-meta-history5.xml-p000518010p000549136.7z',
    'Bioglass': 'enwiki-20161101-pages-meta-history9.xml-p002071291p002171781.7z',
    'Bothrops_jararaca': 'enwiki-20161101-pages-meta-history15.xml-p007991091p008292517.7z',
    'Chlorine': 'enwiki-20161101-pages-meta-history1.xml-p000004536p000006546.7z',
    'Circumcision': 'enwiki-20161101-pages-meta-history15.xml-p008592059p008821460.7z',
    'Communist_Party_of_China': 'enwiki-20161101-pages-meta-history1.xml-p000006547p000008653.7z',
    'Democritus': 'enwiki-20161101-pages-meta-history1.xml-p000006547p000008653.7z',
    'Diana,_Princess_of_Wales': 'enwiki-20161101-pages-meta-history1.xml-p000022917p000025445.7z',
    'Encryption': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'Eritrean_Defence_Forces': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'European_Free_Trade_Association': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'Evolution': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'Geography_of_El_Salvador': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'Germany': 'enwiki-20161101-pages-meta-history1.xml-p000010883p000013026.7z',
    'Home_and_Away': 'enwiki-20161101-pages-meta-history3.xml-p000161222p000169747.7z',
    'Homeopathy': 'enwiki-20161101-pages-meta-history1.xml-p000013027p000015513.7z',
    'Iraq_War': 'enwiki-20161101-pages-meta-history13.xml-p005040438p005137507.7z',
    'Islamophobia': 'enwiki-20161101-pages-meta-history3.xml-p000161222p000169747.7z',
    'Jack_the_Ripper': 'enwiki-20161101-pages-meta-history14.xml-p006733138p006933850.7z',
    'Jesus': 'enwiki-20161101-pages-meta-history7.xml-p001063241p001127973.7z',
    'KLM_destinations': 'enwiki-20161101-pages-meta-history9.xml-p002071291p002171781.7z',
    'Lemur': 'enwiki-20161101-pages-meta-history5.xml-p000466359p000489651.7z',
    'Macedonians_(ethnic_group)': 'enwiki-20161101-pages-meta-history5.xml-p000420318p000440017.7z',
    'Muhammad': 'enwiki-20161101-pages-meta-history1.xml-p000017892p000020545.7z',
    'Newberg,_Oregon': 'enwiki-20161101-pages-meta-history3.xml-p000118475p000143283.7z',
    'Race_and_intelligence': 'enwiki-20161101-pages-meta-history1.xml-p000025446p000028258.7z',
    'Rhapsody_on_a_Theme_of_Paganini': 'enwiki-20161101-pages-meta-history4.xml-p000215173p000232405.7z',
    'Robert_Hues': 'enwiki-20161101-pages-meta-history20.xml-p019630121p020023800.7z',
    "Saturn's_moons_in_fiction": 'enwiki-20161101-pages-meta-history14.xml-p006733138p006933850.7z',
    'Sergei_Korolev': 'enwiki-20161101-pages-meta-history2.xml-p000078261p000088444.7z',
    'South_Western_Main_Line': 'enwiki-20161101-pages-meta-history8.xml-p001348476p001442630.7z',
    'Special_Air_Service': 'enwiki-20161101-pages-meta-history2.xml-p000050799p000057690.7z',
    'The_Holocaust': 'enwiki-20161101-pages-meta-history16.xml-p010182412p010463377.7z',
    'Toshitsugu_Takamatsu': 'enwiki-20161101-pages-meta-history9.xml-p002071291p002171781.7z',
    'Vladimir_Putin': 'enwiki-20161101-pages-meta-history2.xml-p000032259p000034487.7z',
    'Wernher_von_Braun': 'enwiki-20161101-pages-meta-history2.xml-p000032259p000034487.7z'
}


def create_gold_xml():
    # FIXME <page> tags in xml output are duplicated
    from collections import defaultdict
    files = defaultdict(list)
    for title, file_ in article_zips.items():
        file_ = 'wikiwho/tests/test_jsons/{}'.format(file_)
        files[file_].append(title)
    header = """
    <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.5/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.5/
                 http://www.mediawiki.org/xml/export-0.5.xsd" version="0.5"
               xml:lang="en">
    <siteinfo>
    </siteinfo>
    """
    footer = "</mediawiki>"
    p = list(header)

    import os
    for xml_file, titles in files.items():
        # print(os.path.dirname(xml_file))
        os.system('7z x {} -o{}'.format(xml_file, os.path.dirname(xml_file)))
        xml_file = xml_file[:-3]
        p.append('<page>\n')
        add = False
        with open(xml_file, 'r') as f:
            for line in f:
                if not add:
                    for title in titles:
                        if '<title>{}</title>'.format(title) in line or '<title>{}</title>'.format(title.replace(' ', '_')) in line:
                            add = True
                            titles.remove(title)
                if add:
                    p.append(line)
                if add and '</page>' in line:
                    add = False
                    if not titles:
                        break
                    else:
                        p.append('<page>\n')
        os.remove(xml_file)

    p.append(footer)
    with open('gold_standard_articles_20161101.xml', 'a') as f:
        for line in p:
            f.write(line)

    print('done')
    return p
