# Primary Data Set

## Folder and file name conventions:
 - Folder: `<xml_dump_date>-<output type>-parts-<first_partition_id>-<last_partition_id>-pageids-<first_page_id>-<last_page_id>`
 - File: `<xml_dump_date>-<output type>-part<partition_id>-<first_page_id_in_sequence>-<last_page_id_in_sequence>.csv`
 - Each file contains the content for several articles in ordered sequence of their page_ids.
 - Xml dump date is 01.11.2016.
 - Output type can be 'current_content', 'deleted_content' or 'revisions'.

## Current content

 - Contains information of all tokens of each article that are present in the last revision by 01.11.2016.
 - Each line contains one token with the following fields:
    - page_id  (integer scalar): The page ID of the article (as extracted from the XML dumps) to which the token belongs.
    - last_rev_id (integer scalar): The revision ID  where the token last appeared; in this output type, this is the last revision ID included in the downloaded XML dumps as of November 1, 2016 per each article.
    - token_id (integer scalar): The token ID assigned internally by the algorithm, unique per article. Token IDs are assigned increasing from 1 for each new token added to an article.
    - str (string): The string value of the token.
    - origin_rev_id (integer scalar): The ID of the revision where the token was added originally in the article.
    - in (ordered integer list): List of all revisions where the token was REinserted after being deleted previously, ordered sequentially by time. If empty, the token has never been reintroduced after deletion. One in has to be preceded by one out in sequence. Also means that there always has to be at least one out for each in.
    - out (ordered integer list): List of all revisions in which the token was deleted, ordered sequentially by time. If empty, the token has never been deleted.

## Deleted content

 - Contains information of all tokens of each article that have ever been present in the article in at least one revision, but are not present in the last revision by 01.11.2016.
 - The structure of the file is exactly equivalent to current content, with two differences:
    1. At least one entry exists in the out list of each token and at least one more out than in.
    2. The last_rev_id field can contain different values for tokens of the same article, as deleted tokens might have appeared last at different revisions.

## Revisions

 - Contains all revisions of the articles as processed by the algorithm in sequential order. (Note that WikiWho skips about 0.5% of revisions because they are blatant vandalism and they are treated as non-existent for our dataset.)
 - The contained information can be joined with the other two file types on the origin_rev_id or last_rev_id fields.
 - Each line represents one revision, including metadata:
    - page_id (integer scalar): The page ID of the article (as extracted from the XML dumps) to which the revision belongs.
    - rev_id (integer scalar): The revision ID. Revision IDs are extracted from the XML dumps, belong to one article only and are unique for the whole dataset.
    - timestamp (timestamp): The creation timestamp of the revision as extracted from the XML dumps.
    - editor (string value): The user ID of the editor as extracted from the XML dumps. User IDs are integers, are unique for the whole Wikipedia and can be used to fetch the current name of a user. The only exemption is user ID = 0, which identifies all unregistered accounts. To still allow for distinction between unregistered users, the string identifiers of unregistered users are included in this field, prefixed by “0|".

# Secondary Data Set

## Authorship and Survival

 - Contains survival information of all tokens per month-year for different user groups.
 - Each line contains survival data with the following fields:
   - year (integer scalar): Year that these tokens are added.
   - month (integer scalar): Month that these tokens are added.
   - user_type (string value): Type of users that added these tokens: unregistered users (ip), bots, registered users (reg) or all.
   - not_survived_48h (integer scalar): Number of originally added tokens in this month-year that are not survived 48 hours.
   - oadds (integer scalar): Number of originally added tokens in this month-year.
   - survived_to_oct31-2016 (integer scalar): Number of originally added tokens in this month-year that are survived until 01.11.2016. This is available only for all users.

## Conflict

 - Contains conflict information of tokens per article (conflict-all-article.csv) or string value (conflict-all-string.csv).
 - `conflict-all-article.csv` contains conflict data of all tokens per article with the following fields:
   - article_id (integer scalar): The page ID of the article (as extracted from the XML dumps).
   - cbSimple (integer scalar): Simply sum of all deletion ('out') and reinsertion ('in') actions of all tokens of an article. First deletion of a token is not counted.
   - cb (integer scalar): Same as cbSimple. The only difference is that undo-actions of editors on their own actions are not counted neither.
   - cbTime (integer scalar): Equivalent to cb, apart from one feature: instead of just counting up 1 per undo action, it weights rapid undo actions higher by assigning a weight. The weight is computed as the logarithm to the base 3600 of the absolute time in seconds that has passed since the last action on the token was performed.
   - total_revs (integer scalar): Total number of revisions of an article.
 - `conflict-all-string.csv` contains conflict data of all tokens per string value with the following fields:
   - string (string value): The string value of the token.
   - cbSimple (integer scalar): Simply sum of all deletion ('out') and reinsertion ('in') actions of all tokens of an article. First deletion of a token is not counted.
   - cb (integer scalar): Same as cbSimple. The only difference is that undo-actions of editors on their own actions are not counted neither.
   - cbTime (integer scalar): Equivalent to cb, apart from one feature: instead of just counting up 1 per undo action, it weights rapid undo actions higher by assigning a weight. The weight is computed as the logarithm to the base 3600 of the absolute time in seconds that has passed since the last action on the token was performed.
   - total_freq (integer scalar): Total number of occurrences of this string value over whole tokens.

## Reverts

 - Contains information of interactions between users.
 - Each line contains revert data with the following fields:
   - article_id (integer scalar): The page ID of the article (as extracted from the XML dumps).
   - source (integer scalar): Id of revision where revert action is done.
   - target (integer scalar): Id of revision whose action is reverted.
   - reverted_add_actions (integer scalar): Total number of re-introductions of deleted tokens that were deleted in the target. These actions are done in the source.
   - reverted_del_actions (integer scalar): Total number of deletions of originally added or re-introduced tokens of the target. These actions are done in the source.
   - total_actions (integer scalar): Total number of actions (originally addition, deletion, re-introduction) of the target.
   - source_editor (string value): Id of editor who did the revert action.
   - target_editor (string value): Id of editor whose action is reverted.
