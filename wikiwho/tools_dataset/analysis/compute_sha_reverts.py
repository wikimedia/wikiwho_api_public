"""
python wikiwho/tools/compute_sha_reverts.py -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/sha_reverts' -i '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/partitions/revisions' -d '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/server' -m 4
"""

import json
import csv
from os import listdir, mkdir
from os.path import isfile, exists
from time import strftime
from mwxml import Dump
from mwtypes.files import reader
import mwreverts
import pprint
from concurrent.futures import ProcessPoolExecutor, as_completed  # , ThreadPoolExecutor
import sys
import argparse
import logging


def get_sha_task(article_revs, dumps_folder, dump_file, article_ids):
    checksum_revisions = {}
    article_ids_count = len(article_ids)
    # Read the dump.
    dump = Dump.from_file(reader(dumps_folder + "/" + dump_file))
    # Iterate over the pages (articles) of the dump.
    for page in dump:
        # Get the page of our article.
        if page.id in article_ids:
            article_ids_count -= 1
            article_id = page.id
            checksum_revisions.update({article_id: []})
            # Iterate over the revisions.
            for revision in page:
                if revision.id in article_revs[article_id]:
                    # Build the checksum structure.
                    checksum_revisions[article_id].append((revision.sha1, {'rev_id': revision.id}))
        if not article_ids_count:
            break
    return checksum_revisions


def get_sha_parallel(article_revs, dumps_folder, dumps_articles_dict, max_workers):
    """
    To process a single input file concurrently.
    """
    # TODO FIXME, update this method.
    checksum_revisions = {}
    dump_files_iter = iter(list(dumps_articles_dict.keys()))
    files_left = len(dumps_articles_dict)
    files_all = files_left
    if max_workers > files_all:
        max_workers = files_all
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        while files_left:
            for dump_file in dump_files_iter:
                article_ids = dumps_articles_dict[dump_file]
                sub_article_revs = {}
                for i in article_ids:
                    sub_article_revs.update({i: article_revs[i]})
                    del article_revs[i]
                assert len(sub_article_revs) > 0
                job = executor.submit(get_sha_task, sub_article_revs, dumps_folder, dump_file, article_ids)
                del dumps_articles_dict[dump_file]
                jobs[job] = dump_file
                if len(jobs) == max_workers:  # limit number of jobs with max_workers
                    break

            for job in as_completed(jobs):
                files_left -= 1
                # dump_file_ = jobs[job]
                data = job.result()
                checksum_revisions.update(data)
                sys.stdout.write('\r{}-{:.3f}%'.format(files_left, ((files_all - files_left) * 100) / files_all))
                del jobs[job]
                break  # to add a new job, if there is any
    return checksum_revisions


def get_sha_sequential(article_revs, dumps_folder, dumps_articles_dict):
    """
    To process multi input files concurrently and each file sequentially.
    """
    checksum_revisions = {}
    for dump_file, article_ids in dumps_articles_dict.items():
        # sub_article_revs = {}
        # for i in article_ids:
        #     sub_article_revs.update({i: article_revs[i]})
        # assert len(sub_article_revs) > 0
        data = get_sha_task(article_revs, dumps_folder, dump_file, article_ids)
        checksum_revisions.update(data)
    return checksum_revisions


def computeSHAReverts(checksum_revisions, revs_metadata, fout):
    header = "article_id,source,target,source_editor,target_editor".split(',')
    with open(fout, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for article in checksum_revisions:

            reverts = list(mwreverts.detect(checksum_revisions[article]))
            for r in reverts:
                aux = []
                aux2 = []
                for x in r.reverteds:
                    aux.append(x['rev_id'])
                    aux2.append(revs_metadata[x['rev_id']]['editor'])
                row = [article, r.reverting['rev_id'], aux, revs_metadata[r.reverting['rev_id']]['editor'], aux2]
                writer.writerow(row)


def getDumpFile(article_id, dumps):
    for (low, high) in dumps.keys():
        if high >= article_id >= low:
            return dumps[(low, high)]
    print("Article id", str(article_id), " not found in dump")


def getRevisionFiles(filepath):

    files = listdir(filepath)
    d = {}
    for f in files:
        if not isfile(filepath+'/'+f) and not f.endswith('.7z'):
            continue
        pos = f.find("xml")
        aux = f[pos+4:-3]
        (_, low, high) = aux.split("p")
        low = int(low)
        high = int(high)
        assert high > low
        d.update({(low, high): f})

    return d


def getRevisions_old(article_file, revision_file):
    d = {}
    d2 = {}

    print("Load article id.")
    with open(article_file) as infile:
        for line in infile:
            d.update({int(line): []})

    print("Load revision meta-data.")
    with open(revision_file) as infile:
        # Example of line: {"revision_id":288382394,"timestamp":"2009-05-07T02:44:05+02:00","article_id":22677952,"editor":"6774658"}
        for line in infile:
            aux = eval(line)
            d[int(aux["article_id"])].append(int(aux["revision_id"]))
            d2.update({int(aux["revision_id"]): {"editor": aux["editor"]}})
    return d, d2


def getRevisions(revision_file):
    article_revs = {}
    metadata = {}

    # print("Load article id and load revision meta-data.")
    with open(revision_file, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        for line in reader:
            # article_id, revision_id, editor, timestamp, oadds
            if 'article_id' == line[0]:
                continue
            article_id = int(line[0])
            revision_id = int(line[1])
            if article_id in article_revs:
                article_revs[article_id].append(revision_id)
            else:
                article_revs[article_id] = [revision_id]
            metadata.update({revision_id: {"editor": line[2]}})
    return article_revs, metadata


def group_articles(dumps_articles_dict, article_revs, dumps_dict):
    for article_id in article_revs:
        article_dump_file = getDumpFile(article_id, dumps_dict)
        if article_dump_file in dumps_articles_dict:
            dumps_articles_dict[article_dump_file].append(article_id)
        else:
            dumps_articles_dict[article_dump_file] = [article_id]
    return dumps_articles_dict


def compute_sha_reverts(input_file, input_file_name, output_folder, dumps_folder, dumps_dict,
                        max_workers=None, log_folder=None):
    logger = logging.getLogger(input_file_name[:-4])
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                input_file_name,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    try:
        # print("Getting revisions ...")
        article_revs, metadata = getRevisions(input_file)
        # print(article_revs)
        # print('len article_revs', len(article_revs))

        dumps_articles_dict = {}
        group_articles(dumps_articles_dict, article_revs, dumps_dict)
        # pprint.pprint(dumps_articles_dict)
        # print(len(dumps_articles_dict))
        if len(dumps_articles_dict) == 1 and None in dumps_articles_dict:
            raise Exception('None of the articles found in dumps')

        # print("Getting SHA values ...")
        # checksum = get_sha_parallel(article_revs, dumps_folder, dumps_articles_dict, max_workers)
        checksum = get_sha_sequential(article_revs, dumps_folder, dumps_articles_dict)
        # print(checksum)
        # print('\nlen(article_revs)', len(article_revs))
        # print('len(dumps_articles_dict):', len(dumps_articles_dict))
        with open(output_folder + '/{}_checksum.json'.format(input_file_name), 'w') as f:
            # json.dump(checksum, f, ensure_ascii=False, indent=4, separators=(',', ': '), sort_keys=True)
            json.dump(checksum, f, ensure_ascii=False)

        # print("Computing SHA reverts")
        fout = '{}/{}_reverts-sha-out.csv'.format(output_folder, input_file_name)
        computeSHAReverts(checksum, metadata, fout)
    except Exception as e:
        logger.exception(input_file_name)
    return True


def get_args():
    parser = argparse.ArgumentParser(description='Compute sha reverts.')
    # parser.add_argument('input_file', help='File to analyze')
    parser.add_argument('-f', '--base_path', required=True,
                        help='Base folder where input file is and where outputs will be')
    parser.add_argument('-i', '--input_folder', required=True, help='')
    parser.add_argument('-d', '--dumps_folder', required=True, help='')
    parser.add_argument('-m', '--max_workers', type=int, help='Default is 10')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    base_path = args.base_path
    base_path = base_path[:-1] if base_path and base_path.endswith('/') else base_path
    input_folder = args.input_folder
    input_folder = input_folder[:-1] if input_folder and input_folder.endswith('/') else input_folder
    dumps_folder = args.dumps_folder
    max_workers = args.max_workers or 10
    output_folder = '{}/{}'.format(base_path, 'output')
    if not exists(output_folder):
        mkdir(output_folder)

    print("Getting revision files ...")
    dumps_dict = getRevisionFiles(dumps_folder)  # {(first_article_id, last_article_id): dumps_path, ...}
    # pprint.pprint(dumps_dict)

    # for input_file_name in listdir(input_folder):
    #     input_file = '{}/{}'.format(input_folder, input_file_name)
    #     if not isfile(input_file):
    #         continue
    #     print('Start:', input_file, strftime("%Y-%m-%d-%H:%M:%S"))
    #     compute_sha_reverts(input_file, input_file_name, output_folder, dumps_folder, dumps_dict, max_workers)
    #     print('Done:', input_file, strftime("%Y-%m-%d-%H:%M:%S"))

    # order input files
    input_files_dict = {}
    for input_file_name in listdir(input_folder):
        input_file = '{}/{}'.format(input_folder, input_file_name)
        # ex input_file_name: revisions-20161226-part1-12-5617.csv
        input_files_dict[input_file_name.split('-')[2][4:]] = [input_file, input_file_name]

    input_files = []
    for k in sorted(input_files_dict, key=int):
        input_files.append(input_files_dict[k])

    log_folder = '{}/{}'.format(output_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = logging.getLogger('future_log')
    file_handler = logging.FileHandler('{}/sha_reverts_future_at_{}.log'.format(log_folder,
                                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]

    print(max_workers)
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        files_left = len(input_files)
        files_all = len(input_files)
        files_iter = iter(input_files)
        while files_left:
            for input_file, input_file_name in files_iter:
                job = executor.submit(compute_sha_reverts, input_file, input_file_name, output_folder,
                                      dumps_folder, dumps_dict, max_workers, log_folder)
                jobs[job] = input_file_name
                if len(jobs) == max_workers:  # limit # jobs with max_workers
                    break

            for job in as_completed(jobs):
                files_left -= 1
                input_file_name_ = jobs[job]
                try:
                    data = job.result()
                except Exception as exc:
                    logger.exception(input_file_name_)

                del jobs[job]
                sys.stdout.write('\r{}-{:.3f}%'.format(files_left, ((files_all - files_left) * 100) / files_all))
                break  # to add a new job, if there is any
    print("Done: ", strftime("%Y-%m-%d-%H:%M:%S"))


if __name__ == '__main__':
    main()
