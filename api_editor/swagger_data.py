# specification for swagger ui v2.0:
# https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md

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

query_params = [{
    'description': ('Starting from date (inclusive, in YYYY-MM-DD format). The response will '
                    'always contain full months, so it is better to explicitely use YYYY-MM-01'),
    'in': 'query',
    'name': 'start',
    'required': False,
    'type': 'string',
    'format': 'date'
}, {
    'description': ('Ending in this date (inclusive, in YYYY-MM-DD format). The response will '
                    'always contain full months, so it is better to explicitely use YYYY-MM-01'),
    'in': 'query',
    'name': 'end',
    'required': False,
    'type': 'string',
    'format': 'date'
}, ]


definitions = {}
##################################################################
###### This is OK, but it mighte use too much bandwidth  #########
##################################################################
definitions["edition"] = {
    "allOf": [
        {"required": ["year_month"],
         "properties": {"year_month": {"type": "string"}}},
        {"required": ["page_id"],
         "properties": {"page_id": {"type": "integer"}}},
        {"required": ["editor_id"],
         "properties": {"editor_id": {"type": "integer"}}},

        {"required": ["adds"],
         "properties": {"adds": {"type": "integer"}}},
        {"required": ["adds_surv_48h"],
         "properties": {"adds_surv_48h": {"type": "integer"}}},
        {"required": ["adds_persistent"],
         "properties": {"adds_persistent": {"type": "integer"}}},
        {"required": ["adds_stopword_count"],
         "properties": {"adds_stopword_count": {"type": "integer"}}},

        {"required": ["dels"],
         "properties": {"dels": {"type": "integer"}}},
        {"required": ["dels_surv_48h"],
         "properties": {"dels_surv_48h": {"type": "integer"}}},
        {"required": ["dels_persistent"],
         "properties": {"dels_persistent": {"type": "integer"}}},
        {"required": ["dels_stopword_count"],
         "properties": {"dels_stopword_count": {"type": "integer"}}},

        {"required": ["reins"],
         "properties": {"reins": {"type": "integer"}}},
        {"required": ["reins_surv_48h"],
         "properties": {"reins_surv_48h": {"type": "integer"}}},
        {"required": ["reins_persistent"],
         "properties": {"reins_persistent": {"type": "integer"}}},
        {"required": ["reins_stopword_count"], "properties": {
            "reins_stopword_count": {"type": "integer"}}},

    ],
}
#########################################################
#########################################################
#########################################################


########################################################################
###### This would be ideal but it is not supported by OpenAPI  #########
########################################################################
#'editor_id',
#'adds', 'adds_surv_48h', 'adds_persistent', 'adds_stopword_count',
#'dels', 'dels_surv_48h', 'dels_persistent', 'dels_stopword_count',
#'reins', 'reins_surv_48h', 'reins_persistent', 'reins_stopword_count'

# definitions["editions_columns"] = {
#     "type": "array",
#     "items": {
#         "type": [
#             "string",
#             "string", "string", "string", "string",
#             "string", "string", "string", "string",
#             "string", "string", "string", "string"
#             ]
#     }
# }

# definitions["editions_array"] = {
#     "type": "array",
#     "items": {
#         "type": [
#             "integer",
#             "integer", "integer", "integer", "integer",
#             "integer", "integer", "integer", "integer",
#             "integer", "integer", "integer", "integer"
#             ],
#         "format": [
#             "int64",
#             "int64", "int64", "int64", "int64",
#             "int64", "int64", "int64", "int64",
#             "int64", "int64", "int64", "int64"
#             ]
#     }
# }
########################################################################
########################################################################


#######################################################
######### This is poor, but it should be faster #######
#######################################################
definitions["editordata_columns"] = {
    "type": "array",
    "items": {
        "type": "string"
    }
}

definitions["editordata_types"] = {
    "type": "array",
    "items": {
        "type": "string"
    }
}

definitions["editordata_formats"] = {
    "type": "array",
    "items": {
        "type": "string"
    }
}

definitions["editordata_array"] = {
    "type": "array",
    "items": {
        "type": "object"
    }
}
############################################
############################################


definitions["EditorData"] = {
    "required": [
        "success",
        "editordata_columns",
        "editordata_types",
        "editordata_formats",
        "editordata"
    ],
    "properties": {

        "success": {
            "type": "boolean",
            "example": True
        },

        "editordata_columns": {
            "type": "array",
            "items": definitions['editordata_columns']
        },

        "editordata_types": {
            "type": "array",
            "items": definitions['editordata_types']
        },

        "editordata_formats": {
            "type": "array",
            "items": definitions['editordata_formats']
        },

        "editordata": {
            "type": "array",
            "items": definitions['editordata_array']
        },


    },
}

definitions["Editor"] = {
    "required": [
        "success",
        "editions"
    ],
    "properties": {

        "success": {
            "type": "boolean",
            "example": True
        },

        "editions": {
            "type": "array",
            "items": definitions['edition']
        },
    },
}


responses_editor = {
    '200': {
        'description': 'OK',
        'schema': definitions['Editor']
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

responses_editordata = {
    '200': {
        'description': 'OK',
        'schema': definitions['EditorData']
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
        'title': 'WikiWho Edit Persistence API',
        # 'termsOfService': '',
        'version': version,
        # 'license': {'name': 'TODO licence?', 'url': ''},
        # 'description': 'A short description of the application. GFM syntax can be used for rich text '
        #                'representation. \n\nSpecification: http://swagger.io/specification \n\n'
        #                'Example api: http://petstore.swagger.io/',
        'description': 'Documentation can be found at [api.wikiwho.net](https://api.wikiwho.net).\n\n'
                       'We recommend to use the [WikiWho Wrapper](https://pypi.org/project/wikiwho-wrapper/) '
                       'to easily access the API requests from Python 3.\n\n'
                       '### **Created by **[GESIS - Leibniz Institute for the Social Sciences, CSS group]'
                       '(https://www.gesis.org/en/institute/departments/computational-social-science/)\n\n'
                       'Data from this API is published under the CC-BY-SA 4.0 license. Original revision data '
                       'is retrieved from Wikimedia servers and the terms for reuse put forth by Wikimedia apply.',
    },
    'basePath': '/edit_persistence/{}'.format(version_url),
    'host': 'www.wikiwho.net',
    'schemes': 'https',
    'produces': ['application/json'],
    # 'externalDocs': {
    #     'description': 'A short description of the target documentation. '
    #                    'GFM syntax can be used for rich text representation.',
    #     'url': ''
    # },
    'paths': {
        '/editor/{editor_id}/': {
            'get': {
                'description': ('Outputs monthly editions for an editor (include all pages).\n\n'),
                'produces': ['application/json'],
                'parameters': [{'description': 'The id of the editor',
                                'in': 'path',
                                'name': 'editor_id',
                                'required': True,
                                'type': 'integer'},
                               ] + query_params,
                'responses': responses_editor,
                'tags': ['Standard Format'],
                'summary': 'Get monthly editions for an editor'
            }
        },
        '/page/{page_id}/': {
            'get': {
                'description': ('Outputs the monthly editions on a page per month (include all editors).\n\n'),
                'produces': ['application/json'],
                'parameters': [{'description': 'The id of the page',
                                'in': 'path',
                                'name': 'page_id',
                                'required': True,
                                'type': 'integer'},
                               ] + query_params,
                'responses': responses_editor,
                'tags': ['Standard Format'],
                'summary': 'Get all monthly editions on a page per month.'
            }
        },
        '/page/editor/{page_id}/{editor_id}/': {
            'get': {
                'description': ('Outputs the monthly editions on a page for an editor.\n\n'),
                'produces': ['application/json'],
                'parameters': [{'description': 'The id of the page',
                                'in': 'path',
                                'name': 'page_id',
                                'required': True,
                                'type': 'integer'},
                               {'description': 'The id of the editor',
                                'in': 'path',
                                'name': 'editor_id',
                                'required': True,
                                'type': 'integer'},
                               ] + query_params,
                'responses': responses_editor,
                'tags': ['Standard Format'],
                'summary': 'Get monthly editions on a page for an editor'
            }
        },
        '/as_table/editor/{editor_id}/': {
            'get': {
                'description': ('Outputs monthly editions for an editor (include all pages).\n\n'),
                'produces': ['application/json'],
                'parameters': [{'description': 'The id of the editor',
                                'in': 'path',
                                'name': 'editor_id',
                                'required': True,
                                'type': 'integer'},
                               ] + query_params,
                'responses': responses_editordata,
                'tags': ['Table Format'],
                'summary': 'Get monthly editions for an editor'
            }
        },
        '/as_table/page/{page_id}/': {
            'get': {
                'description': ('Outputs the monthly editions on a page per month (include all editors).\n\n'),
                'produces': ['application/json'],
                'parameters': [{'description': 'The id of the page',
                                'in': 'path',
                                'name': 'page_id',
                                'required': True,
                                'type': 'integer'},
                               ] + query_params,
                'responses': responses_editordata,
                'tags': ['Table Format'],
                'summary': 'Get all monthly editions on a page per month.'
            }
        },
        '/as_table/page/editor/{page_id}/{editor_id}/': {
            'get': {
                'description': ('Outputs the monthly editions on a page for an editor.\n\n'),
                'produces': ['application/json'],
                'parameters': [{'description': 'The id of the page',
                                'in': 'path',
                                'name': 'page_id',
                                'required': True,
                                'type': 'integer'},
                                {'description': 'The id of the editor',
                                'in': 'path',
                                'name': 'editor_id',
                                'required': True,
                                'type': 'integer'},
                               ] + query_params,
                'responses': responses_editordata,
                'tags': ['Table Format'],
                'summary': 'Get monthly editions on a page for an editor'
            }
        },
    },
}
