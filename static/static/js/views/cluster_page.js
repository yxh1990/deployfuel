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
    'react',
    'utils',
    'models',
    'views/common',
    'jsx!views/cluster_page_subviews',
    'jsx!views/dialogs',
    'views/cluster_page_tabs/nodes_tab',
    'views/cluster_page_tabs/network_tab',
    'jsx!views/cluster_page_tabs/settings_tab',
    'views/cluster_page_tabs/cloudsettings_tab',
    'views/cluster_page_tabs/ebssettings_tab',
    'views/cluster_page_tabs/clusterscustomsettings_tab',
    'views/cluster_page_tabs/onestsettings_tab',
    'jsx!views/cluster_page_tabs/logs_tab',
    'jsx!views/cluster_page_tabs/actions_tab',
    'jsx!views/cluster_page_tabs/healthcheck_tab',
    'text!templates/cluster/page.html',
    'jquery-timeout'
],
function($, _, i18n, Backbone, React, utils, models, commonViews, clusterPageSubviews, dialogs, NodesTab, NetworkTab, SettingsTab,CloudSettingsTab, EBsSettingsTab,clusterscustomsettingsTab,onestseTab,LogsTab, ActionsTab, HealthCheckTab, clusterPageTemplate) {
    'use strict';

    var ClusterPage = commonViews.Page.extend({
        navbarActiveElement: 'clusters',
        breadcrumbsPath: function() {
            return [
                     ['操作系统安装','#installOscloud'],
                     ['Openstack定制环境','#clusterscustom']
                   ];
        },
        title: function() {
            return this.model.get('name');
        },
        updateInterval: 5000,
        template: _.template(clusterPageTemplate),
        removeFinishedNetworkTasks: function(removeSilently) {
            return this.removeFinishedTasks(this.model.tasks({group: 'network'}), removeSilently);
        },
        removeFinishedDeploymentTasks: function(removeSilently) {
            return this.removeFinishedTasks(this.model.tasks({group: 'deployment'}), removeSilently);
        },
        removeFinishedTasks: function(tasks, removeSilently) {
            var requests = [];
            _.each(tasks, function(task) {
                if (task.get('status') != 'running') {
                    if (!removeSilently) {
                        this.model.get('tasks').remove(task);
                    }
                    requests.push(task.destroy({silent: true}));
                }
            }, this);
            return $.when.apply($, requests);
        },
        discardSettingsChanges: function(options) {
            utils.showDialog(dialogs.DiscardSettingsChangesDialog, options);
        },
        onTabLeave: function(e) {
            var href = $(e.currentTarget).attr('href');
            if (Backbone.history.getHash() != href.substr(1) && _.result(this.tab, 'hasChanges')) {
                e.preventDefault();
                this.discardSettingsChanges({
                    verification: this.model.tasks({group: 'network', status: 'running'}).length,
                    cb: _.bind(function() {
                        app.navigate(href, {trigger: true});
                    }, this)
                });
            }
        },
        scheduleUpdate: function() {
            if (this.model.task({group: ['deployment', 'network'], status: 'running'})) {
                this.registerDeferred($.timeout(this.updateInterval).done(_.bind(this.update, this)));
            }
        },
        update: function() {
            var complete = _.after(2, _.bind(this.scheduleUpdate, this));
            var task = this.model.task({group: 'deployment', status: 'running'});
            if (task) {
                this.registerDeferred(task.fetch().done(_.bind(function() {
                    if (!task.match({status: 'running'})) {
                        this.deploymentTaskFinished();
                    }
                }, this)).always(complete));
                this.registerDeferred(this.model.get('nodes').fetch({data: {cluster_id: this.model.id}}).always(complete));
            }
            var verificationTask = this.model.task('verify_networks', 'running');
            if (verificationTask) {
                this.registerDeferred(verificationTask.fetch().always(_.bind(this.scheduleUpdate, this)));
            }
        },
        deploymentTaskStarted: function() {
            $.when(this.model.fetch(), this.model.fetchRelated('nodes'), this.model.fetchRelated('tasks')).always(_.bind(function() {
                // FIXME: hack to prevent "Deploy" button flashing after deployment is finished
                this.model.set({changes: []}, {silent: true});
                this.scheduleUpdate();
            }, this));
        },
        deploymentTaskFinished: function() {
            $.when(this.model.fetch(), this.model.fetchRelated('nodes'), this.model.fetchRelated('tasks')).always(_.bind(function() {
                app.navbar.refresh();
            }, this));
        },
        beforeTearDown: function() {
            $(window).off('beforeunload.' + this.eventNamespace);
            $('body').off('click.' + this.eventNamespace);
            _.each(['clusterInfo', 'clusterCustomizationMessage', 'deploymentResult', 'deploymentControl', 'tab'], function(subView) {
                if (this[subView]) utils.universalUnmount(this[subView]);
            }, this);
        },
        onBeforeunloadEvent: function() {
            if (_.result(this.tab, 'hasChanges')) {
                return i18n('dialog.dismiss_settings.default_message');
            }
        },
        getAvailableTabs: function() {
            var tabs=[
                {url: 'nodes', tab: NodesTab},
                {url: 'network', tab: NetworkTab},
                {url: 'settings', tab: SettingsTab},
                {url: 'logs', tab: LogsTab},
                {url: 'healthcheck', tab: HealthCheckTab},
                {url: 'actions', tab: ActionsTab}
            ];
            var viewtabs=[];
            //1.默认openstack环境
            //2.定制openstack才有网络设置tab,其余类型环境暂时不要
            //根据不同类型的环境的环境,显示不同的设置tab
            for(var t=0;t<tabs.length;t++)
            {
                if (this.model.get('cluster_type')!="1" && this.model.get('cluster_type')!="4")
                 {
                    if(t!=1){ viewtabs.push(tabs[t]);}
                 }
                else
                 { viewtabs.push(tabs[t]);}
            }
            //cloudmaster
            if(this.model.get('cluster_type')=="2")
            {
              viewtabs[1].tab=CloudSettingsTab;
            }
            //EBS
            if(this.model.get('cluster_type')=="3")
            {
              viewtabs[1].tab=EBsSettingsTab;
            }
            //onest
            if(this.model.get('cluster_type')=="5")
            {
             viewtabs[1].tab=onestseTab;
            }
            //clusterscustom
            if(this.model.get('cluster_type')=="4")
            {
              viewtabs[2].tab=clusterscustomsettingsTab;
            }
            return viewtabs;
        },
        initialize: function(options) {
            _.defaults(this, options);
            var availableTabs = this.getAvailableTabs();
            if (!_.find(availableTabs, {url: this.activeTab})) {
                this.activeTab = availableTabs[0].url;
                app.navigate('cluster/' + this.model.id + '/' + this.activeTab, {replace: true});
                return;
            }
            this.model.on('change:name', app.updateTitle, app);
            this.model.on('change:release_id', function() {
                var release = new models.Release({id: this.model.get('release_id')});
                release.fetch().done(_.bind(function() {
                    this.model.set({release: release});
                }, this));
            }, this);
            this.scheduleUpdate();
            this.eventNamespace = 'unsavedchanges' + this.activeTab;
            $(window).on('beforeunload.' + this.eventNamespace, _.bind(this.onBeforeunloadEvent, this));
            $('body').on('click.' + this.eventNamespace, 'a[href^=#]:not(.no-leave-check)', _.bind(this.onTabLeave, this));
        },
        render: function() {
            this.tearDownRegisteredSubViews();

            var availableTabs = this.getAvailableTabs();
            var Tab = _.find(availableTabs, {url: this.activeTab}).tab;
            
            this.$el.html(this.template({
                cluster: this.model,
                tabs: _.pluck(availableTabs, 'url'),
                activeTab: this.activeTab
            })).i18n();

            var options = {model: this.model, page: this};
            this.clusterInfo = utils.universalMount(clusterPageSubviews.ClusterInfo, options, this.$('.cluster-info'), this);
            this.clusterCustomizationMessage = utils.universalMount(clusterPageSubviews.ClusterCustomizationMessage, options, this.$('.customization-message'), this);
            this.deploymentResult = utils.universalMount(clusterPageSubviews.DeploymentResult, options, this.$('.deployment-result'), this);
            this.deploymentControl = utils.universalMount(clusterPageSubviews.DeploymentControl, options, this.$('.deployment-control'), this);
            this.tab = utils.universalMount(Tab, _.extend({tabOptions: this.tabOptions}, options), this.$('#tab-' + this.activeTab), this);
            var taburl=this.activeTab;
            if(taburl!="nodes" && taburl!="settings")
            {
              this.deploymentControl.setState({hidden:true});
            }
            return this;
        }
    });

    ClusterPage.fetchData = function(id, activeTab) {
        var cluster, tasks, promise, currentClusterId;
        var tabOptions = _.toArray(arguments).slice(2);

        try {
            currentClusterId = app.page.model.id;
        } catch (ignore) {}

        if (currentClusterId == id) {
            // just another tab has been chosen, do not load cluster again
            cluster = app.page.model;
            tasks = app.page.tasks;
            promise = $.Deferred().resolve();
        } else {
            cluster = new models.Cluster({id: id});
            var settings = new models.Settings();
            settings.url = _.result(cluster, 'url') + '/attributes';
            cluster.set({settings: settings});
            tasks = new models.Tasks();
            tasks.fetch = function(options) {
                return this.constructor.__super__.fetch.call(this, _.extend({data: {cluster_id: ''}}, options));
            };
            promise = $.when(cluster.fetch(), cluster.get('settings').fetch(), cluster.fetchRelated('nodes'), cluster.fetchRelated('tasks'), tasks.fetch())
                .then(_.bind(function() {
                    var networkConfiguration = new models.NetworkConfiguration();
                    networkConfiguration.url = _.result(cluster, 'url') + '/network_configuration/' + cluster.get('net_provider');
                    cluster.set({
                        networkConfiguration: networkConfiguration,
                        release: new models.Release({id: cluster.get('release_id')})
                    });
                    return $.when(cluster.get('networkConfiguration').fetch(), cluster.get('release').fetch());
                }, this));
        }

        return promise.then(function() {
            return {
                model: cluster,
                activeTab: activeTab,
                tabOptions: tabOptions,
                tasks: tasks
            };
        });
    };

    return ClusterPage;
});
