
def parse_toktrack_csv(csv_path):
    with open(csv_path, 'r') as f:
        next(f)  # skip the header
        # header: page_id,last_rev_id,token_id,str,origin_rev_id,in,out
        for line in f:
            line = line.split(',')
            page_id = int(line[0])
            last_rev_id = int(line[1])
            token_id = int(line[2])
            if line[3].startswith('"') and line[4].endswith('"'):
                # str is a comma
                string_ = line[3][1:] + ',' + line[4][:-1]
                origin_rev_id = int(line[5])
                ins_outs = line[6:]
            else:
                string_ = line[3]
                origin_rev_id = int(line[4])
                ins_outs = line[5:]
            if string_.startswith('"') and string_.endswith('"'):
                # str contains " and it was correctly written into csv
                string_ = string_[1:-1].replace('""', '"')
            # get in and out revision ids
            is_ins = True
            ins = []
            outs = []
            for in_or_out in ins_outs:
                if is_ins:
                    in_ = in_or_out.replace('}', '').replace('{', '').replace('"', '').replace('\n', '')
                    if in_:
                        ins.append(int(in_))
                else:
                    out_ = in_or_out.replace('}', '').replace('{', '').replace('"', '').replace('\n', '')
                    if out_:
                        outs.append(int(out_))
                if in_or_out.endswith('}"') or in_or_out.endswith('}'):
                    is_ins = False
            # process data
            yield [page_id, last_rev_id, token_id, string_, origin_rev_id, ins, outs]
            # print(page_id, last_rev_id, token_id, string_, origin_rev_id, ins, outs)


if __name__ == '__main__':
    csv_path = '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/current_content_newer/test.csv'
    parse_toktrack_csv(csv_path)
