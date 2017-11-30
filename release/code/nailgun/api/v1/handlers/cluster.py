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

"""
Handlers dealing with clusters
"""

import traceback
import web
import json
import os
import time
import threading

from nailgun.api.v1.handlers.base import BaseHandler
from nailgun.api.v1.handlers.base import DeferredTaskHandler

from nailgun.api.v1.handlers.base import CollectionHandler
from nailgun.api.v1.handlers.base import SingleHandler

from nailgun import objects

from nailgun.db import db
from nailgun.db.sqlalchemy.models import ClusterRoleStatus

from nailgun.api.v1.handlers.base import content_json

from nailgun.api.v1.validators.cluster import AttributesValidator
from nailgun.api.v1.validators.cluster import ClusterValidator
from nailgun.logger import logger
from nailgun.task.manager import ApplyChangesTaskManager
from nailgun.task.manager import ClusterDeletionManager
from nailgun.task.manager import ResetEnvironmentTaskManager
from nailgun.task.manager import StopDeploymentTaskManager
from nailgun.task.manager import UpdateEnvironmentTaskManager



class ClusterHandler(SingleHandler):
    """Cluster single handler
    """

    single = objects.Cluster
    validator = ClusterValidator

    @content_json
    def DELETE(self, obj_id):
        """:returns: {}
        :http: * 202 (cluster deletion process launched)
               * 400 (failed to execute cluster deletion process)
               * 404 (cluster not found in db)
        """
        cluster = self.get_object_or_404(self.single, obj_id)
        task_manager = ClusterDeletionManager(cluster_id=cluster.id)
        try:
            logger.debug('Trying to execute cluster deletion task')
            self.deleteoptfile(obj_id)
            task_manager.execute()
        except Exception as e:
            logger.warn('Error while execution '
                        'cluster deletion task: %s' % str(e))
            logger.warn(traceback.format_exc())
            raise self.http(400, str(e))

        raise self.http(202, '{}')

    def deleteoptfile(self,cluster_id):
        jsondir="/opt/%s" %(cluster_id)
        openstackinifile = "/opt/openstack_init_%s" %(cluster_id)
        role_ip_mapfile = "/opt/role_ip_map_%s.json" %(cluster_id)
        if os.path.exists(jsondir):
           os.popen('rm -rf %s' %(jsondir))
           logger.info("success delete dir %s" %(jsondir))
        if os.path.exists(jsondir):
           os.popen("rm -rf %s" %(openstackinifile))
           logger.info("success delete file %s" %(openstackinifile))
        if os.path.exists(role_ip_mapfile):
           os.popen("rm -rf %s" %(role_ip_mapfile))
           logger.info("success delete file %s" %(role_ip_mapfile))


class ClusterCollectionHandler(CollectionHandler):
    """Cluster collection handler
    """

    collection = objects.ClusterCollection
    validator = ClusterValidator


class ClusterChangesHandler(DeferredTaskHandler):

    log_message = u"Trying to start deployment at environment '{env_id}'"
    log_error = u"Error during execution of deployment " \
                u"task on environment '{env_id}': {error}"
    task_manager = ApplyChangesTaskManager


class ClusterStopDeploymentHandler(DeferredTaskHandler):

    log_message = u"Trying to stop deployment on environment '{env_id}'"
    log_error = u"Error during execution of deployment " \
                u"stopping task on environment '{env_id}': {error}"
    task_manager = StopDeploymentTaskManager


class ClusterResetHandler(DeferredTaskHandler):

    log_message = u"Trying to reset environment '{env_id}'"
    log_error = u"Error during execution of resetting task " \
                u"on environment '{env_id}': {error}"

    task_manager = ResetEnvironmentTaskManager
        


class ClusterUpdateHandler(DeferredTaskHandler):

    log_message = u"Trying to update environment '{env_id}'"
    log_error = u"Error during execution of update task " \
                u"on environment '{env_id}': {error}"
    task_manager = UpdateEnvironmentTaskManager


class ClusterAttributesHandler(BaseHandler):
    """Cluster attributes handler
    """

    fields = (
        "editable",
    )

    validator = AttributesValidator

    @content_json
    def GET(self, cluster_id):
        """:returns: JSONized Cluster attributes.
        :http: * 200 (OK)
               * 404 (cluster not found in db)
               * 500 (cluster has no attributes)
        """
        cluster = self.get_object_or_404(objects.Cluster, cluster_id)
        if not cluster.attributes:
            raise self.http(500, "No attributes found!")

        return objects.Cluster.get_editable_attributes(cluster)

    @content_json
    def PUT(self, cluster_id):
        """:returns: JSONized Cluster attributes.
        :http: * 200 (OK)
               * 400 (wrong attributes data specified)
               * 404 (cluster not found in db)
               * 500 (cluster has no attributes)
        """
        cluster = self.get_object_or_404(objects.Cluster, cluster_id)
        if not cluster.attributes:
            raise self.http(500, "No attributes found!")

        if cluster.is_locked:
            raise self.http(403, "Environment attributes can't be changed "
                                 "after, or in deploy.")

        data = self.checked_data()
        objects.Cluster.update_attributes(cluster, data)
        return objects.Cluster.get_editable_attributes(cluster)

    @content_json
    def PATCH(self, cluster_id):
        """:returns: JSONized Cluster attributes.
        :http: * 200 (OK)
               * 400 (wrong attributes data specified)
               * 404 (cluster not found in db)
               * 500 (cluster has no attributes)
        """
        cluster = self.get_object_or_404(objects.Cluster, cluster_id)

        if not cluster.attributes:
            raise self.http(500, "No attributes found!")

        if cluster.is_locked:
            raise self.http(403, "Environment attributes can't be changed "
                                 "after, or in deploy.")

        data = self.checked_data()
        objects.Cluster.patch_attributes(cluster, data)
        return objects.Cluster.get_editable_attributes(cluster)


class ClusterAttributesDefaultsHandler(BaseHandler):
    """Cluster default attributes handler
    """

    fields = (
        "editable",
    )

    @content_json
    def GET(self, cluster_id):
        """:returns: JSONized default Cluster attributes.
        :http: * 200 (OK)
               * 404 (cluster not found in db)
               * 500 (cluster has no attributes)
        """
        cluster = self.get_object_or_404(objects.Cluster, cluster_id)
        attrs = objects.Cluster.get_default_editable_attributes(cluster)
        if not attrs:
            raise self.http(500, "No attributes found!")
        return {"editable": attrs}

    @content_json
    def PUT(self, cluster_id):
        """:returns: JSONized Cluster attributes.
        :http: * 200 (OK)
               * 400 (wrong attributes data specified)
               * 404 (cluster not found in db)
               * 500 (cluster has no attributes)
        """
        cluster = self.get_object_or_404(
            objects.Cluster,
            cluster_id,
            log_404=(
                "warning",
                "Error: there is no cluster "
                "with id '{0}' in DB.".format(cluster_id)
            )
        )

        if not cluster.attributes:
            logger.error('ClusterAttributesDefaultsHandler: no attributes'
                         ' found for cluster_id %s' % cluster_id)
            raise self.http(500, "No attributes found!")

        cluster.attributes.editable = (
            objects.Cluster.get_default_editable_attributes(cluster))
        objects.Cluster.add_pending_changes(cluster, "attributes")

        logger.debug('ClusterAttributesDefaultsHandler:'
                     ' editable attributes for cluster_id %s were reset'
                     ' to default' % cluster_id)
        return {"editable": cluster.attributes.editable}


class ClusterGeneratedData(BaseHandler):
    """Cluster generated data
    """

    @content_json
    def GET(self, cluster_id):
        """:returns: JSONized cluster generated data
        :http: * 200 (OK)
               * 404 (cluster not found in db)
        """
        cluster = self.get_object_or_404(objects.Cluster, cluster_id)
        return cluster.attributes.generated

class ClusterStartRoleHandler(BaseHandler):

    @content_json
    def POST(self):
        x=web.input(rolename='',clusterId='',clusterType='')
        cluster_type=int(x.clusterType)
        #用glance一个角色代表定制化环境整个停止和启动
        if cluster_type==4:
           startrole="glance" 
        elif cluster_type==5:
           startrole="ONEST"
        else:
           startrole=x.rolename
        cluster_id=int(x.clusterId)
        #使用web.py写入cookie
        web.setcookie("oprolename",startrole)
        cluster_rolestatus=db().query(ClusterRoleStatus).filter_by(cluster_id=cluster_id,cluster_role=startrole).first()
        if startrole != "all":
           if cluster_rolestatus:
              if cluster_type==5:
                 if cluster_rolestatus["role_status"]==3:
                    web.setcookie("opaction","started") #onest第一次启动后的启动
                 else:
                    web.setcookie("opaction","start") #onest第一次启动
              else:
                 web.setcookie("opaction","start")  #其他类型的启动
              objects.ClusterRoleStatusObject.update(cluster_rolestatus, data={'role_status': 2})
           else:
               web.setcookie("opaction","start")
               data={}
               data['cluster_id']=cluster_id
               data['cluster_role']=startrole
               data['role_status']=2
               objects.ClusterRoleStatusCollection.create(data)

           if cluster_type==4:
              logger.info(u'开始创建ip_map_role.json')
              jsondir="/opt/%s" %(cluster_id)
              #生产环境,目录只能创建一次如果已经存在再创建就会报错
              direxists=os.path.exists(jsondir)
              if direxists==False:
                 os.mkdir(jsondir)
              file_object =open("%s/ip_map_role.json" %jsondir, 'w+')

              #本地环境
              #file_object =open("ip_map_role.json", 'w')

              cluster=self.get_object_or_404(objects.Cluster, cluster_id)
              message={}
              rolenamelist=[]
              for node in cluster.nodes:
                  for role in node.role_list:
                      rolenamelist.append(role.name)
                  message[node.ip]=rolenamelist
                  rolenamelist=[]
              file_object.write(json.dumps(message, indent=4))
              file_object.close()

              logger.info(u'开始创建ip_map_uid.json')
              uidjsondir="/opt/%s" %(cluster_id)
              direxists=os.path.exists(uidjsondir)
              if direxists==False:
                 os.mkdir(uidjsondir)
              file_object =open("%s/ip_map_uid.json" %uidjsondir, 'w+')
              cluster=self.get_object_or_404(objects.Cluster, cluster_id)
              message={}

              for node in cluster.nodes:
                  message[node.ip]=node.id
                  
              file_object.write(json.dumps(message, indent=4))
              file_object.close()
              
              threads = []
              f1 = lambda : json.dumps({"result":"sucess"})
              pythoncmd="python /opt/start.py %d" %(cluster_id)
              #cmd=os.system(pythoncmd)
              f2 = lambda : os.system(pythoncmd)
              #time.sleep(50)
              t1 = threading.Thread(target=f1)
              t2 = threading.Thread(target=f2)
              threads.append(t1)
              threads.append(t2)
              for t in threads:
                  t.setDaemon(True)
                  t.start()
        else:  #点击的是一键启动
             if cluster_rolestatus:
                if cluster_type==5:
                   if cluster_rolestatus["role_status"]==3:
                      web.setcookie("opaction","started") #onest第一次启动后的启动
                   else:
                      web.setcookie("opaction","start") #onest第一次启动
                else:
                   web.setcookie("opaction","start")  #其他类型的启动
             else:
                web.setcookie("opaction","start") 

        return json.dumps({"result":"sucess"})


class ClusterStopRoleHandler(BaseHandler):

    @content_json
    def POST(self):
        x=web.input(rolename='',clusterId='',clusterType='')
        cluster_type=int(x.clusterType)
        if cluster_type==4:
           startrole="glance" 
        elif cluster_type==5:
           startrole="ONEST"
        else:
           startrole=x.rolename

        cluster_id=int(x.clusterId)
       
        web.setcookie("oprolename",startrole)
        web.setcookie("opaction","stop")
        
        if startrole !="all":
           cluster_rolestatus=db().query(ClusterRoleStatus).filter_by(cluster_id=cluster_id,cluster_role=startrole).first()
           if cluster_rolestatus:
              if cluster_type==5:
                 objects.ClusterRoleStatusObject.update(cluster_rolestatus, data={'role_status': 3})
              else:
                 objects.ClusterRoleStatusObject.update(cluster_rolestatus, data={'role_status': 1})
           else:
              data={}
              data['cluster_id']=cluster_id
              data['cluster_role']=startrole
              data['role_status']=1
              objects.ClusterRoleStatusCollection.create(data)

           if cluster_type==4:
              pythoncmd="python /opt/stop.py %d" %(cluster_id)
              cmd=os.system(pythoncmd)

        return json.dumps({"result":"sucess"})


class ClusterRoleStatusCollectionHandler(CollectionHandler):
    
    collection =objects.ClusterRoleStatusCollection
