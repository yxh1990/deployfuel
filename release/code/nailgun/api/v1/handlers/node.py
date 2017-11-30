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
Handlers dealing with nodes
"""

from datetime import datetime

import web
import json
from nailgun.openstack.common import jsonutils

from nailgun.api.v1.handlers.base import BaseHandler
from nailgun.api.v1.handlers.base import CollectionHandler
from nailgun.api.v1.handlers.base import content_json
from nailgun.api.v1.handlers.base import SingleHandler
from nailgun.api.v1.validators.network import NetAssignmentValidator
from nailgun.api.v1.validators.node import NodeValidator

from nailgun import consts
from nailgun import objects

from nailgun.objects.serializers.node import NodeInterfacesSerializer

from nailgun.db import db
from sqlalchemy import and_, not_
from nailgun.db.sqlalchemy.models import NetworkGroup
from nailgun.db.sqlalchemy.models import Node
from nailgun.db.sqlalchemy.models import NodeNICInterface

from nailgun.logger import logger
from nailgun import notifier
from nailgun.common.commonutil import CommonUtil

class NodeUsersetHandler(BaseHandler):

    @content_json
    def PUT(self):
        x=web.input(id='',userset={})
        node = objects.Node.get_by_uid(x.id)
        data=json.loads(x.userset)
        if node:
               objects.Node.update(node,{'user_set':data})
               new_node=objects.Node.get_by_uid(x.id)
        return {'result':'sucess'}

      
class NodeHandler(SingleHandler):
    single = objects.Node
    validator = NodeValidator


class NodeCollectionHandler(CollectionHandler):
    """Node collection handler
    """

    fields = ('id', 'name', 'meta', 'progress', 'roles', 'pending_roles',
              'status', 'mac', 'fqdn', 'ip', 'manufacturer', 'platform_name',
              'pending_addition', 'pending_deletion', 'os_platform',
              'error_type', 'online', 'cluster', 'uuid', 'network_data',
              'group_id')

    validator = NodeValidator
    collection = objects.NodeCollection

    @content_json
    def GET(self):
        """May receive cluster_id parameter to filter list
        of nodes

        :returns: Collection of JSONized Node objects.
        :http: * 200 (OK)
        """
        cluster_id = web.input(cluster_id=None,node_type=None).cluster_id
        node_type = web.input(cluster_id=None,node_type=None).node_type
     
        nodes = self.collection.all()
        if cluster_id ==None:
           nodes = nodes.filter_by(cluster_id=None)
        elif cluster_id:
           nodes = nodes.filter_by(cluster_id=cluster_id)
        if node_type==None:
           pass
        elif node_type:
           nodes=nodes.filter_by(node_type=node_type)

        if cluster_id==None and node_type==None:
           nodes=self.collection.all()

        return self.collection.to_json(nodes)

    @content_json
    def PUT(self):
        """:returns: Collection of JSONized Node objects.
        :http: * 200 (nodes are successfully updated)
               * 400 (invalid nodes data specified)
        """
        data = self.checked_data(
            self.validator.validate_collection_update
        )

        nodes_updated = []
        for nd in data:
            node = self.collection.single.get_by_meta(nd)

            if not node:
                raise self.http(404, "Can't find node: {0}".format(nd))
            self.collection.single.update(node, nd)
            nodes_updated.append(node.id)
        # we need eagerload everything that is used in render
        nodes = self.collection.filter_by_id_list(
            self.collection.eager_nodes_handlers(None),
            nodes_updated
        )
        return self.collection.to_json(nodes)


class NodeAgentHandler(BaseHandler):

    collection = objects.NodeCollection
    validator = NodeValidator

    @content_json
    def PUT(self):
        #这个函数是个定时执行函数,用来监听所有节点的变化.
        #120s调用一次
        """:returns: node id.
        :http: * 200 (node are successfully updated)
               * 304 (node data not changed since last request)
               * 400 (invalid nodes data specified)
               * 404 (node not found)
        """
        data=jsonutils.loads(web.data())
        meta = data.get('meta', {})
        ip = data.get("ip")
        nodeinstance =  self.collection.single.get_by_ip(ip)
        if nodeinstance is None:
            logger.info("数据库中不存在ip为 {0} 的机器,使用powerip查询..".format(ip))
            #discover状态发送put请求的时候执行.
            nodeinstance = self.collection.single.get_by_powerip(ip)
            if nodeinstance is None:
                logger.info("数据库中不存在ip和powerip为 {0} 的机器,使用mac查询..".format(ip))
                #重置环境不会删除表中的nodes的数据,但会提交数据到此处,执行新增会引发mac冲突
                self.collection.single.copyfile_to_agent(data["ip"])
                data["nochange_powerip"] = True
                nodeinstance = self.collection.single.get_by_mac_or_uid(data['mac'])
                if nodeinstance is None:
                   logger.info("数据库中不存在当前提交过来的node数据,调用新增节点函数...")
                   self.collection.single.create(data)
                   return
        data['mac'] = nodeinstance.mac
        #ovsbind会提交过来一个不存在的mac地址
        # don't update interfaces information, if agent has sent an empty array
        # 删除集群后,重新发现节点是通过此函数,但是由于删除集群会先删除nodes表中的数据
        # 导致此处会出现异常,nodeinstance会为None
        if meta and len(meta.get('interfaces', [])) == 0 and nodeinstance.meta.get('interfaces'):
           logger.warning(u'Node {0} has received an empty interfaces array - '
                          u'interfaces information will not be updated'.format(
                             nodeinstance.human_readable_name
                          )
            )
           meta['interfaces'] = nodeinstance.meta['interfaces']

        nd = self.checked_data(self.validator.validate_update,data=jsonutils.dumps(data))

        node = self.collection.single.get_by_meta(nd)
        
        if not node:
            raise self.http(404, "Can't find node: {0}".format(nd))

        node.timestamp = datetime.now()

        #test copyfile
        #self.collection.single.copyfile_to_agent(node)

        if not node.online: #判断如果节点处于离线状态
            node.online = True
            msg = u"节点 '{0}' 已经重新上线".format(node.name)
            logger.info(msg)
            notifier.notify("discover", msg, node_id=node.id)
        db().flush()

        if 'agent_checksum' in nd and (
            node.agent_checksum == nd['agent_checksum']
        ):
            return {'id': node.id, 'cached': True}
        self.collection.single.update_by_agent(node, nd)
        return {"id": node.id}



class NodeNICsHandler(BaseHandler):
    """Node network interfaces handler
    """

    model = NodeNICInterface
    validator = NetAssignmentValidator
    serializer = NodeInterfacesSerializer

    @content_json
    def GET(self, node_id):
        """:returns: Collection of JSONized Node interfaces.
        :http: * 200 (OK)
               * 404 (node not found in db)
        """
        node = self.get_object_or_404(objects.Node, node_id)
        return map(self.render, node.interfaces)

    @content_json
    def PUT(self, node_id):
        """:returns: Collection of JSONized Node objects.
        :http: * 200 (nodes are successfully updated)
               * 400 (invalid nodes data specified)
        """
        interfaces_data = self.checked_data(
            self.validator.validate_structure_and_data, node_id=node_id)
        node_data = {'id': node_id, 'interfaces': interfaces_data}

        objects.Cluster.get_network_manager()._update_attrs(node_data)
        node = self.get_object_or_404(objects.Node, node_id)
        objects.Node.add_pending_change(
            node,
            consts.CLUSTER_CHANGES.interfaces
        )
        return map(self.render, node.interfaces)


class NodeCollectionNICsHandler(BaseHandler):
    """Node collection network interfaces handler
    """

    model = NetworkGroup
    validator = NetAssignmentValidator
    serializer = NodeInterfacesSerializer

    @content_json
    def PUT(self):
        """:returns: Collection of JSONized Node objects.
        :http: * 200 (nodes are successfully updated)
               * 400 (invalid nodes data specified)
        """
        data = self.checked_data(
            self.validator.validate_collection_structure_and_data)
        updated_nodes_ids = []
        for node_data in data:
            node_id = objects.Cluster.get_network_manager(
            )._update_attrs(node_data)
            updated_nodes_ids.append(node_id)
        updated_nodes = db().query(Node).filter(
            Node.id.in_(updated_nodes_ids)
        ).all()
        return [
            {
                "id": n.id,
                "interfaces": map(self.render, n.interfaces)
            } for n in updated_nodes
        ]


class NodeNICsDefaultHandler(BaseHandler):
    """Node default network interfaces handler
    """

    @content_json
    def GET(self, node_id):
        """:returns: Collection of default JSONized interfaces for node.
        :http: * 200 (OK)
               * 404 (node not found in db)
        """
        node = self.get_object_or_404(objects.Node, node_id)
        return self.get_default(node)

    def get_default(self, node):
        if node.cluster:
            return objects.Node.get_network_manager(
                node
            ).get_default_networks_assignment(node)


class NodeCollectionNICsDefaultHandler(NodeNICsDefaultHandler):
    """Node collection default network interfaces handler
    """

    validator = NetAssignmentValidator

    @content_json
    def GET(self):
        """May receive cluster_id parameter to filter list
        of nodes

        :returns: Collection of JSONized Nodes interfaces.
        :http: * 200 (OK)
        """
        cluster_id = web.input(cluster_id=None).cluster_id

        if cluster_id:
            nodes = \
                objects.NodeCollection.filter_by(None, cluster_id=cluster_id)
        else:
            nodes = objects.NodeCollection.all()

        return filter(lambda x: x is not None, map(self.get_default, nodes))


class NodesAllocationStatsHandler(BaseHandler):
    """Node allocation stats handler
    """

    @content_json
    def GET(self):
        """:returns: Total and unallocated nodes count.
        :http: * 200 (OK)
        """
        unallocated_nodes = db().query(Node).filter_by(cluster_id=None).count()
        total_nodes = \
            db().query(Node).count()
        return {'total': total_nodes,
                'unallocated': unallocated_nodes}


class NodeUpdateMetaHandler(BaseHandler):

    @content_json
    def PUT(self):
        x=web.input(id='',nodemeta={},ip='')
        node = objects.Node.get_by_uid(x.id)
        data=json.loads(x.nodemeta)
        nodeip=x.ip
        nodefqdn=x.ip+".domain.tld"
        if node:
               objects.Node.update(node,{'meta':data,'ip':nodeip,'fqdn':nodefqdn})
               new_node=objects.Node.get_by_uid(x.id)
        return {'result':'sucess'}



class NodeInterfaceCheckIp(BaseHandler):

    def GET(self):
        x=web.input(ip='',mac='')
        interface=db().query(NodeNICInterface).filter(NodeNICInterface.ip_addr==x.ip).filter(NodeNICInterface.mac!=x.mac).first()
        if interface:
           nodename=interface.node.name
           ethname=interface.name
           return json.dumps({'count':1,'nodename':nodename,'ethname':ethname})
        else:
           return json.dumps({'count':0})






