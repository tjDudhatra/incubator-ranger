package org.apache.ranger.services.yarn.client.json.model;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlRootElement;

import org.codehaus.jackson.annotate.JsonAutoDetect;
import org.codehaus.jackson.annotate.JsonAutoDetect.Visibility;
import org.codehaus.jackson.annotate.JsonIgnoreProperties;
import org.codehaus.jackson.map.annotate.JsonSerialize;



@JsonAutoDetect(getterVisibility=Visibility.NONE, setterVisibility=Visibility.NONE, fieldVisibility=Visibility.ANY)
@JsonSerialize(include=JsonSerialize.Inclusion.NON_NULL )
@JsonIgnoreProperties(ignoreUnknown=true)
@XmlRootElement
@XmlAccessorType(XmlAccessType.FIELD)
public class YarnSchedulerResponse implements java.io.Serializable {
    private static final long serialVersionUID = 1L;

    private YarnScheduler scheduler = null;

    public YarnScheduler getScheduler() { return scheduler; }
    
    public List<String> getQueueNames() {
    	List<String> ret = new ArrayList<String>();

    	if(scheduler != null) {
    		scheduler.collectQueueNames(ret);
    	}

    	return ret;
    }
    

    @JsonAutoDetect(getterVisibility=Visibility.NONE, setterVisibility=Visibility.NONE, fieldVisibility=Visibility.ANY)
    @JsonSerialize(include=JsonSerialize.Inclusion.NON_NULL )
    @JsonIgnoreProperties(ignoreUnknown=true)
    @XmlRootElement
    @XmlAccessorType(XmlAccessType.FIELD)
    public static class YarnScheduler implements java.io.Serializable {
        private static final long serialVersionUID = 1L;

        private YarnSchedulerInfo schedulerInfo = null;

        public YarnSchedulerInfo getSchedulerInfo() { return schedulerInfo; }

        public void collectQueueNames(List<String> queueNames) {
        	if(schedulerInfo != null) {
        		schedulerInfo.collectQueueNames(queueNames, null);
        	}
        }
    }

    @JsonAutoDetect(getterVisibility=Visibility.NONE, setterVisibility=Visibility.NONE, fieldVisibility=Visibility.ANY)
    @JsonSerialize(include=JsonSerialize.Inclusion.NON_NULL )
    @JsonIgnoreProperties(ignoreUnknown=true)
    @XmlRootElement
    @XmlAccessorType(XmlAccessType.FIELD)
    public static class YarnSchedulerInfo implements java.io.Serializable {
        private static final long serialVersionUID = 1L;

        private String     queueName = null;
        private YarnQueues queues    = null;

        public String getQueueName() { return queueName; }

        public YarnQueues getQueues() { return queues; }

        public void collectQueueNames(List<String> queueNames, String parentQueueName) {
        	if(queueName != null) {
        		String queueFqdn = parentQueueName == null ? queueName : parentQueueName + "." + queueName;

        		queueNames.add(queueFqdn);

            	if(queues != null) {
            		queues.collectQueueNames(queueNames, queueFqdn);
            	}
        	}
        }
    }

    @JsonAutoDetect(getterVisibility=Visibility.NONE, setterVisibility=Visibility.NONE, fieldVisibility=Visibility.ANY)
    @JsonSerialize(include=JsonSerialize.Inclusion.NON_NULL )
    @JsonIgnoreProperties(ignoreUnknown=true)
    @XmlRootElement
    @XmlAccessorType(XmlAccessType.FIELD)
    public static class YarnQueues implements java.io.Serializable {
        private static final long serialVersionUID = 1L;

        private List<YarnSchedulerInfo> queue = null;

        public List<YarnSchedulerInfo> getQueue() { return queue; }

        public void collectQueueNames(List<String> queueNames, String parentQueueName) {
        	if(queue != null) {
        		for(YarnSchedulerInfo schedulerInfo : queue) {
        			schedulerInfo.collectQueueNames(queueNames, parentQueueName);
        		}
        	}
        }
    }
}
