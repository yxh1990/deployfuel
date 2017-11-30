#!/usr/bin/env python
# -*- coding:utf-8 -*-
#author yanxianghui

import subprocess
import sys
import os


def execute_cmd(cmd, customer_errmsg):
	res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	res.wait()
	readmsg = res.stdout.read().strip()
	errormsg = res.stderr.read()

	# shell执行成功或者失败可能同时返回stdout和stderr
	# 所以不能以是否返回errormsg来判断是否执行成功
	# shell 执行成功返回0,返回其它数值全部为失败
	if res.returncode == 0:
		return readmsg
	else:
		print(errormsg)
		print(customer_errmsg)
		sys.exit()

cmd="docker inspect -f '{{.ID}}' fuel-core-6.0-nailgun"

nailgunerrmsg="获取nailgun的容器id失败,升级失败......"
nailguncid = execute_cmd(cmd, nailgunerrmsg)

nailgunPythonPwd = "/var/lib/docker/devicemapper/mnt/%s/rootfs/usr/lib/python2.6/site-packages" % (nailguncid,)
mvcmd = "rm -fr %s/nailgun" %(nailgunPythonPwd,)
mverrmsg = "删除原来的nailgun文件夹失败....."
execute_cmd(mvcmd, mverrmsg)

cpcmd= "cp -r code/nailgun %s/" %(nailgunPythonPwd,)
cperrmsg = "复制最新nailgun目录失败...."
execute_cmd(cpcmd, cperrmsg)

cpthreadingcmd = "cp -r packages/threading/threadpool.py %s/"  %(nailgunPythonPwd,)
cperrmsg2 = "复制threadpool.py失败...."
execute_cmd(cpthreadingcmd, cperrmsg2)

print("nailgun升级成功,开始升级static文件................")
static_cmd="docker inspect -f '{{.Volumes}}' fuel-core-6.0-nailgun | awk '{printf(\"%s\\n\", $5);}'"
restr = execute_cmd(static_cmd, "")
reslist=restr.split(":")
if len(reslist)>=2:
	delcmd = "rm -fr %s/*" % (reslist[1])
	cpcmd = "cp -r code/static/* %s" % (reslist[1])
	execute_cmd(delcmd, "删除原来static文件失败")
	execute_cmd(cpcmd, "更新static文件夹失败......")
else:
	print("查找static目录失败..........")
	sys.exit()
print("static目录升级成功,开始升级database............")
if os.path.exists('/usr/lib/python2.6/site-packages/sqlalchemy'):
	print("当前节点上已经安装sqlalchemy,自动跳过安装步骤....")
else:
	sqlalchemycmd = "cp -r packages/sqlalchemy /usr/lib/python2.6/site-packages"
	execute_cmd(sqlalchemycmd, "安装sqlalchemy模块失败")

	pg2cmd = "cp -r packages/psycopg2 /usr/lib/python2.6/site-packages"
	execute_cmd(pg2cmd, "安装数据库驱动模块失败")


import json
import yaml
from sqlalchemy import create_engine

fr = open('/etc/fuel/astute.yaml', 'r')
data = yaml.load(fr)
dbpassword=data["postgres"]["nailgun_password"]
fr.close()
engine = create_engine("postgresql://nailgun:{0}@127.0.0.1:5432/nailgun".format(dbpassword),client_encoding="utf-8")

dropPhymachineCmd="drop table physical_machine_info"
engine.execute(dropPhymachineCmd)

createPhymachineCmd="""
CREATE TABLE physical_machine_info
(
  id serial NOT NULL,
  name character varying(50) NOT NULL,
  ip character varying(20) NOT NULL,
  mp_username character varying(20) NOT NULL,
  mp_passwd character varying(20) NOT NULL,
  cabinet character varying(30) NOT NULL,
  gene_room character varying(30) NOT NULL,
  mac character varying(30) NOT NULL,
  ethname character varying(30) NOT NULL,
  use_type integer NOT NULL,
  additional_info text,
  CONSTRAINT physical_machine_info_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE physical_machine_info
  OWNER TO nailgun;
"""
engine.execute(createPhymachineCmd)

print("the table physical_machine_info is  success updated.....")

restartnailguncmd = "docker restart %s" %(nailguncid,)
execute_cmd(restartnailguncmd, "重启nailgun容器失败")
print("恭喜,升级命令全部成功执行完毕,由于重启服务需要几分钟时间,请你耐心等待下再刷新浏览器！")
