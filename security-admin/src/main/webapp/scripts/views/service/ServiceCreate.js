/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

 
/* 
 * Repository/Service create view
 */

define(function(require){
    'use strict';

	var Backbone		= require('backbone');
	var App				= require('App');

	var XAUtil			= require('utils/XAUtils');
	var XAEnums			= require('utils/XAEnums');
	var XALinks 		= require('modules/XALinks');
	var localization	= require('utils/XALangSupport');
	var ServiceForm		= require('views/service/ServiceForm');
	var RangerServiceDef	= require('models/RangerServiceDef');
	var ServiceCreateTmpl = require('hbs!tmpl/service/ServiceCreate_tmpl');

	var ServiceCreate = Backbone.Marionette.Layout.extend(
	/** @lends ServiceCreate */
	{
		_viewName : 'ServiceCreate',

		template: ServiceCreateTmpl,
		
		templateHelpers : function(){
			return { editService : this.editService};
		},
        
		breadCrumbs :function(){
			if(this.model.isNew())
				return [XALinks.get('RepositoryManager'), XALinks.get('ServiceCreate', {model:this.model})];
			else
				return [XALinks.get('RepositoryManager'), XALinks.get('ServiceEdit',{model:this.model})];
		},        

		/** Layout sub regions */
		regions: {
			'rForm' :'div[data-id="r_form"]'
		},

		/** ui selector cache */
		ui: {
			'btnSave'	: '[data-id="save"]',
			'btnCancel' : '[data-id="cancel"]',
			'btnDelete' : '[data-id="delete"]',
			'btnTestConn' : '[data-id="testConn"]'
		},

		/** ui events hash */
		events: function() {
			var events = {};
			events['click ' + this.ui.btnSave]		= 'onSave';
			events['click ' + this.ui.btnCancel]	= 'onCancel';
			events['click ' + this.ui.btnDelete]	= 'onDelete';
			events['click ' + this.ui.btnTestConn]	= 'onTestConnection';
			return events;
		},

		/**
		 * intialize a new ServiceCreate Layout 
		 * @constructs
		 */
		initialize: function(options) {
			console.log("initialized a ServiceCreate Layout");
			_.extend(this, _.pick(options, 'serviceTypeId'));
			this.initializeServiceDef();
			/*if(! this.model.isNew()){
				this.setupModel();
			}*/
			this.form = new ServiceForm({
				model :	this.model,
				rangerServiceDefModel : this.rangerServiceDefModel,
				template : require('hbs!tmpl/service/ServiceForm_tmpl')
			});
			this.editService = this.model.has('id') ? true : false;

			this.bindEvents();
		},
		initializeServiceDef : function(){
		    this.rangerServiceDefModel	= new RangerServiceDef({ id : this.serviceTypeId});
			this.rangerServiceDefModel.fetch({
			   cache : false,
			   async : false
			});

		},
		setupModel : function(){
		},

		/** all events binding here */
		bindEvents : function(){
			/*this.listenTo(this.model, "change:foo", this.modelChanged, this);*/
			/*this.listenTo(communicator.vent,'someView:someEvent', this.someEventHandler, this)'*/
		},

		/** on render callback */
		onRender: function() {
			if(!this.editService){
				this.ui.btnDelete.hide();
				this.ui.btnSave.html('Add');
			} else {
				
			//	XAUtil.preventNavigation(localization.tt('dialogMsg.preventNavRepositoryForm'));
			}
			this.rForm.show(this.form);
			this.rForm.$el.dirtyFields();
			XAUtil.preventNavigation(localization.tt('dialogMsg.preventNavRepositoryForm'),this.rForm.$el);
			this.initializePlugins();
		},

		/** all post render plugin initialization */
		initializePlugins: function(){
		},

		onSave: function(){
			var errors = this.form.commit({validate : false});
			if(! _.isEmpty(errors)){
				return;
			}
			this.form.formValidation();
			this.saveService();

		},
		saveService : function(){
			var that = this;
			this.form.beforeSave();
			XAUtil.blockUI();
			this.model.save({},{
				wait: true,
				success: function () {
					XAUtil.blockUI('unblock');
					XAUtil.allowNavigation();
					var msg = that.editService ? 'Service updated successfully' :'Service created successfully';
					XAUtil.notifySuccess('Success', msg);
					
					if(that.editService){
						App.appRouter.navigate("#!/policymanager",{trigger: true});
						return;
					}
					
					App.appRouter.navigate("#!/policymanager",{trigger: true});
					
				},
				error: function (model, response, options) {
					XAUtil.blockUI('unblock');
					if ( response && response.responseJSON && response.responseJSON.msgDesc){
						if(response.responseJSON.msgDesc == "serverMsg.fsDefaultNameValidationError"){
							that.form.fields.fsDefaultName.setError(localization.tt(response.responseJSON.msgDesc));
							XAUtil.scrollToField(that.form.fields.fsDefaultName.$el);
						}else if(response.responseJSON.msgDesc == "Repository Name already exists"){
							response.responseJSON.msgDesc = "serverMsg.repositoryNameAlreadyExistsError";
							that.form.fields.name.setError(localization.tt(response.responseJSON.msgDesc));
							XAUtil.scrollToField(that.form.fields.name.$el);
						}else if(response.responseJSON.msgDesc == "XUser already exists"){
							response.responseJSON.msgDesc = "serverMsg.userAlreadyExistsError";
							that.form.fields.userName.setError(localization.tt(response.responseJSON.msgDesc));
							XAUtil.scrollToField(that.form.fields.userName.$el);
						}else
							XAUtil.notifyError('Error', response.responseJSON.msgDesc);
					}else
						XAUtil.notifyError('Error', 'Error creating Service!');
					console.log("error");
				}
			});
		},
		onDelete :function(){
			var that = this;
			XAUtil.confirmPopup({
				//msg :localize.tt('msg.confirmDelete'),
				msg :'Are you sure want to delete ?',
				callback : function(){
					XAUtil.blockUI();
					
					that.model.destroy({
						success: function(model, response) {
							XAUtil.blockUI('unblock');
							XAUtil.allowNavigation();
							XAUtil.notifySuccess('Success', 'Service delete successfully');
							App.appRouter.navigate("#!/policymanager",{trigger: true});
						},
						error: function (model, response, options) {
							XAUtil.blockUI('unblock');
							if ( response && response.responseJSON && response.responseJSON.msgDesc){
									XAUtil.notifyError('Error', response.responseJSON.msgDesc);
							}else{
								XAUtil.notifyError('Error', 'Error occured while deleting service!');
							}
						}
					});
					
				}
			});
		},
		onTestConnection : function(){
			var errors = this.form.commit({validate : false});
			if(! _.isEmpty(errors)){
				return;
			}
			this.form.beforeSave();
			this.model.testConfig(this.model,{
					//wait: true,
					success: function (msResponse, options) {
						if(msResponse.statusCode){
							if(!_.isUndefined(msResponse) && !_.isUndefined(msResponse.msgDesc)){ 
								var popupBtnOpts;
                               if(!_.isEmpty(msResponse.msgDesc)){
                            	   if(_.isArray(msResponse.messageList) && !_.isUndefined(msResponse.messageList[0].message)
                            			   && !_.isEmpty(msResponse.messageList[0].message)){
	                            		   popupBtnOpts = [{
	                            			   label: "Show More..",
	                            			   callback:function(e){
	                            				   console.log(e)
	                            				   if($(e.currentTarget).text() == 'Show More..'){
                        							   var div = '<div class="showMore connection-error-font"><br>'+msResponse.messageList[0].message.split('\n').join('<br>')+'</div>'
                        							   $(e.delegateTarget).find('.modal-body').append(div)
                        							   $(e.currentTarget).html('Show Less..')
	                            				   }else{
	                            					   $(e.delegateTarget).find('.showMore').remove();
	                            					   $(e.currentTarget).html('Show More..')
	                            				   }
	                            				   return false;
	                            			   }
	                            		   }, {
	                            			   label: "OK",
	                            			   callback:function(){}
	                            		   }];
                            	   }else{
                            		   		popupBtnOpts = [{label: "OK",
                            		   			callback:function(){}
                            		   		}];
                            	   }
                                   var msgHtml = '<b>Connection Failed.</b></br>'+msResponse.msgDesc;
                                   bootbox.dialog(msgHtml, popupBtnOpts);
								}else{
										bootbox.alert("Connection Failed.");
								}
							}else{
								bootbox.alert("Connection Failed.");
							}
						}
						else
							bootbox.alert("Connected Successfully.");
					},
					error: function (msResponse, options) {
						bootbox.alert("Connection Failed.");
					}	
				});
		},
		onCancel : function(){
			XAUtil.allowNavigation();
			App.appRouter.navigate("#!/policymanager",{trigger: true});
		},
		/** on close */
		onClose: function(){
			XAUtil.allowNavigation();
		}
	});

	return ServiceCreate; 
});
