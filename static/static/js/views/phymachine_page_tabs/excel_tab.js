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
    'i18n',
    'models',
    'utils',
    'backbone',
    'text!templates/phymachine/excel.html',
    'text!templates/phymachine/x86tr.html',
    'views/pagination'
],
function(_, i18n, models,utils,Backbone,excelTemplate,trTemplate,pagingView) {
    'use strict';

    var x86Page = Backbone.View.extend({
        template: _.template(excelTemplate),
        events:{
            'click #btnaddexcel':'checkuserselectExcel',
            'change #myfile':'resetInputStyle',
            'click #btn_import':'resetmsg',
            'click #btn_callback':"showsuccess"
        },
        showsuccess:function(){
          this.render();
          this.$("#msgsucess").show();
          setTimeout("this.$('#msgsucess').hide();this.$('#msgfail').hide();", 5000);
        },
        render:function()
        {
           this.$el.html(this.template());
           var tbView = new x86tbView();
           //不能用this.$el,因为这个view的el不是table
           //视图后面加上另外一个视图
           //多个视图共同组成一个页面。
           this.$el.append(tbView.render().el);
           return this; 
        },
        importfilename:'', //标志导入文件名
        count:0,      //标志导入次数
        checkuserselectExcel:function()
        {
          var excelname=this.importfilename=this.$('#myfile').val();
          if(!$.trim(excelname) || $.trim(excelname).length == 0)
          {
             this.$('#control-group').addClass('error');
             this.$('.help-inline').html('导入的文件路径不能为空');
             return false;
          }
          else
           {
             if(this.count>0)
                {
                 if(this.importfilename==excelname)
                  {
                      this.$('#control-group').addClass('error');
                      this.$('.help-inline').html('不能连续导入同一文件');
                      return false;
                  }
                }
                else
                {
                   this.count=this.count+1;
                   return true;
                }
            }
        },
       resetInputStyle:function()
        {
          this.count=0;
          this.$('#txtname').val(this.getFilePath(this.$('#myfile')));
          this.$('#control-group').removeClass('error');
        },
        resetmsg:function(){
          this.$('#msgsucess').hide();
          this.$('#msgfail').hide();
        },
       getFilePath:function(obj)
       {  
        if(obj)    
        {    
            if(window.navigator.userAgent.indexOf("MSIE")>=1)    
              {    //设置ie
                obj.select(); 
                window.parent.document.body.focus();    
                return document.selection.createRange().text;    
              }    
            else 
              {    //设置火狐和谷歌
                if(obj.prop('files'))    
                   {    
                    // return window.URL.createObjectURL(obj.prop('files')[0]); 
                    //console.log(obj.prop('files')[0]);
                    //return obj.val();  c:/fakepath/filename
                    return obj.prop('files')[0].name;    
                   }      
             } 
        }    
      }
   });
 
 var  x86tbView=Backbone.View.extend({
        template: _.template(trTemplate),
        initialize: function() {
          this.phymachine=new models.Phymachine();
          this.paginationView=new pagingView();
          Backbone.on('changePage', this.onChangePage, this);
        },
        currentPageIndex:1,
        currentPageLength:0,
        callcount:0,
        onChangePage:function(){
          this.currentPageIndex=app.currentPageIndex;
          this.getRenderData();
        },
        pageChangeSort:function(e){

         var descss="icon-down-dir";
         var ascss="icon-up-dir";

         var sortype="desc";

         var sorta=(e.currentTarget);
         var trhead=$(sorta).parent().parent();
         var sortname=sorta.getAttribute('sortname');
         var sorti=$(sorta).prev();

         var sortdescss=sorti.hasClass(descss);

         var ilist=trhead.children().children("i");
             $(ilist).each(function(i,obj){
                   $(obj).removeClass();
             });
         if(sortdescss)
         {
             sorti.removeClass().addClass(ascss);
             sortype="asc";
         }
          else
         {
             sorti.removeClass().addClass(descss);
             sortype="desc";
         }
          var data={};
          data.currentpage=this.currentPageIndex;
          data.pagesize=app.pageSize;
          app.sortname=data.ordername=sortname;
          app.sortype=data.ordertype=sortype;
          this.getRenderData(data);
        },
        setTableSortIcon:function()
        {
          var trhead=$("#tb_x86 tr th a");
          var descss="icon-down-dir";
          var ascss="icon-up-dir";
          if(app.sortname)
          {
            for(var t=0;t<trhead.length;t++)
            {
               var sorti=$(trhead[t]).prev();
               sorti.removeClass();
               if(trhead[t].getAttribute('sortname')==app.sortname)
               {
                  if(app.sortype=="desc")
                  {
                    sorti.removeClass().addClass(descss);
                  }
                  else
                  {
                    sorti.removeClass().addClass(ascss);
                  }
               }
            }
          }
          app.sortname=null;
          app.sortype=null;
        },
        getRenderData:function(arg){
          //这里的phymachinesCollection不能使用全局的this
          var phymachinesCollection=new models.Phymachines();
          var data={};
              if(arg)
              {
                data=arg;
              }
              else
              {
                this.currentPageIndex=app.returnPageIndex?app.returnPageIndex:this.currentPageIndex;
                data.currentpage=this.currentPageIndex;
                data.pagesize=app.pageSize;
                //及时销毁app的全局变量,以免影响其他操作
                app.returnPageSize=null;
                app.returnPageIndex=null;
              }
              phymachinesCollection.fetch(
                 {data:data,
                 success:_.bind(function(collection,response, options)
                   { 
                      var paginationView=new pagingView({"currentpage":app.returnPageIndex?app.returnPageIndex:this.currentPageIndex});
                      //this.$('#tb_x86').html(this.template({data:collection.toJSON()}));
                      $(this.el).html(this.template({data:collection.toJSON()})).append(paginationView.render().el);
                      this.currentPageLength=collection.length;
                      this.setTableSortIcon();
                      //this.$('#tb_x86 div').remove();
                      //只能更新模板中的table不能更新el.
                      //这里使用remove是因为模板中包含一个div和table同级
                      //这里不能再在后面render this.paginationView.render().el
                  },this),error:function(collection, response, options)
                  {
                    alert('获取物理机信息列表出现异常!');
                  }
             });
        },
        render:function() {
          //只用来第一次渲染和查询总记录数
          //修改保存后调用了render方法,但需要保存修改记录
          //所在的页面索引位置。
          this.phymachinesCollection=new models.Phymachines();
          var data={};
          if(app.returnPageIndex)
          {
            data.currentpage=app.returnPageIndex;
            data.pagesize=app.returnPageSize;
            this.getRenderData(data);
          }
          else
          {
            data.currentpage="0";
            this.getFirstLoadData(data);
          }
            return this;
        },
        getFirstLoadData:function(data)
        {
           this.phymachinesCollection.fetch(
                 {data:data,
                 success:_.bind(function(collection,response, options)
                   { 
                      app.totalrows=collection.length;
                      //筛选出第一页的数据,过滤collection
                      var pageSize=parseInt(app.pageSize);
                      var fristpagecollection=new models.Phymachines();
                      if(pageSize<collection.length)
                      {
                        for(var t=0;t<pageSize;t++)
                        {
                          //console.log(collection.models[t]);
                          fristpagecollection.push(collection.models[t]);
                        }
                        //console.log(fristpagecollection);
                      }
                      else
                      {
                        fristpagecollection=collection;
                      }
                      this.currentPageLength=fristpagecollection.length;
                      $(this.el).html(this.template({data:fristpagecollection.toJSON()})).append(this.paginationView.render().el);
                     
                  },this),error:function(collection, response, options)
                  {
                    alert('获取物理机信息列表出现异常!');
                  }
             });
        },
        events:{
          'click #ckall':'checkallx86',
          'click #btn_del':'deleIds',
          'click #btn_add':'showaddpage',
          'click #tb_x86 .a_edit':'showeditpage',
          'click #tb_x86 .a_delete':'deletex86',
          'click #tb_x86 .a_tb_title':'pageChangeSort',
          'click #tb_x86 .a_poweron':'PowerOnmachine',
          'click #tb_x86 .a_poweroff':'PowerOffmachine',
          'click #btn_poweroff':'poweroffIds',
          'click #btn_poweron' :'poweronIds',
          'click #btn_upstatus':'checkmahinestatus',
          'click #btn_upnodestatus':'refreshpage'
        },
        refreshpage:function()
        {
           this.getRenderData();
           this.paginationView=new pagingView({"currentpage": this.currentPageIndex});
        },
        PowerOnmachine:function(e)
        {
          var obj=e.currentTarget;
          var id=obj.getAttribute('dataid');
          var mp_ip=obj.getAttribute('datampip');
          var mp_user=obj.getAttribute('datampuser');
          var mp_pass=obj.getAttribute('datamppass');


          var loadview=new commonloadview();
          $('#modal-container').after(loadview.render().el);
            $.ajax({
                type: "POST",
                url: "/api/phymachine/poweron",
                data: "id="+id+"&mp_ip="+mp_ip+"&mp_user="+mp_user+"&mp_pass="+mp_pass,
                success:_.bind(function(msg){
                   var obj=JSON.parse(msg);
                   if(obj.result)
                   {
                     $('#modal-container').next().remove();
                     alert('上电成功!');
                     this.getRenderData();
                     this.paginationView=new pagingView({"currentpage": this.currentPageIndex});
                   }
                   else
                   {
                    $('#modal-container').next().remove();
                     alert('上电失败!');
                   }
                },this),
                error:function()
                {
                  $('#modal-container').next().remove();
                  alert('上电失败!');
                }
           });
        },
        PowerOffmachine:function(e)
        {
            var btnoff=(e.currentTarget);
            var id=btnoff.getAttribute('dataid');
            var mp_ip=btnoff.getAttribute('datampip');
            var mp_user=btnoff.getAttribute('datampuser');
            var mp_pass=btnoff.getAttribute('datamppass');
            var loadview=new commonloadview();
            //这个地方有可能会加载两次，需要处理。
            var hasadd=$('#modalshow').length;

            if(hasadd<1)
            {
               $('#modal-container').after(loadview.render().el);
            }
            $.ajax({
                type: "POST",
                url: "/api/phymachine/poweroff",
                data: "id="+id+"&mp_ip="+mp_ip+"&mp_user="+mp_user+"&mp_pass="+mp_pass,
                success: _.bind(function(msg){
                   var obj=JSON.parse(msg);
                    if(obj.result)
                    {
                       $('#modal-container').next().remove();
                       alert('下电成功!');
                       this.getRenderData();
                       this.paginationView=new pagingView({"currentpage": this.currentPageIndex});
                    }
                    else
                    {
                      this.callcount=this.callcount+1;
                      if(this.callcount<3)
                      {
                        this.PowerOffmachine(e);
                      }
                      else
                      {
                        $('#modal-container').next().remove();
                        alert('下电失败!');
                      }
                    }
                },this),
                error:function(msg)
                {
                  $('#modal-container').next().remove();
                  alert('下电失败!');
                }
            });
        },
        changerenderpower:function(e,poweron)
        {
          var btn=$(e.currentTarget);
          if(poweron)
          {
            btn.parent().prev().html('已上电');
            btn.html("<span>上电</span>");
            btn.next().html("<a href='#'>下电</a>");
          }
          else
          {
             btn.parent().prev().html('已下电');
             btn.html("<span>下电</span>");
             btn.next().html("<a href='#'>上电</a>");
          }
        },
        checkallx86:function()
        {
            var ckstatu=this.$("#ckall").is(':checked');
            this.$("input[type='checkbox']").each(function(i,ck) {
              ck.checked=ckstatu;
           });
        },
       showaddpage:function()
       {
          app.navigate('#ops/x86/add', {trigger: true});
       },
       showeditpage:function(e)
       {
         app.returnPageIndex=this.currentPageIndex;
         app.returnPageSize=app.pageSize;
         var editid=(e.currentTarget).getAttribute('dataid');
         app.navigate('#ops/x86/edit/'+editid, {trigger: true});
       },
       deletex86:function(e)
       {
          var deleid=(e.currentTarget).getAttribute('dataid');
          this.phymachine.set({"id":deleid});
          if(confirm('确实要删除id为'+deleid+"的数据吗?"))
          {
             this.phymachine.destroy({
                 success:_.bind(function(model,response, options)
                  {
                    var removemodel=this.phymachinesCollection.get(deleid);
                    this.phymachinesCollection.remove(removemodel);
                    app.totalrows=parseInt(app.totalrows-1);
                    this.updateCollection(1);
                    alert("删除成功!");
                    this.getRenderData();
                    this.paginationView=new pagingView({"currentpage": this.currentPageIndex});
                  },this),error:function(model, response, options)
                  {
                    alert('删除出现异常!');
                  }
             });
          }
       },
       updateCollection:function(arg){

         var idsarr=[];
         if(!arg)
         {
            this.$("input[type='checkbox']").each(function(i,ck) {
              if(ck.checked)
              {
                 if(ck.value!="all")  //all代表全选check的value
                    idsarr.push(ck.value);
              }
            })

           for(var t=0;t<idsarr.length;t++)
            {
              var removemodel=this.phymachinesCollection.get(idsarr[t]);
              this.phymachinesCollection.remove(removemodel);
            }
             app.totalrows=this.phymachinesCollection.length==0?parseInt(app.totalrows-idsarr.length):this.phymachinesCollection.length;
          }

           //处理把整页数据都批量删除完毕，分页索引设置当前索引减1
           //每个页面展示的数据不一定都是pagesize,也有可能小于它
           var deletelength=idsarr.length;
           if(arg){deletelength=1;} //删除单条按钮操作
           if(deletelength>=this.currentPageLength)
           {
             var pageIndex=parseInt(app.currentPageIndex-1);
             this.currentPageIndex=pageIndex<=0?1:pageIndex;
           }
       },
       poweronIds:function()
       {
           var idsarr=[];
           this.$("input[type='checkbox']").each(function(i,ck) {
            if(ck.checked)
            {
              if(ck.value!="all")  //all代表全选check的value
                 idsarr.push(ck.value);
            }
          })
          if(idsarr.length==0){
            alert("请选择需要上电的物理机!");
            return;
          } 

          var loadview=new commonloadview();
          $('#modal-container').after(loadview.render().el);
          $.ajax({
                type: "POST",
                url: "/api/phymachine/poweronIds",
                data: "ids="+idsarr,
                success:_.bind(function(msg){
                   var obj=JSON.parse(msg);
                   if(obj.result)
                   {
                     $('#modal-container').next().remove();
                     alert('批量上电成功!');
                     this.getRenderData();
                     this.paginationView=new pagingView({"currentpage": this.currentPageIndex});
                   }
                   else
                   {
                     $('#modal-container').next().remove();
                     alert('批量上电成功!');
                   }
                },this),
                error:function()
                {
                  $('#modal-container').next().remove();
                  alert('批量下电失败!');
                }
           });
       },
       poweroffIds:function()
       {
           var idsarr=[];
           this.$("input[type='checkbox']").each(function(i,ck) {
            if(ck.checked)
            {
              if(ck.value!="all")  //all代表全选check的value
                 idsarr.push(ck.value);
            }
          })
          if(idsarr.length==0){
            alert("请选择需要下电的物理机!");
            return;
          }

          var loadview=new commonloadview();
          $('#modal-container').after(loadview.render().el);
          $.ajax({
                type: "POST",
                url: "/api/phymachine/poweroffIds",
                data: "ids="+idsarr,
                success:_.bind(function(msg){
                   var obj=JSON.parse(msg);
                   if(obj.result)
                   {
                     $('#modal-container').next().remove();
                     alert('批量下电成功!');
                     this.getRenderData();
                     this.paginationView=new pagingView({"currentpage": this.currentPageIndex});
                   }
                   else
                   {
                    $('#modal-container').next().remove();
                     alert('批量下电成功!');
                   }
                },this),
                error:function()
                {
                  $('#modal-container').next().remove();
                  alert('批量下电失败!');
                }
           });
       },
       checkmahinestatus:function()
       {
          var idsarr=[];
          this.$("input[type='checkbox']").each(function(i,ck) {
            if(ck.checked)
            {
              if(ck.value!="all")  //all代表全选check的value
                 idsarr.push(ck.value);
            }
          })
          if(idsarr.length==0){
            alert("请选择需要被更新的物理机!");
            return;
          }

          var loadview=new commonloadview();
          $('#modal-container').after(loadview.render().el);
          $.ajax({
                type: "POST",
                url: "/api/phymachine/powerstatuIds",
                data: "ids="+idsarr,
                success:_.bind(function(msg){
                   var obj=JSON.parse(msg);
                   if(obj.result)
                   {
                     $('#modal-container').next().remove();
                     alert('批量更新成功!');
                     this.getRenderData();
                     this.paginationView=new pagingView({"currentpage": this.currentPageIndex});
                   }
                   else
                   {
                    $('#modal-container').next().remove();
                     alert('批量更新成功!');
                   }
                },this),
                error:function()
                {
                  $('#modal-container').next().remove();
                  alert('批量更新失败!');
                }
           });
       },
       deleIds:function()
       {
          var idsarr=[];
          this.$("input[type='checkbox']").each(function(i,ck) {
            if(ck.checked)
            {
              if(ck.value!="all")  //all代表全选check的value
                 idsarr.push(ck.value);
            }
          })
          if(idsarr.length==0){
            alert("请选择需要被删除的数据!");
            return;
          }
          if(confirm('确实要删除id为'+idsarr+"的数据吗?"))
          {
            for(var t=0;t<idsarr.length;t++)
            {
               this.phymachine.set({"id":idsarr[t]});
                if(t==idsarr.length-1)
               {
                this.phymachine.destroy({
                   success:_.bind(function(model,response, options)
                  {

                    alert('批量删除成功!');
                    this.updateCollection(0);
                    this.getRenderData();
                    this.paginationView=new pagingView({"currentpage": this.currentPageIndex});
                    //删除数据之后分页组件显示为第二页，但数据显示的是第一页
                    //导致出现了问题
                    //在哪个页面删除后，刷新数据后，必须保留当前的页面索引
                  },this),error:function(model, response, options)
                  {
                    alert('批量删除出现异常!');
                  }
                });
               }
               else
               {
                this.phymachine.destroy();
               }
            }
          }
       }
  });

 var commonloadview = Backbone.View.extend({
     id:'modalshow',
     className:'modal-backdrop fade in',
     render:function()
    {
      this.$el.html("<img style='margin-top:18%;margin-left:45%' src='/static/img/cloud-loader.gif'/>");
      return this;
    }
 });

  return x86Page;
});
