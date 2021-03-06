#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License. See accompanying LICENSE file.
#

import os
import re
import sys
import errno
import shlex
import logging
import subprocess
import fileinput
from os.path import basename
from subprocess import Popen,PIPE
from datetime import date
globalDict = {}

def check_output(query):
	p = subprocess.Popen(query, stdout=subprocess.PIPE)
	output = p.communicate ()[0]
	return output

def log(msg,type):
	if type == 'info':
		logging.info(" %s",msg)
	if type == 'debug':
		logging.debug(" %s",msg)
	if type == 'warning':
		logging.warning(" %s",msg)
	if type == 'exception':
		logging.exception(" %s",msg)
	if type == 'error':
		logging.error(" %s",msg)

def populate_global_dict():
	global globalDict
	read_config_file = open(os.path.join(os.getcwd(),'install.properties'))
	for each_line in read_config_file.read().split('\n') :
		if len(each_line) == 0 : continue
		if re.search('=', each_line):
			key , value = each_line.strip().split("=",1)
			key = key.strip()

			if 'PASSWORD' in key:
				jceks_file_path = os.path.join(os.getenv('RANGER_HOME'), 'jceks','ranger_db.jceks')
				statuscode,value = call_keystore(library_path,key,'',jceks_file_path,'get')
				if statuscode == 1:
					value = ''
			value = value.strip()
			globalDict[key] = value


class BaseDB(object):

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password):	
		log("[I] ---------- Creating user ----------", "info")

	def check_connection(self, db_name, db_user, db_password):
		log("[I] ---------- Verifying DB connection ----------", "info")

	def create_db(self, root_user, db_root_password, db_name, db_user, db_password):
		log("[I] ---------- Verifying database ----------", "info")

	def check_table(self, db_name, db_user, db_password, TABLE_NAME):
		log("[I] ---------- Verifying table ----------", "info")

	def import_db_file(self, db_name, db_user, db_password, file_name):
		log("[I] ---------- Importing db schema ----------", "info")

	def upgrade_db(self, db_name, db_user, db_password, DBVERSION_CATALOG_CREATION):
		self.import_db_file(db_name, db_user, db_password, DBVERSION_CATALOG_CREATION)
		log("[I] Baseline DB upgraded successfully", "info")

	def apply_patches(self, db_name, db_user, db_password, PATCHES_PATH):
		#first get all patches and then apply each patch
		if not os.path.exists(PATCHES_PATH):
			log("[I] No patches to apply!","info")
		else:
			# files: coming from os.listdir() sorted alphabetically, thus not numerically
			files = os.listdir(PATCHES_PATH)
			if files:
				sorted_files = sorted(files, key=lambda x: str(x.split('.')[0]))
				for filename in sorted_files:
					currentPatch = PATCHES_PATH + "/"+filename
					self.import_db_patches(db_name, db_user, db_password, currentPatch)
			else:
				log("[I] No patches to apply!","info")

	def create_auditdb_user(self, xa_db_host , audit_db_host , db_name ,audit_db_name, xa_db_root_user, audit_db_root_user, db_user, audit_db_user, xa_db_root_password, audit_db_root_password, db_password, audit_db_password, file_name, TABLE_NAME):
		log("[I] ----------------- Create audit user ------------", "info")



class MysqlConf(BaseDB):
	# Constructor
	def __init__(self, host,SQL_CONNECTOR_JAR,JAVA_BIN):
		self.host = host
		self.SQL_CONNECTOR_JAR = SQL_CONNECTOR_JAR
		self.JAVA_BIN = JAVA_BIN

	def get_jisql_cmd(self, user, password ,db_name):
		#TODO: User array for forming command
		jisql_cmd = "%s -cp %s:jisql/lib/* org.apache.util.sql.Jisql -driver mysqlconj -cstring jdbc:mysql://%s/%s -u %s -p %s -noheader -trim -c \;" %(self.JAVA_BIN,self.SQL_CONNECTOR_JAR,self.host,db_name,user,password)
		return jisql_cmd

	def verify_user(slef, root_user, db_root_password, host, db_user, get_cmd):
		log("[I] Verifying user " + db_user , "info")
		query = get_cmd + " -query \"select user from mysql.user where user='%s' and host='%s';\"" %(db_user,host)
		output = check_output(shlex.split(query))
		if output.strip(db_user + " |"):
			return True
		else:
			return False

	def check_connection(self, db_name, db_user, db_password):
		log("[I] Checking connection..", "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		query = get_cmd + " -query \"SELECT version();\""
		output = check_output(shlex.split(query))
		if output.strip('Production  |'):
			log("[I] Checking connection passed.", "info")
			return True
		else:
			log("[E] Can't establish connection!! Exiting.." ,"error")
			sys.exit(1)

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password):
		if self.check_connection('mysql', root_user, db_root_password):
			hosts_arr =["%", "localhost"]
			for host in hosts_arr:
				get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
				if self.verify_user(root_user, db_root_password, host, db_user, get_cmd):
					log("[I] MySQL user " + db_user + " already exists for host " + host, "info")
				else:
					log("[I] MySQL user " + db_user + " does not exists for host " + host, "info")
					if db_password == "":
						query = get_cmd + " -query \"create user '%s'@'%s';\"" %(db_user, host)
						ret = subprocess.check_call(shlex.split(query))
						if ret == 0:
							if self.verify_user(root_user, db_root_password, host, db_user, get_cmd):
								log("[I] MySQL user " + db_user +" created for host " + host ,"info")
							else:
								log("[E] Creating MySQL user " + db_user +" failed","error")
								sys.exit(1)
					else:
						query = get_cmd + " -query \"create user '%s'@'%s' identified by '%s';\"" %(db_user, host, db_password)
						ret = subprocess.check_call(shlex.split(query))
						if ret == 0:
							if self.verify_user(root_user, db_root_password, host, db_user, get_cmd):
								log("[I] MySQL user " + db_user +" created for host " + host ,"info")
							else:
								log("[E] Creating MySQL user " + db_user +" failed","error")
								sys.exit(1)
						else:
							log("[E] Creating MySQL user " + db_user +" failed","error")
							sys.exit(1)


	def verify_db(self, root_user, db_root_password, db_name):
		log("[I] Verifying database " + db_name , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
		query = get_cmd + " -query \"show databases like '%s';\"" %(db_name)
		output = check_output(shlex.split(query))
		if output.strip(db_name + " |"):
			return True
		else:
			return False


	def create_db(self, root_user, db_root_password, db_name, db_user, db_password):
		if self.verify_db(root_user, db_root_password, db_name):
			log("[I] Database "+db_name + " already exists.","info")
		else:
			log("[I] Database does not exist! Creating database " + db_name,"info")
			get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
			query = get_cmd + " -query \"create database %s;\"" %(db_name)
			ret = subprocess.check_call(shlex.split(query))
			if ret != 0:
				log("[E] Database creation failed!!","error")
				sys.exit(1)
			else:
				if self.verify_db(root_user, db_root_password, db_name):
					log("[I] Creating database " + db_name + " succeeded", "info")
					return True
				else:
					log("[E] Database creation failed!!","error")
					sys.exit(1)


	def grant_xa_db_user(self, root_user, db_name, db_user, db_password, db_root_password, is_revoke):
		hosts_arr =["%", "localhost"]
		for host in hosts_arr:
			get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
			if self.verify_user(root_user, db_root_password, host, db_user, get_cmd):
				log("[I] MySQL user " + db_user + " exists for host " + host, "info")
			else:
				log("[I] MySQL user " + db_user + " does not exists for host " + host, "error")
				sys.exit(E)
			if self.verify_db(root_user, db_root_password, db_name):
				log("[I] Database "+db_name + " exists!","info")
			else:
				log("[I] Database "+db_name + " does not exists!","error")
				sys.exit(E)

		if is_revoke:
			for host in hosts_arr:
				get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
				query = get_cmd + " -query \"REVOKE ALL PRIVILEGES,GRANT OPTION FROM '%s'@'%s';\"" %(db_user, host)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					query = get_cmd + " -query \"FLUSH PRIVILEGES;\""
					ret = subprocess.check_call(shlex.split(query))
					if ret != 0:
						sys.exit(1)
				else:
					sys.exit(1)

		for host in hosts_arr:
			log("[I] ---------------Granting privileges TO user '"+db_user+"'@'"+host+"' on db '"+db_name+"'-------------" , "info")
			get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'mysql')
			query = get_cmd + " -query \"grant all privileges on %s.* to '%s'@'%s' with grant option;\"" %(db_name,db_user, host)
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				log("[I] ---------------FLUSH PRIVILEGES -------------" , "info")
				query = get_cmd + " -query \"FLUSH PRIVILEGES;\""
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					log("[I] Privileges granted to '" + db_user + "' on '"+db_name+"'", "info")
				else:
					log("[E] Granting privileges to '" +db_user+"' failed on '"+db_name+"'", "error")
					sys.exit(1)
			else:
				log("[E] Granting privileges to '" +db_user+"' failed on '"+db_name+"'", "error")
				sys.exit(1)


	def grant_audit_db_user(self, audit_root_user, audit_db_name, audit_db_user, audit_db_password, audit_db_root_password,TABLE_NAME, is_revoke):
		hosts_arr =["%", "localhost"]
		if is_revoke == True:
			for host in hosts_arr:
				get_cmd = self.get_jisql_cmd(audit_root_user, audit_db_root_password, 'mysql')
				query = get_cmd + " -query \"REVOKE ALL PRIVILEGES,GRANT OPTION FROM '%s'@'%s';\"" %(audit_db_user, host)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					query = get_cmd + " -query \"FLUSH PRIVILEGES;\""
					ret = subprocess.check_call(shlex.split(query))
					if ret != 0:
						sys.exit(1)
				else:
					sys.exit(1)

		for host in hosts_arr:
			log("[I] ---------------Granting privileges TO '"+ audit_db_user + "' on '" + audit_db_name+"'-------------" , "info")
			get_cmd = self.get_jisql_cmd(audit_root_user, audit_db_root_password, 'mysql')
			query = get_cmd + " -query \"GRANT INSERT ON %s.%s TO '%s'@'%s';\"" %(audit_db_name,TABLE_NAME,audit_db_user,host)
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				get_cmd = self.get_jisql_cmd(audit_root_user, audit_db_root_password, 'mysql')
				query = get_cmd + " -query \"FLUSH PRIVILEGES;\""
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					log("[I] Granting privileges to '" + audit_db_user+"' done on '"+ audit_db_name+"'", "info")
				else:
					log("[E] Granting privileges to '" +audit_db_user+"' failed on '" + audit_db_name+"'", "error")
					sys.exit(1)
			else:
				log("[E] Granting privileges to '" + audit_db_user+"' failed on '" + audit_db_name+"'", "error")
				sys.exit(1)


	def import_db_file(self, db_name, db_user, db_password, file_name):
		name = basename(file_name)
		if os.path.isfile(file_name):
			log("[I] Importing db schema to database " + db_name + " from file: " + name,"info")
			get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
			query = get_cmd + " -input %s" %file_name
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				log("[I] "+name + " DB schema imported successfully","info")
			else:
				log("[E] "+name + " DB schema import failed!","error")
				sys.exit(1)
		else:
			log("[E] DB schema file " + name+ " not found","error")
			sys.exit(1)


	def import_db_patches(self, db_name, db_user, db_password, file_name):
		name = basename(file_name)
		if os.path.isfile(file_name):
			version = name.split('-')[0]
			log("[I] Executing patch on  " + db_name + " from file: " + name,"info")
			get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
			query = get_cmd + " -query \"select version from x_db_version_h where version = '%s' and active = 'Y';\"" %(version)
			output = check_output(shlex.split(query))
			if output.strip(version + " |"):
				log("[I] Patch "+ name  +" is already applied" ,"info")
			else:
				get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
				query = get_cmd + " -input %s" %file_name
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					log("[I] "+name + " patch applied","info")
					query = get_cmd + " -query \"insert into x_db_version_h (version, inst_at, inst_by, updated_at, updated_by) values ('%s', now(), user(), now(), user()) ;\"" %(version)
					ret = subprocess.check_call(shlex.split(query))
					if ret == 0:
						log("[I] Patch version updated", "info")
					else:
						log("[E] Updating patch version failed", "error")
						sys.exit(1)
				else:
					log("[E] "+name + " import failed!","error")
					sys.exit(1)
		else:
			log("[I] Import " +name + " file not found","error")
			sys.exit(1)


	def check_table(self, db_name, db_user, db_password, TABLE_NAME):
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		query = get_cmd + " -query \"show tables like '%s';\"" %(TABLE_NAME)
		output = check_output(shlex.split(query))
		if output.strip(TABLE_NAME + " |"):
			log("[I] Table " + TABLE_NAME +" already exists in database '" + db_name + "'","info")
			return True
		else:
			log("[I] Table " + TABLE_NAME +" does not exist in database " + db_name + "","info")
			return False

	def create_auditdb_user(self, xa_db_host, audit_db_host, db_name, audit_db_name, xa_db_root_user, audit_db_root_user, db_user, audit_db_user, xa_db_root_password, audit_db_root_password, db_password, audit_db_password, file_name, TABLE_NAME, DBA_MODE):
		if DBA_MODE == "TRUE" :
			log("[I] --------- Setup audit user ---------","info")
			self.create_rangerdb_user(audit_db_root_user, audit_db_user, audit_db_password, audit_db_root_password)
			hosts_arr =["%", "localhost"]
			for host in hosts_arr:
				get_cmd = self.get_jisql_cmd(audit_db_root_user, audit_db_root_password ,'mysql')
				query = get_cmd + " -query \"REVOKE ALL PRIVILEGES,GRANT OPTION FROM '%s'@'%s';\"" %(audit_db_user, host)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					query = get_cmd + " -query \"FLUSH PRIVILEGES;\""
					ret = subprocess.check_call(shlex.split(query))
					if ret != 0:
						sys.exit(1)
				else:
					sys.exit(1)
			self.create_db(audit_db_root_user, audit_db_root_password, audit_db_name, db_user, db_password)
			self.grant_xa_db_user(audit_db_root_user, audit_db_name, db_user, db_password, audit_db_root_password, False)

		log("[I] --------- Check admin user connection ---------","info")
		self.check_connection(audit_db_name, db_user, db_password)
		#log("[I] --------- Check audit user connection ---------","info")
		#self.check_connection(audit_db_name, audit_db_user, audit_db_password)
		log("[I] --------- Check audit table exists --------- ","info")
		output = self.check_table(audit_db_name, db_user, db_password, TABLE_NAME)
		if output == False:
			self.import_db_file(audit_db_name ,db_user, db_password, file_name)
		if DBA_MODE == "TRUE":
			if audit_db_user == db_user:
				is_revoke = False
			else:
				is_revoke = True
			self.grant_audit_db_user(audit_db_root_user, audit_db_name, audit_db_user, audit_db_password, audit_db_root_password,TABLE_NAME, is_revoke)


class OracleConf(BaseDB):
	# Constructor
	def __init__(self, host, SQL_CONNECTOR_JAR, JAVA_BIN):
		self.host = host 
		self.SQL_CONNECTOR_JAR = SQL_CONNECTOR_JAR
		self.JAVA_BIN = JAVA_BIN

	def get_jisql_cmd(self, user, password):
		#TODO: User array for forming command
		jisql_cmd = "%s -cp %s:jisql/lib/* org.apache.util.sql.Jisql -driver oraclethin -cstring jdbc:oracle:thin:@%s -u '%s' -p '%s' -noheader -trim" %(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, self.host, user, password)
		return jisql_cmd

	def check_connection(self, db_name, db_user, db_password):
		log("[I] Checking connection", "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password)
		query = get_cmd + " -c \; -query \"select * from v$version;\""
		output = check_output(shlex.split(query))
		if output.strip('Production  |'):
			log("[I] Connection success", "info")
			return True
		else:
			log("[E] Can't establish connection!", "error")
			sys.exit(1)

	def verify_user(self, root_user, db_user, db_root_password):
		log("[I] Verifying user " + db_user ,"info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password)		
		query = get_cmd + " -c \; -query \"select username from all_users where upper(username)=upper('%s');\"" %(db_user)
		output = check_output(shlex.split(query))
		if output.strip(db_user + " |"):
			return True
		else:
			return False

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password):
		if self.check_connection(self, root_user, db_root_password):
			if self.verify_user(root_user, db_user, db_root_password):
				log("[I] Oracle user " + db_user + " already exists!", "info")
			else:
				log("[I] User does not exists, Creating user : " + db_user, "info")
				get_cmd = self.get_jisql_cmd(root_user, db_root_password)
				query = get_cmd + " -c \; -query 'create user %s identified by \"%s\";'" %(db_user, db_password)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					if self.verify_user(root_user, db_user, db_root_password):
						log("[I] User " + db_user + " created", "info")
						log("[I] Granting permission to " + db_user, "info")
						query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
						ret = subprocess.check_call(shlex.split(query))
						if ret == 0:
							log("[I] Granting permissions to Oracle user '" + db_user + "' for %s done" %(self.host), "info")
						else:
							log("[E] Granting permissions to Oracle user '" + db_user + "' failed", "error")
							sys.exit(1)
					else:
						log("[E] Creating Oracle user '" + db_user + "' failed", "error")
						sys.exit(1)
				else:
					log("[E] Creating Oracle user '" + db_user + "' failed", "error")
					sys.exit(1)

	def verify_tablespace(self, root_user, db_root_password, db_name):
		log("[I] Verifying tablespace " + db_name, "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password)		
		query = get_cmd + " -c \; -query \"SELECT DISTINCT UPPER(TABLESPACE_NAME) FROM USER_TablespaceS where UPPER(Tablespace_Name)=UPPER(\'%s\');\"" %(db_name)
		output = check_output(shlex.split(query))
		if output.strip(db_name+' |'):
			return True
		else:
			return False

	def create_db(self, root_user, db_root_password, db_name, db_user, db_password):
		if self.verify_tablespace(root_user, db_root_password, db_name):
			log("[I] Tablespace " + db_name + " already exists.","info")
			if self.verify_user(root_user, db_user, db_root_password):
				get_cmd = self.get_jisql_cmd(db_user ,db_password)
				query = get_cmd + " -c \; -query 'select default_tablespace from user_users;'"
				output = check_output(shlex.split(query)).strip()
				db_name = db_name.upper() +' |'
				if output == db_name:
					log("[I] User name " + db_user + " and tablespace " + db_name + " already exists.","info")
				else:
					log("[E] "+db_user + " user already assigned some other tablespace , give some other DB name.","error")
					sys.exit(1)
				#status = self.assign_tablespace(root_user, db_root_password, db_user, db_password, db_name, False)
				#return status
		else:
			log("[I] Tablespace does not exist. Creating tablespace: " + db_name,"info")
		        get_cmd = self.get_jisql_cmd(root_user, db_root_password)
			query = get_cmd + " -c \; -query \"create tablespace %s datafile '%s.dat' size 10M autoextend on;\"" %(db_name, db_name)
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				if self.verify_tablespace(root_user, db_root_password, db_name):
					log("[I] Creating tablespace "+db_name+" succeeded", "info")
					status = self.assign_tablespace(root_user, db_root_password, db_user, db_password, db_name, True)
					return status
				else:
					log("[E] Creating tablespace "+db_name+" failed", "error")
					sys.exit(1)
			else:
				log("[E] Creating tablespace "+db_name+" failed", "error")
				sys.exit(1)

	def assign_tablespace(self, root_user, db_root_password, db_user, db_password, db_name, status):
		log("[I] Assign default tablespace " +db_name + " to " + db_user, "info")
		# Assign default tablespace db_name
		get_cmd = self.get_jisql_cmd(root_user , db_root_password)
		query = get_cmd +" -c \; -query 'alter user %s identified by \"%s\" DEFAULT Tablespace %s;'" %(db_user, db_password, db_name)
		ret = subprocess.check_call(shlex.split(query))
		if ret == 0:
			log("[I] Granting permission to " + db_user, "info")
			query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				log("[I] Granting Oracle user '" + db_user + "' done", "info")
				return status
			else:
				log("[E] Granting Oracle user '" + db_user + "' failed", "error")
				sys.exit(1)
		else:
			log("[E] Assigning default tablespace to user '" + db_user + "' failed", "error")
			sys.exit(1)


	def import_audit_file_to_db(self, audit_db_root_user, db_name ,audit_db_name, db_user, audit_db_user, db_password, audit_db_password, audit_db_root_password, file_name, TABLE_NAME):
		#Verifying Users
		if self.verify_user(audit_db_root_user, db_user, audit_db_root_password):
			log("[I] User " +db_user + " already exists.", "info")
		else:
			log("[E] User does not exist " + db_user, "error")
			sys.exit(1)

		if self.verify_user(audit_db_root_user, audit_db_user, audit_db_root_password):
			log("[I] User " +audit_db_user + " already exists.", "info")
		else:
			log("[E] User does not exist " + audit_db_user, "error")
			sys.exit(1)

		if self.verify_tablespace(audit_db_root_user, audit_db_root_password, audit_db_name):
			log("[I] Tablespace " + audit_db_name + " already exists.","info")
			status1 = True
		else:
			log("[I] Tablespace does not exist. Creating tablespace: " + audit_db_name,"info")
			get_cmd = self.get_jisql_cmd(audit_db_root_user, audit_db_root_password)
			query = get_cmd + " -c \; -query \"create tablespace %s datafile '%s.dat' size 10M autoextend on;\"" %(audit_db_name, audit_db_name)
			ret = subprocess.check_call(shlex.split(query))
			if ret != 0:
				log("[E] Tablespace creation failed!!","error")
				sys.exit(1)
			else:
				log("[I] Creating tablespace "+ audit_db_name + " succeeded", "info")
				status1 = True

		if self.verify_tablespace(audit_db_root_user, audit_db_root_password, db_name):
			log("[I] Tablespace " + db_name + " already exists.","info")
			status2 = True
		else:
			log("[I] Tablespace does not exist. Creating tablespace: " + db_name,"info")
			get_cmd = self.get_jisql_cmd(audit_db_root_user, audit_db_root_password)
			query = get_cmd + " -c \; -query \"create tablespace %s datafile '%s.dat' size 10M autoextend on;\"" %(db_name, db_name)
			ret = subprocess.check_call(shlex.split(query))
			if ret != 0:
				log("[E] Tablespace creation failed!!","error")
				sys.exit(1)
			else:
				log("[I] Creating tablespace "+ db_name + " succeeded", "info")
				status2 = True

		if (status1 == True and status2 == True):
			log("[I] Assign default tablespace " + db_name + " to : " + audit_db_user, "info")
			# Assign default tablespace db_name
			get_cmd = self.get_jisql_cmd(audit_db_root_user , audit_db_root_password)
			query = get_cmd +" -c \; -query 'alter user %s identified by \"%s\" DEFAULT Tablespace %s;'" %(audit_db_user, audit_db_password, db_name)
			ret1 = subprocess.check_call(shlex.split(query))
 
			log("[I] Assign default tablespace " + audit_db_name + " to : " + audit_db_user, "info")
			# Assign default tablespace audit_db_name
			get_cmd = self.get_jisql_cmd(audit_db_root_user , audit_db_root_password)
			query = get_cmd +" -c \; -query 'alter user %s identified by \"%s\" DEFAULT Tablespace %s;'" %(audit_db_user, audit_db_password, audit_db_name)
			ret2 = subprocess.check_call(shlex.split(query))

			if (ret1 == 0 and ret2 == 0):
				log("[I] Granting permission to " + db_user, "info")
				query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					return True
				else:
					log("[E] Granting Oracle user '" + db_user + "' failed", "error")
					sys.exit(1)
			else:
				return False


	def grant_xa_db_user(self, root_user, db_name, db_user, db_password, db_root_password, invoke):
		if self.verify_user(root_user, db_user, db_root_password):
			pass
		else:
			log("[E] User does not exist " + db_user, "error")
			sys.exit(1)
		if self.verify_tablespace(root_user, db_root_password, db_name):
			pass
		else:
			log("[E] Tablespace " + db_name + " does not exists.","error")
			sys.exit(1)

		get_cmd = self.get_jisql_cmd(root_user ,db_root_password)
		query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret == 0:
			log("[I] Granted permission to " + db_user, "info")
			return True
		else:
			log("[E] Granting Oracle user '" + db_user + "' failed", "error")
			sys.exit(1)


	def grant_audit_db_user(self, audit_db_root_user, audit_db_name ,db_user,audit_db_user,db_password,audit_db_password, audit_db_root_password):
		get_cmd = self.get_jisql_cmd(audit_db_root_user, audit_db_root_password)
		query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret == 0:
			log("[I] Granted permission to " + db_user, "info")
			return True
		else:
			log("[E] Granting Oracle user '" + db_user + "' failed", "error")
			sys.exit(1)
		query = get_cmd + " -c \; -query 'GRANT CREATE SESSION TO %s;'" % (audit_db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			sys.exit(1)
		query = get_cmd + " -c \; -query 'GRANT SELECT ON %s.XA_ACCESS_AUDIT_SEQ TO %s;'" % (db_user,audit_db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			sys.exit(1)
		query = get_cmd + " -c \; -query 'GRANT INSERT ON %s.XA_ACCESS_AUDIT TO %s;'" % (db_user,audit_db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			sys.exit(1)


	def import_db_file(self, db_name, db_user, db_password, file_name):
		name = basename(file_name)
		if os.path.isfile(file_name):
			log("[I] Importing script " + db_name + " from file: " + name,"info")
			get_cmd = self.get_jisql_cmd(db_user, db_password)
			query = get_cmd + " -input %s -c \;" %file_name
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				log("[I] "+name + " imported successfully","info")
			else:
				log("[E] "+name + " import failed!","error")
				sys.exit(1)
		else:
			log("[E] Import " +name + " sql file not found","error")
			sys.exit(1)

	def import_db_patches(self, db_name, db_user, db_password, file_name):
		if os.path.isfile(file_name):
			name = basename(file_name)
			version = name.split('-')[0]
			log("[I] Executing patch on " + db_name + " from file: " + name,"info")
			get_cmd = self.get_jisql_cmd(db_user, db_password)
			query = get_cmd + " -c \; -query \"select version from x_db_version_h where version = '%s' and active = 'Y';\"" %(version)
			output = check_output(shlex.split(query))
			if output.strip(version +" |"):
				log("[I] Patch "+ name  +" is already applied" ,"info")
			else:
				get_cmd = self.get_jisql_cmd(db_user, db_password)
				query = get_cmd + " -input %s -c /" %file_name
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					log("[I] "+name + " patch applied","info")
					query = get_cmd + " -c \; -query \"insert into x_db_version_h (id,version, inst_at, inst_by, updated_at, updated_by) values ( X_DB_VERSION_H_SEQ.nextval,'%s', sysdate, '%s', sysdate, '%s');\"" %(version, db_user, db_user)
					ret = subprocess.check_call(shlex.split(query))
					if ret == 0:
						log("[I] Patch version updated", "info")
					else:
						log("[E] Updating patch version failed", "error")
						sys.exit(1)
				else:
					log("[E] "+name + " Import failed!","error")
					sys.exit(1)
		else:
			log("[I] Patch file not found","error")
			sys.exit(1)



	def check_table(self, db_name, db_user, db_password, TABLE_NAME):
		get_cmd = self.get_jisql_cmd(db_user ,db_password)
		query = get_cmd + " -c \; -query 'select default_tablespace from user_users;'"
		output = check_output(shlex.split(query)).strip()
		output = output.strip(' |')
		db_name = db_name.upper()
		if output == db_name:
			log("[I] User name " + db_user + " and tablespace " + db_name + " already exists.","info")
			log("[I] Verifying table " + TABLE_NAME +" in tablespace " + db_name, "info")
			get_cmd = self.get_jisql_cmd(db_user, db_password)
			query = get_cmd + " -c \; -query \"select UPPER(table_name) from all_tables where UPPER(tablespace_name)=UPPER('%s') and UPPER(table_name)=UPPER('%s');\"" %(db_name ,TABLE_NAME)
			output = check_output(shlex.split(query))
			if output.strip(TABLE_NAME.upper() + ' |'):
				log("[I] Table " + TABLE_NAME +" already exists in tablespace " + db_name + "","info")
				return True
			else:
				log("[I] Table " + TABLE_NAME +" does not exist in tablespace " + db_name + "","info")
				return False
		else:
			log("[E] "+db_user + " user already assigned to some other tablespace , provide different DB name.","error")
			sys.exit(1)


	def create_auditdb_user(self, xa_db_host , audit_db_host , db_name ,audit_db_name, xa_db_root_user, audit_db_root_user, db_user, audit_db_user, xa_db_root_password, audit_db_root_password, db_password, audit_db_password, file_name, TABLE_NAME, DBA_MODE):
		if DBA_MODE == "TRUE":
			log("[I] --------- Setup audit user ---------","info")
			#self.create_rangerdb_user(audit_db_root_user, db_user, db_password, audit_db_root_password)
			if self.verify_user(audit_db_root_user, db_user, audit_db_root_password):
				log("[I] Oracle admin user " + db_user + " already exists!", "info")
			else:
				log("[I] User does not exists, Creating user " + db_user, "info")
				get_cmd = self.get_jisql_cmd(audit_db_root_user, audit_db_root_password)
				query = get_cmd + " -c \; -query 'create user %s identified by \"%s\";'" %(db_user, db_password)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					if self.verify_user(audit_db_root_user, db_user, audit_db_root_password):
						log("[I] User " + db_user + " created", "info")
						log("[I] Granting permission to " + db_user, "info")
						query = get_cmd + " -c \; -query 'GRANT CREATE SESSION,CREATE PROCEDURE,CREATE TABLE,CREATE VIEW,CREATE SEQUENCE,CREATE PUBLIC SYNONYM,CREATE TRIGGER,UNLIMITED Tablespace TO %s WITH ADMIN OPTION;'" % (db_user)
						ret = subprocess.check_call(shlex.split(query))
						if ret == 0:
							log("[I] Granting permissions to Oracle user '" + db_user + "' for %s Done" %(self.host), "info")
						else:
							log("[E] Granting permissions to Oracle user '" + db_user + "' failed", "error")
							sys.exit(1)
					else:
						log("[E] Creating Oracle user '" + db_user + "' failed", "error")
						sys.exit(1)
				else:
					log("[E] Creating Oracle user '" + db_user + "' failed", "error")
					sys.exit(1)

			if self.verify_user(audit_db_root_user, audit_db_user, audit_db_root_password):
				log("[I] Oracle audit user " + audit_db_user + " already exist!", "info")
			else:
				log("[I] Audit user does not exists, Creating audit user " + audit_db_user, "info")
				get_cmd = self.get_jisql_cmd(audit_db_root_user, audit_db_root_password)
				query = get_cmd + " -c \; -query 'create user %s identified by \"%s\";'" %(audit_db_user, audit_db_password)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					if self.verify_user(audit_db_root_user, audit_db_user, audit_db_root_password):
						query = get_cmd + " -c \; -query \"GRANT CREATE SESSION TO %s;\"" %(audit_db_user)
						ret = subprocess.check_call(shlex.split(query))
						if ret == 0:
							log("[I] Granting permission to " + audit_db_user + " done", "info")
						else:
							log("[E] Granting permission to " + audit_db_user + " failed", "error")
							sys.exit(1)
					else:
						log("[I] Creating audit user " + audit_db_user + " failed!", "info")
			self.import_audit_file_to_db(audit_db_root_user, db_name ,audit_db_name, db_user, audit_db_user, db_password, audit_db_password, audit_db_root_password, file_name, TABLE_NAME)
		log("[I] --------- Check admin user connection ---------","info")
		self.check_connection(db_name, db_user, db_password)
		log("[I] --------- Check audit user connection ---------","info")
		self.check_connection(audit_db_name, audit_db_user, audit_db_password)
		log("[I] --------- Check table ---------","info")
		if self.check_table(db_name, db_user, db_password, TABLE_NAME):
			pass
		else:
			self.import_db_file(audit_db_name, db_user, db_password ,file_name)

		if DBA_MODE == "TRUE":
			self.grant_xa_db_user(audit_db_root_user, audit_db_name, db_user, db_password, audit_db_root_password, True)
			self.grant_audit_db_user(audit_db_root_user, audit_db_name ,db_user, audit_db_user, db_password,audit_db_password, audit_db_root_password)


class PostgresConf(BaseDB):
	# Constructor
	def __init__(self, host, SQL_CONNECTOR_JAR, JAVA_BIN):
		self.host = host
		self.SQL_CONNECTOR_JAR = SQL_CONNECTOR_JAR
		self.JAVA_BIN = JAVA_BIN


	def get_jisql_cmd(self, user, password, db_name):
		#TODO: User array for forming command
		jisql_cmd = "%s -cp %s:jisql/lib/* org.apache.util.sql.Jisql -driver postgresql -cstring jdbc:postgresql://%s:5432/%s -u %s -p %s -noheader -trim -c \;" %(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, self.host, db_name, user, password)
		return jisql_cmd

	def verify_user(self, root_user, db_root_password, db_user):
		log("[I] Verifying user " + db_user , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'postgres')
		query = get_cmd + " -query \"SELECT rolname FROM pg_roles WHERE rolname='%s';\"" %(db_user)
		output = check_output(shlex.split(query))
		if output.strip(db_user + " |"):
			return True
		else:
			return False

	def check_connection(self, db_name, db_user, db_password):
		log("[I] Checking connection", "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		query = get_cmd + " -query \"SELECT 1;\""
		output = check_output(shlex.split(query))
		if output.strip('1 |'):
			log("[I] connection success", "info")
			return True
		else:
			log("[E] Can't establish connection", "error")
			sys.exit(1)

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password):
		if self.check_connection('postgres', root_user, db_root_password):
			if self.verify_user(root_user, db_root_password, db_user):
				log("[I] Postgres user " + db_user + " already exists!", "info")
			else:
				log("[I] User does not exists, Creating user : " + db_user, "info")
				get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'postgres')
				query = get_cmd + " -query \"CREATE USER %s WITH LOGIN PASSWORD '%s';\"" %(db_user, db_password)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					if self.verify_user(root_user, db_root_password, db_user):
						log("[I] Postgres user " + db_user + " created", "info")
					else:
						log("[E] Postgres user " +db_user+" creation failed", "error")
						sys.exit(1)
				else:
					log("[E] Postgres user " +db_user+" creation failed", "error")
					sys.exit(1)


	def verify_db(self, root_user, db_root_password, db_name):
		log("[I] Verifying database " + db_name , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'postgres')
		query = get_cmd + " -query \"SELECT datname FROM pg_database where datname='%s';\"" %(db_name)
		output = check_output(shlex.split(query))
		if output.strip(db_name + " |"):
			return True
		else:
			return False


	def create_db(self, root_user, db_root_password, db_name, db_user, db_password):
		if self.verify_db(root_user, db_root_password, db_name):
			log("[I] Database "+db_name + " already exists.", "info")
		else:
			log("[I] Database does not exist! Creating database : " + db_name,"info")
			get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'postgres')
			query = get_cmd + " -query \"create database %s with OWNER %s;\"" %(db_name, db_user)
			ret = subprocess.check_call(shlex.split(query))
			if ret != 0:
				log("[E] Database creation failed!!","error")
				sys.exit(1)
			else:
				if self.verify_db(root_user, db_root_password, db_name):
					log("[I] Creating database " + db_name + " succeeded", "info")
					return True
				else:
					log("[E] Database creation failed!!","error")
					sys.exit(1)


	def import_db_file(self, db_name, db_user, db_password, file_name):
		name = basename(file_name)
		if os.path.isfile(file_name):
			log("[I] Importing db schema to database " + db_name + " from file: " + name,"info")
			get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
			query = get_cmd + " -input %s" %file_name
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				log("[I] "+name + " DB schema imported successfully","info")
			else:
				log("[E] "+name + " DB schema import failed!","error")
				sys.exit(1)
		else:
			log("[E] DB schema file " + name+ " not found","error")
			sys.exit(1)


	def grant_xa_db_user(self, root_user, db_name, db_user, db_password, db_root_password , True):
		log("[I] Granting privileges TO user '"+db_user+"' on db '"+db_name+"'" , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, db_name)
		query = get_cmd + " -query \"GRANT ALL PRIVILEGES ON DATABASE %s to %s;\"" %(db_name, db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			log("[E] Granting privileges on tables in schema public failed", "error")
			sys.exit(1)

		query = get_cmd + " -query \"GRANT ALL PRIVILEGES ON SCHEMA public TO %s;\"" %(db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			log("[E] Granting privileges on schema public failed", "error")
			sys.exit(1)

		query = get_cmd + " -query \"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO %s;\"" %(db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			log("[E] Granting privileges on database "+db_name+ " failed", "error")
			sys.exit(1)

		query = get_cmd + " -query \"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO %s;\"" %(db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			log("[E] Granting privileges on database "+db_name+ " failed", "error")
			sys.exit(1)
		log("[I] Granting privileges TO user '"+db_user+"' on db '"+db_name+"' Done" , "info")


	def grant_audit_db_user(self, audit_db_root_user, audit_db_name , db_user, audit_db_user, db_password, audit_db_password, audit_db_root_password):
		log("[I] Granting permission to " + audit_db_user, "info")
		get_cmd = self.get_jisql_cmd(audit_db_root_user, audit_db_root_password, audit_db_name)
		log("[I] Granting select and usage privileges to Postgres audit user '" + audit_db_user + "' on XA_ACCESS_AUDIT_SEQ", "info")
		query = get_cmd + " -query 'GRANT SELECT,USAGE ON XA_ACCESS_AUDIT_SEQ TO %s;'" % (audit_db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			log("[E] Granting select privileges to Postgres user '" + audit_db_user + "' failed", "error")
			sys.exit(1)

		log("[I] Granting insert privileges to Postgres audit user '" + audit_db_user + "' on XA_ACCESS_AUDIT table", "info")
		query = get_cmd + " -query 'GRANT INSERT ON XA_ACCESS_AUDIT TO %s;'" % (audit_db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			log("[E] Granting insert privileges to Postgres user '" + audit_db_user + "' failed", "error")
			sys.exit(1)


	def import_db_patches(self, db_name, db_user, db_password, file_name):
		name = basename(file_name)
		if os.path.isfile(file_name):
			version = name.split('-')[0]
			log("[I] Executing patch on " + db_name + " from file: " + name,"info")
			get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
			query = get_cmd + " -query \"select version from x_db_version_h where version = '%s' and active = 'Y';\"" %(version)
			output = check_output(shlex.split(query))
			if output.strip(version + " |"):
				log("[I] Patch "+ name  +" is already applied" ,"info")
			else:
				query = get_cmd + " -input %s" %file_name
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					log("[I] "+name + " patch applied","info")
					query = get_cmd + " -query \"insert into x_db_version_h (version, inst_at, inst_by, updated_at, updated_by) values ('%s', now(), user(), now(), user()) ;\"" %(version)
					ret = subprocess.check_call(shlex.split(query))
					if ret == 0:
						log("[I] Patch version updated", "info")
					else:
						log("[E] Updating patch version failed", "error")
						sys.exit(1)
				else:
					log("[E] "+name + " import failed!","error")
					sys.exit(1)
		else:
			log("[E] Import " +name + " file not found","error")
			sys.exit(1)


	def check_table(self, db_name, db_user, db_password, TABLE_NAME):
		log("[I] Verifying table " + TABLE_NAME +" in database " + db_name, "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		query = get_cmd + " -query \"select * from (select table_name from information_schema.tables where table_catalog='%s' and table_name = '%s') as temp;\"" %(db_name , TABLE_NAME)
		output = check_output(shlex.split(query))
		if output.strip(TABLE_NAME +" |"):
			log("[I] Table " + TABLE_NAME +" already exists in database " + db_name, "info")
			return True
		else:
			log("[I] Table " + TABLE_NAME +" does not exist in database " + db_name, "info")
			return False


	def create_auditdb_user(self, xa_db_host, audit_db_host, db_name, audit_db_name, xa_db_root_user, audit_db_root_user, db_user, audit_db_user, xa_db_root_password, audit_db_root_password, db_password, audit_db_password, file_name, TABLE_NAME, DBA_MODE):
		if DBA_MODE == "TRUE":
			log("[I] --------- Setup audit user ---------","info")
			self.create_rangerdb_user(audit_db_root_user, db_user, db_password, audit_db_root_password)
			self.create_rangerdb_user(audit_db_root_user, audit_db_user, audit_db_password, audit_db_root_password)
			self.create_db(audit_db_root_user, audit_db_root_password, audit_db_name, db_user, db_password)

		log("[I] --------- Check admin user connection ---------","info")
		self.check_connection(audit_db_name, db_user, db_password)
		log("[I] --------- Check audit user connection ---------","info")
		self.check_connection(audit_db_name, audit_db_user, audit_db_password)
		log("[I] --------- Check table ---------","info")
		output = self.check_table(audit_db_name, audit_db_user, audit_db_password, TABLE_NAME)
		if output == False:
			self.import_db_file(audit_db_name, db_user, db_password, file_name)
		if DBA_MODE == "TRUE":
			self.grant_xa_db_user(audit_db_root_user, audit_db_name, db_user, db_password, audit_db_root_password, True)
			self.grant_audit_db_user(audit_db_root_user, audit_db_name ,db_user, audit_db_user, db_password,audit_db_password, audit_db_root_password)

class SqlServerConf(BaseDB):
	# Constructor
	def __init__(self, host, SQL_CONNECTOR_JAR, JAVA_BIN):
		self.host = host
		self.SQL_CONNECTOR_JAR = SQL_CONNECTOR_JAR
		self.JAVA_BIN = JAVA_BIN


	def get_jisql_cmd(self, user, password, db_name):
		#TODO: User array for forming command
		jisql_cmd = "%s -cp %s:jisql/lib/* org.apache.util.sql.Jisql -user %s -password %s -driver mssql -cstring jdbc:sqlserver://%s:1433\\;databaseName=%s -noheader -trim"%(self.JAVA_BIN, self.SQL_CONNECTOR_JAR, user, password, self.host,db_name)
		return jisql_cmd

	def verify_user(self, root_user, db_root_password, db_user):
		log("[I] Verifying user " + db_user , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
		query = get_cmd + " -c \; -query \"select loginname from master.dbo.syslogins where loginname = '%s';\"" %(db_user)
		output = check_output(shlex.split(query))
		if output.strip(db_user + " |"):
			return True
		else:
			return False

	def check_connection(self, db_name, db_user, db_password):
		log("[I] Checking connection", "info")
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		query = get_cmd + " -c \; -query \"SELECT 1;\""
		output = check_output(shlex.split(query))
		if output.strip('1 |'):
			log("[I] Connection success", "info")
			return True
		else:
			log("[E] Can't establish connection", "error")
			sys.exit(1)

	def create_rangerdb_user(self, root_user, db_user, db_password, db_root_password):
		if self.check_connection('msdb', root_user, db_root_password):
			if self.verify_user(root_user, db_root_password, db_user):
				log("[I] SQL Server user " + db_user + " already exists!", "info")
			else:
				get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
				log("[I] User does not exists, Creating Login user " + db_user, "info")
				query = get_cmd + " -c \; -query \"CREATE LOGIN %s WITH PASSWORD = '%s';\"" %(db_user,db_password)
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					if self.verify_user(root_user, db_root_password, db_user):
						 log("[I] SQL Server user " + db_user + " created", "info")
					else:
						log("[E] SQL Server user " +db_user+" creation failed", "error")
						sys.exit(1)
				else:
					log("[E] SQL Server user " +db_user+" creation failed", "error")
					sys.exit(1)


	def verify_db(self, root_user, db_root_password, db_name):
		log("[I] Verifying database " + db_name, "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
		query = get_cmd + " -c \; -query \"SELECT name from sys.databases where name='%s';\"" %(db_name)
		output = check_output(shlex.split(query))
		if output.strip(db_name + " |"):
			return True
		else:
			return False

	def create_db(self, root_user, db_root_password, db_name, db_user, db_password):
		if self.verify_db(root_user, db_root_password, db_name):
			log("[I] Database " + db_name + " already exists.","info")
		else:
			log("[I] Database does not exist! Creating database : " + db_name,"info")
			get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
			query = get_cmd + " -c \; -query \"create database %s;\"" %(db_name)
			ret = subprocess.check_call(shlex.split(query))
			if ret != 0:
				log("[E] Database creation failed!!","error")
				sys.exit(1)
			else:
				if self.verify_db(root_user, db_root_password, db_name):
					self.create_user(root_user, db_name ,db_user, db_password, db_root_password)
					log("[I] Creating database " + db_name + " succeeded", "info")
					return True
#	        	               	self.import_db_file(db_name, root_user, db_user, db_password, db_root_password, file_name)
				else:
					log("[E] Database creation failed!!","error")
					sys.exit(1)


	def create_user(self, root_user, db_name ,db_user, db_password, db_root_password):
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
		query = get_cmd + " -c \; -query \"USE %s SELECT name FROM sys.database_principals WHERE name = N'%s';\"" %(db_name, db_user)
		output = check_output(shlex.split(query))
		if output.strip(db_user + " |"):
			log("[I] User "+db_user+" exist ","info")
		else:
			query = get_cmd + " -c \; -query \"USE %s CREATE USER %s for LOGIN %s;\"" %(db_name ,db_user, db_user)
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				query = get_cmd + " -c \; -query \"USE %s SELECT name FROM sys.database_principals WHERE name = N'%s';\"" %(db_name ,db_user)
				output = check_output(shlex.split(query))
				if output.strip(db_user + " |"):
					log("[I] User "+db_user+" exist ","info")
				else:
					log("[E] Database creation failed!!","error")
					sys.exit(1)
			else:
				log("[E] Database creation failed!!","error")
				sys.exit(1)

	def import_db_file(self, db_name, db_user, db_password, file_name):
		name = basename(file_name)
		if os.path.isfile(file_name):
			log("[I] Importing db schema to database " + db_name + " from file: " + name,"info")
			get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
			query = get_cmd + " -input %s" %file_name
			ret = subprocess.check_call(shlex.split(query))
			if ret == 0:
				log("[I] "+name + " DB schema imported successfully","info")
			else:
				log("[E] "+name + " DB Schema import failed!","error")
				sys.exit(1)
		else:
			log("[I] DB Schema file " + name+ " not found","error")
			sys.exit(1)

	def check_table(self, db_name, db_user, db_password, TABLE_NAME):
		get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
		query = get_cmd + " -c \; -query \"SELECT TABLE_NAME FROM information_schema.tables where table_name = '%s';\"" %(TABLE_NAME)
		output = check_output(shlex.split(query))
		if output.strip(TABLE_NAME + " |"):
			log("[I] Table '" + TABLE_NAME + "' already exists in  database '" + db_name + "'","info")
			return True
		else:
			log("[I] Table '" + TABLE_NAME + "' does not exist in database '" + db_name + "'","info")
			return False


	def grant_xa_db_user(self, root_user, db_name, db_user, db_password, db_root_password, True):
		log("[I] Granting permission to admin user '" + db_user + "' on db '" + db_name + "'" , "info")
		get_cmd = self.get_jisql_cmd(root_user, db_root_password, 'msdb')
		query = get_cmd + " -c \; -query \"ALTER LOGIN [%s] WITH DEFAULT_DATABASE=[%s];\"" %(db_user, db_name)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			sys.exit(1)
		query = get_cmd + " -c \; -query \" USE %s EXEC sp_addrolemember N'db_owner', N'%s';\"" %(db_name, db_user)
#                query = get_cmd + " -c \; -query \" USE %s GRANT ALL PRIVILEGES to %s;\"" %(db_name , db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0:
			sys.exit(1)


	def grant_audit_db_user(self, audit_db_root_user, audit_db_name, db_user, audit_db_user, db_password, audit_db_password, audit_db_root_password,TABLE_NAME):
		log("[I] Granting permission to audit user '" + audit_db_user + "' on db '" + audit_db_name + "'","info")
		get_cmd = self.get_jisql_cmd(audit_db_root_user, audit_db_root_password, 'msdb')
		query = get_cmd + " -c \; -query \"USE %s GRANT SELECT,INSERT to %s;\"" %(audit_db_name ,audit_db_user)
		ret = subprocess.check_call(shlex.split(query))
		if ret != 0 :
			sys.exit(1)
		else:
			log("[I] Permission granted to audit user " + audit_db_user , "info")

	def import_db_patches(self, db_name, db_user, db_password, file_name):
		name = basename(file_name)
		if os.path.isfile(file_name):
			version = name.split('-')[0]
			log("[I] Executing patch on " + db_name + " from file: " + name,"info")
			get_cmd = self.get_jisql_cmd(db_user, db_password, db_name)
			query = get_cmd + " -query \"select version from x_db_version_h where version = '%s' and active = 'Y';\"" %(version)
			output = check_output(shlex.split(query))
			if output.strip(version + " |"):
				log("[I] Patch "+ name  +" is already applied" ,"info")
			else:
				query = get_cmd + " -input %s" %file_name
				ret = subprocess.check_call(shlex.split(query))
				if ret == 0:
					log("[I] "+name + " patch applied","info")
					query = get_cmd + " -query \"insert into x_db_version_h (version, inst_at, inst_by, updated_at, updated_by) values ('%s', now(), user(), now(), user()) ;\"" %(version)
					ret = subprocess.check_call(shlex.split(query))
					if ret == 0:
						log("[I] Patch version updated", "info")
					else:
						log("[E] Updating patch version failed", "error")
						sys.exit(1)
				else:
					log("[E] "+name + " import failed!","error")
					sys.exit(1)
		else:
			log("[E] Import " +name + " file not found","error")
			sys.exit(1)


	def create_auditdb_user(self, xa_db_host, audit_db_host, db_name, audit_db_name, xa_db_root_user, audit_db_root_user, db_user, audit_db_user, xa_db_root_password, audit_db_root_password, db_password, audit_db_password, file_name, TABLE_NAME, DBA_MODE):
		if DBA_MODE == "TRUE":
			log("[I] --------- Setup audit user --------- ","info")
			self.create_rangerdb_user(audit_db_root_user, db_user, db_password, audit_db_root_password)
			#log("[I] --------- Setup audit user --------- ","info")
			self.create_rangerdb_user(audit_db_root_user, audit_db_user, audit_db_password, audit_db_root_password)
			self.create_db(audit_db_root_user, audit_db_root_password ,audit_db_name, audit_db_user, audit_db_password)
			self.create_user(xa_db_root_user, audit_db_name ,db_user, db_password, xa_db_root_password)
			self.grant_xa_db_user(audit_db_root_user, audit_db_name, db_user, db_password, audit_db_root_password, True)

		log("[I] --------- Check admin user connection --------- ","info")
		self.check_connection(audit_db_name, db_user, db_password)
		log("[I] --------- Check audit user connection --------- ","info")
		self.check_connection(audit_db_name, audit_db_user, audit_db_password)
		log("[I] --------- Check audit table exists --------- ","info")
		output = self.check_table(audit_db_name, db_user, db_password, TABLE_NAME)
		if output == False:
			self.import_db_file(audit_db_name ,db_user, db_password, file_name)
		if DBA_MODE == "TRUE":
			self.grant_audit_db_user(audit_db_root_user, audit_db_name ,db_user, audit_db_user, db_password,audit_db_password, audit_db_root_password,TABLE_NAME)


def main():
	populate_global_dict()

	FORMAT = '%(asctime)-15s %(message)s'
	logging.basicConfig(format=FORMAT, level=logging.DEBUG)

	if 'DBA_MODE' in globalDict :
		DBA_MODE = globalDict['DBA_MODE']
		DBA_MODE = DBA_MODE.upper()
		if DBA_MODE == "FALSE" or DBA_MODE == "TRUE":
			pass
		else:
			log("[E] --------- DBA_MODE should be TRUE or FALSE --------- ","error")
			sys.exit(1)
	else:
		DBA_MODE = "FALSE"

	log("[I] --------- DBA_MODE is :" + DBA_MODE +" --------- ","info")

	JAVA_BIN=globalDict['JAVA_BIN']
	XA_DB_FLAVOR=globalDict['DB_FLAVOR']
	AUDIT_DB_FLAVOR=globalDict['DB_FLAVOR']
	XA_DB_FLAVOR.upper()
	AUDIT_DB_FLAVOR.upper()

	xa_db_host = globalDict['db_host']
	audit_db_host = globalDict['db_host']

	mysql_dbversion_catalog = 'db/mysql/create_dbversion_catalog.sql'
	mysql_core_file = globalDict['mysql_core_file']
	mysql_audit_file = globalDict['mysql_audit_file']
	mysql_patches = 'db/mysql/patches'

	oracle_dbversion_catalog = 'db/oracle/create_dbversion_catalog.sql'
	oracle_core_file = globalDict['oracle_core_file'] 
	oracle_audit_file = globalDict['oracle_audit_file'] 
	oracle_patches = 'db/oracle/patches'

	postgres_dbversion_catalog = 'db/postgres/create_dbversion_catalog.sql'
	postgres_core_file = globalDict['postgres_core_file']
	postgres_audit_file = globalDict['postgres_audit_file']
	postgres_patches = 'db/postgres/patches'

	sqlserver_dbversion_catalog = 'db/sqlserver/create_dbversion_catalog.sql'
	sqlserver_core_file = globalDict['sqlserver_core_file']
	sqlserver_audit_file = globalDict['sqlserver_audit_file']
	sqlserver_patches = 'db/sqlserver/patches'

	db_name = globalDict['db_name']
	db_user = globalDict['db_user']
	db_password = globalDict['db_password']
	xa_db_root_user = globalDict['db_root_user']
	xa_db_root_password = globalDict['db_root_password']

	x_db_version = 'x_db_version_h'
	xa_access_audit = 'xa_access_audit'
	x_user = 'x_portal_user'

	audit_db_name = globalDict['audit_db_name']
	audit_db_user = globalDict['audit_db_user']
	audit_db_password = globalDict['audit_db_password']
	audit_db_root_user = globalDict['db_root_user'] 
	audit_db_root_password = globalDict['db_root_password']

	if XA_DB_FLAVOR == "MYSQL":
		MYSQL_CONNECTOR_JAR=globalDict['SQL_CONNECTOR_JAR']
		xa_sqlObj = MysqlConf(xa_db_host, MYSQL_CONNECTOR_JAR, JAVA_BIN)
		xa_db_version_file = os.path.join(os.getcwd(),mysql_dbversion_catalog)
		xa_db_core_file = os.path.join(os.getcwd(),mysql_core_file)
		xa_patch_file = os.path.join(os.getcwd(),mysql_patches)
		
	elif XA_DB_FLAVOR == "ORACLE":
		ORACLE_CONNECTOR_JAR=globalDict['SQL_CONNECTOR_JAR']
		xa_db_root_user = xa_db_root_user+" AS SYSDBA"
		xa_sqlObj = OracleConf(xa_db_host, ORACLE_CONNECTOR_JAR, JAVA_BIN)
		xa_db_version_file = os.path.join(os.getcwd(),oracle_dbversion_catalog)
		xa_db_core_file = os.path.join(os.getcwd(),oracle_core_file)
		xa_patch_file = os.path.join(os.getcwd(),oracle_patches)

	elif XA_DB_FLAVOR == "POSTGRES":
		POSTGRES_CONNECTOR_JAR = globalDict['SQL_CONNECTOR_JAR']
		xa_sqlObj = PostgresConf(xa_db_host, POSTGRES_CONNECTOR_JAR, JAVA_BIN)
		xa_db_version_file = os.path.join(os.getcwd(),postgres_dbversion_catalog)
		xa_db_core_file = os.path.join(os.getcwd(),postgres_core_file)
		xa_patch_file = os.path.join(os.getcwd(),postgres_patches)

	elif XA_DB_FLAVOR == "SQLSERVER":
		SQLSERVER_CONNECTOR_JAR = globalDict['SQL_CONNECTOR_JAR']
		xa_sqlObj = SqlServerConf(xa_db_host, SQLSERVER_CONNECTOR_JAR, JAVA_BIN)
		xa_db_version_file = os.path.join(os.getcwd(),sqlserver_dbversion_catalog)
		xa_db_core_file = os.path.join(os.getcwd(),sqlserver_core_file)
		xa_patch_file = os.path.join(os.getcwd(),sqlserver_patches)
	else:
		log("[E] --------- NO SUCH SUPPORTED DB FLAVOUR!! ---------", "error")
		sys.exit(1)

	if AUDIT_DB_FLAVOR == "MYSQL":
		MYSQL_CONNECTOR_JAR=globalDict['SQL_CONNECTOR_JAR']
		audit_sqlObj = MysqlConf(audit_db_host,MYSQL_CONNECTOR_JAR,JAVA_BIN)
		audit_db_file = os.path.join(os.getcwd(),mysql_audit_file)

	elif AUDIT_DB_FLAVOR == "ORACLE":
		ORACLE_CONNECTOR_JAR=globalDict['SQL_CONNECTOR_JAR']
		audit_db_root_user = audit_db_root_user+" AS SYSDBA"
		audit_sqlObj = OracleConf(audit_db_host, ORACLE_CONNECTOR_JAR, JAVA_BIN)
		audit_db_file = os.path.join(os.getcwd(),oracle_audit_file)

	elif AUDIT_DB_FLAVOR == "POSTGRES":
		POSTGRES_CONNECTOR_JAR = globalDict['SQL_CONNECTOR_JAR']
		audit_sqlObj = PostgresConf(audit_db_host, POSTGRES_CONNECTOR_JAR, JAVA_BIN)
		audit_db_file = os.path.join(os.getcwd(),postgres_audit_file)

	elif AUDIT_DB_FLAVOR == "SQLSERVER":
		SQLSERVER_CONNECTOR_JAR = globalDict['SQL_CONNECTOR_JAR']
		audit_sqlObj = SqlServerConf(audit_db_host, SQLSERVER_CONNECTOR_JAR, JAVA_BIN)
		audit_db_file = os.path.join(os.getcwd(),sqlserver_audit_file)
	else:
		log("[E] --------- NO SUCH SUPPORTED DB FLAVOUR!! ---------", "error")
		sys.exit(1)

	# Methods Begin
	if DBA_MODE == "TRUE" :
		log("[I] --------- Creating Ranger Admin db user --------- ","info")
		xa_sqlObj.create_rangerdb_user(xa_db_root_user, db_user, db_password, xa_db_root_password)
		log("[I] --------- Creating Ranger Admin database ---------","info")
		xa_sqlObj.create_db(xa_db_root_user, xa_db_root_password, db_name, db_user, db_password)
		log("[I] --------- Granting permission to Ranger Admin db user ---------","info")
		xa_sqlObj.grant_xa_db_user(xa_db_root_user, db_name, db_user, db_password, xa_db_root_password, True)

	log("[I] --------- Verifying Ranger DB connection ---------","info")
	xa_sqlObj.check_connection(db_name, db_user, db_password)
	log("[I] --------- Verifying Ranger DB tables ---------","info")
	if xa_sqlObj.check_table(db_name, db_user, db_password, x_user):
		pass
	else:
		log("[I] --------- Importing Ranger Core DB Schema ---------","info")
		xa_sqlObj.import_db_file(db_name, db_user, db_password, xa_db_core_file)
	log("[I] --------- Verifying upgrade history table ---------","info")
	output = xa_sqlObj.check_table(db_name, db_user, db_password, x_db_version)
	if output == False:
		log("[I] --------- Creating version history table ---------","info")
		xa_sqlObj.upgrade_db(db_name, db_user, db_password, xa_db_version_file)
	log("[I] --------- Applying patches ---------","info")
	xa_sqlObj.apply_patches(db_name, db_user, db_password, xa_patch_file)

	# Ranger Admin DB Host AND Ranger Audit DB Host are Different OR Same
	#log("[I] --------- Verifying/Creating audit user --------- ","info")
	audit_sqlObj.create_auditdb_user(xa_db_host, audit_db_host, db_name, audit_db_name, xa_db_root_user, audit_db_root_user, db_user, audit_db_user, xa_db_root_password, audit_db_root_password, db_password, audit_db_password, audit_db_file, xa_access_audit, DBA_MODE)

main()