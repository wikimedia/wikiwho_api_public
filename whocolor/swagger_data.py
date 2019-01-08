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
    "present_editors": {
        "allOf": [
            {"required": ["editor_name"], "properties": {"editor_name": {"type": "string"}}},
            {"required": ["class_name"], "properties": {"class_name": {"type": "string"}}},
            {"required": ["authorship_score"],
             "properties": {"authorship_score": {"type": "number", "format": "double"}}},
        ],
        "example": ["Kanguole", "5563803", 19.4672131147541]
    },
    'tokens': {
        "allOf": [
            {"required": ["conflict_score"], "properties": {"conflict_score": {"type": "integer"}}},
            {"required": ["str"], "properties": {"str": {"type": "string"}}},
            {"required": ["o_rev_id"], "properties": {"o_rev_id": {"type": "integer"}}},
            {"required": ["in"], "properties": {"in": {"type": "array", "items": {"type": "integer"}}}},
            {"required": ["out"], "properties": {"out": {"type": "array", "items": {"type": "integer"}}}},
            {"required": ["class_name"], "properties": {"class_name": {"type": "string"}}},
            {"required": ["age"], "properties": {"age": {"type": "number", "format": "double"}}},
        ],
        "example": [1, "{{", 294212239, [530917836], [343655203], "773061", 276366173.781772],
    },
    'revisions': {
        "allOf": [
            {"required": ["timestamp"], "properties": {"timestamp": {"type": "string"}}},
            {"required": ["parent_id"], "properties": {"parent_id": {"type": "integer", "format": "int64"}}},
            {"required": ["class_name"], "properties": {"class_name": {"type": "string"}}},
            {"required": ["editor_name"], "properties": {"editor_name": {"type": "string"}}}
        ],
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
            "items": definitions['present_editors'],
        },
        "tokens": {
            'type': 'array',
            # 'description': 'List of lists containing token information',
            'items': definitions['tokens']
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
                "rev_id": definitions['revisions']
            },
            # 'additionalProperties': definitions['revisions'],
            'example': {1048945: ["2003-06-17T10:45:57Z", 0, "5f340c8127b65dc0ee98cc2bd8708e75", "0|157.193.172.88"]}

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
                       '(https://www.gesis.org/en/institute/departments/computational-social-science/)\n\n'
                       'Data from this API is published under the CC-BY-SA 4.0 license. Original revision data '
                       'is retrieved from Wikimedia servers and the terms for reuse put forth by Wikimedia apply.',
    },
    'basePath': '/whocolor/{}'.format(version_url),
    'host': 'www.wikiwho.net',
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
                                'name': 'page_title',
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
