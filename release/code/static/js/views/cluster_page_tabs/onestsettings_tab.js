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
    'text!templates/cluster/onest_setting.html',
    'text!templates/common/ips.html'
],
function($, _, utils, models, commonViews, Backbone, clusterPageviews, dialogs, CloudSettingsTemplate,IpsTemplate) {
    'use strict';
    var CloudSettingsTab;

    CloudSettingsTab = commonViews.Tab.extend({
        className: 'openstack-settings wrapper',
        template: _.template(CloudSettingsTemplate),
        initialize: function(options) {
            _.defaults(this, options);
            Backbone.on('refreshselectips', this.refreshselectips, this);
            this.currentTextId=null;
        },
         events:{
            'click #btnloadDefault':'loadDefaults',
            'click #btn_save':'SaveSetting',
            'click .fieldset-group button':"selectIps"
        },
        selectIps:function(e)
        {
           var obj=this.getIpType(e.target.id);
           var typeips=obj.typeips;
           var checkedips=$("#"+obj.textid).val();
           var loadview=new commonloadview(typeips,checkedips);
           $('#modal-container').append(loadview.render().el);
        },
        getIpType:function(btnid)
        { 
            var ipobj={};
            if (btnid == "btn_zkserversip_ip")
            {
               ipobj.typeips="zkserversip";
               ipobj.textid="txt_zkserversip";
            }
            else if(btnid == "btn_namenodes_ip")
            {
               ipobj.typeips="hadoop_namenodes_ips";
               ipobj.textid="txt_namenodes_ipaddress";
            }
            else if(btnid == "btn_datanodes_ips")
            {
               ipobj.typeips="hadoop_datanodes_ips";
               ipobj.textid="txt_datanodes_ipaddress";
            }
            else if(btnid == "btn_journalnode_ips")
            {
               ipobj.typeips="hadoop_journalnode_ips";
               ipobj.textid="txt_journalnode_ipaddress";
            }
            else if(btnid == "btn_hbase_masterhostname")
            {
              ipobj.typeips="hbase_master_host_name";
              ipobj.textid="txt_hbase_master_host_name";
            }
            else if(btnid == "btn_hbase_backup_masterhostname")
            {
              ipobj.typeips="hbase_backup_master_host_name";
              ipobj.textid="txt_hbase_backup_master_host_name";
            }
            else if(btnid == "btn_hbase_regionservername")
            {
              ipobj.typeips="hbase_regionservers_host_name";
              ipobj.textid="txt_hbase_regionservers_host_name";
            }
            else if(btnid == "btn_onest_license_server")
            {
              ipobj.typeips="onest_license_servers";
              ipobj.textid="txt_onest_license_servers";
            }
            else if(btnid == "btn_onest_aaa_server")
            {
              ipobj.typeips="onest_aaa_master_server";
              ipobj.textid="txt_onest_aaa_master_server";
            }
            else if(btnid == "btn_onest_aaa_gateway")
            {
              ipobj.typeips="onest_aaa_master_gateway";
              ipobj.textid="txt_onest_aaa_master_gateway";
            }
            else if(btnid == "btn_onest_memcached_server")
            {
              ipobj.typeips="onest_memcached_master_servers";
              ipobj.textid="txt_onest_memcached_master_servers";
            }
            else if(btnid == "btn_onest_aaa_vip")
            {
              ipobj.typeips="onest_aaa_vip";
              ipobj.textid="txt_onest_aaa_vip";
            }
            else if(btnid == "btn_onest_console_servers")
            {
              ipobj.typeips="onest_console_servers";
              ipobj.textid="txt_onest_console_servers";
            }
            else if(btnid == "btn_onest_oas_servers")
            {
              ipobj.typeips="onest_oas_servers";
              ipobj.textid="txt_onest_oas_servers";
            }
            else if(btnid == "btn_onest_oas_lightip")
            {
              ipobj.typeips="onest_oas_lightip";
              ipobj.textid="txt_onest_oas_lightip";
            }
            else if(btnid == "btn_onest_oas_keepalived")
            {
              ipobj.typeips="onest_oas_keepalived";
              ipobj.textid="txt_onest_oas_keepalived";
            }
            else if(btnid == "btn_onest_oas_vip")
            {
              ipobj.typeips="onest_oas_vip";
              ipobj.textid="txt_onest_oas_vip";
            }
            else if(btnid == "btn_onest_except_datastorage")
            {
              ipobj.typeips="onest_except_NN_DN_datastorage";
              ipobj.textid="txt_onest_except_NN_DN_datastorage";
            }
            else if(btnid == "btn_onest_except_datastorage")
            {
              ipobj.typeips="onest_except_NN_DN_datastorage";
              ipobj.textid="txt_onest_except_NN_DN_datastorage";
            }
            else if(btnid == "btn_onest_azstat_servers")
            {
              ipobj.typeips="onest_azstat_servers";
              ipobj.textid="txt_onest_azstat_servers";
            }
            else if(btnid == "btn_onest_regionstat_servers")
            {
              ipobj.typeips="onest_regionstat_servers";
              ipobj.textid="txt_onest_regionstat_servers";
            }
            else if(btnid == "btn_onest_datastorage_servers")
            {
              ipobj.typeips="onest_datastorage_servers";
              ipobj.textid="txt_onest_datastorage_servers";
            }
            else if(btnid == "btn_onest_healer_servers")
            {
              ipobj.typeips="onest_healer_servers";
              ipobj.textid="txt_onest_healer_servers";
            }
            this.currentTextId=ipobj.textid;
          return ipobj;
        },
        refreshselectips:function()
        {
          $("#"+this.currentTextId).val(app.onest_selectips);
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
               prepare["onestuid"]=this.$('#txt_onestuid').val();
               prepare["onestpwd"]=this.$('#txt_onestpwd').val();
               prepare["onestprepareuser"]=this.$('#txt_onestprepareuser').val();
               prepare["lightip_vlan"]=this.$('#txt_lightip_vlan').val();
               prepare["light_pre_ip"]=this.$('#txt_light_pre_ip').val();
               prepare["lightIP_gateway"]=this.$('#txt_lightIP_gateway').val();
               prepare["bond_name"]=this.$('#txt_bond_name').val();
               prepare["network_card_name"]=this.$('#txt_network_card_name').val();
               prepare["route_ip"]=this.$('#txt_route_ip').val();
               prepare["filePreDirectory"]=this.$('#txt_filePreDirectory').val();
               prepare["installDir"]=this.$('#txt_installDir').val();

            var java={};
                java["java_home"]=this.$('#txt_java_home').val();
           
            var zookeeper={};
                zookeeper["zkdataDir"]=this.$('#txt_zkdataDir').val();
                zookeeper["zkserversip"]=this.$('#txt_zkserversip').val();

            var hadoop={};
                hadoop["hadoop_namenodes_ipaddress"]=this.$('#txt_namenodes_ipaddress').val();
                hadoop["hadoop_datanodes_ipaddress"]=this.$('#txt_datanodes_ipaddress').val();
                hadoop["hadoop_journalnode_ipaddress"]=this.$('#txt_journalnode_ipaddress').val();
                hadoop["hadoop_heap_size"]=this.$('#txt_hadoop_heap_size').val();
                hadoop["hadoop_temp_dir"]=this.$('#txt_hadoop_temp_dir').val();
                hadoop["hadoop_dfs_dir"]=this.$('#txt_hadoop_dfs_dir').val();
                //这里读取textarea的value,需要测试.
                //alert(this.$('#txt_hadoop_dfs_dir').val());
                hadoop["hadoop_dfs_name_dir"]=this.$('#txt_hadoop_dfs_name_dir').val();
                hadoop["hadoop_dfs_data_dir"]=this.$('#txt_hadoop_dfs_data_dir').val();
                hadoop["hadoop_copynamenode_dir"]=this.$('#txt_hadoop_copynamenode_dir').val();
                hadoop["hadoop_dfs_pre_dir"]=this.$('#txt_hadoop_dfs_pre_dir').val();
                hadoop["hadoop_journalnode_edits_dir"]=this.$('#hadoop_journalnode_edits_dir').val();
                hadoop["hadoop_mapred_dir"]=this.$('#txt_hadoop_mapred_dir').val();
                hadoop["hadoop_mapred_local_dir"]=this.$('#txt_hadoop_mapred_local_dir').val();
          
            var hbase={};
                hbase["hbase_master_host_name"]=this.$('#txt_hbase_master_host_name').val();
                hbase["hbase_backup_master_host_name"]=this.$('#txt_hbase_backup_master_host_name').val();
                hbase["hbase_regionservers_host_name"]=this.$('#txt_hbase_regionservers_host_name').val();
                hbase["hbase_heap_size"]=this.$('#txt_hbase_heap_size').val();

            var onest={};
                onest["action"]="config";
                onest["onestFileName"]=this.$('#txt_onestFileName').val();
                onest["onest_license_servers"]=this.$('#txt_onest_license_servers').val();
                onest["onest_healer_memory"]=this.$('#txt_onest_healer_memory').val();
                onest["onest_region_stat_memory"]=this.$('#txt_onest_region_stat_memory').val();
                onest["onest_oas_memory"]=this.$('#txt_onest_oas_memory').val();
                onest["onest_az_stat_memory"]=this.$('#txt_onest_az_stat_memory').val();
                onest["onest_aaa_master_server"]=this.$('#txt_onest_aaa_master_server').val();
                onest["onest_aaa_master_gateway"]=this.$('#txt_onest_aaa_master_gateway').val();
                onest["onest_memcached_master_servers"]=this.$('#txt_onest_memcached_master_servers').val();
                onest["onest_aaa_vip"]=this.$('#txt_onest_aaa_vip').val();
                onest["onest_console_servers"]=this.$('#txt_onest_console_servers').val();
                onest["onest_oas_servers"]=this.$('#txt_onest_oas_servers').val();
                onest["onest_oas_lightip"]=this.$('#txt_onest_oas_lightip').val();
                onest["onest_oas_keepalived"]=this.$('#txt_onest_oas_keepalived').val();
                onest["onest_oas_vip"]=this.$('#txt_onest_oas_vip').val();
                onest["onest_localAzName"]=this.$('#txt_onest_localAzName').val();
                onest["onest_alarm_url"]=this.$('#txt_onest_alarm_url').val();
                onest["onest_except_NN_DN_datastorage"]=this.$('#txt_onest_except_NN_DN_datastorage').val();
                onest["oNest_DataNode_Application_OAS_Workers"]=this.$('#txt_oNest_DataNode_Application_OAS_Workers').val();
                onest["oNest_DataNode_Application_ZK_Workers"]=this.$('#txt_oNest_DataNode_Application_ZK_Workers').val();
                onest["oNest_DataNode_Application_Healer_Workers"]=this.$('#txt_oNest_DataNode_Application_Healer_Workers').val();
                onest["oNest_DataNode_Application_FileIODispacher_Workers"]=this.$('#txt_oNest_DataNode_Application_FileIODispacher_Workers').val();
                onest["oNest_DataNode_SnmpDst_Addr"]=this.$('#txt_oNest_DataNode_SnmpDst_Addr').val();
                onest["oNest_DataNode_MemSize"]=this.$('#txt_oNest_DataNode_MemSize').val();
                onest["oNest_DataNode_Storage_MaxQuoto"]=this.$('#txt_oNest_DataNode_Storage_MaxQuoto').val();
                onest["oNest_DataNode_Storage_Num"]=this.$('#txt_oNest_DataNode_Storage_Num').val();
                onest["oNest_DataNode_Storage_Quoto"]=this.$('#txt_oNest_DataNode_Storage_Quoto').val();
                onest["oNest_DataNode_Storage_Data"]=this.$('#txt_oNest_DataNode_Storage_Data').val();
                onest["oNest_DataNode_Storage_BucketSize"]=this.$('#txt_oNest_DataNode_Storage_BucketSize').val();
                onest["onest_azstat_servers"]=this.$('#txt_onest_azstat_servers').val();
                onest["onest_regionstat_servers"]=this.$('#txt_onest_regionstat_servers').val();
                onest["onest_datastorage_servers"]=this.$('#txt_onest_datastorage_servers').val();
                onest["onest_healer_servers"]=this.$('#txt_onest_healer_servers').val();
                onest["onest_prefix_dir"]=this.$('#txt_onest_prefix_dir').val();
                onest["oNest_DataNode_Storage_extra_Dir"]=this.$('#txt_oNest_DataNode_Storage_extra_Dir').val();
                onest["oNest_DataNode_Storage_Dir"]=this.$('#txt_oNest_DataNode_Storage_Dir').val();

           cluster_settings['prepare']=prepare;
           cluster_settings['java']=java;
           cluster_settings['zookeeper']=zookeeper;
           cluster_settings['hadoop']=hadoop;
           cluster_settings['hbase']=hbase;
           cluster_settings['onest']=onest;

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

var commonloadview = Backbone.View.extend({
     id:'modalshow',
     className:'modal fade in',
     template: _.template(IpsTemplate),
     events:{
      'click .close':"closeips",
      'click #btn_cancel':"closeips",
      'click #btn_ok':'handlerselectips',
      'click #ckall':'checkallips',
      'click #trdata input[type=checkbox]':'handlerallbox'
     },
     handlerallbox:function()
     {
        var totalcheckbox=this.$("#trdata input[type='checkbox']");
        var ipsarr=[];
        totalcheckbox.each(function(i,ck) {
            if(ck.checked)
            {
              ipsarr.push(ck.value);
            }
       });
       if(totalcheckbox.length == ipsarr.length)
       {
          //this.$("#ckall").attr("checked",true); 此语句不能正确执行.
          this.$("#thcheckall").html("<input type='checkbox' id='ckall' value='all' checked />");
       }
       else
       {
          this.$("#ckall").removeAttr("checked");
       }
     },
     handlerselectips:function()
     {
         var ipsarr=[];
         this.$("input[type='checkbox']").each(function(i,ck) {
            if(ck.checked)
            {
              if(ck.value!="all")  //all代表全选check的value
                 ipsarr.push(ck.value);
            }
          });
         app.onest_selectips=ipsarr;
         Backbone.trigger('refreshselectips'); 
         $(this.el).remove();
     },
     checkallips:function()
     {
        var ckstatu=this.$("#ckall").is(':checked');
            this.$("input[type='checkbox']").each(function(i,ck) {
              ck.checked=ckstatu;
           });
     },
     closeips:function()
     {
       $(this.el).remove();
     },
     initialize: function(checktype,checkedips) 
     {
       this.nodesCollection=new models.Nodes();
       this.checktype=checktype;
       this.checkedips=checkedips.split(',');
       app.onest_selectips=null;
     },
     render:function()
     {   
        this.nodesCollection.fetch({
           success:_.bind(function(collection,response, options)
             {
                var parencollection=collection;
                parencollection=new models.Nodes(parencollection.where({node_type:5},false));
                $(this.el).html(this.template({data:parencollection.toJSON(),checktype:this.checktype,checkedips:this.checkedips}));
             },this),
           error:function(collection, response, options)
             {
                  alert('获取nodes列表出现异常!');
             }
       });
     return this;
   }
 });

  return CloudSettingsTab;
});
