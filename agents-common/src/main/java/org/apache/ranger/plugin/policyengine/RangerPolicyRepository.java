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

package org.apache.ranger.plugin.policyengine;

import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.lang.StringUtils;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.ranger.authorization.hadoop.config.RangerConfiguration;
import org.apache.ranger.plugin.contextenricher.RangerContextEnricher;
import org.apache.ranger.plugin.model.RangerPolicy;
import org.apache.ranger.plugin.model.RangerServiceDef;
import org.apache.ranger.plugin.policyevaluator.RangerPolicyEvaluator;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

public class RangerPolicyRepository {
    private static final Log LOG = LogFactory.getLog(RangerPolicyRepository.class);

    private String serviceName                               = null;
    private List<RangerPolicyEvaluatorFacade> policyEvaluators  = null;
    private List<RangerContextEnricher> contextEnrichers        = null;
    private RangerServiceDef serviceDef                         = null;
    // Not used at this time
    private boolean useCachePolicyEngine                                = false;
    private Map<String, RangerAccessData<Boolean>> accessAuditCache     = null;

    private static int RANGER_POLICYENGINE_AUDITRESULT_CACHE_SIZE = 64*1024;

    RangerPolicyRepository(String serviceName) {
        super();
        this.serviceName = serviceName;
    }
    String getRepositoryName() {
        return serviceName;
    }
    List<RangerPolicyEvaluatorFacade> getPolicyEvaluators() {
        return policyEvaluators;
    }
    List<RangerContextEnricher> getContextEnrichers() {
        return contextEnrichers;
    }
    RangerServiceDef getServiceDef() {
        return serviceDef;
    }

    void init(RangerServiceDef serviceDef, List<RangerPolicy> policies) {

        if(LOG.isDebugEnabled()) {
            LOG.debug("==> RangerPolicyRepository.init(" + serviceDef + ", policies.count=" + (policies == null ? 0 : policies.size()) + ")");
        }

        this.serviceDef = serviceDef;

        contextEnrichers = new ArrayList<RangerContextEnricher>();

        if (!CollectionUtils.isEmpty(serviceDef.getContextEnrichers())) {
            for (RangerServiceDef.RangerContextEnricherDef enricherDef : serviceDef.getContextEnrichers()) {
                if (enricherDef == null) {
                    continue;
                }

                RangerContextEnricher contextEnricher = buildContextEnricher(enricherDef);

                contextEnrichers.add(contextEnricher);
            }
        }

        policyEvaluators = new ArrayList<RangerPolicyEvaluatorFacade>();

        for (RangerPolicy policy : policies) {
            if (!policy.getIsEnabled()) {
                continue;
            }

            RangerPolicyEvaluatorFacade evaluator = buildPolicyEvaluator(policy, serviceDef);

            if (evaluator != null) {
                policyEvaluators.add(evaluator);
            }
        }
        Collections.sort(policyEvaluators);

        String propertyName = "ranger.plugin." + serviceName + ".policyengine.auditcachesize";

        int auditResultCacheSize = RangerConfiguration.getInstance().getInt(propertyName, RANGER_POLICYENGINE_AUDITRESULT_CACHE_SIZE);

        accessAuditCache = new CacheMap<String, RangerAccessData<Boolean>>(auditResultCacheSize);

        if(LOG.isDebugEnabled()) {
            LOG.debug("<== RangerPolicyRepository.init(" + serviceDef + ", policies.count=" + (policies == null ? 0 : policies.size()) + ")");
        }
    }

    private RangerContextEnricher buildContextEnricher(RangerServiceDef.RangerContextEnricherDef enricherDef) {
        if(LOG.isDebugEnabled()) {
            LOG.debug("==> RangerPolicyRepository.buildContextEnricher(" + enricherDef + ")");
        }

        RangerContextEnricher ret = null;

        String name    = enricherDef != null ? enricherDef.getName()     : null;
        String clsName = enricherDef != null ? enricherDef.getEnricher() : null;

        if(! StringUtils.isEmpty(clsName)) {
            try {
                @SuppressWarnings("unchecked")
                Class<RangerContextEnricher> enricherClass = (Class<RangerContextEnricher>)Class.forName(clsName);

                ret = enricherClass.newInstance();
            } catch(Exception excp) {
                LOG.error("failed to instantiate context enricher '" + clsName + "' for '" + name + "'", excp);
            }
        }

        if(ret != null) {
            ret.init(enricherDef);
        }

        if(LOG.isDebugEnabled()) {
            LOG.debug("<== RangerPolicyRepository.buildContextEnricher(" + enricherDef + "): " + ret);
        }
        return ret;
    }

    private RangerPolicyEvaluatorFacade buildPolicyEvaluator(RangerPolicy policy, RangerServiceDef serviceDef) {
        if(LOG.isDebugEnabled()) {
            LOG.debug("==> RangerPolicyRepository.buildPolicyEvaluator(" + policy + "," + serviceDef + ")");
        }

        RangerPolicyEvaluatorFacade ret = null;

        ret = new RangerPolicyEvaluatorFacade(useCachePolicyEngine);
        ret.init(policy, serviceDef);

        if(LOG.isDebugEnabled()) {
            LOG.debug("<== RangerPolicyRepository.buildPolicyEvaluator(" + policy + "," + serviceDef + "): " + ret);
        }
        return ret;
    }

    synchronized void retrieveAuditEnabled(RangerAccessRequest request, RangerAccessResult ret) {
        if (LOG.isDebugEnabled()) {
            LOG.debug("==> RangerPolicyRepository.retrieveAuditEnabled()");
        }
        RangerAccessData<Boolean> value = accessAuditCache.get(request.getResource().toString());
        if ((value != null)) {
            ret.setIsAudited(value.getAccessDetails());
        }

        if (LOG.isDebugEnabled()) {
            LOG.debug("<== RangerPolicyRepository.retrieveAuditEnabled()");
        }
    }

    synchronized void storeAuditEnabled(RangerAccessRequest request, RangerAccessResult ret) {
        if (LOG.isDebugEnabled()) {
            LOG.debug("==> RangerPolicyRepository.storeAuditEnabled()");
        }
        RangerAccessData<Boolean> lookup = accessAuditCache.get(request.getResource().toString());
        if ((lookup == null && ret.getIsAuditedDetermined() == true)) {
            RangerAccessData<Boolean> value = new RangerAccessData<Boolean>(request.toString());
            value.setAccessDetails(ret.getIsAudited());
            accessAuditCache.put(request.getResource().toString(), value);
        }

        if (LOG.isDebugEnabled()) {
            LOG.debug("<== RangerPolicyRepository.storeAuditEnabled()");
        }
    }

    @Override
    public String toString( ) {
        StringBuilder sb = new StringBuilder();

        toString(sb);

        return sb.toString();
    }

    public StringBuilder toString(StringBuilder sb) {

        sb.append("RangerPolicyRepository={");

        sb.append("serviceName={").append(serviceName).append("} ");
        sb.append("serviceDef={").append(serviceDef).append("} ");
        sb.append("policyEvaluators={");
        if (policyEvaluators != null) {
            for (RangerPolicyEvaluator policyEvaluator : policyEvaluators) {
                if (policyEvaluator != null) {
                    sb.append(policyEvaluator).append(" ");
                }
            }
        }
        if (contextEnrichers != null) {
            for (RangerContextEnricher contextEnricher : contextEnrichers) {
                if (contextEnricher != null) {
                    sb.append(contextEnricher).append(" ");
                }
            }
        }
        sb.append("useCachePolicyEngine={").append(useCachePolicyEngine).append("} ");

        sb.append("} ");

        return sb;
    }

}
