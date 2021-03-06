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

 package org.apache.ranger.biz;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;

import javax.persistence.Query;

import org.apache.log4j.Logger;
import org.apache.ranger.common.AppConstants;
import org.apache.ranger.common.ContextUtil;
import org.apache.ranger.common.DateUtil;
import org.apache.ranger.common.GUIDUtil;
import org.apache.ranger.common.MessageEnums;
import org.apache.ranger.common.RESTErrorUtil;
import org.apache.ranger.common.RangerCommonEnums;
import org.apache.ranger.common.RangerConfigUtil;
import org.apache.ranger.common.RangerConstants;
import org.apache.ranger.common.SearchCriteria;
import org.apache.ranger.common.SearchUtil;
import org.apache.ranger.common.StringUtil;
import org.apache.ranger.common.UserSessionBase;
import org.apache.ranger.db.RangerDaoManager;
import org.apache.ranger.entity.XXPortalUser;
import org.apache.ranger.entity.XXPortalUserRole;
import org.apache.ranger.entity.XXTrxLog;
import org.apache.ranger.service.XPortalUserService;
import org.apache.ranger.view.VXPasswordChange;
import org.apache.ranger.view.VXPortalUser;
import org.apache.ranger.view.VXPortalUserList;
import org.apache.ranger.view.VXResponse;
import org.apache.ranger.view.VXString;
import org.apache.velocity.Template;
import org.apache.velocity.app.VelocityEngine;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.encoding.Md5PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Component
public class UserMgr {

	static final Logger logger = Logger.getLogger(UserMgr.class);
	private static final Md5PasswordEncoder md5Encoder = new Md5PasswordEncoder();

	@Autowired
	RangerDaoManager daoManager;

	@Autowired
	RESTErrorUtil restErrorUtil;

	@Autowired
	StringUtil stringUtil;

	@Autowired
	SearchUtil searchUtil;

	@Autowired
	RangerBizUtil msBizUtil;

	@Autowired
	SessionMgr sessionMgr;

	@Autowired
	VelocityEngine velocityEngine;
	Template t;

	@Autowired
	DateUtil dateUtil;

	@Autowired
	RangerConfigUtil configUtil;
	
	@Autowired
	XPortalUserService xPortalUserService;

	String publicRoles[] = new String[] { RangerConstants.ROLE_USER,
			RangerConstants.ROLE_OTHER };

	private static final List<String> DEFAULT_ROLE_LIST = new ArrayList<String>(
			1);

	private static final List<String> VALID_ROLE_LIST = new ArrayList<String>(2);

	static {
		DEFAULT_ROLE_LIST.add(RangerConstants.ROLE_USER);
		VALID_ROLE_LIST.add(RangerConstants.ROLE_SYS_ADMIN);
		VALID_ROLE_LIST.add(RangerConstants.ROLE_USER);
	}

	public UserMgr() {
		if (logger.isDebugEnabled()) {
			logger.debug("UserMgr()");
		}
	}

	public XXPortalUser createUser(VXPortalUser userProfile, int userStatus,
			Collection<String> userRoleList) {
		XXPortalUser user = mapVXPortalUserToXXPortalUser(userProfile);
		user = createUser(user, userStatus, userRoleList);

		return user;
	}

	public XXPortalUser createUser(XXPortalUser user, int userStatus,
			Collection<String> userRoleList) {
		user.setStatus(userStatus);
		String saltEncodedpasswd = encrypt(user.getLoginId(),
				user.getPassword());
		user.setPassword(saltEncodedpasswd);
		user = daoManager.getXXPortalUser().create(user);

		// Create the UserRole for this user
		List<XXPortalUserRole> gjUserRoleList = new ArrayList<XXPortalUserRole>();
		if (userRoleList != null) {
			for (String userRole : userRoleList) {
				XXPortalUserRole gjUserRole = addUserRole(user.getId(), userRole);
				if (gjUserRole != null) {
					gjUserRoleList.add(gjUserRole);
				}
			}
		}

		return user;
	}

	public XXPortalUser createUser(VXPortalUser userProfile, int userStatus) {
		ArrayList<String> roleList = new ArrayList<String>();		
		Collection<String> reqRoleList = userProfile.getUserRoleList();
		if (reqRoleList != null && reqRoleList.size()>0) {
			for (String role : reqRoleList) {
				roleList.add(role);
			}
		}else{
			roleList.add(RangerConstants.ROLE_USER);
		}

		return createUser(userProfile, userStatus, roleList);
	}

	/**
	 * @param userProfile
	 * @return
	 */
	public XXPortalUser updateUser(VXPortalUser userProfile) {
		XXPortalUser gjUser = daoManager.getXXPortalUser().getById(
				userProfile.getId());

		if (gjUser == null) {
			logger.error("updateUser(). User not found. userProfile="
					+ userProfile);
			return null;
		}

		checkAccess(gjUser);

		boolean updateUser = false;
		// Selectively update fields

		// status
		if (userProfile.getStatus() != gjUser.getStatus()) {
			updateUser = true;
		}

		// Allowing email address update even when its set to empty.
		// emailAddress
		String emailAddress = userProfile.getEmailAddress();
		if (stringUtil.isEmpty(emailAddress)) {
			String randomString = GUIDUtil.genGUI();
			userProfile.setEmailAddress(randomString);
			updateUser = true;
		} else {
			if (stringUtil.validateEmail(emailAddress)) {
				XXPortalUser checkUser = daoManager.getXXPortalUser()
						.findByEmailAddress(emailAddress);
				if (checkUser != null) {
					String loginId = userProfile.getLoginId();
					if (loginId == null) {
						throw restErrorUtil.createRESTException(
								"Invalid user, please provide valid "
										+ "username.",
								MessageEnums.INVALID_INPUT_DATA);
					} else if (!loginId.equals(checkUser.getLoginId())) {
						throw restErrorUtil
								.createRESTException(
										"The email address "
												+ "you've provided already exists in system.",
										MessageEnums.INVALID_INPUT_DATA);
					} else {
						userProfile.setEmailAddress(emailAddress);
						updateUser = true;
					}
				} else {
					userProfile.setEmailAddress(emailAddress);
					updateUser = true;
				}
			} else {
				throw restErrorUtil.createRESTException(
						"Please provide valid email address.",
						MessageEnums.INVALID_INPUT_DATA);
			}
		}

		// loginId
		// if (!stringUtil.isEmpty(userProfile.getLoginId())
		// && !userProfile.getLoginId().equals(gjUser.getLoginId())) {
		// gjUser.setLoginId(userProfile.getLoginId());
		// updateUser = true;
		// }

		// firstName
		if (!stringUtil.isEmpty(userProfile.getFirstName())
				&& !userProfile.getFirstName().equals(gjUser.getFirstName())) {
			userProfile.setFirstName(stringUtil.toCamelCaseAllWords(userProfile
					.getFirstName()));
			updateUser = true;
		}

		// lastName allowed to be empty
		if (userProfile.getLastName() != null
				&& !userProfile.getLastName().equals(gjUser.getLastName())) {
			userProfile.setLastName(stringUtil.toCamelCaseAllWords(userProfile
					.getLastName()));
			updateUser = true;
		}

		// publicScreenName
		if (!stringUtil.isEmpty(userProfile.getPublicScreenName())
				&& !userProfile.getPublicScreenName().equals(
						gjUser.getPublicScreenName())) {
			userProfile.setPublicScreenName(userProfile.getFirstName() + " "
					+ userProfile.getLastName());
			updateUser = true;
		}

		// notes
		/*if (!stringUtil.isEmpty(userProfile.getNotes())
				&& !userProfile.getNotes().equalsIgnoreCase(gjUser.getNotes())) {
			updateUser = true;
		}*/

		// userRoleList
		updateRoles(userProfile.getId(), userProfile.getUserRoleList());

		if (updateUser) {

			List<XXTrxLog> trxLogList = xPortalUserService.getTransactionLog(
					userProfile, gjUser, "update");

			userProfile.setPassword(gjUser.getPassword());
			userProfile = xPortalUserService.updateResource(userProfile);
			sessionMgr.resetUserSessionForProfiles(ContextUtil
					.getCurrentUserSession());

			msBizUtil.createTrxLog(trxLogList);
		}

		return gjUser;
	}

	private boolean updateRoles(Long userId, Collection<String> rolesList) {
		boolean rolesUpdated = false;
		if (rolesList == null || rolesList.size() == 0) {
			return false;
		}

		// Let's first delete old roles
		List<XXPortalUserRole> gjUserRoles = daoManager.getXXPortalUserRole().findByUserId(
				userId);

		for (XXPortalUserRole gjUserRole : gjUserRoles) {
			boolean found = false;
			for (String userRole : rolesList) {
				if (gjUserRole.getUserRole().equalsIgnoreCase(userRole)) {
					found = true;
					break;
				}
			}
			if (!found) {
				if (deleteUserRole(userId, gjUserRole)) {
					rolesUpdated = true;
				}
			}
		}

		// Let's add new roles
		for (String userRole : rolesList) {
			boolean found = false;
			for (XXPortalUserRole gjUserRole : gjUserRoles) {
				if (gjUserRole.getUserRole().equalsIgnoreCase(userRole)) {
					found = true;
					break;
				}
			}
			if (!found) {
				if (addUserRole(userId, userRole) != null) {
					rolesUpdated = true;
				}
			}
		}
		return rolesUpdated;
	}

	/**
	 * @param userId
	 * @param vStrings
	 */
	public void setUserRoles(Long userId, List<VXString> vStringRolesList) {
		List<String> stringRolesList = new ArrayList<String>();
		for (VXString vXString : vStringRolesList) {
			stringRolesList.add(vXString.getValue());
		}
		updateRoles(userId, stringRolesList);
	}

	/**
	 * @param pwdChange
	 * @return
	 */
	public VXResponse changePassword(VXPasswordChange pwdChange) {
		// First let's get the XXPortalUser for the current logged in user
		String currentUserLoginId = ContextUtil.getCurrentUserLoginId();
		XXPortalUser gjUserCurrent = daoManager.getXXPortalUser()
				.findByLoginId(currentUserLoginId);

		String encryptedOldPwd = encrypt(gjUserCurrent.getLoginId(),
				pwdChange.getOldPassword());

		VXResponse ret = new VXResponse();

		if (!stringUtil.equals(encryptedOldPwd, gjUserCurrent.getPassword())) {
			logger.info("changePassword(). Invalid old password. userId="
					+ pwdChange.getId());

			throw restErrorUtil.createRESTException(
					"serverMsg.userMgrPassword",
					MessageEnums.OPER_NO_PERMISSION, null, null,
					"" + pwdChange.getId());
		}

		// Get the user for whom we want to change the password
		XXPortalUser gjUser = daoManager.getXXPortalUser().getById(
				pwdChange.getId());
		if (gjUser == null) {
			logger.warn("SECURITY:changePassword(). User not found. userId="
					+ pwdChange.getId());
			throw restErrorUtil.createRESTException(
					"serverMsg.userMgrInvalidUser",
					MessageEnums.DATA_NOT_FOUND, null, null,
					"" + pwdChange.getId());
		}

		if (!stringUtil
				.validatePassword(
						pwdChange.getUpdPassword(),
						new String[] { gjUser.getFirstName(),
								gjUser.getLastName(), gjUser.getLoginId(),
								gjUserCurrent.getFirstName(),
								gjUserCurrent.getLastName(),
								gjUserCurrent.getLoginId() })) {
			logger.warn("SECURITY:changePassword(). Invalid new password. userId="
					+ pwdChange.getId());

			throw restErrorUtil.createRESTException(
					"serverMsg.userMgrNewPassword",
					MessageEnums.INVALID_PASSWORD, null, null,
					"" + pwdChange.getId());
		}

		String encryptedNewPwd = encrypt(gjUser.getLoginId(),
				pwdChange.getUpdPassword());

		String currentPassword = gjUser.getPassword();

		if (!encryptedNewPwd.equals(currentPassword)) {

			List<XXTrxLog> trxLogList = new ArrayList<XXTrxLog>();
			XXTrxLog xTrxLog = new XXTrxLog();

			xTrxLog.setAttributeName("Password");
			xTrxLog.setPreviousValue(currentPassword);
			xTrxLog.setNewValue(encryptedNewPwd);
			xTrxLog.setAction("password change");
			xTrxLog.setObjectClassType(AppConstants.CLASS_TYPE_PASSWORD_CHANGE);
			xTrxLog.setObjectId(pwdChange.getId());
			xTrxLog.setObjectName(pwdChange.getLoginId());
			trxLogList.add(xTrxLog);

			msBizUtil.createTrxLog(trxLogList);

			gjUser.setPassword(encryptedNewPwd);
			gjUser = daoManager.getXXPortalUser().update(gjUser);

			ret.setMsgDesc("Password successfully updated");
			ret.setStatusCode(VXResponse.STATUS_SUCCESS);
		} else {
			ret.setMsgDesc("Password update failed");
			ret.setStatusCode(VXResponse.STATUS_ERROR);
			throw restErrorUtil.createRESTException(
					"serverMsg.userMgrOldPassword",
					MessageEnums.INVALID_INPUT_DATA, gjUser.getId(),
					"password", gjUser.toString());
		}
		return ret;
	}

	/**
	 * @param gjUser
	 * @param changeEmail
	 * @return
	 */
	public VXPortalUser changeEmailAddress(XXPortalUser gjUser,
			VXPasswordChange changeEmail) {

		if (gjUser.getEmailAddress() != null) {
			throw restErrorUtil.createRESTException(
					"serverMsg.userMgrEmailChange",
					MessageEnums.OPER_NO_PERMISSION, null, null, ""
							+ changeEmail);
		}

		String encryptedOldPwd = encrypt(gjUser.getLoginId(),
				changeEmail.getOldPassword());

		if (!stringUtil.validateEmail(changeEmail.getEmailAddress())) {
			logger.info("Invalid email address." + changeEmail);
			throw restErrorUtil.createRESTException(
					"serverMsg.userMgrInvalidEmail",
					MessageEnums.INVALID_INPUT_DATA, changeEmail.getId(),
					"emailAddress", changeEmail.toString());

		}

		if (!stringUtil.equals(encryptedOldPwd, gjUser.getPassword())) {
			logger.info("changeEmailAddress(). Invalid  password. changeEmail="
					+ changeEmail);

			throw restErrorUtil.createRESTException(
					"serverMsg.userMgrWrongPassword",
					MessageEnums.OPER_NO_PERMISSION, null, null, ""
							+ changeEmail);
		}

		// Normalize email. Make it lower case
		gjUser.setEmailAddress(stringUtil.normalizeEmail(changeEmail
				.getEmailAddress()));

		// loginId
		gjUser.setLoginId(gjUser.getEmailAddress());

		String saltEncodedpasswd = encrypt(gjUser.getLoginId(),
				changeEmail.getOldPassword());

		gjUser.setPassword(saltEncodedpasswd);

		daoManager.getXXPortalUser().update(gjUser);
		return mapXXPortalUserVXPortalUser(gjUser);
	}

	/**
	 * @param userId
	 */
	public VXPortalUser deactivateUser(XXPortalUser gjUser) {
		if (gjUser != null
				&& gjUser.getStatus() != RangerConstants.ACT_STATUS_DEACTIVATED) {
			logger.info("Marking user " + gjUser.getLoginId() + " as deleted");
			gjUser.setStatus(RangerConstants.ACT_STATUS_DEACTIVATED);
			gjUser = daoManager.getXXPortalUser().update(gjUser);
			return mapXXPortalUserVXPortalUser(gjUser);
		}
		return null;
	}

	public VXPortalUser getUserProfile(Long id) {
		XXPortalUser user = daoManager.getXXPortalUser().getById(id);
		if (user != null) {
			checkAccessForRead(user);
			return mapXXPortalUserVXPortalUser(user);
		} else {
			if (logger.isDebugEnabled()) {
				logger.debug("User not found. userId=" + id);
			}
			return null;
		}
	}

	public VXPortalUser getUserProfileByLoginId() {
		String loginId = ContextUtil.getCurrentUserLoginId();
		return getUserProfileByLoginId(loginId);
	}

	public VXPortalUser getUserProfileByLoginId(String loginId) {
		XXPortalUser user = daoManager.getXXPortalUser().findByLoginId(loginId);
		if (user != null) {
			return mapXXPortalUserVXPortalUser(user);
		} else {
			if (logger.isDebugEnabled()) {
				logger.debug("User not found. loginId=" + loginId);
			}
			return null;
		}
	}

	public XXPortalUser mapVXPortalUserToXXPortalUser(VXPortalUser userProfile) {
		XXPortalUser gjUser = new XXPortalUser();
		gjUser.setEmailAddress(userProfile.getEmailAddress());
		gjUser.setFirstName(userProfile.getFirstName());
		gjUser.setLastName(userProfile.getLastName());
		gjUser.setLoginId(userProfile.getLoginId());
		gjUser.setPassword(userProfile.getPassword());
		gjUser.setUserSource(userProfile.getUserSource());
		gjUser.setPublicScreenName(userProfile.getPublicScreenName());		
		return gjUser;
	}

	/**
	 * @param user
	 * @return
	 */
	public VXPortalUser mapXXPortalUserToVXPortalUser(XXPortalUser user,
			Collection<String> userRoleList) {
		if (user == null) {
			return null;
		}
		UserSessionBase sess = ContextUtil.getCurrentUserSession();
		if (sess == null) {
			return null;
		}

		VXPortalUser userProfile = new VXPortalUser();
		gjUserToUserProfile(user, userProfile);
		if (sess.isUserAdmin() || sess.getXXPortalUser().getId().equals(user.getId())) {
			if (userRoleList == null) {
				userRoleList = new ArrayList<String>();
				List<XXPortalUserRole> gjUserRoleList = daoManager.getXXPortalUserRole()
						.findByParentId(user.getId());

				for (XXPortalUserRole userRole : gjUserRoleList) {
					userRoleList.add(userRole.getUserRole());
				}
			}

			userProfile.setUserRoleList(userRoleList);
		}
		userProfile.setUserSource(user.getUserSource());
		return userProfile;
	}

	private void gjUserToUserProfile(XXPortalUser user, VXPortalUser userProfile) {
		UserSessionBase sess = ContextUtil.getCurrentUserSession();
		if (sess == null) {
			return;
		}

		// Is accessed by peer from the same account
		boolean isPeer = false;
		boolean isAccountAdmin = false;

		// Admin
		if (sess.isUserAdmin() || sess.getXXPortalUser().getId().equals(user.getId())) {
			userProfile.setLoginId(user.getLoginId());
			userProfile.setStatus(user.getStatus());
			userProfile.setUserRoleList(new ArrayList<String>());
			String emailAddress = user.getEmailAddress();

			if (emailAddress != null && stringUtil.validateEmail(emailAddress)) {
				userProfile.setEmailAddress(user.getEmailAddress());
			}

			if (sess != null) {
				userProfile.setUserSource(sess.getAuthProvider());
			}

			List<XXPortalUserRole> gjUserRoleList = daoManager.getXXPortalUserRole()
					.findByParentId(user.getId());

			for (XXPortalUserRole gjUserRole : gjUserRoleList) {
				userProfile.getUserRoleList().add(gjUserRole.getUserRole());
			}
		}

		if (sess.isUserAdmin() || sess.getXXPortalUser().getId().equals(user.getId())
				|| isPeer) {
			userProfile.setId(user.getId());
			userProfile.setFirstName(user.getFirstName());
			userProfile.setLastName(user.getLastName());
			userProfile.setPublicScreenName(user.getPublicScreenName());
			if (isAccountAdmin) {
				userProfile.setEmailAddress(user.getEmailAddress());
			}
		}

	}

	/**
	 * Translates XXPortalUser to VUserProfile. This method should be called in the
	 * same transaction in which the XXPortalUser was retrieved from the database
	 * 
	 * @param user
	 * @return
	 */
	public VXPortalUser mapXXPortalUserVXPortalUser(XXPortalUser user) {
		return mapXXPortalUserToVXPortalUser(user, null);
	}

	/**
	 * @param emailId
	 * @return
	 */
	public XXPortalUser findByEmailAddress(String emailId) {
		return daoManager.getXXPortalUser().findByEmailAddress(emailId);
	}

	public XXPortalUser findByLoginId(String loginId) {
		return daoManager.getXXPortalUser().findByLoginId(loginId);
	}

	@Transactional(readOnly = true, propagation = Propagation.REQUIRED)
	public Collection<String> getRolesForUser(XXPortalUser user) {
		Collection<String> roleList = new ArrayList<String>();

		Collection<XXPortalUserRole> roleCollection = daoManager.getXXPortalUserRole()
				.findByUserId(user.getId());
		for (XXPortalUserRole role : roleCollection) {
			roleList.add(role.getUserRole());
		}
		return roleList;
	}

	/**
	 * @param searchCriteria
	 * @return
	 */
	public VXPortalUserList searchUsers(SearchCriteria searchCriteria) {

		VXPortalUserList returnList = new VXPortalUserList();
		ArrayList<VXPortalUser> objectList = new ArrayList<VXPortalUser>();
		String queryStr = "SELECT u FROM  XXPortalUser u ";
		String countQueryStr = "SELECT COUNT(u) FROM XXPortalUser u ";

		// Get total count first
		Query query = createUserSearchQuery(countQueryStr, null, searchCriteria);
		Long count = (Long) query.getSingleResult();
		if (count == null || count.longValue() == 0) {
			return returnList;
		}

		// Get actual data

		// Add sort by
		String sortBy = searchCriteria.getSortBy();
		String querySortBy = "u.loginId";
		if (!stringUtil.isEmpty(sortBy)) {
			sortBy = sortBy.trim();
			if (sortBy.equalsIgnoreCase("userId")) {
				querySortBy = "u.id";
			} else if (sortBy.equalsIgnoreCase("loginId")) {
				querySortBy = "ua.loginId";
			} else if (sortBy.equalsIgnoreCase("emailAddress")) {
				querySortBy = "u.emailAddress";
			} else if (sortBy.equalsIgnoreCase("firstName")) {
				querySortBy = "u.firstName";
			} else if (sortBy.equalsIgnoreCase("lastName")) {
				querySortBy = "u.lastName";
			} else {
				sortBy = "loginId";
				logger.error("Invalid sortBy provided. sortBy=" + sortBy);
			}
		} else {
			sortBy = "loginId";
		}

		// Default sort field
		String sortClause = " order by " + querySortBy + " ";

		// Add sort type
		String sortType = searchCriteria.getSortType();
		String querySortType = "asc";
		if (sortType != null) {
			if (sortType.equalsIgnoreCase("asc")
					|| sortType.equalsIgnoreCase("desc")) {
				querySortType = sortType;
			} else {
				logger.error("Invalid sortType. sortType=" + sortType);
			}
		}
		sortClause += querySortType;

		query = createUserSearchQuery(queryStr, sortClause, searchCriteria);

		// Set start index
		query.setFirstResult(searchCriteria.getStartIndex());

		searchUtil.updateQueryPageSize(query, searchCriteria);

		@SuppressWarnings("rawtypes")
		List resultList = query.getResultList();
		// Iterate over the result list and create the return list
		for (Object object : resultList) {
			XXPortalUser gjUser = (XXPortalUser) object;
			VXPortalUser userProfile = new VXPortalUser();
			gjUserToUserProfile(gjUser, userProfile);
			objectList.add(userProfile);
		}

		returnList.setPageSize(query.getMaxResults());
		returnList.setSortBy(sortBy);
		returnList.setSortType(querySortType);
		returnList.setStartIndex(query.getFirstResult());
		returnList.setTotalCount(count.longValue());
		returnList.setVXPortalUsers(objectList);
		return returnList;
	}

	/**
	 * @param queryStr
	 * @param sortClause
	 * @param searchCriteria
	 * @return
	 */
	private Query createUserSearchQuery(String queryStr, String sortClause,
			SearchCriteria searchCriteria) {
		HashMap<String, Object> paramList = searchCriteria.getParamList();

		String whereClause = "WHERE 1 = 1 ";

		// roles
		@SuppressWarnings("unchecked")
		List<String> roleList = (List<String>) paramList.get("roleList");
		if (roleList != null && roleList.size() > 0) {
			whereClause = ", XXPortalUserRole ur WHERE u.id = ur.userId";
			if (roleList.size() == 1) {
				// For only one role, let's do an equal to
				whereClause += " and ur.userRole = :role";
			} else {
				whereClause += " and ur.userRole in (:roleList)";
			}
		}

		// userId
		Long userId = (Long) paramList.get("userId");
		if (userId != null) {
			whereClause += " and u.id = :userId ";
		}

		// loginId
		String loginId = (String) paramList.get("loginId");
		if (loginId != null) {
			whereClause += " and LOWER(u.loginId) = :loginId ";
		}

		// emailAddress
		String emailAddress = (String) paramList.get("emailAddress");
		if (emailAddress != null) {
			whereClause += " and LOWER(u.emailAddress) = :emailAddress ";
		}

		// firstName
		String firstName = (String) paramList.get("firstName");
		if (firstName != null) {
			whereClause += " and LOWER(u.firstName) = :firstName ";
		}

		// lastName
		String lastName = (String) paramList.get("lastName");
		if (lastName != null) {
			whereClause += " and LOWER(u.lastName) = :lastName ";
		}

		// status
		Integer status = null;
		@SuppressWarnings("unchecked")
		List<Integer> statusList = (List<Integer>) paramList.get("statusList");
		if (statusList != null && statusList.size() == 1) {
			// use == condition
			whereClause += " and u.status = :status";
			status = statusList.get(0);
		} else if (statusList != null && statusList.size() > 1) {
			// use in operator
			whereClause += " and u.status in (:statusList) ";
		}

		// publicScreenName
		String publicScreenName = (String) paramList.get("publicScreenName");
		if (publicScreenName != null) {
			whereClause += " and LOWER(u.publicScreenName) = :publicScreenName ";
		}

		// familyScreenName
		String familyScreenName = (String) paramList.get("familyScreenName");
		if (familyScreenName != null) {
			whereClause += " and LOWER(u.familyScreenName) = :familyScreenName ";
		}

		if (sortClause != null) {
			whereClause += sortClause;
		}

		Query query = daoManager.getEntityManager().createQuery(
				queryStr + whereClause);

		if (roleList != null && roleList.size() > 0) {
			if (roleList.size() == 1) {
				query.setParameter("role", roleList.get(0));
			} else {
				query.setParameter("roleList", roleList);
			}
		}

		if (status != null) {
			query.setParameter("status", status);
		}
		if (statusList != null && statusList.size() > 1) {
			query.setParameter("statusList", statusList);
		}
		if (emailAddress != null) {
			query.setParameter("emailAddress", emailAddress.toLowerCase());
		}

		// userId
		if (userId != null) {
			query.setParameter("userId", userId);
		}
		// firstName
		if (firstName != null) {
			query.setParameter("firstName", firstName.toLowerCase());
		}
		// lastName
		if (lastName != null) {
			query.setParameter("lastName", lastName.toLowerCase());
		}

		// loginId
		if (loginId != null) {
			query.setParameter("loginId", loginId.toLowerCase());
		}

		// publicScreenName
		if (publicScreenName != null) {
			query.setParameter("publicScreenName",
					publicScreenName.toLowerCase());
		}

		// familyScreenName
		if (familyScreenName != null) {
			query.setParameter("familyScreenName",
					familyScreenName.toLowerCase());
		}

		return query;
	}

	public boolean deleteUserRole(Long userId, String userRole) {
		List<XXPortalUserRole> roleList = daoManager.getXXPortalUserRole().findByUserId(
				userId);
		for (XXPortalUserRole gjUserRole : roleList) {
			if (gjUserRole.getUserRole().equalsIgnoreCase(userRole)) {
				return deleteUserRole(userId, gjUserRole);
			}
		}
		return false;
	}

	public boolean deleteUserRole(Long userId, XXPortalUserRole gjUserRole) {
		/*if (RangerConstants.ROLE_USER.equals(gjUserRole.getUserRole())) {
			return false;
		}*/
		boolean publicRole = false;
		for (int i = 0; i < publicRoles.length; i++) {
			if (publicRoles[i].equalsIgnoreCase(gjUserRole.getUserRole())) {
				publicRole = true;
				break;
			}
		}
		if (!publicRole) {
			UserSessionBase sess = ContextUtil.getCurrentUserSession();
			if (sess == null || !sess.isUserAdmin()) {
				return false;
			}
		}

		daoManager.getXXPortalUserRole().remove(gjUserRole.getId());
		return true;
	}

	public XXPortalUserRole addUserRole(Long userId, String userRole) {
		List<XXPortalUserRole> roleList = daoManager.getXXPortalUserRole().findByUserId(
				userId);
		boolean publicRole = false;
		for (int i = 0; i < publicRoles.length; i++) {
			if (publicRoles[i].equalsIgnoreCase(userRole)) {
				publicRole = true;
				break;
			}
		}
		if (!publicRole) {
			UserSessionBase sess = ContextUtil.getCurrentUserSession();
			if (sess == null) {
				return null;
			}
			// Admin
			if (!sess.isUserAdmin()) {
				logger.error(
						"SECURITY WARNING: User trying to add non public role. userId="
								+ userId + ", role=" + userRole + ", session="
								+ sess.toString(), new Throwable());
				return null;
			}
		}

		for (XXPortalUserRole gjUserRole : roleList) {
			if (userRole.equalsIgnoreCase(gjUserRole.getUserRole())) {
				return gjUserRole;
			}
		}
		XXPortalUserRole userRoleObj = new XXPortalUserRole();
		userRoleObj.setUserRole(userRole.toUpperCase());
		userRoleObj.setUserId(userId);
		userRoleObj.setStatus(RangerConstants.STATUS_ENABLED);
		daoManager.getXXPortalUserRole().create(userRoleObj);

		// If role is not OTHER, then remove OTHER
		if (!RangerConstants.ROLE_OTHER.equalsIgnoreCase(userRole)) {
			deleteUserRole(userId, RangerConstants.ROLE_OTHER);
		}

		sessionMgr.resetUserSessionForProfiles(ContextUtil
				.getCurrentUserSession());
		return null;
	}

	public void checkAccess(Long userId) {
		XXPortalUser gjUser = daoManager.getXXPortalUser().getById(userId);
		if (gjUser == null) {
			throw restErrorUtil
					.create403RESTException("serverMsg.userMgrWrongUser"
							+ userId);
		}

		checkAccess(gjUser);
	}

	/**
	 * @param gjUser
	 * @return
	 */
	public void checkAccess(XXPortalUser gjUser) {
		if (gjUser == null) {
			throw restErrorUtil
					.create403RESTException("serverMsg.userMgrWrongUser");
		}
		UserSessionBase sess = ContextUtil.getCurrentUserSession();
		if (sess != null) {

			// Admin
			if (sess != null && sess.isUserAdmin()) {
				return;
			}

			// Self
			if (sess.getXXPortalUser().getId().equals(gjUser.getId())) {
				return;
			}

		}
		throw restErrorUtil.create403RESTException("User "
				+ " access denied. loggedInUser="
				+ (sess != null ? sess.getXXPortalUser().getId() : "Not Logged In")
				+ ", accessing user=" + gjUser.getId());

	}

	public void checkAccessForRead(XXPortalUser gjUser) {
		if (gjUser == null) {
			throw restErrorUtil
					.create403RESTException("serverMsg.userMgrWrongUser");
		}
		UserSessionBase sess = ContextUtil.getCurrentUserSession();
		if (sess != null) {

			// Admin
			if (sess != null && sess.isUserAdmin()) {
				return;
			}

			// Self
			if (sess.getXXPortalUser().getId().equals(gjUser.getId())) {
				return;
			}

		}
		throw restErrorUtil.create403RESTException("User "
				+ " access denied. loggedInUser="
				+ (sess != null ? sess.getXXPortalUser().getId() : "Not Logged In")
				+ ", accessing user=" + gjUser.getId());

	}

	public String encrypt(String loginId, String password) {
		String saltEncodedpasswd = md5Encoder.encodePassword(password, loginId);
		return saltEncodedpasswd;
	}

	public VXPortalUser createUser(VXPortalUser userProfile) {
		XXPortalUser xXPortalUser = this
				.createUser(userProfile, RangerCommonEnums.STATUS_ENABLED);
		return mapXXPortalUserVXPortalUser(xXPortalUser);
	}

	public VXPortalUser createDefaultAccountUser(VXPortalUser userProfile) {
		if(userProfile.getPassword()==null||userProfile.getPassword().trim().isEmpty()){
			userProfile.setUserSource(RangerCommonEnums.USER_EXTERNAL);
		}
		// access control
		UserSessionBase session = ContextUtil.getCurrentUserSession();
		if (session != null) {
			if (!session.isUserAdmin()) {
				throw restErrorUtil.create403RESTException("User "
						+ "creation denied. LoggedInUser="
						+ (session != null ? session.getXXPortalUser().getId()
								: "Not Logged In")
						+ " ,isn't permitted to perform the action.");

			}
		}

		XXPortalUser xXPortalUser = null;
		String loginId = userProfile.getLoginId();
		String emailAddress = userProfile.getEmailAddress();

		if (loginId != null && !loginId.isEmpty()) {
			xXPortalUser = this.findByLoginId(loginId);
			if (xXPortalUser == null) {
				if (emailAddress != null && !emailAddress.isEmpty()) {
					xXPortalUser = this.findByEmailAddress(emailAddress);
					if (xXPortalUser == null) {
						xXPortalUser = this.createUser(userProfile,
								RangerCommonEnums.STATUS_ENABLED);
					} else {
						throw restErrorUtil
								.createRESTException(
										"The email address "
												+ emailAddress
												+ " you've provided already exists. Please try again with different "
												+ "email address.",
										MessageEnums.OPER_NOT_ALLOWED_FOR_STATE);
					}
				} else {
					String randomEmail = GUIDUtil.genGUI();
					userProfile.setEmailAddress(randomEmail);
					xXPortalUser = this.createUser(userProfile,
							RangerCommonEnums.STATUS_ENABLED);
				}
			} else {
				/*throw restErrorUtil
						.createRESTException(
								"The login id "
										+ loginId
										+ " you've provided already exists. Please try again with different "
										+ "login id.",
								MessageEnums.OPER_NOT_ALLOWED_FOR_STATE);*/
			}
		}

		return mapXXPortalUserToVXPortalUserForDefaultAccount(xXPortalUser);
	}

	private VXPortalUser mapXXPortalUserToVXPortalUserForDefaultAccount(XXPortalUser user) {

		VXPortalUser userProfile = new VXPortalUser();

		userProfile.setLoginId(user.getLoginId());
		userProfile.setEmailAddress(user.getEmailAddress());
		userProfile.setStatus(user.getStatus());
		userProfile.setUserRoleList(new ArrayList<String>());
		userProfile.setId(user.getId());
		userProfile.setFirstName(user.getFirstName());
		userProfile.setLastName(user.getLastName());
		userProfile.setPublicScreenName(user.getPublicScreenName());
		userProfile.setEmailAddress(user.getEmailAddress());

		List<XXPortalUserRole> gjUserRoleList = daoManager.getXXPortalUserRole()
				.findByParentId(user.getId());

		for (XXPortalUserRole gjUserRole : gjUserRoleList) {
			userProfile.getUserRoleList().add(gjUserRole.getUserRole());
		}

		return userProfile;
	}

	public boolean isUserInRole(Long userId, String role) {
		XXPortalUserRole xXPortalUserRole = daoManager.getXXPortalUserRole().findByRoleUserId(
				userId, role);
		if (xXPortalUserRole != null) {
			String userRole = xXPortalUserRole.getUserRole();
			if (userRole.equalsIgnoreCase(role)) {
				return true;
			}
		}
		return false;
	}

	public XXPortalUser updateUserWithPass(VXPortalUser userProfile) {
		String updatedPassword = userProfile.getPassword();
		XXPortalUser xXPortalUser = this.updateUser(userProfile);

		if (updatedPassword != null && !updatedPassword.isEmpty()) {
			if (!stringUtil.validatePassword(updatedPassword,
					new String[] { xXPortalUser.getFirstName(), xXPortalUser.getLastName(),
							xXPortalUser.getLoginId() })) {
				logger.warn("SECURITY:changePassword(). Invalid new password. userId="
						+ xXPortalUser.getId());

				throw restErrorUtil.createRESTException(
						"serverMsg.userMgrNewPassword",
						MessageEnums.INVALID_PASSWORD, null, null,
						"" + xXPortalUser.getId());
			}

			String encryptedNewPwd = encrypt(xXPortalUser.getLoginId(),
					updatedPassword);
			xXPortalUser.setPassword(encryptedNewPwd);
			xXPortalUser = daoManager.getXXPortalUser().update(xXPortalUser);
		}
		return xXPortalUser;
	}
}
