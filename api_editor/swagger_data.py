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

definitions = {}
##################################################################
###### This is OK, but it mighte use too much bandwidth  #########
##################################################################
definitions["edition"] = {
    "allOf": [
        {"required": ["editor_id"],
         "properties": {"editor_id": {"type": "integer"}}},
        {"required": ["year_month"],
         "properties": {"year_month": {"type": "string"}}},

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
        "page_id",
        "success",
        "editordata_columns",
        "editordata_types",
        "editordata_formats",
        "editordata"
    ],
    "properties": {

        "page_id": {
            "type": "integer",
            "format": "int64",
            "example": 189253
        },

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
        "page_id",
        "success",
        "editions"
    ],
    "properties": {

        "page_id": {
            "type": "integer",
            "format": "int64",
            "example": 189253
        },

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
        'title': 'WikiWho Editor API',
        # 'termsOfService': '',
        'version': version,
        # 'license': {'name': 'TODO licence?', 'url': ''},
        # 'description': 'A short description of the application. GFM syntax can be used for rich text '
        #                'representation. \n\nSpecification: http://swagger.io/specification \n\n'
        #                'Example api: http://petstore.swagger.io/',
        'description': 'Documentation can be found at [api.wikiwho.net](https://api.wikiwho.net/).\n\n'
                       '### **Created by **[GESIS - Leibniz Institute for the Social Sciences, CSS group]'
                       '(https://www.gesis.org/en/institute/departments/computational-social-science/)',
    },
    'basePath': '/api_editor/{}'.format(version_url),
    'host': 'www.wikiwho.net',
    'schemes': 'https',
    'produces': ['application/json'],
    # 'externalDocs': {
    #     'description': 'A short description of the target documentation. '
    #                    'GFM syntax can be used for rich text representation.',
    #     'url': ''
    # },
    'paths':
        {'/{page_id}/':
            {'get': {
                'description': 'Outputs all the editors that have edited a page, and the number of editions.\n\n',
                'produces': ['application/json'],
                'parameters': [{'description': 'The id of the editor',
                                'in': 'path',
                                'name': 'page_id',
                                'required': True,
                                'type': 'integer'},
                               ],
                'responses': responses_editor,
                'tags': ['editor'],
                'summary': 'Get the total of edition per page of an editor'
            }
            },
         '/editor_data/{page_id}/':
            {'get': {
                    'description': 'Outputs all the editors that have edited a page, and the number of editions in a table format\n\n',
                    'produces': ['application/json'],
                    'parameters': [{'description': 'The id of the editor',
                                'in': 'path',
                                'name': 'page_id',
                                'required': True,
                                'type': 'integer'},
                               ],
                    'responses': responses_editordata,
                    'tags': ['editor'],
                    'summary': 'Get the total of edition per page of an editor'
                     }
             },
         },
}
