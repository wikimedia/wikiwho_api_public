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
        # 'content': {
        #     'application/json': {
        #         'schema': {
        #             'type': 'object',
        #             'properties': {
        #                 'id': {
        #                     'type': 'integer',
        #                     'description': 'User ID'
        #                 },
        #                 'username': {
        #                     'type': 'string',
        #                     'description': 'Username'
        #                 },
        #             }
        #         }
        #     }
        # }
    },
    '400': {
        'description': 'BAD REQUEST',
    },
    # '408': {
    #     'description': 'REQUEST TIMEOUT',
    # },
    '503': {
        'description': 'WP SERVICE UNAVAILABLE',
    },
}

version = '1.0.0-beta'
version_url = 'v{}'.format(version)
custom_data = {
    'swagger': '2.0',
    'info': {
        'title': 'WhoColor API',
        # 'termsOfService': '',
        'version': version,
        # 'license': {'name': 'TODO licence?', 'url': ''},
        # 'description': 'A short description of the application. GFM syntax can be used for rich text '
        #                'representation. \n\nSpecification: http://swagger.io/specification \n\n'
        #                'Example api: http://petstore.swagger.io/',
        'description': 'This API provides text highlighting data needed for the WhoColor JavaScript client.'
                       '### **Created by **[GESIS - Leibniz Institute for the Social Sciences, CSS group]'
                       '(https://www.gesis.org/en/institute/departments/computational-social-science/)',
    },
    'basePath': '/whocolor/{}'.format(version_url),
    'host': 'http://127.0.0.1:8000',
    'schemes': 'https',
    'produces': ['application/json'],
    # 'externalDocs': {
    #     'description': 'A short description of the target documentation. '
    #                    'GFM syntax can be used for rich text representation.',
    #     'url': ''
    # },
    'paths':
        {'/{page_title}/':
             {'get': {
                 'description': 'Outputs the extended HTML of the most recent (last) revision of the given article,'
                                ' as available on Wikipedia.\n\n',
                 # 'produces': ['application/json'],
                 'parameters': [{'description': 'The title of the requested article',
                                 'in': 'path',
                                 'name': 'article_title',
                                 'required': True,
                                 'type': 'string'},
                                ],
                 'responses': responses,
                 'tags': ['Extended html'],
                 'summary': 'Get the extended html of last revision of an article'
                 }
              },
         '/{page_title}/{rev_id}/':
             {'get': {'description': 'Outputs the extended HTML of the given revision.',
                      'parameters': [{'description': 'The title of the requested article',
                                      'in': 'path',
                                      'name': 'page_title',
                                      'required': True,
                                      'type': 'string'},
                                     {'description': 'Revision ID to get extended html for',
                                      'in': 'path',
                                      'name': 'rev_id',
                                      'required': True,
                                      'type': 'integer'},
                                     ],
                      'responses': responses,
                      'tags': ['Extended html'],
                      'summary': 'Get the extended html of a specific revision of an article'
                      }
              },
         },
}
