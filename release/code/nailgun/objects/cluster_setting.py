# -*- coding: utf-8 -*-

from nailgun.objects.serializers.cluster_setting\
    import ClusterSettingInfoSerializer

from nailgun.objects.serializers.cluster_setting\
    import ClusterdeployMsgSerializer

from nailgun.objects.serializers.cluster_setting\
    import ClusterRoleStatusSerializer

from nailgun.objects.base import NailgunObject
from nailgun.objects.base import NailgunCollection

from nailgun.db import db
from nailgun.db.sqlalchemy.models import ClusterSetting
from nailgun.db.sqlalchemy.models import ClusterdeployMsg
from nailgun.db.sqlalchemy.models import ClusterRoleStatus
from nailgun.errors import errors
from nailgun.logger import logger

class ClusterSettingObject(NailgunObject):
    
    #:SQLAlchemy model for ClusterSettingObject
    model = ClusterSetting
  
     #:Serializer for ClusterSettingObject
    serializer = ClusterSettingInfoSerializer

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "ClusterSetting",
        "description": "Serialized ClusterSetting object",
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "cluster_id": {"type": "number"},
            "cluster_setting": {"type": "object"}
        }
    }

    @classmethod
    def create(cls,data):
    	new_obj=super(ClusterSettingObject, cls).create(data)
        return new_obj


class ClusterSettingCollection(NailgunCollection):
    """ClusterSetting collection
    """
    # : Single PhysicalMachineInfo object class
    single = ClusterSettingObject




class ClusterdeployMsgObject(NailgunObject):
    
    #:SQLAlchemy model for ClusterSettingObject
    model = ClusterdeployMsg
  
     #:Serializer for ClusterSettingObject
    serializer = ClusterdeployMsgSerializer

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "ClusterdeployMsg",
        "description": "Serialized ClusterdeployMsg object",
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "cluster_id": {"type": "number"},
            "cluster_deploymsg": {"type": "object"}
        }
    }

    @classmethod
    def create(cls,data):
        new_obj=super(ClusterdeployMsgObject, cls).create(data)
        return new_obj


class ClusterdeployMsgCollection(NailgunCollection):
    """ClusterSetting collection
    """
    # : Single PhysicalMachineInfo object class
    single = ClusterdeployMsgObject




class ClusterRoleStatusObject(NailgunObject):

    model=ClusterRoleStatus
    serializer=ClusterRoleStatusSerializer
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "ClusterRoleStatus",
        "description": "Serialized ClusterRoleStatus object",
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "cluster_id": {"type": "number"},
            "cluster_role": {"type": "string"},
            "role_status":{"type": "number"}
        }
    }

    @classmethod
    def create(cls,data):
        new_obj=super(ClusterRoleStatusObject, cls).create(data)
        return new_obj


class ClusterRoleStatusCollection(NailgunCollection):
    """ClusterRoleStatus collection
    """
    # : Single PhysicalMachineInfo object class
    single = ClusterRoleStatusObject



