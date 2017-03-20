from django.conf import settings

query_params = [
    {'description': 'Output origin revision id per token', 'in': 'query', 'name': 'rev_id', 'required': True,
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
    'deleted_content': ['rev_id', 'editor', 'token_id', 'inbound', 'outbound', 'threshold'],
    'content': ['rev_id', 'editor', 'token_id', 'inbound', 'outbound'],
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
        {'/content/page_id/{page_id}/':
         # {'get': {'description': '# Some description \n **with** *markdown* \n\n [Markdown Cheatsheet]
         # (https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)',
             {'get': {'description': 'Outputs the content of the last revision of an article. \n\n'
                                     'Check `GET /content/{article_name}/` for explanations of query parameters.',
                      # 'produces': ['application/json'],
                      'parameters': [{'description': 'Page id of the article from wikipedia',
                                      'in': 'path',
                                      'name': 'page_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['Revision content'],
                      'summary': 'Get the content of the last revision of an article'
                      }
              },
         '/content/revision_id/{revision_id}/':
             {'get': {'description': 'Outputs the content of the given revision.\n\n'
                                     'Check `GET /content/{article_name}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Revision ID',
                                      'in': 'path',
                                      'name': 'revision_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['Revision content'],
                      'summary': 'Get the content of a revision'
                      }
              },
         '/content/{article_name}/':
             {'get': {'description': 'Outputs the content of the last revision of the given article.\n\n'
                                     '#### Query parameter explanations:\n\n'
                                     '**Revision id:** The ID of the revision where the token was added originally '
                                     'in the article.\n\n'
                                     '**Editor:** The user ID of the editor. User '
                                     'IDs are integers, are unique for the whole Wikipedia and can be used to fetch '
                                     'the current name of a user. The only exemption is user ID = 0, which identifies '
                                     'all unregistered accounts. To still allow for distinction between unregistered '
                                     'users, the string identifiers of unregistered users are included in this field, '
                                     'prefixed by “0|".\n\n'
                                     '**Token id:** The token ID assigned internally by the algorithm, unique per '
                                     'article. Token IDs are assigned increasing from 1 for each new token added to '
                                     'an article.\n\n'
                                     '**Inbound:** List of all revisions where the token was REinserted after being '
                                     'deleted previously, ordered sequentially by time. If empty, the token has never '
                                     'been reintroduced after deletion. One in has to be preceded by one out in '
                                     'sequence. Also means that there always has to be at least one out for each in.'
                                     '\n\n'
                                     '**Outbound:** List of all revisions in which the token was deleted, ordered '
                                     'sequentially by time. If empty, the token has never been deleted.',
                      'parameters': [{'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['Revision content'],
                      'summary': 'Get the content of the last revision of an article'
                      }
              },
         '/content/{article_name}/{revision_id}/':
             {'get': {'description': 'Outputs the content of the given revision of the given article.\n\n'
                                     'Check `GET /content/{article_name}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Revision ID to get content',
                                      'in': 'path',
                                      'name': 'revision_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['Revision content'],
                      'summary': 'Get the content of the revision of an article'
                      }
              },
         '/content/{article_name}/{start_revision_id}/{end_revision_id}/':
             {'get': {'description': 'Outputs the content of revisions from start revision to end revision ordered '
                                     'by timestamp.\n\n'
                                     'Check `GET /content/{article_name}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Start revision id',
                                      'in': 'path',
                                      'name': 'end_revision_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'End revision id',
                                      'in': 'path',
                                      'name': 'start_revision_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['Revision content'],
                      'summary': 'Get the content of multiple revisions of an article'
                      }
              },
         '/deleted/page_id/{page_id}/':
             {'get': {'description': 'Outputs the deleted content of the given article.\n\n'
                                     'Deleted content means all tokens of an article that have ever been present in '
                                     'the article in at least one revision, but are not present in the last revision.'
                                     '\n\n'
                                     'Check `GET /deleted/{article_name}/` for explanations of query parameters.',
                      'parameters': [{'description': 'Page id of the article from wikipedia',
                                      'in': 'path',
                                      'name': 'page_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': 'Output tokens that are deleted more times than threshold. '
                                                     'Default is {}'.format(settings.DELETED_CONTENT_THRESHOLD_LIMIT),
                                      'in': 'query',
                                      'name': 'threshold',
                                      'required': False,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['Deleted content'],
                      'summary': 'Get the deleted content an article'
                      }
              },
         '/deleted/{article_name}/':
             {'get': {'description': 'Outputs the deleted content of the given article.\n\n'
                                     'Deleted content means all tokens of an article that have ever been present in '
                                     'the article in at least one revision, but are not present in the last revision.'
                                     '\n\n'
                                     '#### Query parameter explanations:\n\n'
                                     'Query parameters are equivalent to revision content queries except that '
                                     'at least one entry exists in the out list of each token and at least one '
                                     'more out than in.\n',
                      'parameters': [{'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     {'description': 'Output tokens that are deleted more times than threshold. '
                                                     'Default is {}'.format(settings.DELETED_CONTENT_THRESHOLD_LIMIT),
                                      'in': 'query',
                                      'name': 'threshold',
                                      'required': False,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': responses,
                      'tags': ['Deleted content'],
                      'summary': 'Get the deleted content an article'
                      }
              },
         '/revision_ids/page_id/{page_id}/':
             {'get': {'description': 'Outputs revision ids of the given article.\n\n'
                                     'Check `GET /revision_ids/{article_name}/` for explanations of query parameters.',
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
                      'tags': ['Revision ids'],
                      'summary': 'Get revision ids of an article'
                      }
              },
         '/revision_ids/{article_name}/':
             {'get': {'description': 'Outputs revision ids of the given article.\n\n'
                                     '#### Query parameter explanations:\n\n'
                                     '**editor:** The user ID of the editor. User '
                                     'IDs are integers, are unique for the whole Wikipedia and can be used to fetch '
                                     'the current name of a user. The only exemption is user ID = 0, which identifies '
                                     'all unregistered accounts. To still allow for distinction between unregistered '
                                     'users, the string identifiers of unregistered users are included in this field, '
                                     'prefixed by “0|".\n\n'
                                     '**timestamp:** The creation timestamp of the revision.',
                      'parameters': [{'description': 'Article title',
                                      'in': 'path',
                                      'name': 'article_name',
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
                      'tags': ['Revision ids'],
                      'summary': 'Get revision ids of an article'
                      }
              },
         },
}

