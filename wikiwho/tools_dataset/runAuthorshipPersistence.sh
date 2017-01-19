#!/bin/bash
ROOT=/home/nuser/dumps/wikiwho_dataset
INPUT_ROOT=$ROOT/partitions
RESULTS_FILE=$ROOT/output_authorship
BOT_FILE=$INPUT_ROOT/botlist.csv
for i in `seq $1 $2`;
do 
    echo "Processing partition $i"
    art=$(ls $INPUT_ROOT/articles/articles-20161226-part$i-*)
    rev=$(ls $INPUT_ROOT/revisions/revisions-20161226-part$i-*)
    tok=$(ls $INPUT_ROOT/tokens/mac-tokens-all-part$i-*)

    echo $art
    echo $rev
    echo $tok 
    (time python3 $ROOT/ComputeAuthorshipPersistenceFullWikipedia.py $art $rev $tok $BOT_FILE $RESULTS_FILE/authorship-part$i-article.csv)
    echo 
done
