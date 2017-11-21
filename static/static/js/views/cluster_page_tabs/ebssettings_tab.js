/*
 * Copyright 2013 Mirantis, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
**/
define(
[
    'jquery',
    'underscore',
    'utils',
    'models',
    'views/common',
    'backbone',
    'views/cluster_page',
    'jsx!views/dialogs',
    'text!templates/cluster/ebs_setting.html',
],
function($, _, utils, models, commonViews, Backbone, clusterPageviews, dialogs, CloudSettingsTemplate) {
    'use strict';
    var CloudSettingsTab;

    CloudSettingsTab = commonViews.Tab.extend({
        className: 'openstack-settings wrapper',
        template: _.template(CloudSettingsTemplate),
        initialize: function(options) {
            _.defaults(this, options);
        },
         events:{
            'click #btnloadDefault':'loadDefaults',
            'click #btn_save':'SaveSetting',
            'blur input':"validate"
        },
        loadDefaults:function(){  
          Backbone.history.loadUrl();
        },
        onDeployRequest:function() {
            var cluster=app.page.model;
            utils.showDialog(dialogs.DeployChangesDialog, {cluster: cluster});
        },
        SaveSetting:function(){
           var cluster_settings={};

           var prepare={};
               prepare["deploy2user"]=this.$('#txt_deploy2user').val();
               prepare["deploy2group"]=this.$('#txt_deploy2group').val();
               prepare["deploy2userpw"]=this.$('#txt_deploy2userpw').val();
               prepare["action"]="config"; //此参数需要程序动态修改,不能被用户修改。

           var gangliasrv={};
               gangliasrv["serverip"]=this.$('#txt_gserverip').val();
               gangliasrv["action"]="config";

           var nagiossrv={};
               nagiossrv["serverip"]=this.$('#txt_nserverip').val();
               nagiossrv["clientips"]=""; //将所有的nagioscli角色机子的ip组合起来
               nagiossrv["action"]="config";

           var watcher={};
               watcher["serverip"]=this.$('#txt_wserverip').val();
               watcher["action"]="config";

           var management={};
               management["serverip"]=this.$('#txt_mserverip').val();
               management["dbip"]=this.$('#txt_mdbip').val();
               management["dbuser"]=this.$('#txt_mdbuser').val();
               management["dbpwd"]=this.$('#txt_mdbpwd').val();
               management["trapip"]=this.$('#txt_trapip').val();
               management["trapport"]=this.$('#txt_trapport').val();
               management["action"]="config";

          var cinder={};
               cinder["serverip"]=this.$('#txt_cserverip').val();
               cinder["dbip"]=this.$('#txt_cdbip').val();
               cinder["dbuser"]=this.$('#txt_cdbuser').val();
               cinder["dbpwd"]=this.$('#txt_cdbpwd').val();
               cinder["port"]=this.$('#txt_cport').val();
               cinder["action"]="config";
         
           var syslog={};
               syslog["serverip"]=this.$('#txt_rserverip').val();
               syslog["dbip"]=this.$('#txt_rdbip').val();
               syslog["dbuser"]=this.$('#txt_rdbuser').val();
               syslog["dbpwd"]=this.$('#txt_rdbpwd').val();
               syslog["action"]="config";

          var sernode={};
              sernode["ssd_exclude"]=document.getElementById('ck_ssd_exclude').checked;
              //sernode["raid"]=this.$("input[name='ck_raid']").attr("checked");
              sernode["raid"]=document.getElementById('ck_raid').checked;
              sernode["raid_type"]=this.$("input[name='se_raid_type']:checked").val();
              sernode["action"]="config";

          var bacula={};
              bacula["serverip"]=this.$('#txt_bserverip').val();
              bacula["dbip"]=this.$('#txt_bdbip').val();
              bacula["dbuser"]=this.$('#txt_bdbuser').val();
              bacula["dbpwd"]=this.$('#txt_bdbpwd').val();
              bacula["dir_name"]=this.$('#txt_bdir_name').val();
              bacula["fd_name"]=this.$('#txt_fd_name').val();
              bacula["sd_name"]=this.$('#txt_sd_name').val();
              bacula["group_name"]=this.$('#txt_group_name').val();
              bacula["onest_accesskey"]=this.$('#txt_onest_accesskey').val();
              bacula["onest_secreykey"]=this.$('#txt_onest_secreykey').val();
              bacula["onest_srv_ip"]=this.$('#txt_onest_srv_ip').val();
              bacula["onest_bucketname"]=this.$('#txt_onest_bucketname').val();
              bacula["onest_accesskey_sys"]=this.$('#txt_onest_accesskey_sys').val();
              bacula["onest_secreykey_sys"]=this.$('#txt_onest_secreykey_sys').val();
              bacula["onest_srv_ip_sys"]=this.$('#txt_onest_srv_ip_sys').val();
              bacula["onest_bucketname_sys"]=this.$('#txt_onest_bucketname_sys').val();
              bacula["action"]="config";

          var javasetting={};
              javasetting["action"]="config";
          var gangliacli={};
              gangliacli["action"]="config";
          var nagioscli={};
              nagioscli["action"]="config";
          var rsyslogcli={};
              rsyslogcli["action"]="config";
          var smartd={};
              smartd["action"]="config";
          var tgtd={};
              tgtd["action"]="config";
          var zookeeper={};
              zookeeper["action"]="config";
          var sheepdog={};
              sheepdog["action"]="config";
          var agentappnode={};
              agentappnode["action"]="config";
          var baculafd={};
              baculafd["action"]="config";
          var baculasd={};
              baculasd["action"]="config";

           cluster_settings["prepare"]=prepare;
           cluster_settings["gangliasrv"]=gangliasrv;
           cluster_settings["nagiossrv"]=nagiossrv;
           cluster_settings["watcher"]=watcher;
           cluster_settings["management"]=management;
           cluster_settings["ebs-cinder"]=cinder;
           cluster_settings["rsyslogsrv"]=syslog;
           cluster_settings['agent-sernode']=sernode;
           cluster_settings['bacula-dir']=bacula;
           cluster_settings['java']=javasetting;
           cluster_settings['gangliacli']=gangliacli;
           cluster_settings['nagioscli']=nagioscli;
           cluster_settings['rsyslogcli']=rsyslogcli;
           cluster_settings['smartd']=smartd;
           cluster_settings['tgtd']=tgtd;
           cluster_settings['zookeeper']=zookeeper;
           cluster_settings['sheepdog']=sheepdog;
           cluster_settings['agent-appnode']=agentappnode;
           cluster_settings['bacula-fd']=baculafd;
           cluster_settings['bacula-sd']=baculasd;


           var errorslength=this.$('input.error').length;
           if(errorslength>0)
           {
             alert("输入有误,不能保存!");
             return;
           }
           else
           {
             var cluster_id=this.page.model.id;
             var cluster_type=this.page.model.get('cluster_type');
             $.ajax({
                  type: "POST",
                  url: "/api/clusterseting/save/",
                  data: "cluster_id="+cluster_id+"&content="+JSON.stringify(cluster_settings)+"&cluster_type="+cluster_type,
                  success: _.bind(function(msg){
                      var cluster=this.page.model;
                      var nodes = cluster.get('nodes');
                      var msgflag=cluster.get('release').get('state')!='available' || (!cluster.hasChanges() && !cluster.needsRedeployment()) || nodes.every({status: 'ready', pending_deletion: false});
                      if(msgflag==false)
                      { 
                         //不支持ie
                        $(".deploy-btn").attr("disabled",false);
                        $(".deploy-btn").click(this.onDeployRequest);
                        $("#showsetmsg").attr("display","none");
                        cluster.set({cluster_setting: cluster_settings});
                      }
                     alert('保存成功!');
                    },this),
                 error:function(msg)
                  {
                      alert('保存失败!');
                   }
               });
            }
        },
        validate:function(e)
        {
           var ele=this.$(e.currentTarget);
           var datatype=ele.attr("data-type");
           var data=ele.val();
           if(_.isEmpty(data))
           {
             this.handlerrormsg(ele,'不能为空');
           }
           else
           {
             if(datatype)
             {
               this.checkdataformat(ele,data,datatype);
             }
             else
             {
              this.handlerrormsg(ele);
             }
           }
        },
        checkdataformat:function(ele,data,datatype)
         {
          if(datatype=="num")
             {
               if(!data.match(utils.regexes.number))
               {
                 this.handlerrormsg(ele,'格式必须为整数');
               }
               else
               {
                 this.handlerrormsg(ele);
               }
             }
             else if(datatype=="ip")
             {
                if(!data.match(utils.regexes.ip))
                {
                  this.handlerrormsg(ele,'格式必须为ip');
                }
                else
                {
                 this.handlerrormsg(ele);
                }
             }
         },
         handlerrormsg:function(obj,msg){
           var title=obj.prev().children().html();
           var discontrol=obj.parent().next();
           if(msg){
              obj.addClass('error');
              discontrol.addClass('error');
              discontrol.html("<font color='#b94a48'>"+title+msg+"</font>");
            }
          else
           {
             obj.removeClass('error');
             discontrol.html("");
           }
        },
        render: function() {
         /* if(app.selectedRoles){*/
          var cluster_id=this.page.model.id;
          $.ajax({
                type: "GET",
                url: "/api/clusterseting/save/",
                data: "cluster_id="+cluster_id,
                success: _.bind(function(msg){
                  var result={};
                  if(msg.cluster_setting)
                  {
                    result=JSON.parse(msg.cluster_setting)
                  }
                  else
                  {
                    result=msg;
                  }
                  this.$el.html(this.template({data:result}));
                },this),
                error:function(msg)
                {
                   alert('获取设置信息失败!');
                }
            });
            app.selectedRoles=null;
            return this;
         /* }
          else
          {
            alert('请先选择需要安装的角色信息');
            return;
          }*/
        }
    });
    return CloudSettingsTab;
});
