# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import String
from sqlalchemy.orm import relationship, backref

from nailgun.db import db
from nailgun.db.sqlalchemy.models.base import Base
from nailgun.db.sqlalchemy.models.fields import JSON


class ClusterSetting(Base):
  __tablename__ = 'cluster_setting_info'
  id = Column(Integer, primary_key=True)
  cluster_id = Column(Integer, ForeignKey('clusters.id'))
  cluster_setting = Column(Text)


class ClusterdeployMsg(Base):
  __tablename__ = 'cluster_deploy_msg'
  id = Column(Integer, primary_key=True)
  cluster_id = Column(Integer, ForeignKey('clusters.id'))
  cluster_deploymsg = Column(Text)


class ClusterRoleStatus(Base):
  __tablename__='cluster_role_status'
  id=Column(Integer,primary_key=True)
  cluster_id=Column(Integer, ForeignKey('clusters.id'))
  cluster_role=Column(String(20), nullable=False)
  role_status=Column(Integer, nullable=False)


