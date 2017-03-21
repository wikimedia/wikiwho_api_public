TokTrack dataset structure and contents
(base dataset, version 1.0)


# Contents and name conventions:

	- Output types are 'current_content', 'deleted_content' and 'revisions'.

	- Each CSV file contains the token content (or revisions) of several articles in
	sequences ordered by their page_ids. These part(ition)s are numbered from the first one containing the articles with the
	lowest page_ids to the last one containing the articles with the highest page_ids. There are 646 partitions in
	this version of TokTrack.

	- CSV delimiter is comma, quote characters are double quotes

	- CSV file name structure:
	'<xml_dump_date>-<output_type>-part<partition_id>-<first_page_id_in_partition>-<last_page_id_in_partition>.csv'

	- CSV partitions are batched in compressed archives. There are 13 archives each for
	'current_content' and 'deleted_content', and one for 'revisions'.

	- 7zip archive name structure (except 'revisions'):
	'<xml_dump_date>-<output_type>-parts-<first_partition_id_contained>-<last_partition_id_contained>-pageids-<first_page_id_of_first_partition>-<last_page_id_of_last_partition>.7z'

	- XML dump date for this version is Nov 01, 2016. Source:
	 https://dumps.wikimedia.org/enwiki/20161101/ Format is YYYYMMDD.



## Output type: Current_content

	- Contains information of all tokens of each article that are present in the last
	revision of the used XML dump.

	- Each line contains one token with the following fields:

	 -- page_id (integer scalar): The page ID of the article (as extracted from the XML
	 dumps) to which the token belongs.

	 -- last_rev_id (integer scalar): The revision ID  where the token last appeared; in this
	 output type, this is the last revision ID for the respective article included in the downloaded XML dumps.

	 -- token_id (integer scalar): The token ID assigned internally by the WikiWho algorithm, unique
	 per article. Token IDs are assigned increasing from 1 for each new token added to an article.

	 -- str (string): The string value of the token.

	 -- origin_rev_id (integer scalar): The ID of the revision where the token was added
	 originally in the article.

	 -- in (ordered integer list): List of all revisions where the token was REinserted after
	 being deleted previously, ordered sequentially by time. If empty, the token has never been
	 reintroduced after deletion. Each "in" has to be preceded by one equivalent "out" in sequence.

	 -- out (ordered integer list): List of all revisions in which the token was deleted,
	 ordered sequentially by time. If empty, the token has never been deleted.


## Output type: Deleted_content

	- Contains information about all tokens of each article that have ever been present in the
	article in at least one revision, but are not present in the last revision of the article in the used XML
	dump.

	- The structure of the file is exactly equivalent to "current_content", with two differences:

	 1. At least one entry exists in the out list of each token and one more out
	 than in.

	 2. The last_rev_id field can contain different values for tokens of the same article, as
	 deleted tokens might have appeared last at different revisions.


## Output type: Revisions

	- Contains all revisions of the articles as processed by the algorithm in sequential
	order. (Note that for performance reasons, WikiWho skips about 0.5% of revisions because
	they are blatant vandalism and they are treated as non-existent for our dataset.)

	- The contained information can be joined with the other two file types on the
	origin_rev_id or last_rev_id fields.

	- Each line represents one revision, including metadata:

	 -- page_id (integer scalar): The page ID of the article (as extracted from the XML dumps)
	to which the revision belongs.

	 -- rev_id (integer scalar): The revision ID. Revision IDs are extracted from the XML
	dumps, belong to one article only and are unique for the whole dataset.

	 -- timestamp (timestamp): The creation timestamp of the revision as extracted from the XML
	dumps.

	 -- editor (string value): The user ID of the editor as extracted from the XML dumps. User
	IDs are integers, are unique for the whole Wikipedia and can be used to fetch the current
	name of a user from the dumps or the Wikipedia API, if needed. The only exemption is user ID = 0,
	which identifies all unregistered accounts. To still allow for distinction between unregistered
	users, the string identifiers (e.g., IPs, MAC-addresses) of unregistered users are included in
	this field, prefixed by "0|".
