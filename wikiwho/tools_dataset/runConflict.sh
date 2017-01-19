#!/bin/bash
ROOT=/home/nuser/dumps/wikiwho_dataset
INPUT_ROOT=$ROOT/partitions
RESULTS_FILE=$ROOT/output_conflict
for i in `seq $1 $2`;
do 
    echo "Processing partition $i"
    art=$(ls $INPUT_ROOT/current_articles/articles-20161226-part$i-*)
    rev=$(ls $INPUT_ROOT/current_revisions/revisions-20161226-part$i-*)
    tok=$(ls $INPUT_ROOT/current_tokens/currentcontent-20161226-part$i-*)

    echo $art
    echo $rev
    echo $tok 
    (python $ROOT/ComputeConflictFullWikipedia.py $art $rev $tok $RESULTS_FILE/conflict-part$i-article.csv $RESULTS_FILE/conflict-part$i-token.csv)
done
