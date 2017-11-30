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
    控制x86物理机和添加x86物理机页面的切换
**/
define(
[
    'jquery',
    'underscore',
    'utils',
    'models',
    'views/common',
    'views/phymachine_page_tabs/excel_tab',
    'views/phymachine_page_tabs/addx86_tab',
    'views/phymachine_page_tabs/addx86_tab'
],
function($, _, utils, models, commonViews, ListScreen, AddScreen,EditScreen) {
    'use strict';
    var NodesTab;

    NodesTab = commonViews.Tab.extend({
        className: 'wrapper',
        screen: null,
        scrollPositions: {},
        hasChanges: function() {
            return this.screen && _.result(this.screen, 'hasChanges');
        },
        changeScreen: function(NewScreenView, screenOptions) {
            var options = _.extend({model: this.model, tab: this, screenOptions: screenOptions || []});
            //console.log("options "+options.screenOptions);
            if (this.screen) {
                if (this.screen.keepScrollPosition) {
                    this.scrollPositions[this.screen.constructorName || this.screen.displayName] = $(window).scrollTop();
                }
                this.$el.fadeOut('fast', _.bind(function() {
                    utils.universalUnmount(this.screen);
                    this.screen = utils.universalMount(NewScreenView, options, this.$el, this);
                    this.$el.hide().fadeIn('fast');
                    var newScrollPosition = this.screen.keepScrollPosition && this.scrollPositions[this.screen.constructorName || this.screen.displayName];
                    if (newScrollPosition) $(window).scrollTop(newScrollPosition);
                }, this));
            } else {
                this.screen = utils.universalMount(NewScreenView, options, this.$el, this);
            }
        },
        beforeTearDown: function() {
            if (this.screen) utils.universalUnmount(this.screen);
        },
        initialize: function(options) {
            _.defaults(this, options);
            this.revertChanges = _.bind(function() {
                return this.screen && this.screen.revertChanges();
            }, this);
        },
        routeScreen: function(options) {
            var screens = {
                list: ListScreen,
                add: AddScreen,
                edit:EditScreen
            };
            this.changeScreen(screens[options[1]] || screens.list, options.slice(1));
        },
        render: function() {
            this.routeScreen(this.tabOptions);
            return this;
        }
    });

    return NodesTab;
});
