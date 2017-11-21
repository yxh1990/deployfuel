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


class clustercustom(object):
    

    def create_clustercustom_mysql(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_rabbitmq(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_mongodb(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_keystone(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_glance(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_nova(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_nova_compute(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_neutron_server(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_neutron_agent(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_horizon(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_cinder(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_cinder_storage(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_ceilometer(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs
        
    def create_clustercustom_heat(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clustercustom_haproxy(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs