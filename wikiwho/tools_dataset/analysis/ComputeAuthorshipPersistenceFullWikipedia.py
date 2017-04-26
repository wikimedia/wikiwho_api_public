import sys
import csv
import argparse
from collections import defaultdict
from dateutil import parser
# from django.utils.dateparse import parse_datetime
from os.path import realpath, exists
from os import listdir, mkdir
from time import strftime
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging


def get_logger(name, log_folder, is_process=True, is_set=True):
    logger = logging.getLogger(name)
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                name,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    if is_process:
        format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
    else:
        format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    if is_set:
        logger.handlers = [file_handler]
    else:
        logger.addHandler(file_handler)
    return logger


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m+1
        # yield '{}-{}'.format(m+1, y)


def computePersistence(article_file, revision_file, token_file, bot_file, f1):
    """
    per user group
    """
    base = 48 * 3600  # hours

    # Main structures.
    art = {}  
    botList = {}
    # periods = []
    #notsurvived_agg = defaultdict(int)
    #oadds = defaultdict(int)
    
    # Number of tokens added by type of users. 
    oadds_ip = defaultdict(int)
    oadds_reg = defaultdict(int)
    oadds_bot = defaultdict(int)
    
    # Number of tokens that did not survived (a given time frame) by type of user.
    notsurvived_ip = defaultdict(int)
    notsurvived_reg = defaultdict(int)
    notsurvived_bot = defaultdict(int)
        
    print("Load article id.") 
    with open(article_file) as infile:
        next(infile, None)  # skip the header
        for line in infile:
            art.update({int(line): {"revs": {}}})

    print("Load revision meta-data.")
    with open(revision_file) as csvfile:
        # Example of line: article_id,revision_id,editor,timestamp,oadds
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for line in infile:
            aux = line
            aux[0] = int(aux[0])  # article id
            # art[aux[0]]["revs"].update({int(aux[1]): {"editor": aux[2], "timestamp": parser.parse(aux[3]),
            #                                           "oadds": [], "token-ins": [], "token-outs": []}})
            art[aux[0]]["revs"].update({int(aux[1]): {"editor": aux[3], "timestamp": parser.parse(aux[2]),
                                                      "oadds": [], "token-ins": [], "token-outs": []}})

    print("Load bot list.")
    with open(bot_file) as infile:
        next(infile, None)
        for line in infile:
            aux = line.split(",", 1)
            botList.update({aux[0]: aux[1]})  # {bot_id: bot_name}
    
    print("Load token meta-data.")
    with open(token_file) as csvfile:
        # Example of line CSV: page_id,last_rev_id,token_id,str,origin_rev_id,in,out
        infile = csv.reader(csvfile, delimiter=',')
        # next(infile, None)  # skip the headers
        for line in infile:
            # Get line.
            aux = line
            aux[0] = int(aux[0])  # article_id
            aux[4] = int(aux[4])  # label_revision_id (origin)
            # aux[5] = eval(aux[5].replace("{", "[").replace("}", "]"))  # inbound
            aux[6] = eval(aux[6].replace("{", "[").replace("}", "]"))  # outbound
            
            # Getting type of editor of the origin revision.
            isIP = False
            isBot = False
            #isReg = False
            editor = art[aux[0]]["revs"][aux[4]]["editor"]
            if editor[:2] == "0|":
                isIP = True
                #print("Editor is IP", editor)
            elif editor in botList.keys():
                isBot = True
                #print("Editor is bot", editor, botList[editor])
            #else:
            #    print("Editor is regular user")
            #    isReg = True
                
            # Cleaning outbound.
            f6 = aux[6]
            outbound = []
            for rev in f6:
                if rev in art[aux[0]]["revs"]:
                    outbound.append(rev)
            
            t1 = art[aux[0]]["revs"][aux[4]]["timestamp"]  # Timestamp of origin
            
            period = (t1.year, t1.month) #str(t1.year) +"-"+ str(t1.month)
            # periods.append(period)
            
            if isIP:
                oadds_ip[period] += 1
            elif isBot:
                oadds_bot[period] += 1
            else:
                oadds_reg[period] += 1
             
            if len(outbound) > 0:
                firstout = outbound[0]
                t2 = art[aux[0]]["revs"][firstout]["timestamp"]  # Timestamp of first out
                secs = (t2 - t1).total_seconds()
                
                if (secs < base):
                    #print aux["f3"], aux["f2"], t1, firstout, t2
                    if isIP:
                        notsurvived_ip[period] += 1
                    elif isBot:
                        notsurvived_bot[period] += 1
                    else:
                        notsurvived_reg[period] += 1
                    
                #else:
                #    survived_agg[period] += 1 
                    
            #else:
            #    survived_agg[period] += 1
                
    print("Printing persistence.")
    out2 = open(f1, 'w')
    out2.write("year,month,user_type,not_survived_48h,oadds\n")
    # for t in set(periods):
    for t in month_year_iter(1, 2001, 12, 2016):
        (year, month) = t
        # Print data of IP
        out2.write(str(year) + "," + str(month) + ",ip," + str(notsurvived_ip[t]) + "," + str(oadds_ip[t]) + "\n")
        # Print data of bots
        out2.write(str(year) + "," + str(month) + ",bot," + str(notsurvived_bot[t]) + "," + str(oadds_bot[t]) + "\n")
        # Print data of regular users
        out2.write(str(year) + "," + str(month) + ",regular," + str(notsurvived_reg[t]) + "," + str(oadds_reg[t]) + "\n")
    out2.close()


def load_articles_revisions(article_file, revision_file):
    art = {}  # {page_id: {'revs': {rev_id: ['editor', 'timestamp']}}, ..}
    # print("Load article id.")
    with open(article_file) as infile:
        next(infile, None)  # skip the header
        for line in infile:
            art.update({int(line): {"revs": {}}})

    # print("Load revision meta-data.")
    with open(revision_file) as csvfile:
        # Example of line with oadds: article_id,revision_id,editor,timestamp,oadds
        # Example of line: page_id,rev_id,timestamp,editor
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for aux in infile:
            aux[0] = int(aux[0])  # article id
            # art[aux[0]]["revs"].update({int(aux[1]): {"editor": aux[2], "timestamp": parser.parse(aux[3]),
            #                                           "oadds": [], "token-ins": [], "token-outs": []}})
            # art[aux[0]]["revs"].update({int(aux[1]): {"editor": aux[3], "timestamp": parser.parse(aux[2])}})
            art[aux[0]]["revs"].update({int(aux[1]): [aux[3], parser.parse(aux[2])]})
    return art


def load_bots(bot_file):
    bots = {}
    # print("Load bot list.")
    with open(bot_file) as infile:
        next(infile, None)
        for line in infile:
            aux = line.split(",", 1)
            bots.update({aux[0]: aux[1]})  # {bot_id: bot_name}
    return bots


def compute_persistence_per_user(article_file, revision_file, token_file, bot_file, output_file):
    """
    per user.
    """
    # Main structures.
    art = load_articles_revisions(article_file, revision_file)
    # botList = load_bots(bot_file)
    periods = defaultdict(dict)  # {y-m: {editor: [oadds, not_survived], editor2: ..}, y-m: ..}
    # periods_deletion = defaultdict(dict)  # {m-y: {editor: [deletion, deletion_not_survived], editor2: ..}, m-y2: ..}

    # print("Load token meta-data.")
    seconds_limit = 48 * 3600  # hours
    with open(token_file) as csvfile:
        # Example of line CSV: page_id,last_rev_id,token_id,str,origin_rev_id,in,out
        infile = csv.reader(csvfile, delimiter=',')
        # next(infile, None)  # skip the headers
        for line in infile:
            # Get line.
            page_id = int(line[0])
            label_revision_id = int(line[4])  # origin
            outbound = eval(line[6].replace("{", "[").replace("}", "]"))

            article_revs = art[page_id]["revs"]  # {rev_id: [editor, timestamp], }
            # editor and timestamp of origin
            editor_origin, ts_origin = article_revs[label_revision_id]
            # Cleaning outbound.
            outbound_cleaned = []
            for rev in outbound:
                if rev in article_revs:
                    outbound_cleaned.append(rev)
            not_survived = 0
            if len(outbound_cleaned) > 0:
                first_out_rev = outbound_cleaned[0]
                editor_first_out, ts_first_out = article_revs[first_out_rev]  # editor and timestamp of first out rev
                secs = (ts_first_out - ts_origin).total_seconds()
                if secs < seconds_limit:
                    # editors_not_survived[editor] += 1
                    not_survived = 1

                # # deletion analysis start
                # inbound = eval(line[5].replace("{", "[").replace("}", "]"))
                # inbound_cleaned = []
                # for rev in inbound:
                #     if rev in article_revs:
                #         inbound_cleaned.append(rev)
                # period_deletion = (ts_first_out.year, ts_first_out.month)
                # deletion_not_survived = 0
                # if len(inbound_cleaned) > 0:
                #     first_in_rev = inbound_cleaned[0]
                #     editor_first_in, ts_first_in = article_revs[first_in_rev]  # editor and timestamp of first in rev
                #     secs = (ts_first_in - ts_first_out).total_seconds()
                #     if 0 < secs < seconds_limit:
                #         # deletion did not survive (re-inserted in) 48 hours
                #         deletion_not_survived = 1
                # if editor_first_out in periods_deletion[period_deletion]:
                #     periods_deletion[period_deletion][editor_first_out][0] += 1
                #     periods_deletion[period_deletion][editor_first_out][1] += deletion_not_survived
                # else:
                #     periods_deletion[period_deletion][editor_first_out] = [1, deletion_not_survived]
                # # deletion analysis end

            period = (ts_origin.year, ts_origin.month)  # str(t1.year) +"-"+ str(t1.month)
            if editor_origin in periods[period]:
                periods[period][editor_origin][0] += 1
                periods[period][editor_origin][1] += not_survived
            else:
                periods[period][editor_origin] = [1, not_survived]

    # print("Printing persistence.")
    with open(output_file, 'w') as f_out:
        f_out.write("year,month,editor,not_survived_48h,oadds\n")
        for year_month in month_year_iter(1, 2001, 12, 2016):
            (year, month) = year_month
            if year_month in periods:
                for editor, data in periods[year_month].items():
                    editor = '"{}"'.format(editor) if ',' in editor else editor
                    f_out.write(str(year) + "," + str(month) + ',' + editor + ',' + str(data[1]) + "," + str(data[0]) + "\n")
            else:
                f_out.write(str(year) + "," + str(month) + ',0,0,0' + "\n")
    # # output deletion analysis
    # with open(output_file.split('.csv')[0] + '_deletion.csv', 'w') as f_out:
    #     f_out.write("year,month,editor,not_survived_48h,deletions\n")
    #     for year_month in month_year_iter(1, 2001, 12, 2016):
    #         (year, month) = year_month
    #         if year_month in periods_deletion:
    #             for editor, data in periods_deletion[year_month].items():
    #                 editor = '"{}"'.format(editor) if ',' in editor else editor
    #                 f_out.write(str(year) + "," + str(month) + ',' + editor + ',' + str(data[1]) + "," + str(data[0]) + "\n")
    #         else:
    #             f_out.write(str(year) + "," + str(month) + ',0,0,0' + "\n")


def compute_persistence_base(article_file, revision_file, token_file, bot_file, output_file, part_id, log_folder,
                             is_per_user=True):
    logger = get_logger(part_id, log_folder, is_process=True, is_set=False)
    try:
        if is_per_user:
            compute_persistence_per_user(article_file, revision_file, token_file, bot_file, output_file)
        else:
            computePersistence(article_file, revision_file, token_file, bot_file, output_file)
    except Exception as e:
        logger.exception('part_{}'.format(part_id))
    return True


def get_args():
    """
    python ComputeAuthorshipPersistenceFullWikipedia.py -a '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/articles' -r '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/revisions' -t '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/tokens' -b '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/botlist.csv' -o '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/outputs' -m=4 --per_user
    """
    parser = argparse.ArgumentParser(description='Compute sha reverts.')
    # parser.add_argument('input_file', help='File to analyze')
    parser.add_argument('-a', '--articles_folder', required=True, help='Where article partition csvs are.')
    parser.add_argument('-r', '--revisions_folder', required=True, help='Where revision partition csvs are.')
    parser.add_argument('-t', '--tokens_folder', required=True, help='Where token partition csvs are.')
    parser.add_argument('-b', '--bots_file', required=True, help='')
    parser.add_argument('-o', '--output_folder', required=True, help='')
    parser.add_argument('-m', '--max_workers', type=int, help='Default is 16')
    parser.add_argument('-u', '--per_user', action='store_true', default=False,
                        help='Run script per user group or per user. Default is per user group (reg, bot, ip).')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    articles_folder = args.articles_folder
    revisions_folder = args.revisions_folder
    tokens_folder = args.tokens_folder
    bots_file = args.bots_file
    output_folder = args.output_folder
    if not exists(output_folder):
        mkdir(output_folder)
    max_workers = args.max_workers or 16
    is_per_user = args.per_user

    csv.field_size_limit(sys.maxsize)
    # group and order input files.
    articles_dict = {}
    for article_file in listdir(articles_folder):
        # articles-20161226-part6-7431-8783.csv
        articles_dict[article_file.split('-')[2][4:]] = '{}/{}'.format(articles_folder, article_file)
    revisions_dict = {}
    for revision_file in listdir(revisions_folder):
        # 20161101-revisions-part7-8785-10139.csv
        revisions_dict[revision_file.split('-')[2][4:]] = '{}/{}'.format(revisions_folder, revision_file)
    inputs_dict = {}
    for token_file in listdir(tokens_folder):
        # ex input_file_name: 20161226-tokens-part3-3378-4631.csv
        part_id = token_file.split('-')[2][4:]
        inputs_dict[part_id] = [part_id,
                                '{}/{}'.format(tokens_folder, token_file),
                                revisions_dict[part_id],
                                articles_dict[part_id],
                                '{}/authorship-part{}.csv'.format(output_folder, part_id)]
    input_files = []
    for k in sorted(inputs_dict, key=int):
        input_files.append(inputs_dict[k])
    # logging
    log_folder = '{}/{}'.format(output_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = get_logger('future_log', log_folder, is_process=True, is_set=True)

    print('max_workers:', max_workers, 'len inputs:', len(input_files))
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        files_left = len(input_files)
        files_all = len(input_files)
        files_iter = iter(input_files)
        while files_left:
            for part_id, token_file, revision_file, article_file, output_file in files_iter:
                # print(part_id, article_file, revision_file, token_file, bots_file, output_file, log_folder)
                # files_left -= 1
                # continue
                job = executor.submit(compute_persistence_base, article_file, revision_file,
                                      token_file, bots_file, output_file, part_id, log_folder,
                                      is_per_user)
                jobs[job] = part_id
                if len(jobs) == max_workers:  # limit # jobs with max_workers
                    break

            for job in as_completed(jobs):
                files_left -= 1
                part_id_ = jobs[job]
                try:
                    data = job.result()
                except Exception as exc:
                    logger.exception('part_{}'.format(part_id_))

                del jobs[job]
                sys.stdout.write('\rFiles left: {} - Done: {:.3f}%'.
                                 format(files_left, ((files_all - files_left) * 100) / files_all))
                break  # to add a new job, if there is any
    print("Done: ", strftime("%Y-%m-%d-%H:%M:%S"))

    # article_file = sys.argv[1]  # No requirements on article_file.
    # revision_file = sys.argv[2]    # Requirement on revision_file: revisions ordered by timestamp.
    # token_file = sys.argv[3]    # No requirements on token_file.
    # bot_file = sys.argv[4]
    # f1 = sys.argv[5]  # "persisentecesample-part01-token-out1000.txt"
    #
    # print("Computing Authorship and Persistence ...")
    # computePersistence(article_file, revision_file, token_file, bot_file, f1)
    # print("Done!")

if __name__ == '__main__':
    main()
