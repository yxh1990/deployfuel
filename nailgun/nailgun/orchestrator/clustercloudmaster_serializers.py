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


class clustercloudmaster(object):

  def create_cloudmaster_clsmaster(self,clusterSetting):
       attrs={}
       attrs["install"]=True
       attrs.update(clusterSetting)
       return attrs

  def create_cloudmaster_clsslave(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

  def create_cloudmaster_mysql(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs


  def create_cloudmaster_nagios(self,clusterSetting):
       attrs={}
       attrs["install"]=True
       attrs.update(clusterSetting)
       return attrs

  def create_cloudmaster_ganglia(self,clusterSetting):
       attrs={}
       attrs["install"]=True
       attrs.update(clusterSetting)
       return attrs

  def create_cloudmaster_dhcpserver(self,clusterSetting):
       attrs={}
       attrs["install"]=True
       attrs.update(clusterSetting)
       return attrs

