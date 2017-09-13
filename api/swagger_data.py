from django.conf import settings

query_params = [
    {'description': 'Origin revision ID per token', 'in': 'query', 'name': 'o_rev_id', 'required': True,
     'type': 'boolean'},  # 'default': 'false',
    {'description': 'Editor ID/Name per token', 'in': 'query', 'name': 'editor', 'required': True,
     'type': 'boolean'},
    {'description': 'Token ID per token', 'in': 'query', 'name': 'token_id', 'required': True,
     'type': 'boolean'},
    {'description': 'Outbound revision IDs per token', 'in': 'query', 'name': 'out', 'required': True,
     'type': 'boolean'},
    {'description': 'Inbound revision IDs per token', 'in': 'query', 'name': 'in', 'required': True,
     'type': 'boolean'}
]

allowed_params = {
    'rev_content': ['o_rev_id', 'editor', 'token_id', 'in', 'out'],
    'deleted_content': ['o_rev_id', 'editor', 'token_id', 'in', 'out', 'threshold'],
    'all_content': ['o_rev_id', 'editor', 'token_id', 'in', 'out', 'threshold'],
    'rev_ids': ['editor', 'timestamp']
}

headers = {
    "X-Rate-Limit-Limit": {
        "description": "The number of allowed requests in the current period",
        "type": "integer"
    },
    "X-Rate-Limit-Remaining": {
        "description": "The number of remaining requests in the current period",
        "type": "integer"
    },
    "X-Rate-Limit-Reset": {
        "description": "The number of seconds left in the current period",
        "type": "integer"
    }
}
responses = {
    '200': {
        'description': 'OK',
        # TODO http://swagger.io/specification/#responsesObject
        # 'headers': headers,
        # 'examples': {},
        },
    '400': {
        'description': 'BAD REQUEST',
    },
    '408': {
        'description': 'REQUEST TIMEOUT',
    },
    '503': {
        'description': 'WP SERVICE UNAVAILABLE',
    },
}

version = '1.0.0-beta'
version_url = 'v{}'.format(version)
custom_data = {
    'swagger': '2.0',
    'info': {
            'title': 'WikiWho API',
            # 'termsOfService': '',
            'version': version,
            # 'license': {'name': 'TODO licence?', 'url': ''},
            # 'description': 'A short description of the application. GFM syntax can be used for rich text '
            #                'representation. \n\nSpecification: http://swagger.io/specification \n\n'
            #                'Example api: http://petstore.swagger.io/',
            'description': 'This API provides provenance and change information about the tokens a Wikipedia article '
                           'consists of.\n\n'
                           'For each article page it mirrors its current state on the English Wikipedia.\n\n'
                           'It\'s based on the [WikiWho algorithm](https://github.com/wikiwho) - the most accurate '
                           'algorithm for this task, evaluated against a [gold standard dataset]'
                           '(http://f-squared.org/wikiwho/#paper) (~95% acc.).\n\n'
                           'Terminology used here:\n\n'
                           '- *"Wikipedia"*: A selected language version of Wikipedia. Available languages can be '
                           'chosen from the top navigation bar. Will be extended in the future.\n'
                           '- *"article (page)"*: Any Wikipedia page in '
                           '[namespace = 0](https://en.wikipedia.org/wiki/Wikipedia:Namespace).\n'
                           '- *"(article) content"*: The tokenized Wiki Markup text content of a (range of) '
                           'revision(s) of an article page, *not* the front-end HTML (if you want that, you have to '
                           '"untokenize" and appropriately parse it; the original order of tokens is retained).\n'
                           '- *"token"*/*"tokenized"*: The Wiki Markup text is split at (i) white spaces and '
                           '(ii) certain special characters (special chars also act as tokens). E.g., tokens in '
                           '`"A [[house]], a boat."` are `"a", "[[", "house", "]]", ",", "a", "boat", "."` '
                           'I.e., all tokens are converted into lower-case and certain character combinations that '
                           'have a specific function in Wiki Markup, such as double-square brackets, get treated '
                           'as single tokens. '
                           '>> [Current WikiWho tokenization]'
                           '(https://github.com/wikiwho/WikiWho/blob/master/WikiWho/utils.py)\n'
                           '- *"revisions"*: The article revisions and their IDs as retrieved from Wikipedia, with one '
                           'exception: The WikiWho algorithm implements a (very lenient)  filter to avoid spending '
                           'time DIFFing blatant vandalism which gets immediately reverted after. About 0.5% of the '
                           'revisions from Wikipedia are hence not available here as we consider those changes to '
                           'have disappeared immediately. This is a temporary constraint to be removed in an '
                           'upcoming version.\n\n'
                           '**[>> Toy example for how the token metadata is generated]'
                           '(https://gist.github.com/faflo/8bd212e81e594676f8d002b175b79de8)**\n\n'
                           'See the description of the different query types for more information.\n\n'
                           'A dataset with this data (until Nov. 2016, no redirects) is available for download at '
                           'https://doi.org/10.5281/zenodo.345571.\n\n'
                           '**Please cite it** as well if you use data from this API in your research.\n\n'
                           '(note that the dataset excludes redirect articles and tokenization can slightly differ '
                           'from the API version)\n\n'
                           '### **Created by **[GESIS - Leibniz Institute for the Social Sciences, CSS group]'
                           '(http://www.gesis.org/en/institute/gesis-scientific-departments/'
                           'computational-social-science/)\n\n'
                           'Data from this API is published under the CC-BY-SA 4.0 license. Original revision data '
                           'is retrieved from Wikimedia servers and the terms for reuse put forth by Wikimedia apply.',
            # 'contact': {
            #     'name': 'GESIS - Leibniz Institute for the Social Sciences, CSS group',
            #     # 'email': 'kenan.erdogan@gesis.org?cc=fabian.floeck@gesis.org&subject=wikiwho API',
            #     'url': 'http://www.gesis.org/en/institute/gesis-scientific-departments/'
            #            'computational-social-science/'},
        },
    'basePath': '/api/{}'.format(version_url),
    'host': 'api.wikiwho.net',
    'schemes': 'https',
    'produces': ['application/json'],
    # 'externalDocs': {
    #     'description': 'A short description of the target documentation. '
    #                    'GFM syntax can be used for rich text representation.',
    #     'url': ''
    # },
    'paths':
        {'/rev_content/page_id/{page_id}/':
         # {'get': {'description': '# Some description \n **with** *markdown* \n\n [Markdown Cheatsheet]
         # (https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)',
             {'get': {'description': 'Outputs the content of the most recent (last) revision of the given article, '
                                     ' as available on Wikipedia.\n\n'
                                     # 'Outputs the content of the most recent (last) revision of an article. \n\n'
                                     'This is functionally equivalent to `GET /rev_content/{article_title}/`.',
                      # 'produces': ['application/json'],
                      'parameters': [{'description': 'Page ID of the article from Wikipedia',
                                      'in': 'path',
                                      'name': 'page_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Content per revision'],
                      'summary': 'Get the content of the last revision of an article'
                      }
              },
         '/rev_content/rev_id/{rev_id}/':
             {'get': {'description': 'Outputs the content of the given revision. This works almost same as '
                                     '`GET /rev_content/{article_title}/{rev_id}/`, there is no performance '
                                     'difference.\n\n'
                                     'Check `GET /rev_content/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Revision ID',
                                      'in': 'path',
                                      'name': 'rev_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Content per revision'],
                      'summary': 'Get the content of a specific revision of an article'
                      }
              },
         '/rev_content/{article_title}/':
             {'get': {'description': 'Outputs the content of the most recent (last) revision of the given article, '
                                     ' as available on Wikipedia.\n\n'
                                     '#### Query parameter explanations:\n\n'
                                     '**o_rev_id:** The ID of the revision where the token was added originally '
                                     'in the article.\n\n'
                                     '**editor:** The user ID of the editor. User '
                                     'IDs are integers, are unique for the whole Wikipedia and can be used to fetch '
                                     'the current name of a user. The only exemption is user ID = 0, which identifies '
                                     'all unregistered accounts. To still allow for distinction between unregistered '
                                     'users, the string identifiers (e.g., IPs, MAC-addresses) of unregistered users '
                                     'are included in this field, prefixed by "0|".\n\n'
                                     '**token_id:** The token ID assigned internally by the WikiWho algorithm, unique '
                                     'per article. Token IDs are assigned increasing from 1 for each new token added '
                                     'to an article.\n\n'
                                     '**out:** List of all revisions in which the token was deleted, ordered '
                                     'sequentially by time. If empty, the token has never been deleted.\n\n'
                                     '**in:** List of all revisions where the token was REinserted after '
                                     'being deleted previously, ordered sequentially by time. If empty, the token has '
                                     'never been reintroduced after deletion. Each "in" has to be preceded by one '
                                     'equivalent "out" in sequence.',
                      'parameters': [{'description': 'The title of the requested article',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Content per revision'],
                      'summary': 'Get the content of the last revision of an article'
                      }
              },
         '/rev_content/{article_title}/{rev_id}/':
             {'get': {'description': 'Outputs the content of the given revision of the given article.\n\n'
                                     'Check `GET /rev_content/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'The title of the requested article',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     {'description': 'Revision ID to get content for',
                                      'in': 'path',
                                      'name': 'rev_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Content per revision'],
                      'summary': 'Get the content of a specific revision of an article'
                      }
              },
         '/rev_content/{article_title}/{start_rev_id}/{end_rev_id}/':
             {'get': {'description': 'Outputs the content of revisions from start revision to end revision ordered '
                                     'by timestamp.\n\n'
                                     'Note: We only consider the **timestamp** of a revision ID for its '
                                     'ordinal position, **not** its integer value. These two can very rarely be '
                                     'conflicted.\n\n'
                                     'Check `GET /rev_content/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'The title of the requested article',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     {'description': 'Start revision ID',
                                      'in': 'path',
                                      'name': 'start_rev_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'End revision ID',
                                      'in': 'path',
                                      'name': 'end_rev_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Content per revision'],
                      'summary': 'Get the content of a range of revisions of an article'
                      }
              },
         '/all_content/page_id/{page_id}/':
             {'get': {'description': 'Outputs all tokens that have ever existed in a given article, '
                                     'including their change history for each.\n\n'
                                     '\n\n'
                                     'Check `GET /all_content/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Page ID of the article from Wikipedia',
                                      'in': 'path',
                                      'name': 'page_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'Only tokens that are deleted more times than threshold. '
                                                     'Default is {}.'.format(settings.ALL_CONTENT_THRESHOLD_LIMIT),
                                      'in': 'query',
                                      'name': 'threshold',
                                      'required': False,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['2 - All content'],
                      'summary': 'Get the all content an article'
                      }
              },
         '/all_content/{article_title}/':
             {'get': {'description': 'Outputs the complete content of the given article.\n\n'
                                     '\n\n'
                                     '#### Query parameter explanations:\n\n'
                                     'Query parameters are equivalent to revision content queries. '
                                     'There is only an extra `threshold` parameter.',
                      'parameters': [{'description': 'The title of the requested article',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     {'description': 'Only tokens that are deleted more times than threshold. '
                                                     'Default is {}.'.format(settings.ALL_CONTENT_THRESHOLD_LIMIT),
                                      'in': 'query',
                                      'name': 'threshold',
                                      'required': False,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['2 - All content'],
                      'summary': 'Get the all content an article'
                      }
              },
         # '/deleted/page_id/{page_id}/':
         #     {'get': {'description': 'Outputs the deleted content of the given article.\n\n'
         #                             'Deleted content means all tokens of an article that have ever been present in '
         #                             'the article in at least one revision, but are not present in the last revision.'
         #                             '\n\n'
         #                             'Check `GET /deleted/{article_title}/` for explanations of query parameters.',
         #              'parameters': [{'description': 'Page ID of the article from Wikipedia',
         #                              'in': 'path',
         #                              'name': 'page_id',
         #                              'required': True,
         #                              'type': 'integer'},
         #                             {'description': 'Output tokens that are deleted more times than threshold. '
         #                                             'Default is {}'.format(settings.DELETED_CONTENT_THRESHOLD_LIMIT),
         #                              'in': 'query',
         #                              'name': 'threshold',
         #                              'required': False,
         #                              'type': 'integer'},
         #                             ] + query_params,
         #              'responses': responses,
         #              'tags': ['2 - Deleted content'],
         #              'summary': 'Get the deleted content an article'
         #              }
         #      },
         # '/deleted/{article_title}/':
         #     {'get': {'description': 'Outputs the deleted content of the given article.\n\n'
         #                             'Deleted content means all tokens of an article that have ever been present in '
         #                             'the article in at least one revision, but are not present in the last revision.'
         #                             '\n\n'
         #                             '#### Query parameter explanations:\n\n'
         #                             'Query parameters are equivalent to revision content queries except that '
         #                             'at least one entry exists in the out list of each token and at least one '
         #                             'more out than in.\n',
         #              'parameters': [{'description': 'The title of the requested article',
         #                              'in': 'path',
         #                              'name': 'article_title',
         #                              'required': True,
         #                              'type': 'string'},
         #                             {'description': 'Output tokens that are deleted more times than threshold. '
         #                                             'Default is {}'.format(settings.DELETED_CONTENT_THRESHOLD_LIMIT),
         #                              'in': 'query',
         #                              'name': 'threshold',
         #                              'required': False,
         #                              'type': 'integer'},
         #                             ] + query_params,
         #              'responses': responses,
         #              'tags': ['2 - Deleted content'],
         #              'summary': 'Get the deleted content an article'
         #              }
         #      },
         '/rev_ids/page_id/{page_id}/':
             {'get': {'description': 'Outputs revision IDs of the given article as processed by WikiWho.\n\n'
                                     'Check `GET /rev_ids/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Page ID of the article from Wikipedia',
                                      'in': 'path',
                                      'name': 'page_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] +
                                    [{'description': 'Output editor ID of each revision',
                                      'in': 'query',
                                      'name': 'editor',
                                      'required': True,
                                      'type': 'boolean'},
                                     {'description': 'Output timestamp of each revision',
                                      'in': 'query',
                                      'name': 'timestamp',
                                      'required': True,
                                      'type': 'boolean'}
                                     ],
                      'responses': responses,
                      'tags': ['3 - Revision IDs'],
                      'summary': 'Get revision IDs of an article'
                      }
              },
         '/rev_ids/{article_title}/':
             {'get': {'description': 'Outputs revision IDs of the given article as processed by WikiWho.\n\n'
                                     '#### Query parameter explanations:\n\n'
                                     '**editor:** See other query explanations.\n\n'
                                     '**timestamp:** The creation timestamp of the revision as provided by Wikipedia',
                      'parameters': [{'description': 'The title of the requested article',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     ] +
                                    [{'description': 'Output editor ID of each revision',
                                      'in': 'query',
                                      'name': 'editor',
                                      'required': True,
                                      'type': 'boolean'},
                                     {'description': 'Output timestamp of each revision',
                                      'in': 'query',
                                      'name': 'timestamp',
                                      'required': True,
                                      'type': 'boolean'}
                                     ],
                      'responses': responses,
                      'tags': ['3 - Revision IDs'],
                      'summary': 'Get revision IDs of an article'
                      }
              },
         },
}

