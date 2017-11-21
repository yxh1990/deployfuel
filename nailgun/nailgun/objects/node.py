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
Node-related objects and collections
"""
import operator
import traceback

from datetime import datetime

from netaddr import IPAddress
from netaddr import IPNetwork
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import subqueryload_all

from nailgun import consts

from nailgun.objects.serializers.node import NodeSerializer

from nailgun.db import db
from nailgun.db.sqlalchemy import models
from nailgun.errors import errors
from nailgun.logger import logger

from nailgun.objects import Cluster
from nailgun.objects import NailgunCollection
from nailgun.objects import NailgunObject
from nailgun.objects import Notification
from nailgun.settings import settings
from nailgun.common.commonutil import CommonUtil

class Node(NailgunObject):
    """Node object
    """

    #: SQLAlchemy model for Node
    model = models.Node

    #: Serializer for Node
    serializer = NodeSerializer

    #: Node JSON schema
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "Node",
        "description": "Serialized Node object",
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "cluster_id": {"type": "number"},
            "name": {"type": "string"},
            "status": {
                "type": "string",
                "enum": list(consts.NODE_STATUSES)
            },
            "group_id": {"type": "number"},
            "meta": {"type": "object"},
            "mac": {"type": "string"},
            "fqdn": {"type": "string"},
            "manufacturer": {"type": "string"},
            "platform_name": {"type": "string"},
            "kernel_params": {"type": "string"},
            "progress": {"type": "number"},
            "os_platform": {"type": "string"},
            "pending_addition": {"type": "boolean"},
            "pending_deletion": {"type": "boolean"},
            "error_type": {
                "type": "string",
                "enum": list(consts.NODE_ERRORS)
            },
            "error_msg": {"type": "string"},
            "online": {"type": "boolean"},
            "roles": {"type": "array"},
            "pending_roles": {"type": "array"},
            "agent_checksum": {"type": "string"}
        }
    }

    @classmethod
    def get_by_mac_or_uid(cls, mac=None, node_uid=None):
        """Get Node instance by MAC or ID.

        :param mac: MAC address as string
        :param node_uid: Node ID
        :returns: Node instance
        """
        node = None
        if not mac and not node_uid:
            return node

        q = db().query(cls.model)
        if mac:
            node = q.filter_by(mac=mac.lower()).first()
        else:
            node = q.get(node_uid)
        return node

    @classmethod
    def get_by_ip(cls,ip=None):
        node=None
        if not ip:
            return node

        q = db().query(cls.model)
        node=q.filter_by(ip=ip).first()
        return node

    @classmethod
    def get_by_powerip(cls,powerip=None):
        node = None
        if not powerip:
            return node
        q=db().query(cls.model)
        node = q.filter_by(power_ip=powerip).first()
        return node

    @classmethod
    def get_by_mac_phymachine(cls, interfaces=None):
        phymachine=None
        if not interfaces:
            return phymachine

        q=db().query(models.PhysicalMachineInfo)
        if interfaces:
            #phymachine=q.filter_by(mac=mac.lower()).first()
            macsupper=[]
            macs=[]
            logger.info("start check interfaces.......")
            for n in interfaces:
                macs.append(n["mac"].lower())
                macsupper.append(n["mac"].upper())
            macs.extend(macsupper)
            phymachine=q.filter(models.PhysicalMachineInfo.mac.in_(n for n in macs)).first()
            
        logger.info("发现的mac地址组合 %s",macs)    
        return phymachine


    @classmethod
    def get_by_meta(cls, meta):
        """Search for instance using mac, node id or interfaces

        :param meta: dict with nodes metadata
        :returns: Node instance
        """
        node = cls.get_by_mac_or_uid(
            mac=meta.get('mac'), node_uid=meta.get('id'))

        if not node:
            can_search_by_ifaces = all([
                meta.get('meta'), meta['meta'].get('interfaces')])

            if can_search_by_ifaces:
                node = cls.search_by_interfaces(meta['meta']['interfaces'])

        return node

    @classmethod
    def search_by_interfaces(cls, interfaces):
        """Search for instance using MACs on interfaces

        :param interfaces: dict of Node interfaces
        :returns: Node instance
        """
        return db().query(cls.model).join(
            models.NodeNICInterface,
            cls.model.nic_interfaces
        ).filter(
            models.NodeNICInterface.mac.in_(
                [n["mac"].lower() for n in interfaces]
            )
        ).first()

    @classmethod
    def should_have_public(cls, instance):
        """Determine whether this node has Public network.

        :param instance: Node DB instance
        :returns: True when node has Public network
        """
        #把公开网段改成了业务网段,所有node都必须有
        # if Cluster.should_assign_public_to_all_nodes(instance.cluster):
        #     return True
        # ctrl = set(['primary-controller', 'controller', 'zabbix-server'])
        # if ctrl & (set(instance.roles) or set(instance.pending_roles)):
        #     return True
        return True

    @classmethod
    def get_admin_physical_iface(cls, instance):
        """Returns node's physical iface.

        In case if we have bonded admin iface, first
        of the bonded ifaces will be returned

        :param instance: Node instance
        :returns: interface instance
        """
        admin_iface = Cluster.get_network_manager(instance.cluster) \
            .get_admin_interface(instance)

        if admin_iface.type != consts.NETWORK_INTERFACE_TYPES.bond:
            return admin_iface
        
        logger.info(admin_iface.slaves)
        for slave in admin_iface.slaves:

            if slave.pxe or slave.mac == instance.mac:
                return slave

        return admin_iface.slaves[-1]

        
    @classmethod
    def create(cls, data):
        """Create Node instance with specified parameters in DB.
        This includes:

        * generating its name by MAC (if name is not specified in data)
        * adding node to Cluster (if cluster_id is not None in data) \
        (see :func:`add_into_cluster`) with specified roles \
        (see :func:`update_roles` and :func:`update_pending_roles`)
        * creating interfaces for Node in DB (see :func:`update_interfaces`)
        * creating default Node attributes (see :func:`create_attributes`)
        * creating default volumes allocation for Node \
        (see :func:`update_volumes`)
        * creating Notification about newly discovered Node \
        (see :func:`create_discover_notification`)

        :param data: dictionary of key-value pairs as object fields
        :returns: Node instance
        """
       
        data["timestamp"] = datetime.now()
        data.pop("id", None)

        #TODO(enchantner): fix this temporary hack in clients
        if "cluster_id" not in data and "cluster" in data:
            cluster_id = data.pop("cluster", None)
            data["cluster_id"] = cluster_id

        roles = data.pop("roles", None)
        pending_roles = data.pop("pending_roles", None)
        
        if "meta" not in data:
            new_node_meta={}
        else:
            new_node_meta = data["meta"]
        #phymachine=cls.get_by_mac_phymachine(data['mac'].lower())
        logger.info(u"新发现节点添加函数.....")
        #logger.info(new_node_meta)
        data['user_set']={'mysql_disk':'""','var_dir_disk':'""'}
        phymachine=cls.get_by_mac_phymachine(new_node_meta['interfaces'])
        data["power_ip"]=data['ip']
        if phymachine:
           data["node_type"]=phymachine.use_type
           data['ip']=phymachine.ip
           if "name" not in data:
            data["name"] = "{0}".format(
               phymachine.name
            )
        else:
            if "name" not in data:
               splitip=data['ip'].split(".")
               data["name"] = "node{0}".format(
               splitip[-1]
            )
            data["node_type"]=-1

        new_node_cluster_id = data.pop("cluster_id", None)
        #删除集群的时候,在重启node之前,node还会上报数据,但此时数据库中
        #已经删除此node记录,提交的mac在物理机表中也不存在,安装完操作系统
        #后也获取不到interfaces的信息.所以会新增一条未分配的node,影响node
        #安装完bootstrap系统的上报.
        #在安装完bootstrap系统后,新增节点的时候先删除node_type=-1 and nodeip=data['ip']
        cls.deleteconfictnode(data)
        new_node = super(Node, cls).create(data)
        new_node.create_meta(new_node_meta,new_node.ip,new_node.mac)
        db().flush()
        
        #修改ip地址和meta信息中的ip地址
        #cls.update_nodeip(new_node)

        # Add interfaces for node from 'meta'.
        if new_node.meta and new_node.meta.get('interfaces'):
            cls.update_interfaces(new_node)

        # adding node into cluster
        if new_node_cluster_id:
            cls.add_into_cluster(new_node, new_node_cluster_id)

        # updating roles
        if roles is not None:
            cls.update_roles(new_node, roles)
        if pending_roles is not None:
            cls.update_pending_roles(new_node, pending_roles)

        # creating attributes
        cls.create_attributes(new_node)
        cls.update_volumes(new_node)
        cls.copyfile_to_agent(new_node.power_ip)
        cls.create_discover_notification(new_node)
        return new_node
    

    @classmethod
    def deleteconfictnode(cls,data):
        #删除环境的时候node的ip已被设置成物理机信息表中的ip,所以其在将要删除之前
        #上报过来的数据ip是物理机设置的ip.而node在装完bootstrap系统的时候ip被设置
        #为物理机信息表中ip而此时真正能访问node的ip是power_ip
        nodes_to_delete = db().query(models.Node).filter_by(node_type = -1).filter_by(ip = data["ip"]).all()
        map(db().delete, nodes_to_delete)
        logger.info(u"成功删除{0}条ip为{1}冲突类型为未分配的节点数".format(len(nodes_to_delete),data['ip']))
        db().commit()

    @classmethod
    def update_nodeip(cls, instance):
       phy=cls.get_by_mac_phymachine(instance.mac)
       newmeta=cls.update_node_meta(instance)
       if phy.ip:
          Node.update(instance,{'ip': phy.ip})
          db().refresh(instance)
       logger.info('success update node ip') 

    @classmethod
    def update_nodetype(cls,instance,node_type):
        #Node.update(instance,{'node_type': int(node_type)})
        #在下面的update函数中执行了node_type=instance.node_type所以执行无效.
        #只有处于discover状态下才能修改节点用处类型
        if instance.status in ("discover"):
           super(Node, cls).update(instance, {'node_type': int(node_type),'cluster_id':None,'group_id':None})
        logger.info('success update node {0} to type {1}'.format(instance.ip,node_type))

    @classmethod
    def copyfile_to_agent(cls,power_ip,filesrc=None,targetsrc=None):
        util=CommonUtil(ip=power_ip)
        if filesrc:
           filesrc = filesrc
        else:
           filesrc = "/opt/net_probe.rb"
        if targetsrc:
           targetsrc = targetsrc
        else:   
           targetsrc = "/usr/libexec/mcollective/mcollective/agent/"
        util.copyfile(filesrc,targetsrc,"mcollective")

    @classmethod
    def assign_group(cls, instance):
        if instance.group_id is None and instance.ip:
            admin_ngs = db().query(models.NetworkGroup).filter_by(
                name="fuelweb_admin")
            ip = IPAddress(instance.ip)

            for ng in admin_ngs:
                if ip in IPNetwork(ng.cidr):
                    instance.group_id = ng.group_id
                    break

        if not instance.group_id:
            instance.group_id = Cluster.get_default_group(instance.cluster).id

        db().add(instance)
        db().flush()

    @classmethod
    def create_attributes(cls, instance):
        """Create attributes for Node instance

        :param instance: Node instance
        :returns: NodeAttributes instance
        """
        new_attributes = models.NodeAttributes()
        instance.attributes = new_attributes
        db().add(new_attributes)
        db().add(instance)
        db().flush()
        return new_attributes

    @classmethod
    def update_interfaces(cls, instance):
        """Update interfaces for Node instance using Cluster
        network manager (see :func:`get_network_manager`)

        :param instance: Node instance
        :returns: None
        """
        try:
            network_manager = Cluster.get_network_manager(instance.cluster)

            network_manager.check_interfaces_correctness(instance)
            network_manager.update_interfaces_info(instance)

            db().refresh(instance)
        except errors.InvalidInterfacesInfo as exc:
            logger.warning(
                "Failed to update interfaces for node '%s' - invalid info "
                "in meta: %s", instance.human_readable_name, exc.message
            )
            logger.warning(traceback.format_exc())

    @classmethod
    def set_volumes(cls, instance, volumes_data):
        """Set volumes for Node instance from JSON data.
        Adds pending "disks" changes for Cluster which Node belongs to

        :param instance: Node instance
        :param volumes_data: JSON with new volumes data
        :returns: None
        """
        db().query(models.NodeAttributes).filter_by(
            node_id=instance.id
        ).update({'volumes': volumes_data})
        db().flush()
        db().refresh(instance)

    @classmethod
    def update_volumes(cls, instance):
        """Update volumes for Node instance.
        Adds pending "disks" changes for Cluster which Node belongs to

        :param instance: Node instance
        :returns: None
        """
        attrs = instance.attributes
        if not attrs:
            attrs = cls.create_attributes(instance)

        try:
            attrs.volumes = instance.volume_manager.gen_volumes_info()
        except Exception as exc:
            msg = (
                u"Failed to generate volumes "
                u"info for node '{0}': '{1}'"
            ).format(
                instance.name or instance.mac or instance.id,
                str(exc) or "see logs for details"
            )
            logger.warning(traceback.format_exc())
            Notification.create({
                "topic": "error",
                "message": msg,
                "node_id": instance.id
            })

        if instance.cluster_id:
            Cluster.add_pending_changes(
                instance.cluster,
                "disks",
                node_id=instance.id
            )

        db().add(attrs)
        db().flush()

    @classmethod
    def create_discover_notification(cls, instance):
        """Create notification about discovering new Node

        :param instance: Node instance
        :returns: None
        """
        try:
            # we use multiplier of 1024 because there are no problems here
            # with unfair size calculation
            ram = str(round(float(
                instance.meta['memory']['total']) / 1073741824, 1)) + " GB RAM"
        except Exception:
            logger.warning(traceback.format_exc())
            ram = "unknown RAM"

        try:
            # we use multiplier of 1000 because disk vendors specify HDD size
            # in terms of decimal capacity. Sources:
            # http://knowledge.seagate.com/articles/en_US/FAQ/172191en
            # http://physics.nist.gov/cuu/Units/binary.html
            hd_size = round(
                float(
                    sum(
                        [d["size"] for d in instance.meta["disks"]]
                    ) / 1000000000
                ),
                1
            )
            # if HDD > 100 GB we show it's size in TB
            if hd_size > 100:
                hd_size = str(hd_size / 1000) + " TB HDD"
            else:
                hd_size = str(hd_size) + " GB HDD"
        except Exception:
            logger.warning(traceback.format_exc())
            hd_size = "unknown HDD"

        cores = str(instance.meta.get('cpu', {}).get('total', "unknown"))

        Notification.create({
            "topic": "discover",
            "message": u"发现一个新的节点: "
                       u"{0} CPUs / {1} / {2} ".format(cores, ram, hd_size),
            "node_id": instance.id
        })

    @classmethod
    def update(cls, instance, data):
        """Update Node instance with specified parameters in DB.
        This includes:

        * adding node to Cluster (if cluster_id is not None in data) \
        (see :func:`add_into_cluster`)
        * updating roles for Node if it belongs to Cluster \
        (see :func:`update_roles` and :func:`update_pending_roles`)
        * removing node from Cluster (if cluster_id is None in data) \
        (see :func:`remove_from_cluster`)
        * updating interfaces for Node in DB (see :func:`update_interfaces`)
        * creating default Node attributes (see :func:`create_attributes`)
        * updating volumes allocation for Node using Cluster's Release \
        metadata (see :func:`update_volumes`)

        :param data: dictionary of key-value pairs as object fields
        :returns: Node instance
        """
        
        data.pop("id", None)
        data.pop("network_data", None)

        roles = data.pop("roles", None)
        pending_roles = data.pop("pending_roles", None)
        new_meta = data.pop("meta", None)
        
        disks_changed = None
        if new_meta and "disks" in new_meta and "disks" in instance.meta:
            key = operator.itemgetter("name")

            new_disks = sorted(new_meta["disks"], key=key)
            old_disks = sorted(instance.meta["disks"], key=key)

            disks_changed = (new_disks != old_disks)

        # TODO(enchantner): fix this temporary hack in clients
        if "cluster_id" not in data and "cluster" in data:
            cluster_id = data.pop("cluster", None)
            data["cluster_id"] = cluster_id

        if new_meta:
            instance.update_meta(new_meta)
            # The call to update_interfaces will execute a select query for
            # the current instance. This appears to overwrite the object in the
            # current session and we lose the meta changes.
            db().flush()
            # smarter check needed
            cls.update_interfaces(instance)

        cluster_changed = False
        if "cluster_id" in data:
            new_cluster_id = data.pop("cluster_id")
            if instance.cluster_id:
                if new_cluster_id is None:
                    # removing node from cluster
                    cluster_changed = True
                    cls.remove_from_cluster(instance)
                elif new_cluster_id != instance.cluster_id:
                    # changing node cluster to another
                    # (is currently not allowed)
                    raise errors.CannotUpdate(
                        u"Changing cluster on the fly is not allowed"
                    )
            else:
                if new_cluster_id is not None:
                    # assigning node to cluster
                    cluster_changed = True
                    cls.add_into_cluster(instance, new_cluster_id)

        if "group_id" in data:
            new_group_id = data.pop("group_id")
            if instance.group_id != new_group_id:
                nm = Cluster.get_network_manager(instance.cluster)
                nm.clear_assigned_networks(instance)
                nm.clear_bond_configuration(instance)
            instance.group_id = new_group_id
            cls.add_into_cluster(instance, instance.cluster_id)
            
        data["node_type"]=instance.node_type
        if 'nochange_powerip' not in data:
            data["power_ip"]=instance.power_ip
            
        if "name" in data:
            instance.name=data.pop("name")
        #logger.info("这是data['name']的值是 %s",data["name"])
        #data["name"]=instance.name
        # calculating flags
        roles_changed = (
            roles is not None and set(roles) != set(instance.roles)
        )
        pending_roles_changed = (
            pending_roles is not None and
            set(pending_roles) != set(instance.pending_roles)
        )

        super(Node, cls).update(instance, data)

        if roles_changed:
            cls.update_roles(instance, roles)
        if pending_roles_changed:
            cls.update_pending_roles(instance, pending_roles)

        if any((
            roles_changed,
            pending_roles_changed,
            cluster_changed,
            disks_changed,
        )) and instance.status not in (
            consts.NODE_STATUSES.provisioning,
            consts.NODE_STATUSES.deploying
        ):
            cls.update_volumes(instance)

        return instance

    @classmethod
    def reset_to_discover(cls, instance):
        """Flush database objects which is not consistent with actual node
           configuration in the event of resetting node to discover state

        :param instance: Node database object
        :returns: None
        """
        node_data = {
            "online": False,
            "status": consts.NODE_STATUSES.discover,
            "pending_addition": True,
            "pending_deletion": False,
        }
        cls.update_volumes(instance)
        cls.update(instance, node_data)
        cls.move_roles_to_pending_roles(instance)
        # when node reseted to discover:
        # - cobbler system is deleted
        # - mac to ip mapping from dnsmasq.conf is deleted
        # imho we need to revert node to original state, as it was
        # added to cluster (without any additonal state in database)
        #Cluster是导入的objects/Cluster类
        netmanager = Cluster.get_network_manager()
        netmanager.clear_assigned_ips(instance)
        db().flush()

    @classmethod
    def update_by_agent(cls, instance, data):
        """Update Node instance with some specific cases for agent.

        * don't update provisioning or error state back to discover
        * don't update volume information if disks arrays is empty

        :param data: dictionary of key-value pairs as object fields
        :returns: Node instance
        """
        # don't update provisioning and error back to discover
        if instance.status in ('provisioning', 'error'):
            if data.get('status', 'discover') == 'discover':
                logger.debug(
                    u"Node {0} has provisioning or error status - "
                    u"status not updated by agent".format(
                        instance.human_readable_name
                    )
                )

                data['status'] = instance.status

        # don't update volume information, if agent has sent an empty array
        meta = data.get('meta', {})
        if meta and len(meta.get('disks', [])) == 0 \
                and instance.meta.get('disks'):

            logger.warning(
                u'Node {0} has received an empty disks array - '
                u'volume information will not be updated'.format(
                    instance.human_readable_name
                )
            )
            meta['disks'] = instance.meta['disks']

        #(dshulyak) change this verification to NODE_STATUSES.deploying
        # after we will reuse ips from dhcp range
        netmanager = Cluster.get_network_manager()
        admin_ng = netmanager.get_admin_network_group(instance.id)
        if data.get('ip') and not netmanager.is_same_network(data['ip'],
                                                             admin_ng.cidr):
            logger.debug(
                'Corrupted network data %s, skipping update',
                instance.id)
            return instance
        #环境重置被调用和删除环境
        #data包含status,agent_checksum,ip等,不包含name

        data["power_ip"]=data["ip"]

        data["ip"]=instance.ip
        #meta里面的ip也需要修改
        if 'meta' in data:
            instance.create_meta(meta,instance.ip,instance.mac)
            db().flush()
            cls.update_interfaces(instance)
            phymachine=cls.get_by_mac_phymachine(meta['interfaces'])
            if phymachine:
               if "name" not in data:
                   data["name"] = "{0}".format(
                         phymachine.name
                   )
        logger.info(data)
        return cls.update(instance, data)

    @classmethod
    def update_roles(cls, instance, new_roles):
        """Update roles for Node instance.
        Logs an error if node doesn't belong to Cluster

        :param instance: Node instance
        :param new_roles: list of new role names
        :returns: None
        """
        if not instance.cluster_id:
            logger.warning(
                u"Attempting to assign roles to node "
                u"'{0}' which isn't added to cluster".format(
                    instance.name or instance.id
                )
            )
            return

        if new_roles:
            instance.role_list = db().query(models.Role).filter_by(
                release_id=instance.cluster.release_id,
            ).filter(
                models.Role.name.in_(new_roles)
            ).all()
        else:
            instance.role_list = []
        db().flush()
        db().refresh(instance)

    @classmethod
    def update_pending_roles(cls, instance, new_pending_roles):
        """Update pending_roles for Node instance.
        Logs an error if node doesn't belong to Cluster

        :param instance: Node instance
        :param new_pending_roles: list of new pending role names
        :returns: None
        """
        if not instance.cluster_id:
            logger.warning(
                u"Attempting to assign pending roles to node "
                u"'{0}' which isn't added to cluster".format(
                    instance.name or instance.id
                )
            )
            return

        logger.debug(
            u"Updating pending roles for node {0}: {1}".format(
                instance.id,
                new_pending_roles
            )
        )

        if new_pending_roles == []:
            instance.pending_role_list = []
            #TODO(enchantner): research why the hell we need this
            Cluster.clear_pending_changes(
                instance.cluster,
                node_id=instance.id
            )
        else:
            instance.pending_role_list = db().query(models.Role).filter_by(
                release_id=instance.cluster.release_id,
            ).filter(
                models.Role.name.in_(new_pending_roles)
            ).all()

        db().flush()
        db().refresh(instance)

    @classmethod
    def add_into_cluster(cls, instance, cluster_id):
        """Adds Node to Cluster by its ID.
        Also assigns networks by default for Node.

        :param instance: Node instance
        :param cluster_id: Cluster ID
        :returns: None
        """
        instance.cluster_id = cluster_id
        db().flush()
        cls.assign_group(instance)
        network_manager = Cluster.get_network_manager(instance.cluster)
        network_manager.assign_networks_by_default(instance)
        cls.add_pending_change(instance, consts.CLUSTER_CHANGES.interfaces)

    @classmethod
    def add_pending_change(cls, instance, change):
        """Add pending change into Cluster.

        :param instance: Node instance
        :param change: string value of cluster change
        :returns: None
        """
        if instance.cluster:
            Cluster.add_pending_changes(
                instance.cluster, change, node_id=instance.id
            )

    @classmethod
    def get_network_manager(cls, instance=None):
        """Get network manager for Node instance.
        If instance is None then default NetworkManager is returned

        :param instance: Node instance
        :param cluster_id: Cluster ID
        :returns: None
        """
        if not instance.cluster:
            from nailgun.network.manager import NetworkManager
            return NetworkManager
        else:
            return Cluster.get_network_manager(instance.cluster)

    @classmethod
    def remove_from_cluster(cls, instance):
        """Remove Node from Cluster.
        Also drops networks assignment for Node and clears both
        roles and pending roles

        :param instance: Node instance
        :returns: None
        """
        if instance.cluster:
            Cluster.clear_pending_changes(
                instance.cluster,
                node_id=instance.id
            )
            netmanager = Cluster.get_network_manager(
                instance.cluster
            )
            netmanager.clear_assigned_networks(instance)
            netmanager.clear_bond_configuration(instance)
        cls.update_roles(instance, [])
        cls.update_pending_roles(instance, [])
        cls.remove_replaced_params(instance)
        instance.cluster_id = None
        instance.group_id = None
        instance.kernel_params = None
        #instance.reset_name_to_default()
        db().flush()
        db().refresh(instance)

    @classmethod
    def move_roles_to_pending_roles(cls, instance):
        """Move roles to pending_roles
        """
        instance.pending_roles += instance.roles
        instance.roles = []
        db().flush()

    @classmethod
    def make_slave_name(cls, instance):
        #return u"node-{node_id}".format(node_id=instance.name)
        return instance.name

    @classmethod
    def make_slave_fqdn(cls, instance):
        return u"{instance_name}.{dns_domain}" \
            .format(instance_name=cls.make_slave_name(instance),
                    dns_domain=settings.DNS_DOMAIN)

    @classmethod
    def get_kernel_params(cls, instance):
        """Return cluster kernel_params if they wasnot replaced by
           custom params.
        """
        # return (instance.kernel_params or
        #         Cluster.get_default_kernel_params(instance.cluster))
        if instance.cluster:
            return (instance.kernel_params or Cluster.get_default_kernel_params(instance.cluster))
        else:
            return "console=ttyS0,9600 console=tty0 biosdevname=0 crashkernel=none rootdelay=90 nomodeset"

    @classmethod
    def remove_replaced_params(cls, instance):
        instance.replaced_deployment_info = []
        instance.replaced_provisioning_info = {}

    @classmethod
    def all_roles(cls, instance):
        roles = []
        associations = (instance.role_associations +
                        instance.pending_role_associations)
        for assoc in associations:
            if assoc.primary:
                roles.append('primary-{0}'.format(assoc.role_obj.name))
            else:
                roles.append(assoc.role_obj.name)
        return sorted(roles)


class NodeCollection(NailgunCollection):
    """Node collection
    """

    #: Single Node object class
    single = Node

    @classmethod
    def eager_nodes_handlers(cls, iterable):
        """Eager load objects instances that is used in nodes handler.

        :param iterable: iterable (SQLAlchemy query)
        :returns: iterable (SQLAlchemy query)
        """
        options = (
            joinedload('cluster'),
            joinedload('role_list'),
            joinedload('pending_role_list'),
            subqueryload_all('nic_interfaces.assigned_networks_list'),
            subqueryload_all('bond_interfaces.assigned_networks_list'),
            subqueryload_all('ip_addrs.network_data')
        )
        return cls.eager_base(iterable, options)

    @classmethod
    def update_slave_nodes_fqdn(cls, instances):
        for n in instances:
            n.fqdn = cls.single.make_slave_fqdn(n)

        db().flush()

    @classmethod
    def prepare_for_lt_6_1_deployment(cls, instances):
        """Prepare environment for deployment,
        assign management, public, storage ips
        """
        cls.update_slave_nodes_fqdn(instances)

        # TODO(enchantner): check network manager instance for each node
        netmanager = Cluster.get_network_manager()
        if instances:
            netmanager.assign_ips(instances, 'management')
            netmanager.assign_ips(instances, 'public')
            netmanager.assign_ips(instances, 'storage')
            netmanager.assign_admin_ips(instances)


    @classmethod
    def prepare_for_deployment(cls, instances):
        """Prepare environment for deployment,
        assign management, public, storage ips
        """
        #这里处理已经装完操作系统情况
        cls.prepare_for_provisioning(instances)

        cls.update_slave_nodes_fqdn(instances)

        # TODO(enchantner): check network manager instance for each node
        netmanager = Cluster.get_network_manager()
        if instances:
            netmanager.assign_ips(instances, 'management')
            netmanager.assign_ips(instances, 'public')
            netmanager.assign_ips(instances, 'storage')
            netmanager.assign_admin_ips(instances)

    @classmethod
    def prepare_for_provisioning(cls, instances):
        """Prepare environment for provisioning,
        update fqdns, assign admin IPs
        """
        cls.update_slave_nodes_fqdn(instances)
        netmanager = Cluster.get_network_manager()
        netmanager.assign_admin_ips(instances)

    @classmethod
    def lock_nodes(cls, instances):
        """Locking nodes instances, fetched before, but required to be locked
        :param instances: list of nodes
        :return: list of locked nodes
        """
        instances_ids = [instance.id for instance in instances]
        q = cls.filter_by_list(None, 'id', instances_ids, order_by='id')
        return cls.lock_for_update(q).all()

    @classmethod
    def get_by_group_id(cls, group_id):
        return cls.filter_by(None, group_id=group_id)


class NodeNICInterface(NailgunObject):

    #: SQLAlchemy model for NodeNICInterface
    model = models.NodeNICInterface

class NodeNICInterfaceCollection(NailgunCollection):

    single = NodeNICInterface
