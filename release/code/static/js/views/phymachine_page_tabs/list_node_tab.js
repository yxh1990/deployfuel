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
    'views/cluster_page_tabs/nodes_tab_screens/myscreen',
    'jsx!views/dialogs',
    'text!templates/phymachine/node_list.html'
],
function($, _, utils, models, commonViews,Backbone, Screen, dialogs, NodesScreenTemplate) {
    'use strict';
    var NodesListTab;

    NodesListTab=Screen.extend({
        template: _.template(NodesScreenTemplate),
         initialize: function() {
            this.nodesCollection=new models.Nodes();
            this.provisionNodes=new models.Nodes();
            Backbone.on('refreshdata', this.refreshdata, this);
        },
          events:{
            'click .node-details':'showNodeDetails',
            'click #chekcall':'setcheckall',
            'change .custom-tumbler input':'changeNodeToProvision',
            'change #osSelect':'changeSelectOs'
        },
        setcheckall:function(e)
        {
          var checkstatus=$(e.currentTarget).is(':checked');
          this.$(".row-fluid input").each(function(){
              this.checked=checkstatus;
          });
          if(checkstatus)
          {
            //暂时没有做分页处理，所以是collection的全部
           //app.provisionNodes=this.nodesCollection.models;
           for(var t=0;t<this.nodesCollection.length;t++)
           {
             this.provisionNodes.push(this.nodesCollection.models[t]);
           }
          }
          else
          {
             this.provisionNodes=new models.Nodes();
          }
           app.provisionNodeIds=new Array();
           for(var i=0;i<this.provisionNodes.models.length;i++)
           {
             app.provisionNodeIds.push(this.provisionNodes.models[i].get('id'));
           }
           Backbone.trigger('showapplybutton'); 
        },
        changeSelectOs:function()
        {
          app.installosName=this.$("#osSelect").find("option:selected").text();
          app.installosid=this.$("#osSelect").val();
        },
        changeNodeToProvision:function(e){
            var selectobj=$(e.currentTarget);
            var checkstatus=selectobj.is(':checked');
            var nodecheckedIndex=selectobj.attr("node-index");
            var selectnode=this.nodesCollection.models[nodecheckedIndex];
            if(checkstatus)
            {
              this.provisionNodes.push(selectnode);
            }
            else
            {
              this.provisionNodes.remove(selectnode);
            }
            app.provisionNodeIds=new Array();
           for(var i=0;i<this.provisionNodes.models.length;i++)
           {
             app.provisionNodeIds.push(this.provisionNodes.models[i].get('id'));
           }

           app.installosName=this.$("#osSelect").find("option:selected").text();
           app.installosid=this.$("#osSelect").val();
           Backbone.trigger('showapplybutton'); 
        },
        changeScreen: function(action) {
            //这里获取选中的node对象,并共享给相关view.
            var checkedboxs=this.$(" .row-fluid input:checkbox:checked");
            if(!checkedboxs.length)
            {
              alert("请先选择需要配置的节点!");
              return;
            }
            else
            {
               //如果选中多个checkbox，只传递第一个选中的node.
               //磁盘配置关联两个表的数据nodes和node_attributes
               var nodecheckedIndex=$(checkedboxs[0]).attr("node-index");
               var selectnode=this.nodesCollection.models[nodecheckedIndex];
               app.nodeModel=selectnode;
               if(action=="disks")
                 app.navigate('#ops/sys/node/disks', {trigger: true});
               else
                 app.navigate('#ops/sys/node/interfaces', {trigger: true});
           }
        },
        goToConfigurationDiskScreen: function() {
            this.changeScreen('disks');
        },
        goToConfigurationNetworkScreen:function(){
            this.changeScreen('interfaces');
        },
        showNodeDetails: function(e) {
           var index=(e.currentTarget).getAttribute('item_index');
           var currentNode=this.nodesCollection.models[index];
           utils.showDialog(dialogs.ShowMyNodeInfoDialog, {
                node: currentNode,
                title: currentNode.get('name') || currentNode.get('mac')
            });
        },
        showMemorySize:function(bytes) {
            return utils.showSize(bytes, 1024);
        },
        showDiskSize: function(value, power) {
            power = power || 0;
            return utils.showSize(value * Math.pow(1024, power));
        },
        refreshdata:function()
         {
            this.provisionNodes.reset();//清空集合中所有元素
            this.render();//第一次刷新安装状态
            var topthis=this;
            var nodetype=this.getshownodetype();
            app.timergetnodestatus=setInterval(function(){
               topthis.nodesCollection.fetch({
                   success:_.bind(function(collection,response, options)
                   {
                      var parencollection=collection;
                      //0表示导入的机器中用处类型为未分配的机器,-1表示发现的机器没有在物理机表中.
                      parencollection=new models.Nodes(parencollection.where({node_type:nodetype},false));
                      this.nodesCollection=parencollection;
                      var Releases=new models.Releases();
                      Releases.fetch({
                        success:_.bind(function(collection,response, options)
                         {
                          $(this.el).html(this.template({data:parencollection.toJSON(),showMemorySize:this.showMemorySize,showDiskSize:this.showDiskSize,releases:collection.toJSON()}));
                         },topthis),error:function(collection, response, options)
                         {
                           alert('获取nodes列表出现异常!');
                         }
                      });
                  },this),error:function(collection, response, options)
                  {
                        alert('获取nodes列表出现异常!');
                  }
             });
            },1000*60);  //60000
         },
         getshownodetype:function()
         {
             var urlargs=window.location.hash;
             var nodetype=0;
             if(urlargs=="#ops/autonodes")
             {
               nodetype=-1;
             }
             return nodetype;
         },
         render: function () {
             var topthis=this;
             var nodetype=this.getshownodetype();
             clearInterval(app.timergetnodestatus);
             this.nodesCollection.fetch({
                 success:_.bind(function(collection,response, options)
                   {
                      var parencollection=collection;
                      //0表示导入的机器中用处类型为未分配的机器,-1表示发现的机器没有在物理机表中.
                      parencollection=new models.Nodes(parencollection.where({node_type:nodetype},false));
                      this.nodesCollection=parencollection;
                      var Releases=new models.Releases();
                      Releases.fetch({
                        success:_.bind(function(collection,response, options)
                         {
                          $(this.el).html(this.template({data:parencollection.toJSON(),showMemorySize:this.showMemorySize,showDiskSize:this.showDiskSize,releases:collection.toJSON()}));
                          //topthis.getinstallStatus();
                         },topthis),error:function(collection, response, options)
                         {
                           alert('获取nodes列表出现异常!');
                         }
                      });
                  },this),error:function(collection, response, options)
                  {
                        alert('获取nodes列表出现异常!');
                  }
             });
           return this;
         }
    });

  return NodesListTab;
});
