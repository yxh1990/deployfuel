/*
 * Copyright 2014 Mirantis, Inc.
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
    'react',
    'utils',
    'models',
    'jsx!views/controls',
    'jsx!views/dialogs',
    'jsx!component_mixins'
],
function($, _, i18n, React, utils, models, controls, dialogs, componentMixins) {
    'use strict';
    var cx = React.addons.classSet,
        NodeListScreen, ManagementPanel, RolePanel, SelectAllMixin, NodeList, NodeGroup, Node;
        /*
           NodeListScreen  模块名称,外部调用名称
           ManagementPanel 部署变更按钮模块和设置查询条件
           RolePanel 角色勾选列表
           NodeList 最外面的选择全部勾选框
           NodeGroup 节点分组显示
           Node      单条节点显示信息
           getEmptyListWarning  执行提示目前没有可选节点
        */
    NodeListScreen = React.createClass({
        mixins: [
            componentMixins.pollingMixin(20),
            componentMixins.backboneMixin('model', 'change:status'),
            componentMixins.backboneMixin('nodes', 'add remove change'),
            componentMixins.backboneMixin({
                modelOrCollection: function(props) {return props.cluster.get('tasks');},
                renderOn: 'add remove change:status'
            })
        ],
        getInitialState: function() {
            return {
                loading: true,
                filter: '',
                reload:false,
                grouping: this.props.mode == 'add' ? 'hardware' : this.props.cluster.get('grouping'),
                selectedNodeIds: this.props.nodes.reduce(function(result, node) {
                    result[node.id] = this.props.mode == 'edit';
                    return result;
                }, {}, this)
            };
        },
        selectNodes: function(ids, name, checked) {
            var nodeSelection = this.state.selectedNodeIds;
            _.each(ids, function(id) {nodeSelection[id] = checked;});
            this.setState({selectedNodeIds: nodeSelection});
        },
        shouldReload:function(flag)
        {
          this.setState({reload: flag});
        },
        shouldDataBeFetched: function() {
            return !this.state.loading;
        },
        fetchData: function() {
            return this.props.nodes.fetch();
        },
        componentWillMount: function() {
            var clusterId = this.props.mode == 'add' ? '' : this.props.cluster.id;
            this.props.nodes.fetch = function(options) {
                return this.constructor.__super__.fetch.call(this, _.extend({data:{cluster_id:clusterId,node_type:app.cluster_type}}, options));
            };
            if (this.props.mode == 'edit') {
                var ids = this.props.nodes.pluck('id');
                this.props.nodes.parse = function(response) {
                    return _.filter(response, function(node) {return _.contains(ids, node.id);});
                };
            }
             this.updateInitialRoles();
             this.props.nodes.on('add remove reset', this.updateInitialRoles, this);
            // hack to prevent node roles update after node polling
             if (this.props.mode != 'list') this.props.nodes.on('change:pending_roles', this.checkRoleAssignment, this);
        },
        componentWillUnmount: function() {
            this.props.nodes.off('add remove reset', this.updateInitialRoles, this);
            this.props.nodes.off('change:pending_roles', this.checkRoleAssignment, this);
        },
        updateInitialRoles: function() {
             this.initialRoles = _.zipObject(this.props.nodes.pluck('id'), this.props.nodes.pluck('pending_roles'));
        },
        checkRoleAssignment: function(node, roles, options) {
            if (!options.assign) node.set({pending_roles: node.previous('pending_roles')}, {assign: true});
        },
        componentDidMount: function() {
            if (this.props.mode == 'add') {
                $.when(this.props.nodes.fetch(), this.props.cluster.get('settings').fetch({cache: true})).always(_.bind(function() {
                    this.setState({loading: false});
                }, this));
            } else {
                this.setState({loading: false});
            }
        },
        hasChanges: function() {
            return this.props.nodes.any(function(node) {
                return !_.isEqual(node.get('pending_roles'), this.initialRoles[node.id]);
            }, this);
        },
        changeFilter: _.debounce(function(value) {
            this.setState({filter: value});
        }, 200),
        clearFilter: function() {
            this.setState({filter: ''});
        },
        changeGrouping: function(name, value) {
            this.setState({grouping: value});
            this.props.cluster.save({grouping: value}, {patch: true, wait: true});
        },
        revertChanges: function() {
            this.props.nodes.each(function(node) {
                node.set({pending_roles: this.initialRoles[node.id]}, {silent: true});
            }, this);
        },
        render: function() {
            var assignedRoles = _.chain(this.props.nodes.pluck('roles')).union(this.props.nodes.pluck('pending_roles')).flatten().uniq().value(),
                locked = !!this.props.cluster.tasks({group: 'deployment', status: 'running'}).length;
            return (
                <div>
                    {this.props.mode == 'edit' &&
                        <div className='alert'>{i18n('cluster_page.nodes_tab.disk_configuration_reset_warning')}</div>
                    }
                    <ManagementPanel
                        mode={this.props.mode}
                        nodes={new models.Nodes(_.compact(_.map(this.state.selectedNodeIds, function(checked, id) {
                            if (checked) return this.props.nodes.get(id);
                        }, this)))}
                        totalNodeAmount={this.props.nodes.length}
                        cluster={this.props.cluster}
                        grouping={this.state.grouping}
                        shouldReload={this.shouldReload}
                        changeGrouping={this.changeGrouping}
                        filter={this.state.filter}
                        filtering={this.state.filtering}
                        changeFilter={this.changeFilter}
                        clearFilter={this.clearFilter}
                        hasChanges={!this.isMounted() || this.hasChanges()}
                        locked={locked || this.state.loading}
                        revertChanges={this.revertChanges}
                    />
                    {this.state.loading ? <controls.ProgressBar /> :
                        <div>
                            {(this.props.mode != 'list' &&  this.props.cluster.get('cluster_type')!=3 )&&
                              //model等于list的时候不需要显示选择角色列表 
                            <RolePanel {...this.props} selectedNodeIds={this.state.selectedNodeIds} />}
                            <NodeList {...this.props}
                                nodes={this.props.nodes.models}
                                grouping={this.state.grouping}
                                filter={this.state.filter}
                                locked={locked}
                                selectedNodeIds={this.state.selectedNodeIds}
                                selectNodes={this.selectNodes}
                                // FIXME: one more role limits hack
                                roleLimitation={(this.props.cluster.get('mode') == 'multi-node' && _.contains(assignedRoles, 'controller')) || _.contains(assignedRoles, 'zabbix-server')}
                            />

                            {(this.props.mode != 'list' &&  this.props.cluster.get('cluster_type')==3 )&& 
                            <RolePanel {...this.props} selectedNodeIds={this.state.selectedNodeIds} />}
                        </div>
                    }
                </div>
            );
        }
    });

    ManagementPanel = React.createClass({
        getInitialState: function() {
            return {
                isFilterButtonVisible: !!this.props.filter,
                actionInProgress: false
            };
        },
        shouldReload:function(){
            this.props.shouldReload(true);
        },
        changeScreen: function(url, passNodeIds) {
            if (!url) this.props.revertChanges();
            url = url ? '/' + url : '';
            if (passNodeIds) url += '/' + utils.serializeTabOptions({nodes: this.props.nodes.pluck('id')});
            var newurl='cluster/' + this.props.cluster.id + '/nodes' + url;
            app.navigate(newurl,{trigger: true, replace: true});
        },
        goToConfigurationScreen: function(action, conflict) {
            if (conflict) {
                var ns = 'cluster_page.nodes_tab.node_management_panel.node_management_error.';
                utils.showErrorDialog({title: i18n(ns + 'title'), message: i18n(ns + action + '_configuration_warning')});
                return;
            }
            this.changeScreen(action, true);
        },
        showDeleteNodesDialog: function() {
            utils.showDialog(dialogs.DeleteNodesDialog, {nodes: this.props.nodes, cluster: this.props.cluster,shouldReload:this.shouldReload});
        },
        applyChanges: function() {
            this.setState({actionInProgress: true});
            this.props.nodes.each(function(node) {
                var data;
                if (this.props.mode == 'add') data = {cluster_id: this.props.cluster.id, pending_addition: true};
                if (!node.get('pending_roles').length && node.get('pending_addition')) data = {cluster_id: null, pending_addition: false};
                node.set(data, {silent: true});
            }, this);
            this.props.nodes.toJSON = function() {
                return this.map(function(node) {
                    return _.pick(node.attributes, 'id', 'cluster_id', 'pending_roles', 'pending_addition');
                });
            };
            this.props.nodes.sync('update', this.props.nodes)
                .done(_.bind(function() {
                    $.when(this.props.cluster.fetch(), this.props.cluster.fetchRelated('nodes')).always(_.bind(function() {
                        this.changeScreen();
                        app.navbar.refresh();
                        app.page.removeFinishedNetworkTasks();
                    }, this));
                }, this))
                .fail(_.bind(function() {
                    this.setState({actionInProgress: false});
                    utils.showErrorDialog({message: i18n('cluster_page.nodes_tab.node_management_panel.node_management_error.saving_warning')});
                }, this));
        },
        startFiltering: function(name, value) {
            this.setState({isFilterButtonVisible: !!value});
            this.props.changeFilter(value);
        },
        clearFilter: function() {
            this.setState({isFilterButtonVisible: false});
            this.refs.filter.getInputDOMNode().value = '';
            this.props.clearFilter();
        },
        render: function() {
            var ns = 'cluster_page.nodes_tab.node_management_panel.',
                sampleNode = this.props.nodes.at(0),
                disksConflict = this.props.nodes.any(function(node) {
                    var roleConflict = _.difference(_.union(sampleNode.get('roles'), sampleNode.get('pending_roles')), _.union(node.get('roles'), node.get('pending_roles'))).length;
                    return roleConflict || !_.isEqual(sampleNode.resource('disks'), node.resource('disks'));
                }),
                interfaceConflict = _.uniq(this.props.nodes.map(function(node) {return node.resource('interfaces');})).length > 1;
            return (
                <div className='node-management-panel'>
                    <controls.Input
                        type='select'
                        name='grouping'
                        label={i18n(ns + 'group_by')}
                        children={_.map(this.props.cluster.groupings(), function(label, grouping) {
                            return <option key={grouping} value={grouping}>{label}</option>;
                        })}
                        defaultValue={this.props.grouping}
                        disabled={!this.props.totalNodeAmount || this.props.mode == 'add'}
                        onChange={this.props.changeGrouping}
                    />
                    <div className='node-filter'>
                        <controls.Input
                            type='text'
                            name='filter'
                            ref='filter'
                            defaultValue={this.props.filter}
                            label={i18n(ns + 'filter_by')}
                            placeholder={i18n(ns + 'filter_placeholder')}
                            disabled={!this.props.totalNodeAmount}
                            onChange={this.startFiltering}
                        />
                        {this.state.isFilterButtonVisible &&
                            <button className='close btn-clear-filter' onClick={this.clearFilter}>&times;</button>
                        }
                    </div>
                    <div className='buttons'>
                        {this.props.mode != 'list' ? [
                            <button
                                key='cancel'
                                className='btn'
                                disabled={this.state.actionInProgress}
                                onClick={_.bind(this.changeScreen, this, '', false)}
                            >
                                {i18n('common.cancel_button')}
                            </button>,
                            <button
                                key='apply'
                                className='btn btn-success btn-apply'
                                disabled={this.state.actionInProgress || !this.props.hasChanges}
                                onClick={this.applyChanges}
                            >
                                {i18n('common.apply_changes_button')}
                            </button>
                        ] : [
                            <button
                                key='disks'
                                className={cx({'btn btn-configure-disks': true, conflict: disksConflict})}
                                disabled={this.props.locked || !this.props.nodes.length}
                                onClick={_.bind(this.goToConfigurationScreen, this, 'disks', disksConflict)}
                            >
                                {disksConflict && <i className='icon-attention text-error' />}
                                <span>{i18n('dialog.show_node.disk_configuration_button')}</span>
                            </button>,
                            !this.props.nodes.any(function(node) {return node.get('status') == 'error';}) &&
                                <button
                                    key='interfaces'
                                    className={cx({'btn btn-configure-interfaces': true, conflict: interfaceConflict})}
                                    disabled={this.props.locked || !this.props.nodes.length}
                                    onClick={_.bind(this.goToConfigurationScreen, this, 'interfaces', interfaceConflict)}
                                >
                                    {interfaceConflict && <i className='icon-attention text-error' />}
                                    <span>{i18n('dialog.show_node.network_configuration_button')}</span>
                                </button>,
                            !!this.props.nodes.length && this.props.nodes.any(function(node) {return !node.get('pending_deletion');}) &&
                                <button
                                    key='delete'
                                    className='btn btn-danger btn-delete-nodes'
                                    onClick={this.showDeleteNodesDialog}
                                >
                                    <i className='icon-trash' />
                                    <span>{i18n('common.delete_button')}</span>
                                </button>,
                            !!this.props.nodes.length && !this.props.nodes.any(function(node) {return !node.get('pending_addition');}) &&
                                <button
                                    key='roles'
                                    className='btn btn-success btn-edit-roles'
                                    onClick={_.bind(this.changeScreen, this, 'edit', true)}
                                >
                                    <i className='icon-edit' />
                                    <span>{i18n(ns + 'edit_roles_button')}</span>
                                </button>,
                            !this.props.nodes.length &&
                                <button
                                    key='add'
                                    className='btn btn-success btn-add-nodes'
                                    onClick={_.bind(this.changeScreen, this, 'add', false)}
                                    disabled={this.props.locked}
                                >
                                    <i className='icon-plus' />
                                    <span>{i18n(ns + 'add_nodes_button')}</span>
                                </button>
                        ]}
                    </div>
                </div>
            );
        }
    });

    RolePanel = React.createClass({
        getInitialState: function() {
            var roles = this.props.cluster.get('release').get('roles'),
                selectedRoles = this.props.nodes.length ? _.filter(roles, function(role) {
                    return !this.props.nodes.any(function(node) {return !node.hasRole(role);});
                }, this) : [];
            return {
                selectedRoles: selectedRoles,
                indeterminateRoles: this.props.nodes.length ? _.filter(_.difference(roles, selectedRoles), function(role) {
                    return this.props.nodes.any(function(node) {return node.hasRole(role);});
                }, this) : []
            };
        },
        componentDidMount: function() {
            this.updateIndeterminateRolesState();
        },
        componentDidUpdate: function() {
            this.updateIndeterminateRolesState();
            this.assignRoles();
        },
        updateIndeterminateRolesState: function() {
            _.each(this.refs, function(roleView, role) {
                roleView.getInputDOMNode().indeterminate = _.contains(this.state.indeterminateRoles, role);
            }, this);
        },
        onChange: function(role, checked) {
            var selectedRoles = this.state.selectedRoles;
            if (checked) {
                selectedRoles.push(role);
            } else {
                selectedRoles = _.without(selectedRoles, role);
            }
            this.setState({
                selectedRoles: selectedRoles,
                indeterminateRoles: _.without(this.state.indeterminateRoles, role)
            });
            app.selectedRoles=selectedRoles;
        },
        assignRoles: function() {
            var roles = this.props.cluster.get('release').get('roles');
            this.props.nodes.each(function(node) {
                if (this.props.selectedNodeIds[node.id]) _.each(roles, function(role) {
                    if (!node.hasRole(role, true)) {
                        var nodeRoles = node.get('pending_roles');
                        if (_.contains(this.state.selectedRoles, role)) {
                            if (this.isRoleAvailable(role)) nodeRoles = _.union(nodeRoles, [role]);
                        } else if (!_.contains(this.state.indeterminateRoles, role)) {
                            nodeRoles = _.without(nodeRoles, role);
                        }
                        node.set({pending_roles: nodeRoles}, {assign: true});
                    }
                }, this);
            }, this);
        },
        isRoleAvailable: function(role) {
            // FIXME: the following hack should be described declaratively in yaml
            if ((role == 'controller' && this.props.cluster.get('mode') == 'multinode') || role == 'zabbix-server') {
                return _.compact(_.values(this.props.selectedNodeIds)).length <= 1 && !this.props.cluster.get('nodes').any(function(node) {
                    return !this.props.selectedNodeIds[node.id] && node.hasRole(role) && !node.get('pending_deletion');
                }, this);
            }
            return true;
        },
        processRestrictions: function(role, models) {
            var name = role.get('name'),
                restrictionsCheck = role.checkRestrictions(models, 'disable'),
                roles = this.props.cluster.get('release').get('role_models'),
                conflicts = _.chain(this.state.selectedRoles)
                    .union(this.state.indeterminateRoles)
                    .map(function(role) {return roles.findWhere({name: role}).conflicts;})
                    .flatten()
                    .uniq()
                    .value(),
                isAvailable = this.isRoleAvailable(name),
                messages = [];
                var roletype=this.props.cluster.get('cluster_type');
                var clusterRoles=roles.where({cluster_type:roletype.toString()});
            if(role.get('cluster_type')!=1 && (clusterRoles.length==conflicts.length)){
                conflicts=_.without(conflicts,name);
            }
            if (restrictionsCheck.message) messages.push(restrictionsCheck.message);
            if (_.contains(conflicts, name)) messages.push(i18n('cluster_page.nodes_tab.role_conflict'));
            if (!isAvailable) messages.push(i18n('cluster_page.nodes_tab.' + name + '_restriction'));
            return {
                result: restrictionsCheck.result || _.contains(conflicts, name) || (!isAvailable && !_.contains(this.state.selectedRoles, name)),
                message: messages.join(' ')
            };
        },
        changeroleshowname:function(rolename)
        {
           var newrolename=rolename;
           if(rolename =="neutron-agent")
           {
             newrolename ="network";
           }
           else if(rolename == "cinder-storage")
           {
             newrolename = "cinder-volume";
           }
           return newrolename;
        },
        render: function() {
            var settings = this.props.cluster.get('settings'),
                configModels = {
                    cluster: this.props.cluster,
                    settings: settings,
                    version: app.version,
                    default: settings
                };
            return (
                <div className='role-panel'>
                    <h4>{i18n('cluster_page.nodes_tab.assign_roles')}</h4>
                    {this.props.cluster.get('release').get('role_models').map(function(role) {
                        if (!role.checkRestrictions(configModels, 'hide').result) {
                          if(role.get('cluster_type')==this.props.cluster.get('cluster_type'))
                          {
                            var name = role.get('name'),
                                processedRestrictions = this.props.nodes.length ? this.processRestrictions(role, configModels) : {};
                            return (
                                <controls.Input
                                    key={name}
                                    ref={name}
                                    type='checkbox'
                                    name={name}
                                    label={this.changeroleshowname(role.get('label'))}
                                    description={role.get('description')}
                                    defaultChecked={_.contains(this.state.selectedRoles, name)}
                                    disabled={!this.props.nodes.length || processedRestrictions.result}
                                    tooltipText={!!this.props.nodes.length && processedRestrictions.message}
                                    wrapperClassName='role-container'
                                    labelClassName='role-label'
                                    descriptionClassName='role-description'
                                    onChange={this.onChange}
                                />
                            );
                          } 
                        }
                    }, this)}
                </div>
            );
        }
    });

    SelectAllMixin = {
        setStartRole:function(rolename,fla)
        {
            //fla是表示用来区分openstack定制环境和其他类型的环境
            //如果不是定制化openstack在操作完clusterRolesStatus表后
            //就必须开始启动执行task

            var btn = $(this.refs.btnstart.getDOMNode());
            $(btn).attr("disabled","true");
            alert("正在启动中,请等待....");

            $.ajax({
                type: "POST",
                url: "/api/cluster/startrole/",
                data: "rolename="+rolename+"&clusterId="+this.props.cluster.id+"&clusterType="+this.props.cluster.get('cluster_type'),
                success: _.bind(function(msg){
                    console.log("成功设置启动角色");
                    if(this.refs.btnstart)
                    {
                      if(fla){this.afterStartOrStop();} 
                      //启动和停止后必须重新读取数据库,否则启动和停止按钮不会自动切换.
                      var clusterRolesStatus=new models.ClusterRoleStatus();
                      clusterRolesStatus.fetch().done(_.bind(function(){this.setState({clusterRolesStatus: clusterRolesStatus});},this)).fail(function(){});
                      if(this.setbtnstatu){this.setbtnstatu(2);}else{this.props.changestartallbtn(rolename,2);}
                    }
                },this),
                error:function(msg)
                {
                   //alert('设置启动角色失败!');
                }
            });
        },
        setStopRole:function(rolename,fla)
        {
           $.ajax({
                type: "POST",
                url: "/api/cluster/stoprole/",
                data: "rolename="+rolename+"&clusterId="+this.props.cluster.id+"&clusterType="+this.props.cluster.get('cluster_type'),
                success: _.bind(function(msg){
                    console.log("成功设置停止角色");
                    if(this.refs.btnstop)
                    {
                       var btn = $(this.refs.btnstop.getDOMNode());
                       $(btn).attr("disabled","true");
                       if(fla){this.afterStartOrStop();}  
                       var clusterRolesStatus=new models.ClusterRoleStatus();
                       clusterRolesStatus.fetch().done(_.bind(function(){this.setState({clusterRolesStatus: clusterRolesStatus});},this)).fail(function(){});
                       if(this.setbtnstatu){this.setbtnstatu(1);}else{this.props.changestartallbtn(rolename,1);}
                    }
                },this),
                error:function(msg)
                {
                   //alert('设置停止角色失败!');
                }
            });
        },
         deployCluster: function(rolename,flag) {
            var cluster_type=this.props.cluster.get('cluster_type');
            app.page.removeFinishedDeploymentTasks();
           if(rolename != "all") 
           {   
              //this.props.changestartallbtn(true); //这里是nodelist子组件触发
              //rolename="all"表示一键启动和停止,否则单独按rolename启动或者停止角色
              if(flag==2) //flag=2表示启动角色flag=1表示停止角色
              {
                  if(cluster_type==4)
                  {
                    //如果是定制化openstack集群,那么直接调用shell
                    //不需要再向puppet发送task消息
                    this.setStartRole(rolename,0);
                    return;
                  }
                  else
                  {
                    this.props.cluster.save({status: "deployment"}, {patch: true, wait: true});
                    this.setStartRole(rolename,1);
                  }
               }
               else
               {
                  if(cluster_type==4)
                  {
                    this.setStopRole(rolename,0);
                    return;
                  }
                  else
                  {
                    this.props.cluster.save({status: "deployment"}, {patch: true, wait: true});
                    this.setStopRole(rolename,1);
                  }
               }
         }
         else
         {
           //this.setbtnstatu(true); //这里是nodelist组件本身触发
           if(flag==2) //flag=2表示一键启动1表示一键停止
            {
                if(cluster_type==4)
                {
                  this.setStartRole(rolename,0);
                  return;
                }
                else
                {
                 this.props.cluster.save({status: "deployment"}, {patch: true, wait: true});
                 this.setStartRole(rolename,1);
                }
            }
            else
            {
                if(cluster_type==4)
                {
                  this.setStopRole(rolename,0);
                  return;
                }
                else
                {
                 this.props.cluster.save({status: "deployment"}, {patch: true, wait: true});
                 this.setStopRole(rolename,1);
                }
            }
          }
        },
      afterStartOrStop:function()
        {
            var task = new models.Task();
             task.save({}, {url: _.result(this.props.cluster, 'url') + '/changes', type: 'PUT'})
                .always(this.close)
                .done(_.bind(app.page.deploymentTaskStarted, app.page))
                .fail(this.showError);
        },
        componentDidUpdate: function() {
            if (this.refs['select-all']){
             var input = this.refs['select-all'].getInputDOMNode();
             input.indeterminate = !input.checked && _.any(this.props.nodes, function(node) {return this.props.selectedNodeIds[node.id];}, this);
          }
        },
        renderSelectAllCheckbox: function() {
            var availableNodesIds = _.compact(this.props.nodes.map(function(node) {if (node.isSelectable()) return node.id;}));
            return (
                <controls.Input
                    ref='select-all'
                    type='checkbox'
                    checked={this.props.mode == 'edit' || (availableNodesIds.length && !_.any(availableNodesIds, function(id) {return !this.props.selectedNodeIds[id];}, this))}
                    disabled={this.props.mode == 'edit' || this.props.locked || !availableNodesIds.length || (this.props.roleLimitation && availableNodesIds.length > 1)}
                    label={i18n('common.select_all')}
                    wrapperClassName='span1 select-all'
                    onChange={_.bind(this.props.selectNodes, this.props, availableNodesIds)}
                />
            );
        }
    };

    NodeList = React.createClass({
        mixins: [SelectAllMixin],
        getEmptyListWarning: function() {
            var ns = 'cluster_page.nodes_tab.';
            if (this.props.mode == 'add') return i18n(ns + 'no_nodes_in_fuel');
            if (this.props.cluster.get('nodes').length) return i18n(ns + 'no_filtered_nodes_warning');
            return i18n(ns + 'no_nodes_in_environment');
        },
        getInitialState: function () {
        var clusterRolesStatus=new models.ClusterRoleStatus();
            clusterRolesStatus.fetch().done(_.bind(function(){this.setState({clusterRolesStatus: clusterRolesStatus});},this)).fail(function(){});
         return {
               actionInProgress:  false,
               clusterRolesStatus:clusterRolesStatus
            };
         },
        setbtnstatu:function(statusflag){
           var clusterRolesStatus=this.state.clusterRolesStatus;
           for (var t=0;t<clusterRolesStatus.length;t++)
           {
             clusterRolesStatus.models[t].set({"role_status":statusflag});
           }
        },
        changestartallbtn:function(rolename,roleflag)
        {
          var clusterRolesStatus=this.state.clusterRolesStatus;
          for (var t=0;t<clusterRolesStatus.length;t++)
           {
             if(clusterRolesStatus.models[t].get('cluster_role') == rolename)
             {
                clusterRolesStatus.models[t].set({"role_status":roleflag});
                break;
             }
           }
        },
        groupNodes: function() {
            var nodes = _.filter(this.props.nodes, function(node) {
                    return _.contains(node.get('name').concat(' ', node.get('mac')).toLowerCase(), this.props.filter);
                }, this);
                 //按照过滤条件过滤
            var nodesroles=_.map(nodes, function(node){ return node.get('roles'); });
            var nodespending_roles=_.map(nodes, function(node){ return node.get('pending_roles'); });
            var roles=_.union(_.flatten(nodesroles));
            var pending_roles=_.union(_.flatten(nodespending_roles));//没有部署前也需要显示节点
            var releaseRoles = this.props.cluster.get('release').get('role_models'),
                method = _.bind(function(node) {
                    if (this.props.grouping == 'roles' && this.props.cluster.get('status')=='new') {return node.getRolesSummary(releaseRoles,roles);}
                    if (this.props.grouping == 'hardware') return node.getHardwareSummary();
                    return node.getRolesSummary(releaseRoles) + '; \u00A0' + node.getHardwareSummary();
                }, this),
              groups = _.pairs(_.groupBy(nodes, method)); //按角色分组则不用上面原来的规则
              if (this.props.grouping == 'roles' && this.props.cluster.get('status')!='new')
              {
                //没有部署cluster之前,也需要显示集群节点列表,但没有启动停止按钮
                //目前cluster没有部署,按原来的格式显示.也可在此if后加else,把if
                //中的roles变成pending_roles即可
                groups=new Array();//清空原来的数据,重新生成自己的角色分组数据
                /*groups.push(["mysqlcls",nodes]);
                groups.push(["nagios",nodes]);*/
                var union_roles=_.union(roles,pending_roles);
                _.each(union_roles,_.bind(function(role){
                   groups.push([role,_.filter(nodes,function(node){return _.contains(_.union(node.get('roles'),node.get('pending_roles')),role)},this)]);
                },this));
                return groups;
              }
              else if(this.props.grouping == 'roles' && this.props.cluster.get('status') == 'new')
              {
                 groups=new Array();
                 _.each(pending_roles,_.bind(function(role){
                   groups.push([role,_.filter(nodes,function(node){return _.contains(_.union(node.get('roles'),node.get('pending_roles')),role)},this)]);
                },this));
                return groups;
              }
              
            if (this.props.grouping == 'hardware') return _.sortBy(groups, _.first);
            var preferredOrder = releaseRoles.pluck('name');
            return groups.sort(function(group1, group2) {
                var roles1 = group1[1][0].sortedRoles(preferredOrder),
                    roles2 = group2[1][0].sortedRoles(preferredOrder),
                    order;
                while (!order && roles1.length && roles2.length) {
                    order = _.indexOf(preferredOrder, roles1.shift()) - _.indexOf(preferredOrder, roles2.shift());
                }
                return order || roles1.length - roles2.length;
            });
        },
        render: function() {
             //this.props.mode 有list add edit三个值
              var groups = this.groupNodes();
              var clusterRolesStatus=this.state.clusterRolesStatus;
              var clusterid=this.props.cluster.get('id');
              var clusterstatus=this.props.cluster.get('status');
              var cluster_type=this.props.cluster.get('cluster_type');

              //where 后面如果加false,返回的数据有可能是多条数据
              var clusterRoles=clusterRolesStatus.where({cluster_id:clusterid},false);
              var disabledstartall=false;
              var disabledstopall=false;
             if(clusterRoles.length)
             {
                //此集群下面所有的角色都处于停止状态才启用一键启动
                for (var t=0;t<clusterRoles.length;t++)
                {
                  if (clusterRoles[t].get('role_status')=="1" || clusterRoles[t].get('role_status')=="3")
                  {
                    disabledstopall=true;
                    break;
                  }
                }

              //此集群下面所有的角色都处于停止状态才启用一键停止
              for (var t=0;t<clusterRoles.length;t++)
               {
                 if (clusterRoles[t].get('role_status')=="2")
                 {
                   disabledstartall=true;
                   break;
                 }
               }
             }
            else
            {
              disabledstopall=true;
            }
            
            var  startdisabled=(!disabledstartall && this.props.mode =="list" && !this.state.actionInProgress && clusterstatus == "operational" );
            var  stopdisabled =(!disabledstopall && this.props.mode =="list" && !this.state.actionInProgress && clusterstatus == "operational" );
            return (
                <div className='node-list'>
                    {!!groups.length &&
                        <div className='row-fluid node-list-header'>
                          <div className='span6'></div>
                        {this.props.mode != 'add' || this.props.mode !='edit' ? [
                        　　<div>
                               <div className='span6' style={{width:'567px'}}></div>
                                 <div className='span2' style={{textAlign:"right",width:'100px'}}> 
                                  <button
                                    key='start'
                                    ref='btnstart'
                                    className='btn btn-success btn-add-nodes'
                                    disabled={!startdisabled}
                                    onClick={_.bind(this.deployCluster, this, "all",2)}
                                  >
                                   <i className='icon-play' />
                                   <span>一键启动</span>
                                 </button>
                              </div>
                             <div className='span2' style={{textAlign:"left",width:'100px'}}> 
                                 <button
                                   key='stop'
                                   ref='btnstop'
                                   className='btn btn-success btn-add-nodes'
                                   disabled={!stopdisabled}
                                   onClick={_.bind(this.deployCluster, this, "all",1)}
                                  >
                                   <i className='icon-play' />
                                   <span>一键停止</span>
                                </button>
                              </div>
                            </div>
                           ]:[
                           ]}
                        {this.renderSelectAllCheckbox()}
                      </div>
                    }
                    <div className='row-fluid'>
                        {groups.length ?
                            <div>
                                {groups.map(function(group) {
                                    return <NodeGroup {...this.props}
                                        key={group[0]}
                                        label={group[0]}
                                        nodes={group[1]}
                                        clusterRolesStatus={this.state.clusterRolesStatus}
                                        changestartallbtn={this.changestartallbtn}
                                    />;
                                }, this)}
                            </div>
                        :
                            <div className='alert alert-warning'>{this.getEmptyListWarning()}</div>
                        }
                    </div>
                </div>
            );
        }
    });

    NodeGroup = React.createClass({
        mixins: [SelectAllMixin],
        getInitialState: function() {
            return {clusterRolesStatus:this.props.clusterRolesStatus};
        },
        render: function() {
            //can_start_down>0 && clusterstatus=="operational"
            //按角色启动和停止没有按照cluster_type设置,而是按照can_start_down标志位
            //因为customopenstack没有针对角色启动和停止,而是整个集群来启动和停止
            //所有还需要加上cluster_type来判断显示和隐藏启动和停止
            //cloudmaster启动和停止按钮
            var showstartbtn=false;
            var showstopbtn=false;
            var roledivclass="span10";
            //this.state.clusterRolesStatus.models.length获取这个表的记录数
            if (this.state.clusterRolesStatus.models.length<=0 && this.props.mode != 'list') {
                 //return <controls.ProgressBar />;首次创建集群后
                 //添加节点的时候也会执行这里的条件,导致页面异常
                 showstartbtn=false;
                 showstopbtn=false;
             }
             else
             {
                var clusterstatus=this.props.cluster.get('status');
                var clusterid=this.props.cluster.get('id');
                var rolename=this.props.label;
             
                
                var roleobj=this.props.cluster.get('release').get('role_models').where({name: rolename},true);
                 //console.log(this.props.cluster.get('release').get('role_models'));
                var can_start_down=roleobj?roleobj.get('can_start_down'):0;
                var cluster_type=this.props.cluster.get('cluster_type');
                if(can_start_down>0 && clusterstatus=="operational")
                  {
                    //控制原生openstack的隐藏启动按钮是can_start_down=0
                    if(cluster_type==4)//这里控制定制化openstack启动和停止
                    {
                     //控制定制化环境的启动停止按钮在父组件NodeList中控制 
                     //这里不用再编写代码
                     //控制原生openstack的角色启动和停止用can_start_down=0
                    }
                    else //这里控制不是定制化openstack类型
                    {
                       roledivclass="span8";
                       var clusterRolesStatus=this.state.clusterRolesStatus;
                       var clusterRolesStatu=clusterRolesStatus.where({cluster_id:clusterid,cluster_role:rolename},true);
                       if(clusterRolesStatu && clusterRolesStatu.get('role_status')=="2")
                          {
                             showstartbtn=false;
                             showstopbtn=true;
                          }
                       else
                          {
                             showstartbtn=true;
                             showstopbtn=false;
                          }
                    }
                 }
              }
            return (
                <div className='node-group'>
                    <div className='row-fluid node-group-header'>
                        <div className={roledivclass}>
                            <h4>{this.props.label} ({this.props.nodes.length})</h4>
                        </div>
                        { showstartbtn && 
                          <div className='span2' style={{textAlign:"right"}}> <button
                                    key='start'
                                    ref='btnstart'
                                    className='btn btn-success btn-add-nodes'
                                    onClick={_.bind(this.deployCluster, this, this.props.label,2)}
                                 >
                                <i className='icon-play' />
                                <span>启动</span>
                              </button>
                          </div>
                        }
                         { showstopbtn && 
                          <div className='span2' style={{textAlign:"right"}}> <button
                                    key='stop'
                                    ref='btnstop'
                                    className='btn btn-success btn-add-nodes'
                                    onClick={_.bind(this.deployCluster, this, this.props.label,1)}
                                 >
                                <i className='icon-play' />
                                <span>停止</span>
                              </button>
                          </div>
                        }
                        {this.renderSelectAllCheckbox()}
                    </div>
                    <div>
                        {this.props.nodes.map(function(node) {
                            return <Node
                                key={node.id}
                                node={node}
                                checked={this.props.mode == 'edit' || this.props.selectedNodeIds[node.id]}
                                cluster={this.props.cluster}
                                locked={this.props.mode == 'edit' || this.props.locked}
                                onNodeSelection={_.bind(this.props.selectNodes, this.props, [node.id])}
                            />;
                        }, this)}
                    </div>
                </div>
            );
        }
    });

    Node = React.createClass({
        getInitialState: function() {
            return {
                renaming: false,
                actionInProgress: false,
                eventNamespace: 'click.editnodename' + this.props.node.id
            };
        },
        componentWillUnmount: function() {
            $('html').off(this.state.eventNamespace);
        },
        componentDidUpdate: function() {
            if (!this.props.node.get('cluster') && !this.props.checked) this.props.node.set({pending_roles: []}, {assign: true});
        },
        startNodeRenaming: function(e) {
            e.preventDefault();
            $('html').on(this.state.eventNamespace, _.bind(function(e) {
                if ($(e.target).hasClass('node-name')) {
                    e.preventDefault();
                } else {
                    this.endNodeRenaming();
                }
            }, this));
            this.setState({renaming: true});
        },
        endNodeRenaming: function() {
            $('html').off(this.state.eventNamespace);
            this.setState({
                renaming: false,
                actionInProgress: false
            });
        },
        applyNewNodeName: function(newName) {
            if (newName && newName != this.props.node.get('name')) {
                this.setState({actionInProgress: true});
                this.props.node.save({name: newName}, {patch: true, wait: true}).always(this.endNodeRenaming);
            } else {
                this.endNodeRenaming();
            }
        },
        onNodeNameInputKeydown: function(e) {
            if (e.key == 'Enter') {
                this.applyNewNodeName(this.refs.name.getInputDOMNode().value);
            } else if (e.key == 'Escape') {
                this.endNodeRenaming();
            }
        },
        discardNodeChanges: function() {
            if (this.state.actionInProgress) return;
            this.setState({actionInProgress: true});
            var data = this.props.node.get('pending_addition') ? {cluster_id: null, pending_addition: false, pending_roles: [],name:this.props.node.get('name') } : {pending_deletion: false};
            this.props.node.save(data, {patch: true, wait: true, silent: true})
                .done(_.bind(function() {
                    $.when(this.props.cluster.fetch(), this.props.cluster.fetchRelated('nodes')).done(_.bind(function() {
                        this.setState({actionInProgress: false});
                    }, this));
                    app.navbar.refresh();
                    app.page.removeFinishedNetworkTasks();
                }, this))
                .fail(function() {utils.showErrorDialog({title: i18n('dialog.discard_changes.cant_discard')});});
        },
        getNodeLogsLink: function() {
            var status = this.props.node.get('status'),
                error = this.props.node.get('error_type'),
                options = {type: 'remote', node: this.props.node.id};
            if (status == 'discover') {
                options.source = 'bootstrap/messages';
            } else if (status == 'provisioning' || status == 'provisioned' || (status == 'error' && error == 'provision')) {
                options.source = 'install/anaconda';
            } else if (status == 'deploying' || status == 'ready' || (status == 'error' && error == 'deploy')) {
                options.source = 'install/puppet';
            }
            return '#cluster/' + this.props.cluster.id + '/logs/' + utils.serializeTabOptions(options);
        },
        showNodeDetails: function() {
            utils.showDialog(dialogs.ShowNodeInfoDialog, {
                node: this.props.node,
                title: this.props.node.get('name') || this.props.node.get('mac')
            });
        },
        calculateNodeViewStatus: function() {
            var node = this.props.node;
            if (!node.get('online')) return 'offline';
            if (node.get('pending_addition')) return 'pending_addition';
            if (node.get('pending_deletion')) return 'pending_deletion';
            return node.get('status');
        },
        sortRoles: function(roles) {
            var preferredOrder = this.props.cluster.get('release').get('roles');
            return roles.sort(function(a, b) {
                return _.indexOf(preferredOrder, a) - _.indexOf(preferredOrder, b);
            });
        },
        renderRoleList: function(attribute) {
            var roles = this.props.node.get(attribute);
            if (!roles.length) return null;
            return (
                <ul key={attribute} className={attribute}>
                    {_.map(this.sortRoles(roles), function(role, index) {
                        return <li key={index}>{role}</li>;
                    })}
                </ul>
            );
        },
        getClusterTypeName:function(type){
          if (type==1 || type==4)  return "OpenStack环境";
          if (type==2)             return "CloudMaster环境";
          if (type==3)             return "EBS环境";
          if (type==5)             return "ONEST环境";
          return "未知环境";
        },
        render: function() {
            var ns = 'cluster_page.nodes_tab.node.',
                node = this.props.node,
                disabled = this.props.locked || !node.isSelectable() || this.state.actionInProgress,
                roles = [this.renderRoleList('roles'), this.renderRoleList('pending_roles')];
            var noderolenames=node.get('roles');
            var nodependingroles=node.get('pending_roles');
            var noderolestr=noderolenames+','+nodependingroles;
                //console.log(node.get('roles'));
            var status = this.calculateNodeViewStatus(),
                statusClass = {
                    offline: 'msg-offline',
                    pending_addition: 'msg-ok',
                    pending_deletion: 'msg-warning',
                    ready: 'msg-ok',
                    provisioning: 'provisioning',
                    provisioned: 'msg-provisioned',
                    deploying: 'deploying',
                    error: 'msg-error',
                    discover: 'msg-discover'
                }[status],
                iconClass = {
                    offline: 'icon-block',
                    pending_addition: 'icon-ok-circle-empty',
                    pending_deletion: 'icon-cancel-circle',
                    ready: 'icon-ok',
                    provisioned: 'icon-install',
                    error: 'icon-attention',
                    discover: 'icon-ok-circle-empty'
                }[status];
            var statusClasses = {'node-status': true};
            statusClasses[statusClass] = true;
            var logoClasses = {'node-logo': true};
            logoClasses['manufacturer-' + node.get('manufacturer').toLowerCase()] = node.get('manufacturer');
            var nodeBoxClasses = {'node-box': true, disabled: disabled};
            nodeBoxClasses[status] = status;
            return (
                <div className={cx({node: true, checked: this.props.checked})}>
                    <label className={cx(nodeBoxClasses)}>
                        <controls.Input
                            type='checkbox'
                            name={node.id}
                            checked={this.props.checked}
                            disabled={disabled}
                            onChange={this.props.onNodeSelection}
                        />
                        <div className='node-content'>
                            <div className={cx(logoClasses)} />
                            <div className='node-name-roles'>
                                <div className='name enable-selection'>
                                    {this.state.renaming ?
                                        <controls.Input
                                            ref='name'
                                            type='text'
                                            defaultValue={node.get('name')}
                                            inputClassName='node-name'
                                            disabled={this.state.actionInProgress}
                                            onKeyDown={this.onNodeNameInputKeydown}
                                            autoFocus
                                        />
                                    :
                                        <p title={i18n(ns + 'edit_name')} onClick={!disabled && this.startNodeRenaming}>
                                            {node.get('name') || node.get('mac')}
                                        </p>
                                    }
                                </div>
                                <div className='role-list' title={noderolestr}>
                                    {_.compact(roles).length ? _.union(roles) : i18n(ns + 'unallocated')}
                                </div>
                            </div>
                            <div className='node-button'>
                                {!!node.get('cluster') && (
                                    (this.props.locked || !node.hasChanges()) ?
                                        <a className='btn btn-link' title={i18n(ns + 'view_logs')} href={this.getNodeLogsLink()}>
                                            <i className='icon-logs' />
                                        </a>
                                    :
                                        <button
                                            className='btn btn-link'
                                            title={i18n(ns + (node.get('pending_addition') ? 'discard_addition' : 'discard_deletion'))}
                                            onClick={this.discardNodeChanges}
                                        >
                                            <i className='icon-back-in-time' />
                                        </button>
                                )}
                            </div>
                            <div className={cx(statusClasses)}>
                                <div className='node-status-container'>
                                    {_.contains(['provisioning', 'deploying'], status) &&
                                        <div className={cx({progress: true, 'progress-success': status == 'deploying'})}>
                                            <div className='bar' style={{width: _.max([node.get('progress'), 3]) + '%'}} />
                                        </div>
                                    }
                                    <i className={iconClass} />
                                    <span>
                                        {i18n(ns + 'status.' + status, {os: this.props.cluster.get('release').get('operating_system') || 'OS',env:this.getClusterTypeName(this.props.cluster.get('cluster_type'))})}
                                    </span>
                                </div>
                            </div>
                            <div className='node-details' onClick={this.showNodeDetails} />
                            <div className='node-hardware'>
                                <span>
                                    {i18n('node_details.cpu')}: {node.resource('cores') || '0'} ({node.resource('ht_cores') || '?'})
                                </span>
                                <span>
                                    {i18n('node_details.hdd')}: {node.resource('hdd') ? utils.showDiskSize(node.resource('hdd')) : '?' + i18n('common.size.gb')}
                                </span>
                                <span>
                                    {i18n('node_details.ram')}: {node.resource('ram') ? utils.showMemorySize(node.resource('ram')) : '?' + i18n('common.size.gb')}
                                </span>
                            </div>
                        </div>
                    </label>
                </div>
            );
        }
    });

    return NodeListScreen;
});
