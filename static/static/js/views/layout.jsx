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
    'i18next',
    'backbone',
    'react',
    'utils',
    'models',
    'jsx!component_mixins',
    'jsx!views/dialogs',
    'jsx!views/clusters_page'
],
function($, _, i18n, i18next, Backbone, React, utils, models, componentMixins, dialogs,clustersPage) {
    'use strict';

    var components = {};

    var cx = React.addons.classSet;

    components.Navbar = React.createClass({
        mixins: [
            componentMixins.backboneMixin('user'),
            componentMixins.backboneMixin('version'),
            componentMixins.pollingMixin(20)
        ],
        showChangePasswordDialog: function(e) {
            e.preventDefault();
            utils.showDialog(dialogs.ChangePasswordDialog);
        },
        togglePopover: function(visible) {
            this.setState({popoverVisible: _.isBoolean(visible) ? visible : !this.state.popoverVisible});
        },
        setActive: function(url) {
            this.setState({activeElement: url});
        },
        shouldDataBeFetched: function() {
            return this.props.user.get('authenticated');
        },
        fetchData: function() {
            return $.when(this.props.statistics.fetch(), this.props.notifications.fetch({limit: this.props.notificationsDisplayCount}));
        },
        refresh: function() {
            if (this.shouldDataBeFetched()) {
                return this.fetchData();
            }
            return $.Deferred().reject();
        },
        componentDidMount: function() {
            this.props.user.on('change:authenticated', function(model, value) {
                if (value) {
                    this.startPolling();
                } else {
                    this.stopPolling();
                    this.props.statistics.clear();
                    this.props.notifications.reset();
                }
            }, this);
        },
        getDefaultProps: function() {
            return {notificationsDisplayCount: 5};
        },
        getInitialState: function() {
            return {
                activeElement: "onetab",
                popoverVisible: false,
                hidden: false,
                setindex:false
            };
        },
        changeActiveElement:function(e){
          this.state.setindex=true;
          var abtn=$(e.target);
          var ul=abtn.parent().parent();
          var alist=ul.find("li a");
          alist.removeClass('active');
          abtn.addClass('active');
        },
        render: function() {
            if (this.state.hidden) {
                return null;
            }
            return (
                <div>
                    <div className='user-info-box'>
                        {this.props.version.get('auth_required') && this.props.user.get('authenticated') &&
                            <div>
                                <i className='icon-user'></i>
                                <span className='username'>{this.props.user.get('username')}</span>
                                <a className='change-password' onClick={this.showChangePasswordDialog}>{i18n('common.change_password')}</a>
                                <a href='#logout'>{i18n('common.logout')}</a>
                            </div>
                        }
                    </div>
                    <div className='navigation-bar'>
                        <div className='navigation-bar-box'>
                            <ul className='navigation-bar-ul'>
                                <li className='product-logo'>
                                    <a href='#'><div className='logo'></div></a>
                                </li>
                                {_.map(this.props.elements, function(element) { 
                                    return <li key={element.label}>
                                        <a className={cx({active: this.state.activeElement == element.url.slice(1) || ((this.state.activeElement=="onetab" ||this.state.activeElement=="clusters") && element.url.slice(1)=="ops/sys")})} onClick={this.changeActiveElement} href={element.url}>{i18n('navbar.' + element.label, {defaultValue: element.label})}</a>
                                    </li>;
                                }, this)}
                                <li className='space'></li>
                                <Notifications ref='notifications'
                                    notifications={this.props.notifications}
                                    togglePopover={this.togglePopover}
                                />
                                <NodeStats statistics={this.props.statistics} />
                            </ul>
                        </div>
                    </div>
                    <div className='notification-wrapper'>
                        {this.state.popoverVisible &&
                            <NotificationsPopover ref='popover'
                                notifications={this.props.notifications}
                                displayCount={this.props.notificationsDisplayCount}
                                togglePopover={this.togglePopover}
                            />
                        }
                    </div>
                </div>
            );
        }
    });

    var NodeStats = React.createClass({
        mixins: [componentMixins.backboneMixin('statistics')],
        render: function() {
            return (
                <li className='navigation-bar-icon nodes-summary-container'>
                    <div className='statistic'>
                        {_.map(['total', 'unallocated'], function(prop) {
                            var value = this.props.statistics.get(prop);
                            return _.isUndefined(value) ? '' : [
                                <div className='stat-count'>{value}</div>,
                                <div className='stat-title' dangerouslySetInnerHTML={{__html: utils.linebreaks(_.escape(i18n('navbar.stats.' + prop, {count: value})))}}></div>
                            ];
                        }, this)}
                    </div>
                </li>
            );
        }
    });

    var Notifications = React.createClass({
        mixins: [componentMixins.backboneMixin('notifications', 'add remove change:status')],
        render: function() {
            var unreadNotifications = this.props.notifications.where({status: 'unread'});
            return (
                <li className='navigation-bar-icon notifications' onClick={this.props.togglePopover}>
                    <i className='icon-comment'></i>
                    {unreadNotifications.length && <span className='badge badge-warning'>{unreadNotifications.length}</span>}
                </li>
            );
        }
    });

    var NotificationsPopover = React.createClass({
         mixins: [componentMixins.backboneMixin('notifications')],
        getDefaultProps: function() {
            return {
                eventNamespace: 'click.click-notifications'
            };
        },
        showNodeInfo: function(id) {
            var node = new models.Node({id: id});
            node.fetch();
            dialogs.ShowNodeInfoDialog.show({node: node});
        },
        markAsRead: function() {
            var notificationsToMark = new models.Notifications(this.props.notifications.where({status: 'unread'}));
            if (notificationsToMark.length) {
                this.setState({unreadNotificationsIds: notificationsToMark.pluck('id')});
                notificationsToMark.toJSON = function() {
                    return notificationsToMark.map(function(notification) {
                        notification.set({status: 'read'});
                        return _.pick(notification.attributes, 'id', 'status');
                    }, this);
                };
                Backbone.sync('update', notificationsToMark);
            }
        },
        componentDidMount: function() {
            this.markAsRead();
            $('html').on(this.props.eventNamespace, this.props.handleBodyClick);
            Backbone.history.on('route', _.partial(this.props.togglePopover, false), this);
        },
        componentWillUnmount: function() {
            $('html').off(this.props.eventNamespace);
            Backbone.history.off('route', this.props.togglePopover, this);
        },
        getInitialState: function() {
            return {unreadNotificationsIds: []};
        },
        render: function() {
            var showMore = (Backbone.history.getHash() != 'notifications') && this.props.notifications.length;
            var notifications = this.props.notifications.first(this.props.displayCount);
            return (
                <div className='message-list-placeholder'>
                    <ul className='message-list-popover'>
                        {this.props.notifications.length ? (
                            _.map(notifications, function(notification, index, collection) {
                                var unread = notification.get('status') == 'unread' || _.contains(this.state.unreadNotificationsIds, notification.id);
                                var nodeId = notification.get('node_id');
                                return [
                                    <li
                                        key={'notification' + notification.id}
                                        className={utils.classNames({'enable-selection': true, new: unread, clickable: nodeId}) + ' ' + notification.get('topic')}
                                        onClick={nodeId && _.bind(this.showNodeInfo, this, nodeId)}
                                    >
                                        <i className={{error: 'icon-attention', warning: 'icon-attention', discover: 'icon-bell'}[notification.get('topic')] || 'icon-info-circled'}></i>
                                        <span dangerouslySetInnerHTML={{__html: utils.urlify(notification.escape('message'))}}></span>
                                    </li>,
                                    (showMore || index < (collection.length - 1)) && <li key={'divider' + notification.id} className='divider'></li>
                                ];
                            }, this)
                        ) : <li key='no_notifications'>{i18n('notifications_popover.no_notifications_text')}</li>}
                    </ul>
                    {showMore && <div className='show-more-notifications'><a href='#notifications'>{i18n('notifications_popover.view_all_button')}</a></div>}
                </div>
            );
        }
    });

    components.Footer = React.createClass({
        mixins: [componentMixins.backboneMixin('version')],
        getInitialState: function() {
            return {
                hidden: false
            };
        },
        setColorScreen:function(options)
        {
           //$.cookie('skin', options);
           window.location.reload();
        },
        render: function() {
            if (this.state.hidden) {
                return null;
            }
            return (
                <div className='footer-box'>
                   <div>
                        <div className='footer-copyright pull-center'>中国移动2015</div>
                        <div className='footer-copyright pull-center'>
                             <li key="1"><a style={{color:'white'}} onClick={_.bind(this.setColorScreen,this,"")}>默认皮肤</a></li>
                             <li key="2"><a style={{color:'white'}} onClick={_.bind(this.setColorScreen,this,"blue")}>蓝色皮肤</a></li>
                             <li key="3"><a style={{color:'white'}} onClick={_.bind(this.setColorScreen,this,"white")}>白色皮肤</a></li>
                        </div>
                    </div>
                </div>
            );
        },
        setLocale: function(newLocale) {
            i18next.setLng(newLocale.locale, {});
            window.location.reload();
        },
        getAvailableLocales: function() {
            return _.map(_.keys(i18next.options.resStore).sort(), function(locale) {
                return {locale: locale, name: i18n('language', {lng: locale})};
            }, this);
        },
        getCurrentLocale: function() {
            return _.find(this.props.locales, {locale: i18next.lng()});
        },
        setDefaultLocale: function() {
            if (!this.getCurrentLocale()) {
                i18next.setLng(this.props.locales[0].locale, {});
            }
        },
        getDefaultProps: function() {
            return {locales: this.prototype.getAvailableLocales()};
        },
        componentWillMount: function() {
            this.setDefaultLocale();
        }
    });

    components.Breadcrumbs = React.createClass({
        getInitialState: function() {
            return {
                hidden: false
            };
        },
        update: function(path) {
            path = path || _.result(app.page, 'breadcrumbsPath');
            this.setProps({path: path});
        },
        setClustertype: function(e) {
          var abtn=$(e.target);
          var clusterype=abtn.attr('href');
           
     
          app.cluster_type=4;
         
          
          var ul=abtn.parent().parent();
          ul.children().children().css("background-color","");
          abtn.css("background-color","#003e83");
        },
        setfristsencodbar:function()
        {
            var ul=$("body").find(".breadcrumb");
            var alist=ul.find("li a");
            ul.children().children().css("background-color","");
            $(alist[0]).css("background-color","#003e83");
        },
        render:function() {
            if (this.state.hidden) {
                return null;
            }
            return <ul className='breadcrumb'>
                {_.map(this.props.path, function(breadcrumb, index) {
                    if (_.isArray(breadcrumb)) {
                        if (breadcrumb[2]) {
                            return <li key={index} className='active'>{breadcrumb[0]}</li>;
                        }
                        return <li key={index}><a href={breadcrumb[1]} onClick={_.bind(this.setClustertype,this)}>{i18n('breadcrumbs.' + breadcrumb[0], {defaultValue: breadcrumb[0]})}</a></li>;
                    }
                    return <li key={index} className='active'>{i18n('breadcrumbs.' + breadcrumb, {defaultValue: breadcrumb})}</li>;
                },this)}
            </ul>;
        }
    });

    return components;
});
