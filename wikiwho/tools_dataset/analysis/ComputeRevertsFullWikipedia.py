'''
Created on 29.12.2016

@author: maribelacosta
'''
import csv
import sys


def buildNetworkReverts(d, fout):
    out = open(fout, 'w')
    # header
    out.write("article,source,target,reverted_add_actions,reverted_del_actions,total_actions,source_editor,target_editor\n")

    # Iterate over each article.
    for article in d:
        # Iterate over each revision i,
        # starting by the first revision of the article.
        for i in range(1, len(d[article]["rev_order"])):
            # Obtain meta-data of revision i.
            rev_i_id = d[article]["rev_order"][i]
            rev_i = d[article]["revs"][rev_i_id]
            s_outs = (set(rev_i["token-outs"]))
            s_ins = (set(rev_i["token-ins"]))

            # Iterate over previous revisions j, starting from i and backwards.
            # Loop to detect reverts from i to j.
            # i is the source, j is the target.
            for j in range(i-1, -1, -1):
                # Obtain meta-data of revision j.
                rev_j_id = d[article]["rev_order"][j]
                rev_j = d[article]["revs"][rev_j_id]

                # Count number of reverted actions from i to j.
                reverted_actions_del = 0
                reverted_actions_add = 0

                # Detect reverts by deletion.
                if len(s_outs) > 0:
                    s1 = (set(rev_j["oadds"]) | set(rev_j["token-ins"]))
                    # Revision i deleted content created or re-introduced in j.
                    s_intersection = s1 & s_outs
                    if len(s_intersection) > 0:
                        reverted_actions_del = reverted_actions_del + len(s_intersection)
                        s_outs = s_outs - s_intersection

                # Detect reverts by re-introduction.
                if len(s_ins) > 0:
                    s1 = set(rev_j["token-outs"])
                    # Revision i re-introduced content deleted in j.
                    s_intersection = s1 & s_ins
                    if len(s_intersection) > 0:
                        reverted_actions_add = reverted_actions_add + len(s_intersection)
                        s_ins = s_ins - s_intersection

                # Check if i reverted actions from j.
                if (reverted_actions_del + reverted_actions_add) > 0:
                    # total actions of j (target)
                    total_actions = len(rev_j["oadds"]) + len(rev_j["token-ins"]) + len(rev_j["token-outs"])
                    # reverts.append((rev_i_id, rev_j_id, reverted_actions, total_actions))
                    out.write(str(article) +
                              "," + str(rev_i_id) +  # source i
                              "," + str(rev_j_id) +  # target j
                              "," + str(reverted_actions_add) +  # source_add_reverted_actions
                              "," + str(reverted_actions_del) +  # source_del_reverted_actions
                              "," + str(total_actions) +  # target_total_actions
                              "," + d[article]["revs"][rev_i_id]["editor"] +
                              "," + d[article]["revs"][rev_j_id]["editor"] + "\n")

                # Exit loop.
                if len(s_outs) == 0 and len(s_ins) == 0:
                    break
        out.flush()
    out.close()


def buildActionsPerRevision(article_file, revision_file, token_file):
    d = {}
    print("Load article id.")
    with open(article_file) as infile:
        next(infile, None)  # skip the headers
        for line in infile:
            d.update({int(line): {"rev_order": [], "revs": {}}})

    print("Load revision meta-data.")
    with open(revision_file) as csvfile:
        # Example of line: article_id,revision_id,editor,timestamp,oadds
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for line in infile:
            aux = line
            aux[0] = int(aux[0])
            d[aux[0]]["rev_order"].append(int(aux[1]))
            d[aux[0]]["revs"].update({int(aux[1]) : {"editor": aux[2], "oadds": [], "token-ins": [], "token-outs": []}})

    print("Load token meta-data.")
    with open(token_file) as csvfile:
        # article_id,label_revision_id(origin),token_id,value,inbound,outbound
        infile = csv.reader(csvfile, delimiter=',')
        # next(infile, None)  # skip the headers
        for line in infile:
            aux = line
            aux[0] = int(aux[0])  # article_id
            aux[1] = int(aux[1])  # label_revision_id (origin)
            aux[2] = int(aux[2])  # token_id
            aux[4] = eval(aux[4].replace("{", "[").replace("}", "]"))  # inbound
            aux[5] = eval(aux[5].replace("{", "[").replace("}", "]"))  # outbound
            # original additions
            d[aux[0]]["revs"][aux[1]]["oadds"].append(aux[2])
            # iterate inbound
            for elem in aux[4]:
                try:
                    d[aux[0]]["revs"][int(elem)]["token-ins"].append(aux[2])
                except:
                    pass
            # iterate outbound
            for elem in aux[5]:
                try:
                    d[aux[0]]["revs"][int(elem)]["token-outs"].append(aux[2])
                except:
                    pass

    return d


if __name__ == '__main__':
    csv.field_size_limit(sys.maxsize)

    article_file = sys.argv[1]
    revision_file = sys.argv[2]
    token_file = sys.argv[3]
    fout = sys.argv[4]

    print("Building actions per revisions ...")
    data = buildActionsPerRevision(article_file, revision_file, token_file)
    # data = {int_article_id:
    # {"rev_order": [int_rev_id, ...],  # ordered list of revisions
    #  "revs": {int_rev_id : {"editor": editor_id,  # editor of the revision
    #                         "oadds": [token_id, ],  # list of token ids that are originally added in this revision
    #                         "token-ins": [token_id, ],  # list of token ids that are re-introduced in this revision
    #                         "token-outs": [token_id, ]  # list of token ids that are deleted in this revision
    # }}}}
    print("Building network reverts ...")
    buildNetworkReverts(data, fout)
    print("Done!")
