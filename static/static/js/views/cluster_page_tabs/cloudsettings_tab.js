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
    'text!templates/cluster/cloud_setting.html',
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

           var clsmasterSetting={};
               clsmasterSetting["installDir"]=this.$('#txt_dir_name').val();
               clsmasterSetting["db_hostIp"]=this.$('#txt_db_hostIp').val();
               clsmasterSetting["db_user"]=this.$('#txt_db_root').val();
               clsmasterSetting["db_port"]=this.$('#txt_db_port').val();
               clsmasterSetting["db_passwd"]=this.$('#txt_db_passwd').val();
               clsmasterSetting["PublicCloudWS"]=this.$('#txt_PublicCloudWS').val();
               clsmasterSetting["SouthBaseWS"]=this.$('#txt_SouthBaseWS').val();
               clsmasterSetting["log_dir"]=this.$('#txt_log_dir').val();
               clsmasterSetting["mq_tcp_url"]=this.$('#txt_mq_tcp_url').val();
               clsmasterSetting["webservice_url"]=this.$('#txt_webservice_url').val();
               clsmasterSetting["onecmdb_url"]=this.$('#txt_onecmdb_url').val();
               clsmasterSetting["Search_SoftInstall_Url"]=this.$('#txt_Search_SoftInstall_Url').val();
               clsmasterSetting["kickstart_ip"]=this.$('#txt_kickstart_ip').val();
               clsmasterSetting["kickstart_user"]=this.$('#txt_kickstart_user').val();
               clsmasterSetting["kickstart_passwd"]=this.$('#txt_kickstart_passwd').val();
               clsmasterSetting["kickstart_port"]=this.$('#txt_kickstart_port').val();
               clsmasterSetting["kickstart_dir"]=this.$('#txt_kickstart_dir').val();
               clsmasterSetting["dhcpd_ksfile_path"]=this.$('#txt_dhcpd_ksfile_path').val();
               clsmasterSetting["ksfile_url"]=this.$('#txt_ksfile_url').val();
               clsmasterSetting["dhcpd_bootfile_path"]=this.$('#txt_dhcpd_bootfile_path').val();
               clsmasterSetting["os_callback_url"]=this.$('#txt_os_callback_url').val();
               clsmasterSetting["collect_server_ip"]=this.$('#txt_collect_server_ip').val();
               clsmasterSetting["collect_server_id"]=this.$('#txt_collect_server_id').val();
               clsmasterSetting["action"]="config"; //此参数需要程序动态修改,不能被用户修改。
               clsmasterSetting["label"]="0"; //即使是数字标志位也需要加双引号,否则不会生效
           var clsslaveSetting={};
               clsslaveSetting["installDir"]=this.$('#txt_clsslave_installDir').val();
               clsslaveSetting["log_dir"]=this.$('#txt_clsslave_log_dir').val();
               clsslaveSetting["db_hostIp"]=this.$('#txt_clsslave_db_hostIp').val();
               clsslaveSetting["db_user"]=this.$('#txt_clsslave_db_root').val();
               clsslaveSetting["db_port"]=this.$('#txt_clsslave_db_port').val();
               clsslaveSetting["db_passwd"]=this.$('#txt_clsslave_db_passwd').val();
               clsslaveSetting["octopus_url"]=this.$('#txt_octopus_url').val();
               clsslaveSetting["ruleXml_path"]=this.$('#txt_ruleXml_path').val();
               clsslaveSetting["onecmdb_url"]=this.$('#txt_clsslave_onecmdb_url').val();
               clsslaveSetting["mq_tcp_url"]=this.$('#txt_clsslave_mq_tcp_url').val();
               clsslaveSetting["action"]="config";
               clsslaveSetting["label"]="0";
           var mysqlSetting={};
               mysqlSetting["installDir"]=this.$('#txt_mysql_installDir').val();
               mysqlSetting["db_user"]=this.$('#txt_mysql_db_user').val();
               mysqlSetting["db_password"]=this.$('#txt_mysql_db_password').val();
               mysqlSetting["db_port"]=this.$('#txt_mysql_db_port').val();
               mysqlSetting["action"]="config";
               mysqlSetting["label"]="0";

           var nagiosSetting={};
               nagiosSetting["installDir"]=this.$('#txt_nagios_installDir').val();
               nagiosSetting["cmagentUrl"]=this.$('#txt_cmagentUrl').val();
               nagiosSetting["action"]="config";
               nagiosSetting["label"]="0";

           var gangliaSetting={};
               gangliaSetting["installDir"]=this.$('#txt_ganglia_installDir').val();
               gangliaSetting["ganglia_hostIp"]=this.$('#txt_ganglia_hostIp').val();
               gangliaSetting["action"]="config";
               gangliaSetting["label"]="0";

           var dhcpserverSetting={};
               dhcpserverSetting["installDir"]=this.$('#txt_dhcpserver_installDir').val();
               dhcpserverSetting["subnet"]=this.$('#txt_dhcpserver_subnet').val();
               dhcpserverSetting["netmask"]=this.$('#txt_dhcpserver_netmask').val();
               dhcpserverSetting["routers"]=this.$('#txt_dhcpserver_routers').val();
               dhcpserverSetting["action"]="config";
               dhcpserverSetting["label"]="0";

           cluster_settings["clsmaster"]=clsmasterSetting;
           cluster_settings["clsslave"]=clsslaveSetting;
           cluster_settings["mysqlcls"]=mysqlSetting;
           cluster_settings["nagios"]=nagiosSetting;
           cluster_settings["ganglia"]=gangliaSetting;
           cluster_settings["dhcpserver"]=dhcpserverSetting;

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
