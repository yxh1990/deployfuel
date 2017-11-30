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
    'underscore',
    'models',
    'backbone',
    'text!templates/common/pagination.html'
],
function(_, models,Backbone,pagingTemplate) {
    'use strict';
   
 var  pagingView=Backbone.View.extend({
         template: _.template(pagingTemplate),
         events:{
          'click #pagelist li:not(:last):not(:first)':'changePageIndex',
          'click #pageNext':'changeNextPage',
          'click #pagePrev':'changePrevPage'
         },
         initialize: function(options) {
           app.pageSize=this.pageSize;
           if(options)
              this.currentPageIndex=options.currentpage;
         },
         pageSize:10,  //默认的单页显示条数
         currentPageIndex:1,  //默认的显示的页面索引
         changePageIndex:function(e){
             var liobj=e.currentTarget;
             if(liobj.className!='disabled'){
              var pageToIndex=liobj.getAttribute('data-index');
              this.currentPageIndex=pageToIndex==null?this.currentPageIndex:pageToIndex;
              this.render();

              app.currentPageIndex=this.currentPageIndex;
              Backbone.trigger('changePage'); //刷新列表view
           }
           else
           {
             return;
           }
         },
         changeNextPage:function()
         {
            //点击前进和后退按钮会执行changePageIndex和changeNextPage两个函数
            //'click #pagelist li':'changePageIndex',
            //'click #pageNext':'changeNextPage',
            var nextbtn=this.$("#pageNext");
            if(nextbtn.attr('class')!='disabled'){
                 this.currentPageIndex=parseInt(this.currentPageIndex)+1;
                 this.render();
                 app.currentPageIndex=this.currentPageIndex;
                 Backbone.trigger('changePage');
            }
            else
            {
              alert('已经到达最后一页!');
              return;
            }
         },
         changePrevPage:function()
         {
            var prevbtn=this.$("#pagePrev");
            if(prevbtn.attr('class')!='disabled'){
                 this.currentPageIndex=parseInt(this.currentPageIndex)-1;
                 this.render();
                 app.currentPageIndex=this.currentPageIndex;
                 Backbone.trigger('changePage');
            }
            else
            {
              alert('已经到达第一页!');
              return;
            }

         },
         render: function() 
         {
            var total=app.totalrows;
          /*  alert(total);
            alert(this.pageSize);
            alert(this.currentPageIndex);*/
            $(this.el).html(this.template({total:total,pageSize:this.pageSize,currentPageIndex:this.currentPageIndex}));
            return this;
          }
       });
  return pagingView;
});
