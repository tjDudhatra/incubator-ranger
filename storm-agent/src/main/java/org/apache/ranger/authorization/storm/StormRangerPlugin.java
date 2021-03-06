package org.apache.ranger.authorization.storm;

import java.util.Set;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.hadoop.security.authentication.util.KerberosName;
import org.apache.ranger.authorization.storm.StormRangerPlugin.StormConstants.PluginConfiguration;
import org.apache.ranger.authorization.storm.StormRangerPlugin.StormConstants.ResourceName;
import org.apache.ranger.plugin.audit.RangerDefaultAuditHandler;
import org.apache.ranger.plugin.policyengine.RangerAccessRequest;
import org.apache.ranger.plugin.policyengine.RangerAccessRequestImpl;
import org.apache.ranger.plugin.policyengine.RangerResourceImpl;
import org.apache.ranger.plugin.service.RangerBasePlugin;

import com.google.common.collect.Sets;

public class StormRangerPlugin extends RangerBasePlugin {
	
	private static final Log LOG = LogFactory.getLog(StormRangerPlugin.class);
	boolean initialized = false;
	
	public StormRangerPlugin() {
		super(PluginConfiguration.ServiceType, PluginConfiguration.AuditApplicationType);
	}
	
	// this method isn't expected to be invoked often.  Per knox design this would be invoked ONCE right after the authorizer servlet is loaded
	@Override
	synchronized public void init() {
		if (!initialized) {
			// mandatory call to base plugin
			super.init();
			// One time call to register the audit hander with the policy engine.
			super.setDefaultAuditHandler(new RangerDefaultAuditHandler());
			// this needed to set things right in the nimbus process
			if (KerberosName.getRules() == null) {
				KerberosName.setRules("DEFAULT") ;
			}
			initialized = true;
			LOG.info("StormRangerPlugin initialized!");
		}
	}

	public RangerAccessRequest buildAccessRequest(String _user, String[] _groups, String _clientIp, String _topology, String _operation) {
		
		RangerAccessRequestImpl request = new RangerAccessRequestImpl();
		request.setUser(_user);
		if (_groups != null && _groups.length > 0) {
			Set<String> groups = Sets.newHashSet(_groups);
			request.setUserGroups(groups);
		}
		request.setAccessType(_operation);
		request.setClientIPAddress(_clientIp);
		// build resource and connect stuff into request
		RangerResourceImpl resource = new RangerResourceImpl();
		resource.setValue(ResourceName.Topology, _topology);
		request.setResource(resource);
		
		if (LOG.isDebugEnabled()) {
			LOG.debug("Returning request: " + request.toString());
		}
		
		return request;
	}

	static public class StormConstants {
		// Plugin parameters
		static class PluginConfiguration {
			static final String ServiceType = "storm";
			static final String AuditApplicationType = "storm";
		}
		
		// must match the corresponding string used in service definition file
		static class ResourceName {
			static final String Topology = "topology";
		}
	}

}
