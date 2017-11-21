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


class clusterebs(object):

    def create_clusterebs_prepare(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_ganglia(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_nagios(self,clusterSetting,clientips):
        attrs={}
        attrs["install"]=True
        clusterSetting["clientips"]=clientips
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_watcher(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_management(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_cinder(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_syslog(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs


    def create_clusterebs_sernode(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_bacula(self,clusterSetting):
        attrs={}
        attrs["install"]=True
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_java(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_gangliacli(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_nagioscli(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_rsyslogcli(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_smartd(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_tgtd(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_zookeeper(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_sheepdog(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_agentappnode(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_baculafd(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusterebs_baculasd(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs




