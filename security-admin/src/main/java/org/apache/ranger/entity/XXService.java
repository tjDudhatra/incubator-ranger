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
package org.apache.ranger.entity;

import java.util.Date;

import javax.persistence.*;
import javax.xml.bind.annotation.XmlRootElement;

@Entity
@Cacheable
@XmlRootElement
@Table(name = "x_service")
public class XXService extends XXDBBase implements java.io.Serializable {
	private static final long serialVersionUID = 1L;
	/**
	 * id of the XXService
	 * <ul>
	 * </ul>
	 *
	 */
	@Id
	@SequenceGenerator(name = "x_service_SEQ", sequenceName = "x_service_SEQ", allocationSize = 1)
	@GeneratedValue(strategy = GenerationType.AUTO, generator = "x_service_SEQ")
	@Column(name = "id")
	protected Long id;
	
	/**
	 * Global Id for the object
	 * <ul>
	 * <li>The maximum length for this attribute is <b>512</b>.
	 * </ul>
	 *
	 */
	@Column(name = "guid", unique = true, nullable = false, length = 512)
	protected String guid;

	/**
	 * version of the XXServiceDef
	 * <ul>
	 * </ul>
	 *
	 */
	@Column(name = "version")
	protected Long version;

	/**
	 * type of the XXService
	 * <ul>
	 * </ul>
	 *
	 */
	@Column(name = "type")
	protected Long type;

	/**
	 * name of the XXService
	 * <ul>
	 * </ul>
	 *
	 */
	@Column(name = "name")
	protected String name;

	/**
	 * policyVersion of the XXService
	 * <ul>
	 * </ul>
	 *
	 */
	@Column(name = "policy_version")
	protected Long policyVersion;

	/**
	 * policyUpdateTime of the XXService
	 * <ul>
	 * </ul>
	 *
	 */
	@Temporal(TemporalType.TIMESTAMP)
	@Column(name = "policy_update_time")
	protected Date policyUpdateTime;

	/**
	 * description of the XXService
	 * <ul>
	 * </ul>
	 *
	 */
	@Column(name = "description")
	protected String description;

	/**
	 * isEnabled of the XXService
	 * <ul>
	 * </ul>
	 *
	 */
	@Column(name = "is_enabled")
	protected Boolean isEnabled;

	/**
	 * This method sets the value to the member attribute <b> id</b> . You
	 * cannot set null to the attribute.
	 * 
	 * @param id
	 *            Value to set member attribute <b> id</b>
	 */
	public void setId(Long id) {
		this.id = id;
	}

	/**
	 * Returns the value for the member attribute <b>id</b>
	 * 
	 * @return Date - value of member attribute <b>id</b> .
	 */
	public Long getId() {
		return this.id;
	}
	
	/**
	 * @return the gUID
	 */
	public String getGuid() {
		return this.guid;
	}

	/**
	 * @param guid
	 *            the gUID to set
	 */
	public void setGuid(String guid) {
		this.guid = guid;
	}

	/**
	 * This method sets the value to the member attribute <b> version</b> . You
	 * cannot set null to the attribute.
	 * 
	 * @param version
	 *            Value to set member attribute <b> version</b>
	 */
	public void setVersion(Long version) {
		this.version = version;
	}

	/**
	 * Returns the value for the member attribute <b>version</b>
	 * 
	 * @return Date - value of member attribute <b>version</b> .
	 */
	public Long getVersion() {
		return this.version;
	}

	/**
	 * This method sets the value to the member attribute <b> type</b> . You
	 * cannot set null to the attribute.
	 * 
	 * @param type
	 *            Value to set member attribute <b> type</b>
	 */
	public void setType(Long type) {
		this.type = type;
	}

	/**
	 * Returns the value for the member attribute <b>type</b>
	 * 
	 * @return Date - value of member attribute <b>type</b> .
	 */
	public Long getType() {
		return this.type;
	}

	/**
	 * This method sets the value to the member attribute <b> name</b> . You
	 * cannot set null to the attribute.
	 * 
	 * @param name
	 *            Value to set member attribute <b> name</b>
	 */
	public void setName(String name) {
		this.name = name;
	}

	/**
	 * Returns the value for the member attribute <b>name</b>
	 * 
	 * @return Date - value of member attribute <b>name</b> .
	 */
	public String getName() {
		return this.name;
	}

	/**
	 * This method sets the value to the member attribute <b> policyVersion</b>
	 * . You cannot set null to the attribute.
	 * 
	 * @param policyVersion
	 *            Value to set member attribute <b> policyVersion</b>
	 */
	public void setPolicyVersion(Long policyVersion) {
		this.policyVersion = policyVersion;
	}

	/**
	 * Returns the value for the member attribute <b>policyVersion</b>
	 * 
	 * @return Date - value of member attribute <b>policyVersion</b> .
	 */
	public Long getPolicyVersion() {
		return this.policyVersion;
	}

	/**
	 * This method sets the value to the member attribute <b>
	 * policyUpdateTime</b> . You cannot set null to the attribute.
	 * 
	 * @param policyUpdateTime
	 *            Value to set member attribute <b> policyUpdateTime</b>
	 */
	public void setPolicyUpdateTime(Date policyUpdateTime) {
		this.policyUpdateTime = policyUpdateTime;
	}

	/**
	 * Returns the value for the member attribute <b>policyUpdateTime</b>
	 * 
	 * @return Date - value of member attribute <b>policyUpdateTime</b> .
	 */
	public Date getPolicyUpdateTime() {
		return this.policyUpdateTime;
	}

	/**
	 * This method sets the value to the member attribute <b> description</b> .
	 * You cannot set null to the attribute.
	 * 
	 * @param description
	 *            Value to set member attribute <b> description</b>
	 */
	public void setDescription(String description) {
		this.description = description;
	}

	/**
	 * Returns the value for the member attribute <b>description</b>
	 * 
	 * @return Date - value of member attribute <b>description</b> .
	 */
	public String getDescription() {
		return this.description;
	}

	/**
	 * This method sets the value to the member attribute <b> isEnabled</b> .
	 * You cannot set null to the attribute.
	 * 
	 * @param isEnabled
	 *            Value to set member attribute <b> isEnabled</b>
	 */
	public void setIsEnabled(Boolean isEnabled) {
		this.isEnabled = isEnabled;
	}

	/**
	 * Returns the value for the member attribute <b>isEnabled</b>
	 * 
	 * @return Date - value of member attribute <b>isEnabled</b> .
	 */
	public Boolean getIsenabled() {
		return this.isEnabled;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see java.lang.Object#equals(java.lang.Object)
	 */
	@Override
	public boolean equals(Object obj) {
		if (!super.equals(obj)) {
			return false;
		}
		if (this == obj) {
			return true;
		}
		if (getClass() != obj.getClass()) {
			return false;
		}
		XXService other = (XXService) obj;
		if (description == null) {
			if (other.description != null) {
				return false;
			}
		} else if (!description.equals(other.description)) {
			return false;
		}
		if (id == null) {
			if (other.id != null) {
				return false;
			}
		} else if (!id.equals(other.id)) {
			return false;
		}
		if (isEnabled == null) {
			if (other.isEnabled != null) {
				return false;
			}
		} else if (!isEnabled.equals(other.isEnabled)) {
			return false;
		}
		if (name == null) {
			if (other.name != null) {
				return false;
			}
		} else if (!name.equals(other.name)) {
			return false;
		}
		if (policyUpdateTime == null) {
			if (other.policyUpdateTime != null) {
				return false;
			}
		} else if (!policyUpdateTime.equals(other.policyUpdateTime)) {
			return false;
		}
		if (policyVersion == null) {
			if (other.policyVersion != null) {
				return false;
			}
		} else if (!policyVersion.equals(other.policyVersion)) {
			return false;
		}
		if (type == null) {
			if (other.type != null) {
				return false;
			}
		} else if (!type.equals(other.type)) {
			return false;
		}
		if (version == null) {
			if (other.version != null) {
				return false;
			}
		} else if (!version.equals(other.version)) {
			return false;
		}
		if (guid == null) {
			if (other.guid != null) {
				return false;
			}
		} else if (!guid.equals(other.guid)) {
			return false;
		}
		return true;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see java.lang.Object#toString()
	 */
	@Override
	public String toString() {
		return "XXService [" + super.toString() + " id=" + id + ", guid="
				+ guid + ", version=" + version + ", type=" + type + ", name="
				+ name + ", policyVersion=" + policyVersion
				+ ", policyUpdateTime=" + policyUpdateTime + ", description="
				+ description + ", isEnabled=" + isEnabled + "]";
	}

}