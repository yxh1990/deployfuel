# -*- coding: utf-8 -*-
#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#objects 的model同时引用serializers和sqlalchemy.db


from nailgun.objects.serializers.physical_machine \
    import PhysicalMachineInfoSerializer

from nailgun.objects.base import NailgunObject
from nailgun.objects.base import NailgunCollection

from nailgun.db import db
from nailgun.db.sqlalchemy.models import PhysicalMachineInfo

from nailgun.errors import errors
from nailgun.logger import logger

class PhysicalMachineInfoObject(NailgunObject):
    
    #:SQLAlchemy model for PhysicalMachineInfo
    model = PhysicalMachineInfo
  
     #:Serializer for PhysicalMachineInfo
    serializer = PhysicalMachineInfoSerializer

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "PhysicalMachineInfo",
        "description": "Serialized PhysicalMachineInfo object",
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "name": {"type": "string"},
            "ip": {"type": "string"},
            "mp_ip": {"type": "string"},
            "mp_username": {"type": "string"},
            "mp_passwd": {"type": "string"},
            "cabinet": {"type": "string"},
            "gene_room": {"type": "string"},
            "power_status": {"type": "number"},
            "operation_status": {"type": "number"},
            "mac": {"type": "string"},
            "use_type": {"type": "number"},
            "additional_info":{"type": "object"}
        }
    }

    @classmethod
    def create(cls,data):
    	new_obj=super(PhysicalMachineInfoObject, cls).create(data)
        return new_obj



class PhysicalMachineInfoCollection(NailgunCollection):
    """PhysicalMachineInfo collection
    """
    # : Single PhysicalMachineInfo object class
    single = PhysicalMachineInfoObject

    
