# -*- coding: utf-8 -*-

single_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "clustersetting",
    "description": "Serialized clustersetting object",
    "type": "object",
    "properties": {
      "id": {"type": ["number","null"]},
      "cluster_id": {"type": ["number","null"]}
    }
}

collection_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "clustersetting collection",
    "description": "Serialized clustersetting collection",
    "type": "object",
    "items": single_schema["properties"]
}