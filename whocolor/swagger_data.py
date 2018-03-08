# specification for swagger ui v2.0: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md

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

definitions = {
    "editor": {
        "required": [
            "editor_name", "class_name", "authorship_score"
        ],
        "properties": {
            "editor_name": {
                "type": "string",
            },
            "class_name": {
                "type": "string",
            },
            "authorship_score": {
                "type": "number",
                "format": "double"
            }
        },
        "example": {
            "name": "Vanjagenije",
            "id": "1646408",
            "score": 14.754098360655737
        }
    },
    'token': {
        "required": ["conflict_score", "str", "o_rev_id", "in", "out", "class_name", "age"],
        "properties": {
            "conflict_score": {"type": "integer"},
            "str": {"type": "string"},
            "o_rev_id": {"type": "integer"},
            "in": {"type": "array", "items": {"type": "integer"}},
            "out": {"type": "array", "items": {"type": "integer"}},
            "class_name": {"type": "string"},
            "age": {"type": "number", "format": "double"},
        },
        "example": [1, "{{", 294212239, [530917836], [343655203], "773061", 276366173.781772],
    },
    'revision': {
        "type": "object",
        "required": ["timestamp", "parent_id", "class_name", "editor_name"],
        "properties": {
            "timestamp": {
                "type": "string",
                "example": "2003-06-17T10:45:57Z",
            },
            "parent_id": {
                "type": "integer",
                "format": "int64",
                "example": 1047879
            },
            "class_name": {
                "type": "string",
                "example": "5f340c8127b65dc0ee98cc2bd8708e75"
            },
            "editor_name": {
                "type": "string",
                "example": "Frecklefoot",
            }
        },
        # 'example': ["2003-06-17T10:45:57Z", 0, "5f340c8127b65dc0ee98cc2bd8708e75", "0|157.193.172.88"]
    }
}

definitions["Article"] = {
    "required": [
        "extended_html", "page_title", "success", "present_editors", "tokens", "rev_id", "biggest_conflict_score",
        "revisions"
    ],
    "properties": {
        "page_title": {
            "type": "string",
            "example": "Dinar"
        },
        "extended_html": {
            "type": "string",
            "example": '<span class="editor-token token-editor-6412b9565d4a22098ef4b20bca7413b7" '
                       'id="token-69">seven</span> <span class="editor-token token-editor-7614868" '
                       'id="token-70">mostly</span><span class="editor-token token-editor-7614868" id="token-71"> '
        },
        "success": {
            "type": "boolean",
            "example": True
        },
        'present_editors': {
            "type": "array",
            "items": definitions['editor'],
            "example": [[
                "Kanguole",
                "5563803",
                19.4672131147541
            ]],
        },
        "tokens": {
            'type': 'array',
            # 'description': 'List of lists containing token information',
            'items': definitions['token']
        },
        "rev_id": {
            "type": "integer",
            "format": "int64",
            "example": 56498152
        },
        "biggest_conflict_score": {
            "type": "integer",
            "format": "int64",
            "example": 11
        },
        "revisions": {
            # 'description': 'a dictionary. `1048945` is an example key',
            'required': ['rev_id'],
            'type': 'object',
            'properties': {
                "rev_id": definitions['revision']
            },
            'additionalProperties': definitions['revision'],
            'example': {1048945:
                            ["2003-06-17T10:45:57Z", 0, "5f340c8127b65dc0ee98cc2bd8708e75", "0|157.193.172.88"]}

        }
    },
}

responses = {
    '200': {
        'description': 'OK',
        'schema': definitions['Article']
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
        'description': 'Documentation can be found at [api.wikiwho.net](https://api.wikiwho.net).\n\n'
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
                'produces': ['application/json'],
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
                         'produces': ['application/json'],
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
