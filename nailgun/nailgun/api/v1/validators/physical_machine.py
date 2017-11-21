# -*- coding: utf-8 -*-
#    Copyright 2013 Mirantis, Inc.
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

from nailgun.api.v1.validators.base import BasicValidator
from nailgun.errors import errors
from nailgun.api.v1.validators.json_schema import physical_machine_schema
from nailgun.logger import logger

class physicalmachineValidator(BasicValidator):

   single_schema = physical_machine_schema.single_schema
   collection_schema = physical_machine_schema.collection_schema

   @classmethod
   def validate_update(cls, data, instance):
     d = cls.validate_json(data)
     return d

   @classmethod
   def validate_delete(cls, instance):
     pass


   @classmethod
   def validate(cls, data):
     d = cls.validate_json(data)
     return d

