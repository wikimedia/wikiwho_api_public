from django.conf import settings

query_params = [
    {'description': 'Output origin revision id per token', 'in': 'query', 'name': 'origin_rev_id', 'required': True,
     'type': 'boolean'},  # 'default': 'false',
    {'description': 'Output editor id per token', 'in': 'query', 'name': 'editor', 'required': True,
     'type': 'boolean'},
    {'description': 'Output token id per token', 'in': 'query', 'name': 'token_id', 'required': True,
     'type': 'boolean'},
    {'description': 'Output inbound revision ids per token', 'in': 'query', 'name': 'inbound', 'required': True,
     'type': 'boolean'},
    {'description': 'Output outbound revision ids per token', 'in': 'query', 'name': 'outbound', 'required': True,
     'type': 'boolean'}
]

allowed_params = {
    'rev_content': ['origin_rev_id', 'editor', 'token_id', 'inbound', 'outbound'],
    'deleted_content': ['origin_rev_id', 'editor', 'token_id', 'inbound', 'outbound', 'threshold'],
    'all_content': ['origin_rev_id', 'editor', 'token_id', 'inbound', 'outbound', 'threshold'],
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
}

version = '1.0.0-beta'
custom_data = {
    'swagger': '2.0',
    'info': {
            'title': 'wikiwho API',
            # 'termsOfService': '',
            'version': version,
            # 'license': {'name': 'TODO licence?', 'url': ''},
            'description': 'TODO A short description of the application. GFM syntax can be used for rich text '
                           'representation. \n\nSpecification: http://swagger.io/specification \n\n'
                           'Example api: http://petstore.swagger.io/',
            'contact': {
                'name': 'GESIS - Leibniz Institute for the Social Sciences',
                # 'email': 'kenan.erdogan@gesis.org?cc=fabian.floeck@gesis.org&subject=wikiwho API',
                'url': 'http://www.gesis.org/en/institute/gesis-scientific-departments/computational-social-science/'},
        },
    'basePath': '/api/v{}'.format(version),
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
             {'get': {'description': 'Outputs the content of the last revision of an article. \n\n'
                                     'Check `GET /rev_content/{article_title}/` for explanations of query parameters.',
                      # 'produces': ['application/json'],
                      'parameters': [{'description': 'Page id of the article from wikipedia',
                                      'in': 'path',
                                      'name': 'page_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Revision content'],
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
                      'tags': ['1 - Revision content'],
                      'summary': 'Get the content of a revision'
                      }
              },
         '/rev_content/{article_title}/':
             {'get': {'description': 'Outputs the content of the last revision of the given article.\n\n'
                                     '#### Query parameter explanations:\n\n'
                                     '**origin_rev_id:** The ID of the revision where the token was added originally '
                                     'in the article.\n\n'
                                     '**editor:** The user ID of the editor. User '
                                     'IDs are integers, are unique for the whole Wikipedia and can be used to fetch '
                                     'the current name of a user. The only exemption is user ID = 0, which identifies '
                                     'all unregistered accounts. To still allow for distinction between unregistered '
                                     'users, the string identifiers (e.g., IPs, MAC-addresses) of unregistered users '
                                     'are included in this field, prefixed by "0|".\n\n'
                                     '**token_id:** The token ID assigned internally by the WikiWho algorithm, unique'
                                     'per article. Token IDs are assigned increasing from 1 for each new token added '
                                     'to an article.\n\n'
                                     '**inbound:** List of all revisions where the token was REinserted after'
                                     'being deleted previously, ordered sequentially by time. If empty, the token has '
                                     'never been reintroduced after deletion. Each "in" has to be preceded by one '
                                     'equivalent "out" in sequence.\n\n'
                                     '**outbound:** List of all revisions in which the token was deleted, ordered '
                                     'sequentially by time. If empty, the token has never been deleted.',
                      'parameters': [{'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Revision content'],
                      'summary': 'Get the content of the last revision of an article'
                      }
              },
         '/rev_content/{article_title}/{rev_id}/':
             {'get': {'description': 'Outputs the content of the given revision of the given article.\n\n'
                                     'Check `GET /rev_content/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Revision ID to get content',
                                      'in': 'path',
                                      'name': 'rev_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Revision content'],
                      'summary': 'Get the content of the revision of an article'
                      }
              },
         '/rev_content/{article_title}/{start_rev_id}/{end_rev_id}/':
             {'get': {'description': 'Outputs the content of revisions from start revision to end revision ordered '
                                     'by timestamp.\n\n'
                                     'Check `GET /rev_content/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'End revision id',
                                      'in': 'path',
                                      'name': 'end_rev_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'Start revision id',
                                      'in': 'path',
                                      'name': 'start_rev_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['1 - Revision content'],
                      'summary': 'Get the content of range of revisions of an article'
                      }
              },
         '/all_content/page_id/{page_id}/':
             {'get': {'description': 'Outputs the complete content (all tokens) of the given article.\n\n'
                                     '\n\n'
                                     'Check `GET /all_content/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Page id of the article from wikipedia',
                                      'in': 'path',
                                      'name': 'page_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'Output tokens that are deleted more times than threshold. '
                                                     'Default is {}'.format(settings.ALL_CONTENT_THRESHOLD_LIMIT),
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
                      'parameters': [{'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     {'description': 'Output tokens that are deleted more times than threshold. '
                                                     'Default is {}'.format(settings.ALL_CONTENT_THRESHOLD_LIMIT),
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
         #              'parameters': [{'description': 'Page id of the article from wikipedia',
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
         #              'parameters': [{'description': 'Article title',
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
             {'get': {'description': 'Outputs revision ids of the given article.\n\n'
                                     'Check `GET /rev_ids/{article_title}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Page id of the article from wikipedia',
                                      'in': 'path',
                                      'name': 'page_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] +
                                    [{'description': 'Output editor id of each revision',
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
                      'tags': ['3 - Revision ids'],
                      'summary': 'Get revision ids of an article'
                      }
              },
         '/rev_ids/{article_title}/':
             {'get': {'description': 'Outputs revision ids of the given article.\n\n'
                                     '#### Query parameter explanations:\n\n'
                                     '**editor:** The user ID of the editor. User '
                                     'IDs are integers, are unique for the whole Wikipedia and can be used to fetch '
                                     'the current name of a user. The only exemption is user ID = 0, which identifies '
                                     'all unregistered accounts. To still allow for distinction between unregistered '
                                     'users, the string identifiers (e.g., IPs, MAC-addresses) of unregistered users '
                                     'are included in this field, prefixed by "0|".\n\n'
                                     '**timestamp:** The creation timestamp of the revision as extracted from the '
                                     'XML dumps',
                      'parameters': [{'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_title',
                                      'required': True,
                                      'type': 'string'},
                                     ] +
                                    [{'description': 'Output editor id of each revision',
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
                      'tags': ['3 - Revision ids'],
                      'summary': 'Get revision ids of an article'
                      }
              },
         },
}

