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
import sys
import subprocess
import yaml
import threading

class CommonUtil(object):
	"""docstring for ClassName"""
	def __init__(self,ip=None,ssh_user=None,ssh_password=None):
		if not ip:
		   self.ip=settings.MASTER_IP
		else:
		   self.ip = ip
		if not ssh_user:
			self.ssh_user='root'
		else:
			self.ssh_user=ssh_user
		if not ssh_password:
			self.ssh_password='r00tme'
		else:	
			self.ssh_password = ssh_password
		self.key_filename = '/root/.ssh/id_rsa'
		self.timeout=40
		#self.sshclient = SSHClient(self.ip,self.ssh_user,self.ssh_password,self.timeout)
		
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


	def create_ssh_masterToAgent(self,**kwargs):
		#如果UI返回的是504超时的话,需要改小timeout的值,才能捕获到后台异常
		try:
			ssh_client=SSHClient(self.ip,self.ssh_user,self.ssh_password,self.timeout)
			self.create_authorized_keys(ssh_client)
			self.change_sshdconfig(ssh_client)
			self.changeshcontent(ethname=kwargs["ethname"])
			self.copyshToAgent(ssh_client)
		except Exception,e:
			logger.info(self.ip+":"+e.message)
			return False
		return True

	def create_authorized_keys(self,ssh_client):
		dele_tagfile_cmd = "rm -fr /root/initnode_res"
		ssh_client.exec_command(dele_tagfile_cmd)

		delete_network_cmd = "rm -fr /root/.network && rm -fr /root/.network2"
		ssh_client.exec_command(delete_network_cmd)

		authorized_keys_con = CommonUtil.execute_cmd("cat /root/.ssh/id_rsa.pub")
		mksshdir_cmd = "mkdir -p /root/.ssh && chmod 700 /root/.ssh"
		ssh_client.exec_command(mksshdir_cmd)

		cpfilekey_cmd="echo \""+authorized_keys_con+"\" > /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys"
		ssh_client.exec_command(cpfilekey_cmd)

		
	def change_sshdconfig(self,ssh_client):
		changesshd_cmd1 = 'sed -i -e "/^\s*GSSAPICleanupCredentials yes/d" -e "/^\s*GSSAPIAuthentication yes/d" /etc/ssh/sshd_config'
		ssh_client.exec_command(changesshd_cmd1)
		changesshd_cmd2 = "sed -i --follow-symlinks -e '/UseDNS/d' /etc/ssh/sshd_config && echo 'UseDNS no' >> /etc/ssh/sshd_config"
		ssh_client.exec_command(changesshd_cmd2)
		sshrestart_cmd = "service sshd restart"
		ssh_client.exec_command(sshrestart_cmd)

	def changeshcontent(self,**kwargs):
		initsh_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"init_node.sh")
		fr = open('/etc/fuel/astute.yaml', 'r')
		data = yaml.load(fr)

		master_ip = data["ADMIN_NETWORK"]["ipaddress"]
		setmasterip_cmd = "sed -i 's/master_ip=10.20.0.0/master_ip="+master_ip+"/' "+initsh_path+""
		CommonUtil.execute_cmd(setmasterip_cmd)

		setpxethname_cmd = "sed -i 's/eth_name=eth0/eth_name="+kwargs["ethname"]+"/' "+initsh_path+""
		CommonUtil.execute_cmd(setpxethname_cmd)

		setpxeip_cmd = "sed -i 's/pxe_ip=10.20.0.0/pxe_ip="+self.ip+"/' "+initsh_path+""
		CommonUtil.execute_cmd(setpxeip_cmd)

		netmask=data["ADMIN_NETWORK"]["netmask"]
		setnetmask_cmd = "sed -i 's/netmask=255.255.255.0/netmask="+netmask+"/' "+initsh_path+""
		CommonUtil.execute_cmd(setnetmask_cmd)

		puppetmaster = data["HOSTNAME"]+"."+data["DNS_DOMAIN"]
		puppetmaster_cmd = "sed -i 's/puppet_master=fuel.domain.tld/puppet_master="+puppetmaster+"/' "+initsh_path+""
		CommonUtil.execute_cmd(puppetmaster_cmd)

		mco_password = data["mcollective"]["password"]
		mco_password_cmd = "sed -i 's/mco_password=111/mco_password="+mco_password+"/' "+initsh_path+""
		CommonUtil.execute_cmd(mco_password_cmd)


	def copyshToAgent(self,ssh_client):
		initsh_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"init_node.sh")
		cpinitsh_cmd = "scp "+initsh_path+" root@"+self.ip+":/root"
		CommonUtil.execute_cmd(cpinitsh_cmd)
		chmodcmd = "chmod 777 /root/init_node.sh && sed -i 's/\r$//' init_node.sh"
		ssh_client.exec_command(chmodcmd)


	def excute_initnodeshell(self,shclient=None):
		#参数shclient暂时没有用到
		#ssh_client=SSHClient(self.ip,self.ssh_user,self.ssh_password,self.timeout)
		#在某些时候脚本日志显示只执行了一部分就终止了
		
		excute_shellcmd = "ssh {0} '/root/init_node.sh >> /var/log/init-node.log 2>&1'".format(self.ip)
		#excute_shellcmd = "ssh {0} 'ls'".format(self.ip)
		CommonUtil.execute_cmd(excute_shellcmd)

	def getshellresulst(self):
		excute_shellcmd = "ssh {0} 'cat /root/initnode_res'".format(self.ip)
		msg=CommonUtil.execute_cmd(excute_shellcmd)
		logger.info(u"initnode_res的内容{0}".format(msg))
		return msg

	def copynailgunagent(self):
		agent_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"nailgun-agent")
		agent_path_cmd = "scp -r "+agent_path+" root@"+self.ip+":/usr/bin"
		#logger.info(agent_path_cmd)
		msg=CommonUtil.execute_cmd(agent_path_cmd)
		chmodcmd = "ssh {0} 'chmod 777 /usr/bin/nailgun-agent'".format(self.ip)
		CommonUtil.execute_cmd(chmodcmd)
		#logger.info(msg)

	@staticmethod
	def execute_cmd(cmd, customer_errmsg=None):
		res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		res.wait()

		readmsg = res.stdout.read().strip()
		errormsg = res.stderr.read()

		#shell执行成功或者失败可能同时返回stdout和stderr
	    #所以不能以是否返回errormsg来判断是否执行成功
        #shell 执行成功返回0,返回其它数值全部为失败

		if res.returncode == 0:
			return readmsg
		else:
			raise Exception


