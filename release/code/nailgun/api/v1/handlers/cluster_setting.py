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


import web
import json


from nailgun import objects
from nailgun.db import db
from nailgun.db.sqlalchemy.models import ClusterSetting

from nailgun.api.v1.handlers.base import BaseHandler
from nailgun.api.v1.handlers.base import SingleHandler
from nailgun.api.v1.handlers.base import CollectionHandler
from nailgun.api.v1.handlers.base import content_json

from nailgun.logger import logger
from nailgun.common.ShellCmdExecutor import ShellCmdExecutor
from nailgun.openstack.common import jsonutils
from nailgun.settings import settings
from nailgun.common.commonutil import CommonUtil


class ClusterSettingHandler(SingleHandler):

  single = objects.ClusterSettingObject

  def create_password(self):
    output,exitcode=ShellCmdExecutor.execCmd("openssl rand -hex 10")
    random_password=output.strip()
    return random_password

  def create_randomnumber(self,length):
    util=CommonUtil()
    return util.generate_randnumber(length)

  def save_oldpass(self,oldclusterSetting,newcontent):
      oldclusterSetting=jsonutils.loads(oldclusterSetting["cluster_setting"])
      settingcontent={}
      settingcontent['cluster_setting']=jsonutils.loads(newcontent)
      settingcontent["cluster_setting"]["mysql"]["root_password"]=oldclusterSetting["mysql"]["root_password"]
      settingcontent["cluster_setting"]["rabbitmq"]["rabbit_password"]=oldclusterSetting["rabbitmq"]["rabbit_password"]
      settingcontent["cluster_setting"]["mongodb"]["mongo_password"]=oldclusterSetting["mongodb"]["mongo_password"]
      settingcontent["cluster_setting"]["keystone"]["keystone_mysql_password"]=oldclusterSetting["keystone"]["keystone_mysql_password"]
      settingcontent["cluster_setting"]["glance"]["glance_mysql_password"]=oldclusterSetting["glance"]["glance_mysql_password"]
      settingcontent["cluster_setting"]["nova-api"]["nova_mysql_password"]=oldclusterSetting["nova-api"]["nova_mysql_password"]
      settingcontent["cluster_setting"]["nova-api"]["metadata_secret"]=oldclusterSetting["nova-api"]["metadata_secret"]
      settingcontent["cluster_setting"]["neutron-server"]["neutron_mysql_password"]=oldclusterSetting["neutron-server"]["neutron_mysql_password"]
      settingcontent["cluster_setting"]["cinder-api"]["cinder_mysql_password"]=oldclusterSetting["cinder-api"]["cinder_mysql_password"]
      settingcontent["cluster_setting"]["cinder-storage"]["cinder_mysql_password"]=oldclusterSetting["cinder-storage"]["cinder_mysql_password"]
      settingcontent["cluster_setting"]["ceilometer"]["ceilometer_mongo_password"]=oldclusterSetting["ceilometer"]["ceilometer_mongo_password"]
      settingcontent["cluster_setting"]["ceilometer"]["metadata_secret"]=oldclusterSetting["ceilometer"]["metadata_secret"]
      settingcontent["cluster_setting"]["heat"]["heat_mysql_password"]=oldclusterSetting["heat"]["heat_mysql_password"]
      settingcontent["cluster_setting"]["global"]["keystone_admin_password"]=oldclusterSetting["global"]["keystone_admin_password"]
      settingcontent["cluster_setting"]["global"]["keystone_glance_password"]=oldclusterSetting["global"]["keystone_glance_password"]
      settingcontent["cluster_setting"]["global"]["keystone_nova_password"]=oldclusterSetting["global"]["keystone_nova_password"]
      settingcontent["cluster_setting"]["global"]["keystone_neutron_password"]=oldclusterSetting["global"]["keystone_neutron_password"]
      settingcontent["cluster_setting"]["global"]["keystone_ceilometer_password"]=oldclusterSetting["global"]["keystone_ceilometer_password"]
      settingcontent["cluster_setting"]["global"]["keystone_heat_password"]=oldclusterSetting["global"]["keystone_heat_password"]
      settingcontent["cluster_setting"]["global"]["keystone_cinder_password"]=oldclusterSetting["global"]["keystone_cinder_password"]
      settingcontent["cluster_setting"]["global"]["admin_token"]=oldclusterSetting["global"]["admin_token"]
      settingcontent["cluster_setting"]["global"]["keystone_dbpass"]=oldclusterSetting["global"]["keystone_dbpass"]
      settingcontent["cluster_setting"]["global"]["glance_dbpass"]=oldclusterSetting["global"]["glance_dbpass"]
      settingcontent["cluster_setting"]["global"]["nova_dbpass"]=oldclusterSetting["global"]["nova_dbpass"]
      settingcontent["cluster_setting"]["global"]["neutron_dbpass"]=oldclusterSetting["global"]["neutron_dbpass"]
      settingcontent["cluster_setting"]["global"]["cinder_dbpass"]=oldclusterSetting["global"]["cinder_dbpass"]
      settingcontent["cluster_setting"]["global"]["ceilometer_dbpass"]=oldclusterSetting["global"]["ceilometer_dbpass"]
      settingcontent["cluster_setting"]["global"]["heat_dbpass"]=oldclusterSetting["global"]["heat_dbpass"]
      settingcontent["cluster_setting"]["haproxy-keepalived"]["virtual_router_id"] = oldclusterSetting["haproxy-keepalived"]["virtual_router_id"]
      settingcontent["cluster_setting"]["haproxy-keepalived"]["auth_pass"] = oldclusterSetting["haproxy-keepalived"]["auth_pass"]
      return jsonutils.dumps(settingcontent['cluster_setting'])
  @content_json
  def POST(self):
      data={}
      settingcontent={}
      x=web.input(cluster_id='0',content={},cluster_type='1')
      data['cluster_id']=x.cluster_id
      cluster_type=int(x.cluster_type)
      settingcontent['cluster_setting']=jsonutils.loads(x.content)
      newcontent=x.content
      clusterSetting=db().query(ClusterSetting).filter_by(cluster_id=x.cluster_id).first()
      if clusterSetting:
         if cluster_type==4:
            newcontent=self.save_oldpass(clusterSetting,x.content)
      	 objects.ClusterSettingObject.update(clusterSetting,{'cluster_setting':newcontent})
      else:
        if cluster_type==4:
           settingcontent["cluster_setting"]["mysql"]["root_password"]=self.create_password()
           settingcontent["cluster_setting"]["rabbitmq"]["rabbit_password"]=self.create_password()
           settingcontent["cluster_setting"]["mongodb"]["mongo_password"]=self.create_password()
           settingcontent["cluster_setting"]["keystone"]["keystone_mysql_password"]=self.create_password()
           settingcontent["cluster_setting"]["glance"]["glance_mysql_password"]=self.create_password()
           settingcontent["cluster_setting"]["nova-api"]["nova_mysql_password"]=self.create_password()
           settingcontent["cluster_setting"]["nova-api"]["metadata_secret"]=self.create_password()
           settingcontent["cluster_setting"]["neutron-server"]["neutron_mysql_password"]=self.create_password()
           settingcontent["cluster_setting"]["cinder-api"]["cinder_mysql_password"]=self.create_password()
           settingcontent["cluster_setting"]["cinder-storage"]["cinder_mysql_password"]=self.create_password()
           settingcontent["cluster_setting"]["ceilometer"]["ceilometer_mongo_password"]=self.create_password()
           settingcontent["cluster_setting"]["ceilometer"]["metadata_secret"]=self.create_password()
           settingcontent["cluster_setting"]["heat"]["heat_mysql_password"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["keystone_admin_password"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["keystone_glance_password"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["keystone_nova_password"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["keystone_neutron_password"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["keystone_ceilometer_password"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["keystone_heat_password"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["keystone_cinder_password"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["admin_token"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["keystone_dbpass"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["glance_dbpass"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["nova_dbpass"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["neutron_dbpass"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["cinder_dbpass"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["ceilometer_dbpass"]=self.create_password()
           settingcontent["cluster_setting"]["global"]["heat_dbpass"]=self.create_password()
           settingcontent["cluster_setting"]["haproxy-keepalived"]["virtual_router_id"]= self.create_randomnumber(3)
           settingcontent["cluster_setting"]["haproxy-keepalived"]["auth_pass"] = self.create_randomnumber(4)
        data['cluster_setting']=jsonutils.dumps(settingcontent['cluster_setting'])
        objects.ClusterSettingObject.create(data)
      return json.dumps({'result':'1'})

  @content_json
  def GET(self):
    x=web.input(cluster_id='0')
    clusterSetting=db().query(ClusterSetting).filter_by(cluster_id=x.cluster_id).first()
    if clusterSetting:
       return self.single.to_json(clusterSetting)
    else:
       return json.dumps({'global':{'fuel_master_ip':settings.MASTER_IP}})




class ClusterSettingCollectionHandler(CollectionHandler):

  collection =objects.ClusterSettingCollection
		