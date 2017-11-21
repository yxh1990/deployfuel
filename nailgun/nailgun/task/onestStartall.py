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

import copy
from nailgun.consts import CLUSTER_STATUSES
from nailgun.consts import NODE_STATUSES
from nailgun.consts import TASK_NAMES
from nailgun.consts import TASK_STATUSES
from nailgun.db import db
from nailgun.db.sqlalchemy.models import Cluster
from nailgun.db.sqlalchemy.models import Task
from nailgun.db.sqlalchemy.models import ClusterdeployMsg
from nailgun.db.sqlalchemy.models import Role
from nailgun.db.sqlalchemy.models import ClusterRoleStatus
from nailgun.logger import logger
from nailgun import objects
from nailgun.openstack.common import jsonutils



class StartAllRole(object):

    def make_deploy_msgs(self,cluster,supertask,deploymsg,status):
        #ebs_rolelist=["gangliasrv","nagiossrv","gangliacli","nagioscli"]
        task_messages=[]
        ebs_rolelist=["gangliasrv","nagiossrv","gangliacli","nagioscli","management","watcher","tgtd","rsyslogsrv","rsyslogcli"]
        if status== 1:
           ebs_rolelist=["rsyslogcli","rsyslogsrv","tgtd","watcher","management","nagioscli","gangliacli","nagiossrv","gangliasrv"]

        deployment_info_list=deploymsg['args']['deployment_info']
        for deployment_info in deployment_info_list:
            for role in ebs_rolelist:
                if deployment_info["role"] == role:
                    task_deployment = supertask.create_subtask(TASK_NAMES.deployment)
                    db().commit()
                    newdeploymsg=copy.deepcopy(deploymsg)
                    newdeploymsg['respond_to']="start_stop_resp"
                    newdeploymsg['args']['task_uuid']=task_deployment.uuid

                    if status == 2:
                       deployment_info[role]['action']="start"
                       logger.info(u"匹配到角色{0},节点id {1},开始启动...".format(role,deployment_info["uid"]))
                    else:
                        deployment_info[role]['action']="stop"
                        logger.info(u"匹配到角色{0},节点id {1},开始停止...".format(role,deployment_info["uid"]))
                    newdeploymsg['args']['deployment_info']=[]
                    newdeploymsg['args']['deployment_info'].append(deployment_info)
                    task_messages.append(newdeploymsg)
                    task_deployment = objects.Task.get_by_uid(
                        task_deployment.id,
                        fail_if_not_found=True,
                        lock_for_update=True
                    )

                    # if failed to generate task message for orchestrator
                    # then task is already set to error
                    if task_deployment.status == TASK_STATUSES.error:
                       return supertask

                    task_deployment.cache = newdeploymsg
                    db().commit()
                    self.update_cluster_role_status(cluster,role,status)

                else:
                    continue
                    #代表此环境没有安装role角色
        #需要对task_messages按照role排序,否则多个节点有相同角色的时候将不是按照角色顺序执行
        new_task_messages=[]
        for ebsrole in ebs_rolelist:
            for task in task_messages:
                if task['args']['deployment_info'][0]['role'] == ebsrole:
                   new_task_messages.append(task)

        return new_task_messages


    def update_cluster_role_status(self,cluster,role,status):
        #此处只对ebs环境生效,对onest以及其他类型环境无用,rolestatus只有1和2没有3
        cluster_rolestatus=db().query(ClusterRoleStatus).filter_by(cluster_id=cluster.id,cluster_role=role).first()
        if cluster_rolestatus:
            if status==2:
               objects.ClusterRoleStatusObject.update(cluster_rolestatus, data={'role_status': 2})
            else:
               objects.ClusterRoleStatusObject.update(cluster_rolestatus, data={'role_status': 1})
        else:
            data={}
            data['cluster_id']=cluster.id
            data['cluster_role']=role
            if status==2:
               data['role_status']=2
            else:
               data['role_status']=1
            objects.ClusterRoleStatusCollection.create(data)


