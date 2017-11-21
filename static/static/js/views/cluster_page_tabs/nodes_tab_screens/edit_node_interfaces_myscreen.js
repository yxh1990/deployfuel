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
    'i18n',
    'backbone',
    'utils',
    'models',
    'views/cluster_page_tabs/nodes_tab_screens/edit_node_myscreen',
    'text!templates/phymachine/node_interface_list.html'
],
function($, _, i18n, Backbone, utils, models, EditNodeScreen, editNodeInterfacesScreenTemplate) {
    'use strict';
    var EditNodeInterfacesScreen;

    EditNodeInterfacesScreen = EditNodeScreen.extend({
        className: 'edit-node-networks-screen', //给el的div添加一个样式名称
        template: _.template(editNodeInterfacesScreenTemplate),
        events: {
            'click .btn-revert-changes:not(:disabled)': 'revertChanges',
            'click .btn-apply:not(:disabled)': 'applyChanges',
            'click .btn-return:not(:disabled)': 'returnToNodeList',
            'blur  #tablebox input':'checkself'
        },
         goToNodeList: function() {
            var node=app.nodeModel;
           if(node.get('node_type')==0){
               app.navigate('#ops/sys', {trigger: true});
           }
           else
           {
             app.navigate('#ops/autonodes', {trigger: true});
           }
        },
        revertChanges:function()
        {
          Backbone.history.loadUrl();
        },
        checkself:function(e){
            var checkobj=$(e.currentTarget);
            var checkvalue=checkobj.val();
            if(!checkvalue.match(utils.regexes.ip) && checkvalue!="")
              {
                 checkobj.addClass('error');
                 checkobj.parent().next().children().first().html("<font color='#b94a48'>输入格式有误</font>");
              }
            else
              {
                //这里验证每一个网卡必须设置不同的ip
                var data_type=checkobj.attr("data-type");
                if(checkvalue!="") //输入的ip为null时候,不需要进行重复验证
                {
                   if(data_type=="nip")
                   {
                    var data_mac=checkobj.attr("data-mac");
                    this.checkhasthisIp(checkvalue,data_mac,checkobj);
                   }
                   else
                   {
                    checkobj.removeClass('error');
                    checkobj.parent().next().children().first().html("");
                   }
                }
                else
                {
                   checkobj.removeClass('error');
                   checkobj.parent().next().children().first().html("");
                }
              }
        },
        checkhasthisIp:function(ip,mac,checkobj)
        {
             $.ajax({
                type: "GET",
                url: "/api/interfaces/checkip/",
                data: "ip="+ip+"&mac="+mac,
                success: _.bind(function(msg){
                  var obj=JSON.parse(msg);
                  var count=parseInt(obj.count);
                  if(count>0)
                    {
                      var nodename=obj.nodename;
                      var ethname=obj.ethname;
                      checkobj.addClass('error');
                      checkobj.parent().next().children().first().html("<font color='#b94a48'>此ip已经被"+nodename+"("+ethname+")使用</font>");
                    }
                    else
                    {
                      checkobj.removeClass('error');
                      checkobj.parent().next().children().first().html("");
                    }
                },this),
                error:function(msg)
                {
                  alert('验证失败!');
                }
            });
        },
        applyChanges:function() {
            var groups=this.$('.network-box-item');
            var groupsresult=[];
            var ipsarray=[];
            var dnsarray=[];
            var netmaskarray=[];
            var nodeip="";
            for(var t=0;t<groups.length;t++)
            {
                var erroriphtml="<font color='#b94a48'>IP格式输入有误</font>";
                var errordnshtml="<font color='#b94a48'>dns格式输入有误</font>";
                var errornethtml="<font color='#b94a48'>netmask格式输入有误</font>";
                var ipobj=this.$('#'+t+'_txt_ip');
                var dnsnameobj=this.$('#'+t+'_txt_dns_name');
                var netmaskobj=this.$('#'+t+'_txt_netmask');

                var ip_type=ipobj.attr("node_ip_type");
                if (ip_type=="node")
                {
                  nodeip=ipobj.val();
                }
                if(ipobj.val()=="" && dnsnameobj.val()=="" && netmaskobj.val()=="")
                {
                  groupsresult.push(1);
                  ipsarray.push(ipobj.val());
                  dnsarray.push(dnsnameobj.val());
                  netmaskarray.push(netmaskobj.val());
                }
                else
                {
                  if(!ipobj.val().match(utils.regexes.ip) && ipobj.val()!="")
                    {
                        ipobj.addClass('error');
                        ipobj.parent().next().children().first().html(erroriphtml);
                    }
                    else
                    {
                        ipsarray.push(ipobj.val());
                        ipobj.removeClass('error');
                        ipobj.parent().next().children().first().html("");
                    }

                    if(!dnsnameobj.val().match(utils.regexes.ip) && dnsnameobj.val()!="")
                    {
                        dnsnameobj.addClass('error');
                        dnsnameobj.parent().next().children().first().html(errordnshtml);
                    }
                    else
                    {
                        dnsarray.push(dnsnameobj.val());
                        dnsnameobj.removeClass('error');
                        dnsnameobj.parent().next().children().first().html("");
                    }

                    if(!netmaskobj.val().match(utils.regexes.ip) && netmaskobj.val()!="")
                    {
                        netmaskobj.addClass('error');
                        netmaskobj.parent().next().children().first().html(errornethtml);
                    }
                    else
                    {
                        netmaskarray.push(netmaskobj.val());
                        netmaskobj.removeClass('error');
                        netmaskobj.parent().next().children().first().html("");
                    }
                }
            }
           var erros=this.$(".error");
           if(erros.length)
           {
             return;
           }
           else
           {
              var cansave=true;
              outlook:
              for (var i = 0; i < ipsarray.length; i++) {
                   for (var j = i + 1; j < ipsarray.length; j++) {
                       var ipobj1=this.$('#'+i+'_txt_ip');
                       var ipobj2=this.$('#'+j+'_txt_ip');
                       if (ipsarray[i] && ipsarray[j] && ipsarray[i] == ipsarray[j]) {
                          ipobj1.addClass('error');
                          ipobj1.parent().next().children().first().html("<font color='#b94a48'>已存在相同ip</font>");
                          ipobj2.addClass('error');
                          ipobj2.parent().next().children().first().html("<font color='#b94a48'>已存在相同ip</font>");
                       
                         cansave=false;
                         break outlook;   
                      }
                     else
                     {
                      ipobj1.removeClass('error');
                      ipobj1.parent().next().children().first().html("");
                     }
                  }
              }

              if(!cansave)
               {
                   alert('IP地址设置重复,请确认后再保存!');
               }
              else
              {
                 var nodemeta=this.nodes.at(0).get('meta');
                 var interfaces=nodemeta.interfaces;
                 for(var t=0;t<interfaces.length;t++)
                  {
                     var item=interfaces[t];
                     item["ip"]=ipsarray[t];
                     item["netmask"]=netmaskarray[t];
                     item["dns"]=dnsarray[t];
                  }
                 nodemeta["interfaces"]=interfaces;
                 this.saveNewMeta(nodemeta,nodeip);
              }
           }
        },
        saveNewMeta:function(nodemeta,nodeip)
        {
             var id=app.nodeModel.get('id');
             $.ajax({
                type: "PUT",
                url: "/api/node/updatemeta/",
                data: "id="+id+"&ip="+nodeip+"&nodemeta="+JSON.stringify(nodemeta),
                success: _.bind(function(msg){
                   alert('保存成功!');
                },this),
                error:function(msg)
                {
                   alert('保存失败!');
                }
            });
        },
        initialize: function() {
            this.nodes=new models.Nodes(app.nodeModel);
            this.initButtons();
        },
        render: function() {
            this.$el.html(this.template({
                nodes: this.nodes,
            })).i18n();
            if (this.loading && this.loading.state() != 'pending') {
                
            }
            return this;
        }
    });
    return EditNodeInterfacesScreen;
});
