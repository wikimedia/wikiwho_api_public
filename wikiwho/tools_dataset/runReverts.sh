#!/bin/bash
ROOT=/bigdata/kerdogan
INPUT_ROOT=$ROOT/partitions
RESULTS_FILE=$ROOT/output_reverts
for i in `seq $1 $2`;
do 
    echo "Processing partition $i"
    art=$(ls $INPUT_ROOT/articles/articles-20161226-part$i-*)
    rev=$(ls $INPUT_ROOT/revisions/revisions-20161226-part$i-*)
    tok=$(ls $INPUT_ROOT/tokens/mac-tokens-all-part$i-*)

    echo $art
    echo $rev
    echo $tok 
    (time python3 $ROOT/ComputeRevertsFullWikipedia.py $art $rev $tok $RESULTS_FILE/reverts-part$i.csv)
    echo
done
