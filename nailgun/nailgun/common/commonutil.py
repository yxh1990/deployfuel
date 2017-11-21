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


from nailgun.settings import settings
from nailgun.common.ShellCmdExecutor import ShellCmdExecutor
from nailgun.common.ssh import Client as SSHClient
from nailgun.logger import logger
import time
import os
import random

class CommonUtil(object):
	"""docstring for ClassName"""
	def __init__(self,ip=None):
		if not ip:
		   self.ip=settings.MASTER_IP
		else:
		   self.ip = ip
		self.ssh_user='root'
		self.ssh_password='r00tme'
		self.key_filename = '/root/.ssh/id_rsa'
		self.timeout=60
		
	def get_master_gateway(self):

		ssh_client=SSHClient(self.ip,self.ssh_user,self.ssh_password,self.timeout,self.key_filename)
		cmd="route -n | grep 'UG' | awk '{print $2}'"
		result = ssh_client.exec_command(cmd)
        #0.0.0.0         192.168.181.126 0.0.0.0         UG    0      0        0 eth0.20
		#cmd="ip route show | grep 'default'"
		#default via 10.254.9.254 dev eth4
		#default dev eth0  scope link
		#不能直接在此方法做操作,执行远程shell有时间延迟
		return result

	def format_gwip(self):
		result=self.get_master_gateway().strip("\n\r")
		#results=result.split(" ")
		#['default', 'via', '10.254.9.254', 'dev', 'eth4', '\r\n']
		#logger.info(results[2])
		return result
		#return results[1]

	def copyfile(self,filesrc,targetsrc,service):
		#filesrc   文件源路径
		#targetsrc 文件目标路径
		#service   是否需要重启服务
		#执行shell命令0代表成功,其他数字都是失败.
		cmd ="scp -r {0} root@{1}:{2}".format(filesrc,self.ip,targetsrc)
		logger.info(cmd)
		result=os.system(cmd)
		if result == 0:
		   logger.info(u"成功复制net_probe.rb到{0}节点上".format(self.ip))
		   if service =="mcollective":
		   	  self.restartmocllective()
		else:
		   logger.error(u"复制net_probe.rb到{0}节点上失败".format(self.ip))

		
	def restartmocllective(self):
		#只能ssh登录正常安装操作系统的节点,处于discover状态的节点无法登录.
		#ssh_client=SSHClient(self.ip,self.ssh_user,self.ssh_password,self.timeout,self.key_filename)
		cmd = "ssh {0} 'systemctl restart  mcollective.service'".format(self.ip)
		logger.info(cmd)
		result = os.system(cmd)
		if result == 0:
		    logger.info(u"成功重启节点{0}上的mocllective服务....".format(self.ip))
		else:
			logger.info(u"重启节点{0}上的mocllective服务失败....".format(self.ip))

	def generate_randnumber(self,length):
		randomnumber = 0
		if length == 3:
			randomnumber = random.randint(101,255)
		elif length == 4:
			randomnumber = random.randint(1000,9999)
		return randomnumber


