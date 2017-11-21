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
  控制x86物理机和操作系统安装两个tab切换
**/
define(
[
    'jquery',
    'underscore',
    'i18n',
    'backbone',
    'utils',
    'models',
    'views/common',
    'views/phymachine_page_tabs/tab_control', //x86物理机tab tab_control是为了控制列表页面和添加页面
    'views/phymachine_page_tabs/list_tab',    //操作系统安装tab
    'views/phymachine_page_tabs/listauto_tab',    //操作系统安装tab
    'text!templates/phymachine/opspage.html'
],
function($, _, i18n, Backbone, utils, models, commonViews, NodesTab, NodesNeedInstallTab,NodesNotImportTab,clusterPageTemplate) {
    'use strict';

    var OpsPage = commonViews.Page.extend({
        navbarActiveElement:"",
        breadcrumbsPath: function() {
          if(app.showtab=="x86")
          {
            return [];
          }
          else
          {
             return [
                     ['操作系统安装','#installOscloud'],
                     ['Openstack定制环境','#clusters']
                   ];
          }
        },
        setPageActiveElement:function(){
          if(app.showtab=="x86")
          {
            return "operations";
          }
          else
          {
            return "clusters";
          }
        },
        template: _.template(clusterPageTemplate),
        getAvailableTabs: function() {
          if(app.showtab=="x86"){
            return [
                {url: 'x86', tab: NodesTab}  //这里的x86在模板中调用
            ];
          }
          else
          {
             return [
                {url: 'sys', tab: NodesNeedInstallTab},
                {url: 'autonodes', tab: NodesNotImportTab}
            ];
          }
        },
         events:{
            'click .deploy-btn':'onDeployRequest',
        },
        initialize: function(options) {
             _.defaults(this, options);
            var availableTabs = this.getAvailableTabs();
            Backbone.on('showapplybutton', this.showapplybutton, this);
            if (!_.find(availableTabs, {url: this.activeTab})) {
                this.activeTab = availableTabs[0].url;
                app.navigate('ops/' +this.activeTab, {replace: true});
                return;
            }
        },
        onDeployRequest: function() {
            var osName=app.installosName;
            var NodeIds=app.provisionNodeIds;
            var Osid=app.installosid;
           if(confirm("确认开始给选中的节点安装操作"+osName+"系统!"))
           {
             $.ajax({
                type: "GET",
                url: "/api/phymachine/install",
                data: "NodeIds="+NodeIds+"&Osid="+Osid+"&osName="+osName,
                success: function(msg){
                   $('.deploy-btn').hide();
                   Backbone.trigger('refreshdata');
                },
                error:function()
                {
                  $('.deploy-btn').hide();
                  Backbone.trigger('refreshdata');
                }
             });
           }
        },
        showapplybutton:function()
        {
          if(app.provisionNodeIds.length>0)
          {
            this.$('.deploy-btn').show(); 
          }
          else
          {
            this.$('.deploy-btn').hide();
          }
        },
        render: function() { 
             clearInterval(app.timergetnodestatus);
             this.tearDownRegisteredSubViews();
            //从这里可以看出每次点击都会重新执行render
            var availableTabs = this.getAvailableTabs();
            var Tab = _.find(availableTabs, {url: this.activeTab}).tab;  
            //tab代表,如nodes页面,setttings页面
            this.$el.html(this.template({
                tabs: _.pluck(availableTabs, 'url'),
                activeTab: this.activeTab
            })).i18n();
            this.$('.deploy-btn').hide();
           var options = {page: this};
           this.tab = utils.universalMount(Tab, _.extend({tabOptions: this.tabOptions}, options), this.$('#tab-' + this.activeTab), this);
         return this;
        }
    });

  OpsPage.fetchData = function(activeTab) {
        var  promise;
        var  tabOptions = _.toArray(arguments).slice(2);
             promise = $.Deferred().resolve();
        return promise.then(function() {
            return {
                activeTab: activeTab,
                tabOptions: tabOptions
            };
        });
    };
    return OpsPage;
});
