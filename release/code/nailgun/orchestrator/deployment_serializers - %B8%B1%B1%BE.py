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

"""Deployment serializers for orchestrator"""

from collections import defaultdict
from copy import deepcopy
from itertools import groupby

from netaddr import IPNetwork
from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

import math
import six
import json

from nailgun import objects

from nailgun import consts
from nailgun.db import db
from nailgun.db.sqlalchemy.models import NetworkGroup
from nailgun.db.sqlalchemy.models import Node
from nailgun.db.sqlalchemy.models import ClusterSetting
from nailgun.db.sqlalchemy.models import PhysicalMachineInfo
from nailgun.errors import errors
from nailgun.logger import logger
from nailgun.objects import Cluster
from nailgun.orchestrator import priority_serializers as ps
from nailgun.orchestrator import clustercustom_serializers as custom
from nailgun.orchestrator import clusterebs_serializers as ebs
from nailgun.orchestrator import clusteronest_serializers as onest
from nailgun.orchestrator import clustercloudmaster_serializers as cloudmaster
from nailgun.settings import settings
from nailgun.utils import dict_merge
from nailgun.utils import extract_env_version
from nailgun.volumes import manager as volume_manager
from nailgun.common.commonutil import CommonUtil


def get_nodes_not_for_deletion(cluster):
    """All clusters nodes except nodes for deletion."""
    return db().query(Node).filter(
        and_(Node.cluster == cluster,
             False == Node.pending_deletion)).order_by(Node.id)


class NetworkDeploymentSerializer(object):

    @classmethod
    def get_common_attrs(cls, cluster, attrs):
        """Cluster network attributes."""
        common = cls.network_provider_cluster_attrs(cluster)
        common.update(
            cls.network_ranges(Cluster.get_default_group(cluster).id))
        common.update({'master_ip': settings.MASTER_IP})
        common['nodes'] = deepcopy(attrs['nodes'])
        #

        # Addresses
        for node in get_nodes_not_for_deletion(cluster):
            netw_data = node.network_data
            addresses = {}
            for net in node.cluster.network_groups:
                if net.name == 'public' and \
                        not objects.Node.should_have_public(node):
                    continue
                if net.meta.get('render_addr_mask'):
                    addresses.update(cls.get_addr_mask(
                        netw_data,
                        net.name,
                        net.meta.get('render_addr_mask')))

            [n.update(addresses) for n in common['nodes']
             if n['uid'] == str(node.uid)]
        return common

    @classmethod
    def get_node_attrs(cls, node):
        """Node network attributes."""
        return cls.network_provider_node_attrs(node.cluster, node)

    @classmethod
    def network_provider_cluster_attrs(cls, cluster):
        raise NotImplementedError()

    @classmethod
    def network_provider_node_attrs(cls, cluster, node):
        raise NotImplementedError()

    @classmethod
    def network_ranges(cls, group_id):
        """Returns ranges for network groups
        except range for public network for each node
        """
        ng_db = db().query(NetworkGroup).filter_by(group_id=group_id).all()
        attrs = {}
        for net in ng_db:
            net_name = net.name + '_network_range'
            if net.meta.get("render_type") == 'ip_ranges':
                attrs[net_name] = cls.get_ip_ranges_first_last(net)
            elif net.meta.get("render_type") == 'cidr' and net.cidr:
                attrs[net_name] = net.cidr
        return attrs

    @classmethod
    def get_ip_ranges_first_last(cls, network_group):
        """Get all ip ranges in "10.0.0.0-10.0.0.255" format
        """
        return [
            "{0}-{1}".format(ip_range.first, ip_range.last)
            for ip_range in network_group.ip_ranges
        ]

    @classmethod
    def get_addr_mask(cls, network_data, net_name, render_name):
        """Get addr for network by name
        """
        nets = filter(
            lambda net: net['name'] == net_name,
            network_data)

        if not nets or 'ip' not in nets[0]:
            raise errors.CanNotFindNetworkForNode(
                'Cannot find network with name: %s' % net_name)

        net = nets[0]['ip']
        return {
            render_name + '_address': str(IPNetwork(net).ip),
            render_name + '_netmask': str(IPNetwork(net).netmask)
        }

    @staticmethod
    def get_admin_ip_w_prefix(node):
        """Getting admin ip and assign prefix from admin network."""
        network_manager = objects.Node.get_network_manager(node)
        admin_ip = network_manager.get_admin_ip_for_node(node.id)
        admin_ip = IPNetwork(admin_ip)

        # Assign prefix from admin network
        admin_net = IPNetwork(
            network_manager.get_admin_network_group(node.id).cidr
        )
        admin_ip.prefixlen = admin_net.prefixlen

        return str(admin_ip)


class NovaNetworkDeploymentSerializer(NetworkDeploymentSerializer):

    @classmethod
    def network_provider_cluster_attrs(cls, cluster):
        return {
            'novanetwork_parameters': cls.novanetwork_attrs(cluster),
            'dns_nameservers': cluster.network_config.dns_nameservers,
            'fixed_network_range': cluster.network_config.fixed_networks_cidr,
            'floating_network_range': [
                "{0}-{1}".format(ip_range[0], ip_range[1])
                for ip_range in cluster.network_config.floating_ranges
            ]
        }

    @classmethod
    def network_provider_node_attrs(cls, cluster, node):
        network_data = node.network_data
        interfaces = cls.configure_interfaces(node)
        cls.__add_hw_interfaces(interfaces, node.meta['interfaces'])

        # Interfaces assignment
        attrs = {'network_data': interfaces}
        attrs.update(cls.interfaces_list(network_data))

        if cluster.network_config.net_manager == 'VlanManager':
            attrs.update(cls.add_vlan_interfaces(node))

        return attrs

    @classmethod
    def novanetwork_attrs(cls, cluster):
        """Network configuration
        """
        attrs = {'network_manager': cluster.network_config.net_manager}

        # network_size is required for all managers, otherwise
        # puppet will use default (255)
        if attrs['network_manager'] == consts.NOVA_NET_MANAGERS.VlanManager:
            attrs['num_networks'] = \
                cluster.network_config.fixed_networks_amount
            attrs['vlan_start'] = \
                cluster.network_config.fixed_networks_vlan_start
            attrs['network_size'] = cluster.network_config.fixed_network_size
        elif (attrs['network_manager'] ==
              consts.NOVA_NET_MANAGERS.FlatDHCPManager):
            # We need set maximum available size for specific mask for FlatDHCP
            # because default 256 caused problem
            net_cidr = IPNetwork(cluster.network_config.fixed_networks_cidr)
            attrs['network_size'] = net_cidr.size
            attrs['num_networks'] = 1

        return attrs

    @classmethod
    def add_vlan_interfaces(cls, node):
        """Assign fixed_interfaces and vlan_interface.
        They should be equal.
        """
        net_manager = objects.Node.get_network_manager(node)
        fixed_interface = net_manager._get_interface_by_network_name(
            node.id, 'fixed')

        attrs = {'fixed_interface': fixed_interface.name,
                 'vlan_interface': fixed_interface.name}
        return attrs

    @classmethod
    def configure_interfaces(cls, node):
        """Configure interfaces
        """
        network_data = node.network_data
        interfaces = {}

        for network in network_data:
            network_name = network['name']
            name = cls.__make_interface_name(network.get('dev'),
                                             network.get('vlan'))

            interfaces.setdefault(name, {'interface': name, 'ipaddr': []})
            interface = interfaces[name]
            if network.get('ip'):
                interface['ipaddr'].append(network.get('ip'))

            if network_name == 'fuelweb_admin':
                admin_ip_addr = cls.get_admin_ip_w_prefix(node)
                interface['ipaddr'].append(admin_ip_addr)
            elif network_name == 'public' and network.get('gateway'):
                interface['gateway'] = network['gateway']
                interface['default_gateway'] = True

        for if_name, if_data in interfaces.iteritems():
            if len(if_data['ipaddr']) == 0:
                if_data['ipaddr'] = 'none'

        interfaces['lo'] = {'interface': 'lo', 'ipaddr': ['127.0.0.1/8']}

        return interfaces

    @classmethod
    def __make_interface_name(cls, name, vlan):
        """Make interface name
        """
        if name and vlan:
            return '.'.join([name, str(vlan)])
        return name

    @classmethod
    def __add_hw_interfaces(cls, interfaces, hw_interfaces):
        """Add interfaces which not represents in
        interfaces list but they are represented on node
        """
        for hw_interface in hw_interfaces:
            if hw_interface['name'] not in interfaces:
                interfaces[hw_interface['name']] = {
                    'interface': hw_interface['name'],
                    'ipaddr': "none"
                }

    @classmethod
    def interfaces_list(cls, network_data):
        """Generate list of interfaces
        """
        interfaces = {}
        for network in network_data:
            if_name = cls.__make_interface_name(
                network.get('dev'),
                network.get('vlan'))
            interfaces['%s_interface' % network['name']] = if_name
            if network['name'] == 'public':
                interfaces['floating_interface'] = if_name
        return interfaces


class NeutronNetworkDeploymentSerializer(NetworkDeploymentSerializer):

    @classmethod
    def network_provider_cluster_attrs(cls, cluster):
        """Cluster attributes."""
        attrs = {'quantum': True,
                 'quantum_settings': cls.neutron_attrs(cluster)}

        if cluster.mode == 'multinode':
            for node in cluster.nodes:
                if cls._node_has_role_by_name(node, 'controller'):
                    net_manager = objects.Node.get_network_manager(node)
                    mgmt_cidr = net_manager.get_node_network_by_netname(
                        node,
                        'management'
                    )['ip']
                    attrs['management_vip'] = mgmt_cidr.split('/')[0]
                    break

        return attrs

    @classmethod
    def network_provider_node_attrs(cls, cluster, node):
        """Serialize node, then it will be
        merged with common attributes
        """
        node_attrs = {'network_scheme': cls.generate_network_scheme(node)}
        node_attrs = cls.mellanox_settings(node_attrs, node)
        return node_attrs

    @classmethod
    def mellanox_settings(cls, node_attrs, node):
        """Serialize mellanox node attrs, then it will be
        merged with common attributes, if mellanox plugin or iSER storage
        enabled.
        """
        # Get Mellanox data
        neutron_mellanox_data =  \
            Cluster.get_attributes(node.cluster).editable\
            .get('neutron_mellanox', {})

        # Get storage data
        storage_data = \
            Cluster.get_attributes(node.cluster).editable.get('storage', {})

        # Get network manager
        nm = objects.Node.get_network_manager(node)

        # Init mellanox dict
        node_attrs['neutron_mellanox'] = {}

        # Find Physical port for VFs generation
        if 'plugin' in neutron_mellanox_data and \
           neutron_mellanox_data['plugin']['value'] == 'ethernet':
            node_attrs = cls.set_mellanox_ml2_config(node_attrs, node, nm)

        # Fix network scheme to have physical port for RDMA if iSER enabled
        if 'iser' in storage_data and storage_data['iser']['value']:
            node_attrs = cls.fix_iser_port(node_attrs, node, nm)

        return node_attrs

    @classmethod
    def set_mellanox_ml2_config(cls, node_attrs, node, nm):
        """Change the yaml file to include the required configurations
        for ml2 mellanox mechanism driver.
        should be called only in case of mellanox SR-IOV plugin usage.
        """
        # Set physical port for SR-IOV virtual functions
        node_attrs['neutron_mellanox']['physical_port'] = \
            nm.get_node_network_by_netname(node, 'private')['dev']

        # Set ML2 eswitch section conf
        ml2_eswitch = {}
        ml2_eswitch['vnic_type'] = 'hostdev'
        ml2_eswitch['apply_profile_patch'] = True
        node_attrs['neutron_mellanox']['ml2_eswitch'] = ml2_eswitch

        return node_attrs

    @classmethod
    def fix_iser_port(cls, node_attrs, node, nm):
        """Change the iser port to eth_iser probed (VF on the HV) interface
        instead of br-storage. that change is made due to RDMA
        (Remote Direct Memory Access) limitation of working with physical
        interfaces.
        """
        # Set a new unique name for iSER virtual port
        iser_new_name = 'eth_iser0'

        # Add iSER extra params to astute.yaml
        node_attrs['neutron_mellanox']['storage_parent'] = \
            nm.get_node_network_by_netname(node, 'storage')['dev']
        node_attrs['neutron_mellanox']['iser_interface_name'] = iser_new_name

        # Get VLAN if exists
        storage_vlan = \
            nm.get_node_network_by_netname(node, 'storage').get('vlan')

        if storage_vlan:
            vlan_name = "vlan{0}".format(storage_vlan)

            # Set storage rule to iSER interface vlan interface
            node_attrs['network_scheme']['roles']['storage'] = vlan_name

            # Set iSER interface vlan interface
            node_attrs['network_scheme']['interfaces'][vlan_name] = \
                {'L2': {'vlan_splinters': 'off'}}
            node_attrs['network_scheme']['endpoints'][vlan_name] = \
                node_attrs['network_scheme']['endpoints'].pop('br-storage', {})
            node_attrs['network_scheme']['endpoints'][vlan_name]['vlandev'] = \
                iser_new_name
        else:

            # Set storage rule to iSER port
            node_attrs['network_scheme']['roles']['storage'] = iser_new_name

            # Set iSER endpoint with br-storage parameters
            node_attrs['network_scheme']['endpoints'][iser_new_name] = \
                node_attrs['network_scheme']['endpoints'].pop('br-storage', {})
            node_attrs['network_scheme']['interfaces'][iser_new_name] = \
                {'L2': {'vlan_splinters': 'off'}}

        return node_attrs

    @classmethod
    def _node_has_role_by_name(cls, node, rolename):
        if rolename in node.pending_roles or rolename in node.roles:
            return True
        return False

    @classmethod
    def neutron_attrs(cls, cluster):
        """Network configuration for Neutron
        """
        attrs = {}
        attrs['L3'] = cls.generate_l3(cluster)
        attrs['L2'] = cls.generate_l2(cluster)
        attrs['predefined_networks'] = \
            cls.generate_predefined_networks(cluster)

        if cluster.release.operating_system == 'RHEL':
            attrs['amqp'] = {'provider': 'qpid-rh'}

        cluster_attrs = Cluster.get_attributes(cluster).editable
        if 'nsx_plugin' in cluster_attrs and \
                cluster_attrs['nsx_plugin']['metadata']['enabled']:
            attrs['L2']['provider'] = 'nsx'

        return attrs

    @classmethod
    def generate_network_scheme(cls, node):

        # Create a data structure and fill it with static values.

        attrs = {
            'version': '1.1',
            'provider': 'lnx',
            'interfaces': {},  # It's a list of physical interfaces.
            'endpoints': {
                'br-storage': {},
                'br-mgmt': {},
                'br-fw-admin': {},
            },
            'roles': {
                'management': 'br-mgmt',
                'storage': 'br-storage',
                'fw-admin': 'br-fw-admin',
            },
        }

        if objects.Node.should_have_public(node):
            attrs['endpoints']['br-ex'] = {}
            attrs['roles']['ex'] = 'br-ex'

        nm = objects.Node.get_network_manager(node)


        """ 开始注释 
        iface_types = consts.NETWORK_INTERFACE_TYPES

        # Add a dynamic data to a structure.

        vlan_splinters_data = \
            node.cluster.attributes.editable\
            .get('vlan_splinters', {})\

        # if vlan_splinters is enabled - use its value
        use_vlan_splinters = 'disabled'
        if vlan_splinters_data\
                .get('metadata', {})\
                .get('enabled'):

            use_vlan_splinters = \
                vlan_splinters_data\
                .get('vswitch', {})\
                .get('value', 'disabled')

        # Fill up interfaces and add bridges for them.
        bonded_ifaces = [x for x in node.nic_interfaces if x.bond]
        for iface in node.interfaces:
            # Handle vlan splinters.
            if iface.type == iface_types.ether:
                attrs['interfaces'][iface.name] = {
                    'L2': cls._get_vlan_splinters_desc(
                        use_vlan_splinters, iface, node.cluster
                    )
                }

            if iface in bonded_ifaces:
                continue
            attrs['transformations'].append({
                'action': 'add-br',
                'name': 'br-%s' % iface.name
            })
            if iface.type == iface_types.ether:
                attrs['transformations'].append({
                    'action': 'add-port',
                    'bridge': 'br-%s' % iface.name,
                    'name': iface.name
                })
            elif iface.type == iface_types.bond:
                attrs['transformations'].append({
                    'action': 'add-bond',
                    'bridge': 'br-%s' % iface.name,
                    'name': iface.name,
                    'interfaces': [x['name'] for x in iface.slaves],
                    'properties': nm.get_ovs_bond_properties(iface)
                })
         """
        # Add bridges for networks.
        # We have to add them after br-ethXX bridges because it is the way
        # to provide a right ordering of ifdown/ifup operations with
        # IP interfaces.

        # brnames = ['br-ex', 'br-mgmt', 'br-storage', 'br-fw-admin']
        # if not objects.Node.should_have_public(node):
        #     brnames.pop(0)

        # for brname in brnames:
        #     attrs['transformations'].append({
        #         'action': 'add-br',
        #         'name': brname
        #     })

        # Populate IP address information to endpoints.
        netgroup_mapping = [
            ('storage', 'br-storage'),
            ('management', 'br-mgmt'),
            ('fuelweb_admin', 'br-fw-admin'),
        ]
        if objects.Node.should_have_public(node):
            netgroup_mapping.append(('public', 'br-ex'))

        is_public = objects.Node.should_have_public(node)
   
        netgrouptemp =[]
        ngroup=nm.get_node_network_by_netname(node, "fuelweb_admin")
        if ngroup.get('ip'):
            netgrouptemp = ngroup['ip']

        netgroups = {}
        nets_by_ifaces = defaultdict(list)
        fixed_sub_iface = None

        for ngname, brname in netgroup_mapping:
            
            # Here we get a dict with network description for this particular
            # node with its assigned IPs and device names for each network.
            netgroup = nm.get_node_network_by_netname(node, ngname)
            # netgroup {'netmask': '255.255.255.0', 'brd': '10.254.9.255', 'name': 'fuelweb_admin', 'ip': '10.254.9.8/24', 'cidr': u'10.254.9.0/24', 'vlan': None, 'gateway': None, 'dev': u'enp130s0f0'}
            # netgroup['ip'] is str
            #logger.info(netgroup)

            if ngname == "fuelweb_admin":
                if netgroup.get('ip'):
                   attrs['endpoints'][brname]['IP'] = [netgroup['ip']]
            else:
                if netgroup.get('ip'):
                   currentnetgroup=netgroup['ip']
                   newipgroup=cls.handleipgroup(netgrouptemp,currentnetgroup)
                   attrs['endpoints'][brname]['IP'] = [newipgroup]
            netgroups[ngname] = netgroup

        # if objects.Node.should_have_public(node):
        #     attrs['endpoints']['br-ex']['gateway'] = \
        #         netgroups['public']['gateway']
        # else:
        util=CommonUtil()
            #logger.info("the master gateway is %s", util.get_master_gateway())
            #attrs['endpoints']['br-fw-admin']['gateway'] = settings.MASTER_IP
        attrs['endpoints']['br-fw-admin']['gateway'] =util.format_gwip()

        # Connect interface bridges to network bridges.
        # for ngname, brname in netgroup_mapping:
        #     netgroup = nm.get_node_network_by_netname(node, ngname)
        #     if not netgroup['vlan']:
        #         # Untagged network.
        #         attrs['transformations'].append({
        #             'action': 'add-patch',
        #             'bridges': ['br-%s' % netgroup['dev'], brname],
        #             'trunks': [0]
        #         })
        #     elif netgroup['vlan'] > 1:
        #         # Tagged network.
        #         attrs['transformations'].append({
        #             'action': 'add-patch',
        #             'bridges': ['br-%s' % netgroup['dev'], brname],
        #             'tags': [netgroup['vlan'], 0]
        #         })
        #     else:
        #         # FIXME! Should raise some exception I think.
        #         logger.error('Invalid vlan for network: %s' % str(netgroup))
        
        for iface in node.nic_interfaces:
            if iface.bond:
                attrs['interfaces'][iface.name] ={}
            else:
                attrs['interfaces'][iface.name]=nm.get_iface_properties(iface)

        prv_base_ep =None

        # Dance around Neutron segmentation type.
        if node.cluster.network_config.segmentation_type == 'vlan':
            pass
            #attrs['endpoints']['br-prv'] = {'IP': 'none'}
            #attrs['roles']['private'] = 'br-prv'

            # attrs['transformations'].append({
            #     'action': 'add-br',
            #     'name': 'br-prv',
            # })

            # attrs['transformations'].append({
            #     'action': 'add-patch',
            #     'bridges': [
            #         'br-%s' % nm.get_node_interface_by_netname(
            #             node.id,
            #             'private'
            #         ).name,
            #         'br-prv'
            #     ]
            # })
        elif node.cluster.network_config.segmentation_type == 'gre':
            # attrs['roles']['mesh'] = 'br-mgmt'
            pass
        attrs['transformations'] = cls.generate_transformations(
             node, nm, nets_by_ifaces, is_public, prv_base_ep)

        if objects.NodeGroupCollection.get_by_cluster_id(node.cluster.id).count() >1 :
            cls.generate_routes(node,attrs,nm,netgroup_mapping,netgroups)
        attrs = cls.generate_driver_information(node,attrs,nm)
        return attrs

    @classmethod
    def generate_driver_information(cls, node, network_scheme, nm):

        network_mapping = network_scheme.get('roles', {})
        endpoints = network_scheme.get('endpoints', {})
        bonds_map = dict((b.name, b) for b in node.bond_interfaces)
        net_name_mapping = {'ex': 'public'}
        managed_networks = ['public', 'storage', 'management', 'private']

        # Add interfaces drivers data
        for iface in node.nic_interfaces:
            if iface.driver or iface.bus_info:
                iface_dict = network_scheme['interfaces'][iface.name]
                if 'vendor_specific' not in iface_dict:
                    iface_dict['vendor_specific'] = {}
                if iface.driver:
                    iface_dict['vendor_specific']['driver'] = iface.driver
                if iface.bus_info:
                    iface_dict['vendor_specific']['bus_info'] = iface.bus_info

        # Add physical allocation data
        for ngname, brname in six.iteritems(network_mapping):
            if ngname in net_name_mapping:
                ngname = net_name_mapping[ngname]
            if ngname not in managed_networks:
                continue
            if 'vendor_specific' not in endpoints[brname]:
                endpoints[brname]['vendor_specific'] = {}
            netgroup = nm.get_node_network_by_netname(node, ngname)
            ep_dict = endpoints[brname]['vendor_specific']
            ep_dict['phy_interfaces'] = \
                cls.get_phy_interfaces(bonds_map, netgroup)
            if netgroup['vlan'] > 1:
                logger.info("vlan is %s", netgroup['vlan'])
                ep_dict['vlans'] = netgroup['vlan']

        # if node.cluster.network_config.segmentation_type == 'vlan':
        #     private_ep = endpoints[network_mapping['neutron/private']]
        #     netgroup = nm.get_node_network_by_netname(node, 'private')
        #     phys = cls.get_phy_interfaces(bonds_map, netgroup)
        #     if 'vendor_specific' not in private_ep:
        #         private_ep['vendor_specific'] = {}
        #     private_ep['vendor_specific']['phy_interfaces'] = phys
        #     private_ep['vendor_specific']['vlans'] = utils.join_range(
        #         node.cluster.network_config.vlan_range)

        return network_scheme

    @classmethod
    def get_phy_interfaces(cls, bonds_map, netgroup):
        if netgroup['dev'] in bonds_map.keys():
            phys = [s['name'] for s in bonds_map[netgroup['dev']].slaves]
        else:
            phys = [netgroup['dev']]
        return phys
        

    @classmethod
    def handleipgroup(cls,netgrouptemp,currentnet):
        #以pxe网段最后的数字为标准,修改其他网段最后一位数字
        #endpoints
        newipgroup=""
        #logger.info("netgrouptemp is %s",netgrouptemp)
        #logger.info("currentnet is %s",currentnet)

        lastnum = netgrouptemp.split(".")[3]
        currlist=currentnet.split(".")
        currlist[3]=lastnum
        newipgroup=(".").join(currlist)

        #logger.info("newipgroup is %s", newipgroup)
        return newipgroup
        

    @classmethod
    def _get_vlan_splinters_desc(cls, use_vlan_splinters, iface,
                                 cluster):
        iface_attrs = {}
        if use_vlan_splinters in ('disabled', 'kernel_lt'):
            iface_attrs['vlan_splinters'] = 'off'
            return iface_attrs
        iface_attrs['vlan_splinters'] = 'auto'
        trunks = [0]

        if use_vlan_splinters == 'hard':
            for ng in iface.assigned_networks_list:
                if ng.name == 'private':
                    vlan_range = cluster.network_config.vlan_range
                    trunks.extend(xrange(*vlan_range))
                    trunks.append(vlan_range[1])
                else:
                    if ng.vlan_start in (0, None):
                        continue
                    trunks.append(ng.vlan_start)
        elif use_vlan_splinters == 'soft':
            pass
        else:
            logger.warn('Invalid vlan_splinters value: %s', use_vlan_splinters)
            return {}

        iface_attrs['trunks'] = trunks

        return iface_attrs

    @classmethod
    def _generate_external_network(cls, cluster):
        public_cidr, public_gw = db().query(
            NetworkGroup.cidr,
            NetworkGroup.gateway
        ).filter_by(
            group_id=Cluster.get_default_group(cluster).id,
            name='public'
        ).first()
        join_range = lambda r: (":".join(map(str, r)) if r else None)
        return {
            "L3": {
                "subnet": public_cidr,
                "gateway": public_gw,
                "nameservers": [],
                "floating": join_range(
                    cluster.network_config.floating_ranges[0]),
                "enable_dhcp": False
            },
            "L2": {
                "network_type": "flat",
                "segment_id": None,
                "router_ext": True,
                "physnet": "physnet1"
            },
            "tenant": objects.Cluster.get_creds(cluster)['tenant']['value'],
            "shared": False
        }

    @classmethod
    def _generate_internal_network(cls, cluster):
        return {
            "L3": {
                "subnet": cluster.network_config.internal_cidr,
                "gateway": cluster.network_config.internal_gateway,
                "nameservers": cluster.network_config.dns_nameservers,
                "floating": None,
                "enable_dhcp": True
            },
            "L2": {
                "network_type": cluster.network_config.segmentation_type,
                "segment_id": None,
                "router_ext": False,
                "physnet": "physnet2"
                if cluster.network_config.segmentation_type == "vlan" else None
            },
            "tenant": objects.Cluster.get_creds(cluster)['tenant']['value'],
            "shared": False
        }

    @classmethod
    def generate_predefined_networks(cls, cluster):
        return {
            "net04_ext": cls._generate_external_network(cluster),
            "net04": cls._generate_internal_network(cluster)
        }

    @classmethod
    def generate_l2(cls, cluster):
        join_range = lambda r: (":".join(map(str, r)) if r else None)
        res = {
            "base_mac": cluster.network_config.base_mac,
            "segmentation_type": cluster.network_config.segmentation_type,
            "phys_nets": {
                "physnet1": {
                    "bridge": "br-ex",
                    "vlan_range": None
                }
            }
        }
        if cluster.network_config.segmentation_type == 'gre':
            res["tunnel_id_ranges"] = join_range(
                cluster.network_config.gre_id_range)
        elif cluster.network_config.segmentation_type == 'vlan':
            res["phys_nets"]["physnet2"] = {
                "bridge": "br-prv",
                "vlan_range": join_range(cluster.network_config.vlan_range)
            }

        # Set non-default ml2 configurations
        attrs = Cluster.get_attributes(cluster).editable
        if 'neutron_mellanox' in attrs and \
                attrs['neutron_mellanox']['plugin']['value'] == 'ethernet':
            res['mechanism_drivers'] = 'mlnx,openvswitch'
            seg_type = cluster.network_config.segmentation_type
            res['tenant_network_types'] = seg_type
            res['type_drivers'] = '{0},flat,local'.format(seg_type)

        return res

    @classmethod
    def generate_l3(cls, cluster):
        l3 = {
            "use_namespaces": True
        }
        attrs = Cluster.get_attributes(cluster).editable
        if 'nsx_plugin' in attrs and \
                attrs['nsx_plugin']['metadata']['enabled']:
            dhcp_attrs = l3.setdefault('dhcp_agent', {})
            dhcp_attrs['enable_isolated_metadata'] = True
            dhcp_attrs['enable_metadata_network'] = True

        return l3


class NeutronNetworkDeploymentSerializer51(NeutronNetworkDeploymentSerializer):

    @classmethod
    def _generate_external_network(cls, cluster):
        ext_netw = super(NeutronNetworkDeploymentSerializer51, cls).\
            _generate_external_network(cluster)
        ext_netw["L2"] = {
            "network_type": "local",
            "segment_id": None,
            "router_ext": True,
            "physnet": None
        }
        return ext_netw

    @classmethod
    def generate_l2(cls, cluster):
        l2 = super(NeutronNetworkDeploymentSerializer51, cls).\
            generate_l2(cluster)
        l2["phys_nets"].pop("physnet1")
        return l2


class NeutronNetworkDeploymentSerializer60(
    NeutronNetworkDeploymentSerializer51
):
    
    @classmethod
    def add_bridge(cls, name, provider=None):
        """Add bridge to schema
        It will take global provider if it is omitted here
        """
        bridge = {
            'action': 'add-br',
            'name': name
        }
        if provider:
            bridge['provider'] = provider
        return bridge

    @classmethod
    def add_port(cls, name, bridge, provider=None):
        """Add port to schema
        Bridge name may be None, port will not be connected to any bridge then
        It will take global provider if it is omitted here
        Port name can be in form "XX" or "XX.YY", where XX - NIC name,
        YY - vlan id. E.g. "eth0", "eth0.1021". This will create corresponding
        interface if name includes vlan id.
        """
        port = {
            'action': 'add-port',
            'name': name
        }
        if bridge:
            port['bridge'] = bridge
        if provider:
            port['provider'] = provider
        return port   
        
    @classmethod
    def add_bond(cls, iface, parameters):
        """Add bond to schema
        All required parameters should be inside parameters dict. (e.g.
        bond_properties, interface_properties, provider, bridge).
        bond_properties is obligatory, others are optional.
        bridge should be set if bridge for untagged network is to be connected
        to bond. Ports are to be created for tagged networks which should be
        connected to bond (e.g. port "bond-X.212" for bridge "br-ex").
        """
        bond = {
            'action': 'add-bond',
            'name': iface.name,
            'interfaces': sorted(x['name'] for x in iface.slaves),
        }
        if iface.interface_properties.get('mtu'):
            bond['mtu'] = iface.interface_properties['mtu']
        if parameters:
            bond.update(parameters)
        return bond
    

    @classmethod
    def add_patch(cls, bridges, provider=None, mtu=None):
        """Add patch to schema
        Patch connects two bridges listed in 'bridges'.
        OVS bridge must go first in 'bridges'.
        It will take global provider if it is omitted here
        """
        patch = {
            'action': 'add-patch',
            'bridges': bridges,
        }
        if provider:
            patch['provider'] = provider
        if mtu:
            patch['mtu'] = mtu
        return patch

    @classmethod
    def subiface_name(self,iface_name,net_descr):
        if not net_descr['vlan_id']:
            return iface_name
        else:
            return "{0}.{1}".format(iface_name,net_descr['vlan_id'])

    @classmethod
    def generate_routes(cls, node, attrs, nm, netgroup_mapping, netgroups):
        other_nets = nm.get_networks_not_on_node(node)

        for ngname, brname in netgroup_mapping:
            netgroup = netgroups[ngname]
            if netgroup.get('gateway'):
                via = netgroup['gateway']
                attrs['endpoints'][brname]['routes'] = []
                for cidr in other_nets.get(ngname, []):
                    attrs['endpoints'][brname]['routes'].append({
                        'net': cidr,
                        'via': via
                    })

    @classmethod
    def generate_transformations(cls, node, nm, nets_by_ifaces, is_public,
                                 prv_base_ep):
        transformations = []

        iface_types = consts.NETWORK_INTERFACE_TYPES
        brnames = ['br-fw-admin', 'br-mgmt', 'br-storage']
        if is_public:
            brnames.append('br-ex')

        # Add bridges for networks.
        for brname in brnames:
            transformations.append(cls.add_bridge(brname))

        if is_public:
            # br-floating is an OVS bridge and it's always connected with br-ex
            transformations.append(
                cls.add_bridge('br-floating', provider='ovs'))
            transformations.append(cls.add_patch(
                bridges=['br-floating', 'br-ex'],
                provider='ovs',
                mtu=65000))

        # Dance around Neutron segmentation type.
        if node.cluster.network_config.segmentation_type == 'vlan':
            transformations.append(
                cls.add_bridge('br-prv', provider='ovs'))

            if not prv_base_ep:
                prv_base_ep = 'br-aux'
                transformations.append(cls.add_bridge(prv_base_ep))

            transformations.append(cls.add_patch(
                bridges=['br-prv', prv_base_ep],
                provider='ovs',
                mtu=65000))

        elif node.cluster.network_config.segmentation_type == 'gre':
            transformations.append(
                cls.add_bridge('br-mesh'))

        # Add ports and bonds.
        for iface in node.interfaces:
            if iface.type == iface_types.ether:
                # Add ports for all networks on every unbonded NIC.
                if not iface.bond and iface.name in nets_by_ifaces:
                    tagged = []
                    for net in nets_by_ifaces[iface.name]:
                        # Interface must go prior to subinterfaces.
                        sub_iface = cls.subiface_name(iface.name, net)
                        if not net['vlan_id']:
                            transformations.append(cls.add_port(
                                sub_iface, net['br_name']))
                        else:
                            tagged.append(cls.add_port(
                                sub_iface, net['br_name']))
                    transformations.extend(tagged)
            elif iface.type == iface_types.bond:
                # Add bonds and connect untagged networks' bridges to them.
                # There can be no more than one untagged network on each bond.
                bond_params = {
                    'bond_properties': nm.get_lnx_bond_properties(iface),
                    'interface_properties': nm.get_iface_properties(iface)
                }
                bond_ports = []
                if iface.name in nets_by_ifaces:
                    for net in nets_by_ifaces[iface.name]:
                        if net['vlan_id']:
                            bond_ports.append(cls.add_port(
                                cls.subiface_name(iface.name, net),
                                net['br_name']))
                        else:
                            bond_params['bridge'] = net['br_name']
                transformations.append(cls.add_bond(iface, bond_params))
                transformations.extend(bond_ports)

        return transformations

    @classmethod
    def generate_network_scheme(cls, node):
        
        # Create a data structure and fill it with static values.

        attrs = {
            'version': '1.1',
            'provider': 'lnx',
            'interfaces': {},  # It's a list of physical interfaces.
            'endpoints': {
                'br-storage': {},
                'br-mgmt': {},
                'br-fw-admin': {},
            },
            'roles': {
                'management': 'br-mgmt',
                'storage': 'br-storage',
                'fw-admin': 'br-fw-admin',
            },
        }

        if objects.Node.should_have_public(node):
            attrs['endpoints']['br-ex'] = {}
            attrs['roles']['ex'] = 'br-ex'

        nm = objects.Node.get_network_manager(node)

        # Populate IP address information to endpoints.
        netgroup_mapping = [
            ('storage', 'br-storage'),
            ('management', 'br-mgmt'),
            ('fuelweb_admin', 'br-fw-admin'),
        ]
        if objects.Node.should_have_public(node):
            netgroup_mapping.append(('public', 'br-ex'))

        is_public = objects.Node.should_have_public(node)
   
        netgrouptemp =[]
        ngroup=nm.get_node_network_by_netname(node, "fuelweb_admin")
        if ngroup.get('ip'):
            netgrouptemp = ngroup['ip']

        netgroups = {}
        nets_by_ifaces = defaultdict(list)
        fixed_sub_iface = None

        for ngname, brname in netgroup_mapping:
            
            # Here we get a dict with network description for this particular
            # node with its assigned IPs and device names for each network.
            netgroup = nm.get_node_network_by_netname(node, ngname)
            # netgroup {'netmask': '255.255.255.0', 'brd': '10.254.9.255', 'name': 'fuelweb_admin', 'ip': '10.254.9.8/24', 'cidr': u'10.254.9.0/24', 'vlan': None, 'gateway': None, 'dev': u'enp130s0f0'}
            # netgroup['ip'] is str
            #logger.info(netgroup)

            if ngname == "fuelweb_admin":
                if netgroup.get('ip'):
                   attrs['endpoints'][brname]['IP'] = [netgroup['ip']]
            else:
                if netgroup.get('ip'):
                   currentnetgroup=netgroup['ip']
                   newipgroup=cls.handleipgroup(netgrouptemp,currentnetgroup)
                   attrs['endpoints'][brname]['IP'] = [newipgroup]
            netgroups[ngname] = netgroup

        # if objects.Node.should_have_public(node):
        #     attrs['endpoints']['br-ex']['gateway'] = \
        #         netgroups['public']['gateway']
        # else:
        util=CommonUtil()
            #logger.info("the master gateway is %s", util.get_master_gateway())
            #attrs['endpoints']['br-fw-admin']['gateway'] = settings.MASTER_IP
        attrs['endpoints']['br-fw-admin']['gateway'] =util.format_gwip()

        
        for iface in node.nic_interfaces:
            if iface.bond:
                attrs['interfaces'][iface.name] ={}
            else:
                attrs['interfaces'][iface.name]=nm.get_iface_properties(iface)

        prv_base_ep =None

        
        attrs['transformations'] = cls.generate_transformations(
             node, nm, nets_by_ifaces, is_public, prv_base_ep)

        if objects.NodeGroupCollection.get_by_cluster_id(node.cluster.id).count() >1 :
            cls.generate_routes(node,attrs,nm,netgroup_mapping,netgroups)
        attrs = cls.generate_driver_information(node,attrs,nm)
        return attrs

    @classmethod
    def handleipgroup(cls,netgrouptemp,currentnet):
        #以pxe网段最后的数字为标准,修改其他网段最后一位数字
        #endpoints
        newipgroup=""
        lastnum = netgrouptemp.split(".")[3]
        currlist=currentnet.split(".")
        currlist[3]=lastnum
        newipgroup=(".").join(currlist)

        return newipgroup

class DeploymentMultinodeSerializer(object):

    nova_network_serializer = NovaNetworkDeploymentSerializer
    neutron_network_serializer = NeutronNetworkDeploymentSerializer

    critical_roles = ['controller', 'ceph-osd', 'primary-mongo']

    def __init__(self, priority_serializer):
        self.priority = priority_serializer

    def serialize(self, cluster, nodes, ignore_customized=False):
        """Method generates facts which
        through an orchestrator passes to puppet
        """
        serialized_nodes = []
        keyfunc = lambda node: bool(node.replaced_deployment_info)
        for customized, node_group in groupby(nodes, keyfunc):
            if customized and not ignore_customized:
                serialized_nodes.extend(
                    self.serialize_customized(cluster, node_group))
            else:
                serialized_nodes.extend(self.serialize_generated(
                    cluster, node_group))
        return serialized_nodes

    def serialize_generated(self, cluster, nodes):
        nodes = self.serialize_nodes(nodes)
        common_attrs = self.get_common_attrs(cluster)

        self.set_deployment_priorities(nodes)
        self.set_critical_nodes(nodes)

        return [dict_merge(node, common_attrs) for node in nodes]

    def serialize_customized(self, cluster, nodes):
        serialized = []
        release_data = objects.Release.get_orchestrator_data_dict(
            self.current_release(cluster))
        for node in nodes:
            for role_data in node.replaced_deployment_info:
                role_data.update(release_data)
                serialized.append(role_data)
        return serialized

    def get_common_attrs(self, cluster):
        """Cluster attributes."""

        cluster_attrs = objects.Attributes.merged_attrs_values(
            cluster.attributes
        )
        attrs={}
        release = self.current_release(cluster)
        attrs.update(
            objects.Release.get_orchestrator_data_dict(release)
        )
        attrs['nodes'] = self.node_list(get_nodes_not_for_deletion(cluster))
        attrs['deployment_id'] = cluster.id
        attrs["cobbler"]=cluster_attrs['cobbler']
        role_list=attrs['nodes']
        clusterSetting=db().query(ClusterSetting).filter_by(cluster_id=cluster.id).first()
        if cluster.cluster_type==2:
           dataSetting=json.loads(clusterSetting.cluster_setting)
           #attrs["cobbler"]={"profile":"centos-x86_64"}
           #attrs["cobbler"]['profile']=cluster_attrs['cobbler']['profile']
           #cluster_attrs['cobbler']['profile']取值于attributes表中的generated值
           cloud=cloudmaster.clustercloudmaster()
           for node in role_list:
               if node.get("role")=="clsmaster":
                  attrs['clsmaster']=cloud.create_cloudmaster_clsmaster(dataSetting["clsmaster"])
               if node.get("role")=="clsslave":
                  attrs['clsslave']=cloud.create_cloudmaster_clsslave(dataSetting["clsslave"])
               if node.get("role")=="mysqlcls":
                  attrs['mysqlcls']=cloud.create_cloudmaster_mysql(dataSetting["mysqlcls"])
               if node.get("role")=="nagios":
                  attrs['nagios']=cloud.create_cloudmaster_nagios(dataSetting["nagios"])
               if node.get("role")=="ganglia":
                  attrs['ganglia']=cloud.create_cloudmaster_ganglia(dataSetting["ganglia"])
               if node.get("role")=="dhcpserver":
                  attrs['dhcpserver']=cloud.create_cloudmaster_dhcpserver(dataSetting["dhcpserver"])
        elif cluster.cluster_type==3:
             dataSetting=json.loads(clusterSetting.cluster_setting)
             #attrs["cobbler"]={"profile":"bclinux7.1"}
             #attrs["cobbler"]=cluster_attrs['cobbler']['profile']
             #deployment_serializers.py和provisioning_serializers.py都需要修改profile
             cus=ebs.clusterebs()
             #for node in role_list:
                 #if node.get('role')=="prepare":
             attrs['prepare']=cus.create_clusterebs_prepare(dataSetting["prepare"])
                 #if node.get('role')=="gangliasrv":
             attrs['gangliasrv']=cus.create_clusterebs_ganglia(dataSetting["gangliasrv"])
                 #if node.get('role')=="nagiossrv":
             clientips=self.get_nagios_clientips(attrs['nodes'])
             attrs['nagiossrv']=cus.create_clusterebs_nagios(dataSetting["nagiossrv"],clientips)
                 #if node.get('role')=="watcher":
             attrs['watcher']=cus.create_clusterebs_watcher(dataSetting["watcher"])
                 #if node.get('role')=="management":
             attrs['management']=cus.create_clusterebs_management(dataSetting["management"])
                 #if node.get('role')=="ebs-cinder":
             attrs['ebs-cinder']=cus.create_clusterebs_cinder(dataSetting["ebs-cinder"])
                 #if node.get('role')=="rsyslogsrv":
             attrs['rsyslogsrv']=cus.create_clusterebs_syslog(dataSetting["rsyslogsrv"])
                 #if node.get('role')=="agent-sernode":
             attrs['agent-sernode']=cus.create_clusterebs_sernode(dataSetting["agent-sernode"])
                 #if node.get('role')=="bacula-dir":
             attrs['bacula-dir']=cus.create_clusterebs_bacula(dataSetting["bacula-dir"])
             attrs['java']=cus.create_clusterebs_java(dataSetting["java"])
             attrs['gangliacli']=cus.create_clusterebs_gangliacli(dataSetting["gangliacli"])
             attrs['nagioscli']=cus.create_clusterebs_nagioscli(dataSetting["nagioscli"])
             attrs['rsyslogcli']=cus.create_clusterebs_rsyslogcli(dataSetting["rsyslogcli"])
             attrs['smartd']=cus.create_clusterebs_smartd(dataSetting["smartd"])
             attrs['tgtd']=cus.create_clusterebs_tgtd(dataSetting["tgtd"])
             attrs['zookeeper']=cus.create_clusterebs_zookeeper(dataSetting["zookeeper"])
             attrs['sheepdog']=cus.create_clusterebs_sheepdog(dataSetting["sheepdog"])
             attrs['agent-appnode']=cus.create_clusterebs_agentappnode(dataSetting["agent-appnode"])
             attrs['bacula-fd']=cus.create_clusterebs_baculafd(dataSetting["bacula-fd"])
             attrs['bacula-sd']=cus.create_clusterebs_baculasd(dataSetting["bacula-sd"])
        
        elif cluster.cluster_type==5:
             dataSetting=json.loads(clusterSetting.cluster_setting)
             cus=onest.clusteronest()
             attrs['prepare']=cus.create_clusteronest_prepare(dataSetting["prepare"])
             attrs['java']=cus.create_clusteronest_java(dataSetting["java"])
             attrs['zookeeper']=cus.create_clusteronest_zookeeper(dataSetting["zookeeper"])
             attrs['hadoop']=cus.create_clusteronest_hadoop(dataSetting["hadoop"])
             attrs['hbase']=cus.create_clusteronest_hadoop(dataSetting["hbase"])
             attrs['onest']=cus.create_clusteronest_hadoop(dataSetting["onest"])

        elif cluster.cluster_type==4:
           attrs.update(objects.Attributes.merged_attrs_values(cluster.attributes))
           dataSetting=json.loads(clusterSetting.cluster_setting)
           attrs['masterip']=self.set_mysql_masterip(attrs['nodes'])
           cus=custom.clustercustom()
           attrs['mysql']=cus.create_clustercustom_mysql(dataSetting["mysql"])
           attrs['rabbitmq']=cus.create_clustercustom_rabbitmq(dataSetting["rabbitmq"])
           attrs['mongodb']=cus.create_clustercustom_mongodb(dataSetting["mongodb"])
           attrs['keystone']=cus.create_clustercustom_keystone(dataSetting["keystone"])
           attrs['glance']=cus.create_clustercustom_glance(dataSetting["glance"])
           attrs['nova-api']=cus.create_clustercustom_nova(dataSetting["nova-api"])
           attrs['nova-compute']=cus.create_clustercustom_nova_compute(dataSetting["nova-compute"])
           attrs['neutron-server']=cus.create_clustercustom_neutron_server(dataSetting["neutron-server"])
           attrs['neutron-agent']=cus.create_clustercustom_neutron_agent(dataSetting["neutron-agent"])
           attrs['horizon']=cus.create_clustercustom_horizon(dataSetting["horizon"])
           attrs['cinder-api']=cus.create_clustercustom_cinder(dataSetting["cinder-api"])
           attrs['cinder-storage']=cus.create_clustercustom_cinder_storage(dataSetting["cinder-storage"])
           attrs['ceilometer']=cus.create_clustercustom_ceilometer(dataSetting["ceilometer"])
           attrs['heat']=cus.create_clustercustom_heat(dataSetting["heat"])
           attrs['haproxy-keepalived']=cus.create_clustercustom_haproxy(dataSetting['haproxy-keepalived'])
           attrs['global']=dataSetting['global']

        # else:
        #    attrs.update(objects.Attributes.merged_attrs_values(cluster.attributes))
           attrs['deployment_mode'] = cluster.mode
           attrs['openstack_version_prev'] = getattr(
            self.previous_release(cluster), 'version', None)
           attrs['openstack_version'] = release.version
           attrs['fuel_version'] = cluster.fuel_version

           for node in attrs['nodes']:
               if node['role'] in 'cinder':
                  attrs['use_cinder'] = True

           #self.set_storage_parameters(cluster, attrs)
           #self.set_primary_mongo(attrs['nodes'])

           attrs = dict_merge(
            attrs,
            self.get_net_provider_serializer(cluster).get_common_attrs(cluster,
                                                                       attrs))
        return attrs

    def set_mysql_masterip(self,nodes):
        mysqlnodes=[]
        for node in nodes:
               if node['role'] in 'mysql':
                  mysqlnodes.append(node)
        mysqlnodes=sorted(mysqlnodes, key=lambda node: node['uid'])
        if mysqlnodes:
           return mysqlnodes[0]['ip']

    def get_nagios_clientips(self,nodes):
        clientips=[]
        for node in nodes:
            if node['role'] in 'nagioscli':
               clientips.append(node["ip"])
        return ",".join(clientips)

   

    def current_release(self, cluster):
        """Actual cluster release."""
        return objects.Release.get_by_uid(cluster.pending_release_id) \
            if cluster.status == consts.CLUSTER_STATUSES.update \
            else cluster.release

    def previous_release(self, cluster):
        """Returns previous release.

        :param cluster: a ``Cluster`` instance to retrieve release from
        :returns: a ``Release`` instance of previous release or ``None``
            in case there's no previous release (fresh deployment).
        """
        if cluster.status == consts.CLUSTER_STATUSES.update:
            return cluster.release
        return None

    def set_storage_parameters(self, cluster, attrs):
        """Generate pg_num as the number of OSDs across the cluster
        multiplied by 100, divided by Ceph replication factor, and
        rounded up to the nearest power of 2.
        """
        osd_num = 0
        nodes = db().query(Node). \
            filter(or_(
                Node.role_list.any(name='ceph-osd'),
                Node.pending_role_list.any(name='ceph-osd'))). \
            filter(Node.cluster == cluster). \
            options(joinedload('attributes'))
        for node in nodes:
            for disk in node.attributes.volumes:
                for part in disk.get('volumes', []):
                    if part.get('name') == 'ceph' and part.get('size', 0) > 0:
                        osd_num += 1
        if osd_num > 0:
            repl = int(attrs['storage']['osd_pool_size'])
            pg_num = 2 ** int(math.ceil(math.log(osd_num * 100.0 / repl, 2)))
        else:
            pg_num = 128
        attrs['storage']['pg_num'] = pg_num

    def node_list(self, nodes):
        """Generate nodes list. Represents
        as "nodes" parameter in facts.
        """
        node_list = []
        # if node.cluster.cluster_type==5:
        #    node_attrs.update(self.get_node_cabinetNumber(node))
        for node in nodes:
            for role in objects.Node.all_roles(node):
                node_list.append({
                    'uid': node.uid,
                    'ip':node.ip,
                    'fqdn': node.fqdn,
                    'cabinet':self.get_node_cabinetNumber(node),
                    'name': objects.Node.make_slave_name(node),
                    'role': role})
    
        return node_list

    def by_role(self, nodes, role):
        return filter(lambda node: node['role'] == role, nodes)

    def not_roles(self, nodes, roles):
        return filter(lambda node: node['role'] not in roles, nodes)

    def set_deployment_priorities(self, nodes):
        """Set priorities of deployment."""
        self.priority.set_deployment_priorities(nodes)

    def set_critical_nodes(self, nodes):
        """Set behavior on nodes deployment error
        during deployment process.
        """
        for n in nodes:
            n['fail_if_error'] = n['role'] in self.critical_roles

    def serialize_nodes(self, nodes):
        """Serialize node for each role.
        For example if node has two roles then
        in orchestrator will be passed two serialized
        nodes.
        """
        serialized_nodes = []
        for node in nodes:
            for role in objects.Node.all_roles(node):
                serialized_nodes.append(self.serialize_node(node, role))
        self.set_primary_mongo(serialized_nodes)
        return serialized_nodes

    def serialize_node(self, node, role):
        """Serialize node, then it will be
        merged with common attributes
        """
        node_attrs = {
            # Yes, uid is really should be a string
            'uid': node.uid,
            'ip':node.ip,
            'fqdn': node.fqdn,
            'status': node.status,
            'role': role,
            # TODO (eli): need to remove, requried
            # for the fake thread only
            'online': node.online
        }
        
        node_attrs.update(self.get_net_provider_serializer(node.cluster).get_node_attrs(node))
        node_attrs.update(self.get_net_provider_serializer(node.cluster).network_ranges(node.group_id))
        node_attrs.update(self.get_image_cache_max_size(node))
        node_attrs.update(self.generate_test_vm_image_data(node))

        return node_attrs

    def get_node_cabinetNumber(self,node):
        cabinetNumber=""
        physicalnode=db().query(PhysicalMachineInfo).filter_by(mac=node['mac'].lower()).first()
        if physicalnode:
           cabinetNumber=physicalnode["cabinet"]
        return cabinetNumber

    def get_image_cache_max_size(self, node):
        images_ceph = (node.cluster.attributes['editable']['storage']
                       ['images_ceph']['value'])
        if images_ceph:
            image_cache_max_size = '0'
        else:
            image_cache_max_size = volume_manager.calc_glance_cache_size(
                node.attributes.volumes)
        return {'glance': {'image_cache_max_size': image_cache_max_size}}

    def generate_test_vm_image_data(self, node):
        # Instantiate all default values in dict.
        image_data = {
            'container_format': 'bare',
            'public': 'true',
            'disk_format': 'qcow2',
            'img_name': 'TestVM',
            'img_path': '',
            'os_name': 'cirros',
            'min_ram': 64,
            'glance_properties': '',
        }
        # Generate a right path to image.
        c_attrs = node.cluster.attributes
        if 'ubuntu' in c_attrs['generated']['cobbler']['profile']:
            img_dir = '/usr/share/cirros-testvm/'
        else:
            img_dir = '/opt/vm/'
        image_data['img_path'] = '{0}cirros-x86_64-disk.img'.format(img_dir)
        # Add default Glance property for Murano.
        glance_properties = [
            """--property murano_image_info="""
            """'{"title": "Murano Demo", "type": "cirros.demo"}'"""
        ]

        # Alternate VMWare specific values.
        if c_attrs['editable']['common']['libvirt_type']['value'] == 'vcenter':
            image_data.update({
                'disk_format': 'vmdk',
                'img_path': '{0}cirros-i386-disk.vmdk'.format(img_dir),
            })
            glance_properties.append('--property vmware_disktype=sparse')
            glance_properties.append('--property vmware_adaptertype=lsilogic')
            glance_properties.append('--property hypervisor_type=vmware')

        image_data['glance_properties'] = ' '.join(glance_properties)

        return {'test_vm_image': image_data}

    def get_net_provider_serializer(self, cluster):
        if cluster.net_provider == 'nova_network':
            return self.nova_network_serializer
        else:
            return self.neutron_network_serializer

    def set_primary_node(self, nodes, role, primary_node_index):
        """Set primary node for role if it not set yet.
        primary_node_index defines primary node position in nodes list
        """
        sorted_nodes = sorted(
            nodes, key=lambda node: int(node['uid']))

        primary_role = 'primary-{0}'.format(role)
        primary_node = self.filter_by_roles(
            sorted_nodes, [primary_role])
        if primary_node:
            return

        result_nodes = self.filter_by_roles(
            sorted_nodes, [role])
        if result_nodes:
            result_nodes[primary_node_index]['role'] = primary_role

    def set_primary_mongo(self, nodes):
        """Set primary mongo for the last mongo node
        node if it not set yet
        """
        self.set_primary_node(nodes, 'mongo', 0)

    def filter_by_roles(self, nodes, roles):
        return filter(
            lambda node: node['role'] in roles, nodes)


class DeploymentHASerializer(DeploymentMultinodeSerializer):
    """Serializer for ha mode."""

    critical_roles = ['primary-controller',
                      'primary-mongo',
                      'primary-swift-proxy',
                      'ceph-osd']

    def get_last_controller(self, nodes):
        sorted_nodes = sorted(
            nodes, key=lambda node: int(node['uid']))

        controller_nodes = self.filter_by_roles(
            sorted_nodes, ['controller', 'primary-controller'])

        last_controller = None
        if len(controller_nodes) > 0:
            last_controller = controller_nodes[-1]['name']

        return {'last_controller': last_controller}

    def node_list(self, nodes):
        """Node list
        """
        node_list = super(
            DeploymentHASerializer,
            self
        ).node_list(nodes)
        for node in node_list:
            node['swift_zone'] = node['uid']

        return node_list

    def get_common_attrs(self, cluster):
        """Common attributes for all facts
        """
        common_attrs = super(
            DeploymentHASerializer,
            self
        ).get_common_attrs(cluster)
        if cluster.cluster_type==1:
           net_manager = objects.Cluster.get_network_manager(cluster)

           for ng in cluster.network_groups:
               if ng.meta.get("assign_vip"):
                  common_attrs[ng.name + '_vip'] = net_manager.assign_vip(
                    cluster.id, ng.name)

           common_attrs['mp'] = [
            {'point': '1', 'weight': '1'},
            {'point': '2', 'weight': '2'}]

           last_controller = self.get_last_controller(common_attrs['nodes'])
           common_attrs.update(last_controller)

        return common_attrs


class DeploymentMultinodeSerializer51(DeploymentMultinodeSerializer):

    nova_network_serializer = NovaNetworkDeploymentSerializer
    neutron_network_serializer = NeutronNetworkDeploymentSerializer51


class DeploymentHASerializer51(DeploymentHASerializer):

    nova_network_serializer = NovaNetworkDeploymentSerializer
    neutron_network_serializer = NeutronNetworkDeploymentSerializer51


class DeploymentMultinodeSerializer60(DeploymentMultinodeSerializer):

    nova_network_serializer = NovaNetworkDeploymentSerializer
    neutron_network_serializer = NeutronNetworkDeploymentSerializer60


class DeploymentHASerializer60(DeploymentHASerializer):

    nova_network_serializer = NovaNetworkDeploymentSerializer
    neutron_network_serializer = NeutronNetworkDeploymentSerializer60


def create_serializer(cluster):
    """Returns a serializer depends on a given `cluster`.

    :param cluster: a cluster to process
    :returns: a serializer for a given cluster
    """
    # env-version serializer map
    serializers_map = {
        '5.0': {
            'multinode': (
                DeploymentMultinodeSerializer,
                ps.PriorityMultinodeSerializer50,
            ),
            'ha': (
                DeploymentHASerializer,
                ps.PriorityHASerializer50,
            ),
        },
        '5.1': {
            'multinode': (
                DeploymentMultinodeSerializer51,
                ps.PriorityMultinodeSerializer51,
            ),
            'ha': (
                DeploymentHASerializer51,
                ps.PriorityHASerializer51,
            ),
        },
        '6.0': {
            'multinode': (
                DeploymentMultinodeSerializer60,
                ps.PriorityMultinodeSerializer60,
            ),
            'ha': (
                DeploymentHASerializer60,
                ps.PriorityHASerializer60,
            ),
        },
    }

    env_version = extract_env_version(cluster.release.version)
    env_mode = 'ha' if cluster.is_ha_mode else 'multinode'

    # choose serializer
    for version, serializers in six.iteritems(serializers_map):
        if env_version.startswith(version):
            serializer, priority = serializers[env_mode]
            if cluster.pending_release_id:
                priority = {
                    'ha': ps.PriorityHASerializerPatching,
                    'multinode': ps.PriorityMultinodeSerializerPatching,
                }.get(env_mode)
            return serializer(priority())

    raise errors.UnsupportedSerializer()


def serialize(cluster, nodes, ignore_customized=False):
    """Serialization depends on deployment mode
    """
    objects.Cluster.set_primary_roles(cluster, nodes)
    objects.NodeCollection.prepare_for_deployment(cluster.nodes)
    serializer = create_serializer(cluster)

    return serializer.serialize(
        cluster, nodes, ignore_customized=ignore_customized)
