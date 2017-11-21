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

class clusteronest(object):

    def stripdict(self,olddict):

        for key in olddict.iterkeys():
            olddict[key]=olddict[key].strip()
        return olddict

    def create_clusteronest_prepare(self,clusterSetting):
        attrs={}
        clusterSetting["onestpwd"]=clusterSetting["onestpwd"].strip()
        attrs.update(clusterSetting)
        return attrs

    def create_clusteronest_java(self,clusterSetting):
        attrs={}
        attrs.update(clusterSetting)
        return attrs

    def create_clusteronest_zookeeper(self,clusterSetting):
        attrs={}
        attrs.update(self.stripdict(clusterSetting))
        return attrs

    def create_clusteronest_hadoop(self,clusterSetting):
        attrs={}
        attrs.update(self.stripdict(clusterSetting))
        return attrs

    def create_clusteronest_hbase(self,clusterSetting):
        attrs={}
        attrs.update(self.stripdict(clusterSetting))
        return attrs

    def create_clusteronest_onest(self,clusterSetting):
        attrs={}
        attrs.update(self.stripdict(clusterSetting))
        return attrs

   



