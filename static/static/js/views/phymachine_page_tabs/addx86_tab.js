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
    'backbone',
    'utils',
    'text!templates/phymachine/addx86.html'
],
function(_, i18n, models,Backbone,utils,osTemplate) {
    'use strict';

    var ReleasesPage = Backbone.View.extend({
        template: _.template(osTemplate),
        events:{
            'click #btn-cancel':'gotoListPage',
            'blur input':"validate",
            'click #btn-save':"savemodel"
        },
        initialize:function(options){
          this.editid=options.screenOptions[1];
          this.phymachine=new models.Phymachine();
        },
        gotoListPage:function()
        {
          //{replace:true} 不会跳转页面，必须使用{trigger:true}
          app.navigate('ops/x86',{trigger:true});
        },
        validate:function(e)
        {
           var ele=e!=null?this.$(e.currentTarget):$(arguments[1]);
           var datatype=ele.attr("data-type");
           var data=ele.val();
           
           if(_.isEmpty(data.replace(/(^\s*)|(\s*$)/g, "")))
           {
             //console.log(ele);
             this.handlerrormsg(ele,'不能为空');
           }
           else
           {
             if(datatype=="mac")
             {
               if(!data.match(utils.regexes.mac))
               {
                 this.handlerrormsg(ele,'格式输入有误');
               }
               else
               {
                 //this.handlerrormsg(ele);
                  if(this.editid)
                    {
                       this.checkpropsrepeat(4,data,this.editid,ele);
                    }
                    else
                    {
                      this.checkpropsrepeat(4,data,0,ele);
                    } 
               }
             }
             else if(datatype=="ip")
             {
                if(!data.match(utils.regexes.ip))
                {
                  this.handlerrormsg(ele,'格式输入有误'); //输入错误
                }
                else
                {
                  //this.handlerrormsg(ele);
                   var input_name=ele.attr('id');
                   if(input_name=="txt_ip")
                   {
                     if(this.editid)
                    {
                       this.checkpropsrepeat(2,data,this.editid,ele);
                    }
                    else
                    {
                      this.checkpropsrepeat(2,data,0,ele);
                    } 
                   }
                  else if(input_name=="txt_mp_ip")
                   {
                     if(this.editid)
                    {
                       this.checkpropsrepeat(3,data,this.editid,ele);
                    }
                    else
                    {
                      this.checkpropsrepeat(3,data,0,ele);
                    } 
                   }
                  else
                   {
                    this.handlerrormsg(ele);
                   }
                }
             }
             else
             {
                //主机名称不能包含特殊字符
                var input_name=ele.attr('id');
                if(input_name=="txt_name")
                {
                  //[~#^$@%&!、\\*\s]需要判断什么特殊字符,在此里面添加即可
                  if(/[~#^$@%&!、\\\/*\s]/gi.test(data))
                  {
                     this.handlerrormsg(ele,'不能包含特殊字符'); 
                  }
                  else
                  {
                    //this.handlerrormsg(ele); //输入正确的格式
                    //在这里验证主机名是否已经存在
                    if(this.editid)
                    {
                       this.checkpropsrepeat(1,data,this.editid,ele);
                    }
                    else
                    {
                      this.checkpropsrepeat(1,data,0,ele);
                    } 
                  }
                }
                else
                {
                  this.handlerrormsg(ele); //输入正确的格式
                }
             }
           }
        },
        checkpropsrepeat:function(prop,value,id,ele){
            var url="";
            var data="";
            if(prop==1)
            {
              url="/api/phymachine/checkname/";
              data="name="+value+"&id="+id;
            }
            else if(prop==2)
            {
              url="/api/phymachine/checkip/";
              data="ip="+value+"&id="+id;
            }
            else if(prop==3)
            {
              url="/api/phymachine/checkmip/";
              data="mip="+value+"&id="+id;
            }
            else 
            {
              url="/api/phymachine/checkmac/";
              data="mac="+value+"&id="+id;
            }
            $.ajax({
                type: "GET",
                url: url,
                data: data,
                success: _.bind(function(msg){
                  var obj=JSON.parse(msg);
                  var count=parseInt(obj.count);
                  if(count>0)
                    {
                      this.handlerrormsg(ele,'已经存在');
                    }
                    else
                    {
                      this.handlerrormsg(ele);
                    }
                },this),
                error:function(msg)
                {
                  alert('验证失败!');
                }
            });
        },
        handlerrormsg:function(obj,msg)
        {
           var title=obj.parent().prev().html();
           var discontrol=obj.parent().next().children(":first");
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
        savemodel:function(){
           var parentScope=this;
           this.$("#form1 input").each(function(){
                parentScope.validate(null,this);
           });
          var errors=this.$("#form1 input.error").length;
          if(errors>0)
          {
            return;
          }
          else
          {
            this.$("#btn-save").attr('disabled',"true");
            var phymachinemodel=new models.Phymachine();
            if(this.editid) {phymachinemodel.set({"id": Number(this.editid)});}
            phymachinemodel.set({
              "name":$("#txt_name").val(),
              "ip":$("#txt_ip").val(),
              "mp_ip":$("#txt_mp_ip").val(),
              "mp_username":$("#txt_mp_username").val(),
              "mp_passwd":$("#txt_mp_passwd").val(),
              "cabinet":$("#txt_cabinet").val(),
              "gene_room":$("#txt_gene_room").val(),
              "mac":$("#txt_mac").val(),
              "use_type":$("#txt_use_type").val(),
              "power_status":1,
              "operation_status":3
            });
            
            phymachinemodel.save(null,{
              success:_.bind(function(model,response,options)
              {
                  alert('保存成功');
                  this.gotoListPage();
              },this),
              error:function(model,response,options){
                  alert("保存失败");
                  this.$("#btn-save").removeAttr("disabled");
              }
            });
          }
        },
        render:function()
        {   
            //this.$("#txt_use_type").html();
            this.phymachine.set({"id":this.editid});
            this.phymachine.fetch({
                 success:_.bind(function(model,response, options)
                  {
                     //$(this.el).html(this.template({model:model.toJSON()}));
                      var objItemValue=model.get('use_type');
                      var mac=model.get('mac');
                      this.set_select_item(model,objItemValue,mac);
                  },this),error:function(model, response, options)
                  {
                    alert('出现异常');
                  }
             });
            return  this;
        },
        set_select_item:function(model,objItemValue,mac)
        {    
             var nodesCollection=new models.Nodes();
             $.when(nodesCollection.fetch()).done(_.bind(function(){
                 var nodes=nodesCollection.nodesFiterMac(mac);
                 //var status=nodes[0].get('status');
                 var objselect=this.$("#txt_use_type");
                 var parentScope=this;
                 var selectopt;
                 if(nodes[0] && nodes[0].get('status') !='discover')
                 {
                    var valuedesc="未分配";
                    if(objItemValue==1)
                    {
                      valuedesc="原生openstack";
                    }
                    else if(objItemValue==2)
                    {
                      valuedesc="BC-CLOUDMASTER";
                    }
                    else if(objItemValue==3)
                    {
                      valuedesc="BC-EBS";
                    }
                    else if(objItemValue==4)
                    {
                      valuedesc="定制化openstack";
                    }
                    else if(objItemValue==5)
                    {
                      valuedesc="BC-ONEST";
                    }
                    else if(objItemValue==6)
                    {
                      valuedesc="BC-OP";
                    }
                     //htmlstr="<option value="+objItemValue+">"+valuedesc+"</option>";
                    //this.$("#txt_use_type").html(htmlstr);
                 }
                else
                {
                 selectopt = objItemValue;
                }

              if(selectopt)
              {
                $(this.el).html(this.template({model:model.toJSON(),objItemValue:objItemValue,valuedesc:valuedesc,selectopt:selectopt}));
              }
              else if(model.get('use_type'))
              {
                $(this.el).html(this.template({model:model.toJSON(),objItemValue:objItemValue,valuedesc:valuedesc,selectopt:"edit"}));
              }
              else
              {
                $(this.el).html(this.template({model:model.toJSON(),objItemValue:objItemValue,valuedesc:valuedesc,selectopt:"add"}));
              }
             },this))
        }
   });
  return ReleasesPage;
});