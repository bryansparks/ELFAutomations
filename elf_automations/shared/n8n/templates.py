"""
N8N Workflow Templates

Pre-built workflow patterns for common business operations.
"""

from typing import Dict, Any, List
from datetime import datetime


class WorkflowTemplates:
    """Collection of workflow templates organized by category"""
    
    @staticmethod
    def data_pipeline_etl() -> Dict[str, Any]:
        """Extract, Transform, Load data pipeline"""
        return {
            "name": "ETL Data Pipeline",
            "nodes": [
                {
                    "id": "schedule",
                    "name": "Daily Schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {
                        "rule": {
                            "interval": [{"field": "days", "intervalValue": 1}],
                            "hour": 2,
                            "minute": 0
                        }
                    }
                },
                {
                    "id": "extract",
                    "name": "Extract Data",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 4,
                    "position": [450, 300],
                    "parameters": {
                        "method": "GET",
                        "url": "={{$vars.source_url}}",
                        "authentication": "genericCredentialType",
                        "genericAuthType": "httpHeaderAuth",
                        "options": {
                            "timeout": 30000
                        }
                    }
                },
                {
                    "id": "transform",
                    "name": "Transform Data",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 1,
                    "position": [650, 300],
                    "parameters": {
                        "jsCode": """
// Transform the extracted data
const items = $input.all();
const transformedItems = [];

for (const item of items) {
    const data = item.json;
    
    // Example transformation
    transformedItems.push({
        json: {
            id: data.id,
            processed_at: new Date().toISOString(),
            // Add your transformations here
            transformed_value: data.value * 1.1
        }
    });
}

return transformedItems;
"""
                    }
                },
                {
                    "id": "load",
                    "name": "Load to Database",
                    "type": "n8n-nodes-base.postgres",
                    "typeVersion": 2.3,
                    "position": [850, 300],
                    "parameters": {
                        "operation": "insert",
                        "table": "{{$vars.target_table}}",
                        "columns": "id,processed_at,transformed_value",
                        "options": {}
                    }
                },
                {
                    "id": "notify",
                    "name": "Notify Completion",
                    "type": "n8n-nodes-base.emailSend",
                    "typeVersion": 2.1,
                    "position": [1050, 300],
                    "parameters": {
                        "sendTo": "={{$vars.notification_email}}",
                        "subject": "ETL Pipeline Completed",
                        "message": "Pipeline processed {{$node['Transform Data'].outputCount}} records successfully.",
                        "options": {}
                    }
                }
            ],
            "connections": {
                "Daily Schedule": {"main": [[{"node": "Extract Data", "type": "main", "index": 0}]]},
                "Extract Data": {"main": [[{"node": "Transform Data", "type": "main", "index": 0}]]},
                "Transform Data": {"main": [[{"node": "Load to Database", "type": "main", "index": 0}]]},
                "Load to Database": {"main": [[{"node": "Notify Completion", "type": "main", "index": 0}]]}
            },
            "settings": {
                "saveDataSuccessExecution": "all",
                "saveManualExecutions": True,
                "callerPolicy": "workflowsFromSameOwner",
                "errorWorkflow": "error-handler"
            }
        }
    
    @staticmethod
    def crm_sync_integration() -> Dict[str, Any]:
        """Sync data between CRM systems"""
        return {
            "name": "CRM Sync Integration",
            "nodes": [
                {
                    "id": "webhook",
                    "name": "CRM Update Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {
                        "httpMethod": "POST",
                        "path": "crm-sync",
                        "responseMode": "responseNode",
                        "options": {
                            "rawBody": False
                        }
                    }
                },
                {
                    "id": "validate",
                    "name": "Validate Data",
                    "type": "n8n-nodes-base.if",
                    "typeVersion": 1,
                    "position": [450, 300],
                    "parameters": {
                        "conditions": {
                            "string": [
                                {
                                    "value1": "={{$json.customer_id}}",
                                    "operation": "isNotEmpty"
                                },
                                {
                                    "value1": "={{$json.email}}",
                                    "operation": "regex",
                                    "value2": "^[^@]+@[^@]+\\.[^@]+$"
                                }
                            ]
                        },
                        "combineOperation": "all"
                    }
                },
                {
                    "id": "fetch_existing",
                    "name": "Check Existing Record",
                    "type": "n8n-nodes-base.postgres",
                    "typeVersion": 2.3,
                    "position": [650, 200],
                    "parameters": {
                        "operation": "select",
                        "table": "customers",
                        "limit": 1,
                        "where": {
                            "customer_id": "={{$json.customer_id}}"
                        }
                    }
                },
                {
                    "id": "merge",
                    "name": "Merge Data",
                    "type": "n8n-nodes-base.merge",
                    "typeVersion": 2,
                    "position": [850, 300],
                    "parameters": {
                        "mode": "combine",
                        "combinationMode": "multiplex"
                    }
                },
                {
                    "id": "update_target",
                    "name": "Update Target CRM",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 4,
                    "position": [1050, 300],
                    "parameters": {
                        "method": "PUT",
                        "url": "={{$vars.target_crm_url}}/api/customers/{{$json.customer_id}}",
                        "sendBody": True,
                        "bodyParameters": {
                            "parameters": [
                                {
                                    "name": "data",
                                    "value": "={{$json}}"
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "respond",
                    "name": "Send Response",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1,
                    "position": [1250, 300],
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": {
                            "success": True,
                            "message": "CRM sync completed",
                            "customer_id": "={{$json.customer_id}}"
                        }
                    }
                },
                {
                    "id": "error_response",
                    "name": "Error Response",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1,
                    "position": [650, 500],
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": {
                            "success": False,
                            "error": "Invalid data format"
                        },
                        "options": {
                            "responseCode": 400
                        }
                    }
                }
            ],
            "connections": {
                "CRM Update Webhook": {"main": [[{"node": "Validate Data", "type": "main", "index": 0}]]},
                "Validate Data": {
                    "main": [
                        [{"node": "Check Existing Record", "type": "main", "index": 0}],
                        [{"node": "Error Response", "type": "main", "index": 0}]
                    ]
                },
                "Check Existing Record": {"main": [[{"node": "Merge Data", "type": "main", "index": 0}]]},
                "Merge Data": {"main": [[{"node": "Update Target CRM", "type": "main", "index": 0}]]},
                "Update Target CRM": {"main": [[{"node": "Send Response", "type": "main", "index": 0}]]}
            }
        }
    
    @staticmethod
    def approval_workflow() -> Dict[str, Any]:
        """Multi-step approval process"""
        return {
            "name": "Approval Workflow",
            "nodes": [
                {
                    "id": "form",
                    "name": "Approval Request Form",
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {
                        "httpMethod": "POST",
                        "path": "approval-request",
                        "responseMode": "responseNode"
                    }
                },
                {
                    "id": "create_ticket",
                    "name": "Create Approval Ticket",
                    "type": "n8n-nodes-base.postgres",
                    "typeVersion": 2.3,
                    "position": [450, 300],
                    "parameters": {
                        "operation": "insert",
                        "table": "approval_tickets",
                        "columns": "requester,type,amount,description,status,created_at",
                        "columnData": {
                            "requester": "={{$json.requester}}",
                            "type": "={{$json.type}}",
                            "amount": "={{$json.amount}}",
                            "description": "={{$json.description}}",
                            "status": "pending",
                            "created_at": "={{new Date().toISOString()}}"
                        }
                    }
                },
                {
                    "id": "check_amount",
                    "name": "Check Approval Level",
                    "type": "n8n-nodes-base.switch",
                    "typeVersion": 1,
                    "position": [650, 300],
                    "parameters": {
                        "dataType": "number",
                        "value1": "={{$json.amount}}",
                        "rules": {
                            "rules": [
                                {
                                    "operation": "smaller",
                                    "value2": 1000,
                                    "output": 0
                                },
                                {
                                    "operation": "smaller",
                                    "value2": 10000,
                                    "output": 1
                                }
                            ]
                        },
                        "fallbackOutput": 2
                    }
                },
                {
                    "id": "notify_manager",
                    "name": "Notify Manager",
                    "type": "n8n-nodes-base.slack",
                    "typeVersion": 2.1,
                    "position": [850, 200],
                    "parameters": {
                        "operation": "post",
                        "channel": "#approvals-level1",
                        "text": "New approval request from {{$json.requester}} for ${{$json.amount}}",
                        "otherOptions": {}
                    }
                },
                {
                    "id": "notify_director",
                    "name": "Notify Director",
                    "type": "n8n-nodes-base.slack",
                    "typeVersion": 2.1,
                    "position": [850, 300],
                    "parameters": {
                        "operation": "post",
                        "channel": "#approvals-level2",
                        "text": "Approval escalation: {{$json.requester}} requesting ${{$json.amount}}",
                        "otherOptions": {}
                    }
                },
                {
                    "id": "notify_executive",
                    "name": "Notify Executive",
                    "type": "n8n-nodes-base.slack",
                    "typeVersion": 2.1,
                    "position": [850, 400],
                    "parameters": {
                        "operation": "post",
                        "channel": "#approvals-executive",
                        "text": "Executive approval needed: {{$json.requester}} requesting ${{$json.amount}}",
                        "otherOptions": {}
                    }
                },
                {
                    "id": "wait",
                    "name": "Wait for Decision",
                    "type": "n8n-nodes-base.wait",
                    "typeVersion": 1,
                    "position": [1050, 300],
                    "webhookId": "approval-decision",
                    "parameters": {
                        "resume": "webhook",
                        "options": {
                            "webhookSuffix": "/decision/{{$json.ticket_id}}"
                        }
                    }
                },
                {
                    "id": "update_status",
                    "name": "Update Ticket Status",
                    "type": "n8n-nodes-base.postgres",
                    "typeVersion": 2.3,
                    "position": [1250, 300],
                    "parameters": {
                        "operation": "update",
                        "table": "approval_tickets",
                        "updateKey": "ticket_id",
                        "columnData": {
                            "status": "={{$json.decision}}",
                            "approved_by": "={{$json.approver}}",
                            "approved_at": "={{new Date().toISOString()}}"
                        }
                    }
                },
                {
                    "id": "notify_requester",
                    "name": "Notify Requester",
                    "type": "n8n-nodes-base.emailSend",
                    "typeVersion": 2.1,
                    "position": [1450, 300],
                    "parameters": {
                        "sendTo": "={{$json.requester_email}}",
                        "subject": "Approval Request {{$json.decision}}",
                        "message": "Your approval request has been {{$json.decision}}.",
                        "options": {}
                    }
                }
            ],
            "connections": {
                "Approval Request Form": {"main": [[{"node": "Create Approval Ticket", "type": "main", "index": 0}]]},
                "Create Approval Ticket": {"main": [[{"node": "Check Approval Level", "type": "main", "index": 0}]]},
                "Check Approval Level": {
                    "main": [
                        [{"node": "Notify Manager", "type": "main", "index": 0}],
                        [{"node": "Notify Director", "type": "main", "index": 0}],
                        [{"node": "Notify Executive", "type": "main", "index": 0}]
                    ]
                },
                "Notify Manager": {"main": [[{"node": "Wait for Decision", "type": "main", "index": 0}]]},
                "Notify Director": {"main": [[{"node": "Wait for Decision", "type": "main", "index": 0}]]},
                "Notify Executive": {"main": [[{"node": "Wait for Decision", "type": "main", "index": 0}]]},
                "Wait for Decision": {"main": [[{"node": "Update Ticket Status", "type": "main", "index": 0}]]},
                "Update Ticket Status": {"main": [[{"node": "Notify Requester", "type": "main", "index": 0}]]}
            }
        }
    
    @staticmethod
    def report_generator() -> Dict[str, Any]:
        """Scheduled report generation and distribution"""
        return {
            "name": "Report Generator",
            "nodes": [
                {
                    "id": "schedule",
                    "name": "Weekly Schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {
                        "rule": {
                            "interval": [{"field": "weeks", "intervalValue": 1}],
                            "weekday": [1],  # Monday
                            "hour": 9,
                            "minute": 0
                        }
                    }
                },
                {
                    "id": "fetch_metrics",
                    "name": "Fetch Metrics",
                    "type": "n8n-nodes-base.postgres",
                    "typeVersion": 2.3,
                    "position": [450, 300],
                    "parameters": {
                        "operation": "executeQuery",
                        "query": """
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_sales,
    SUM(amount) as revenue,
    AVG(amount) as avg_order_value
FROM sales
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;
"""
                    }
                },
                {
                    "id": "generate_report",
                    "name": "Generate Report",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 1,
                    "position": [650, 300],
                    "parameters": {
                        "jsCode": """
const metrics = $input.all();
const reportDate = new Date().toISOString().split('T')[0];

// Calculate totals
let totalSales = 0;
let totalRevenue = 0;

const reportData = metrics.map(item => {
    totalSales += item.json.total_sales;
    totalRevenue += parseFloat(item.json.revenue);
    return item.json;
});

// Generate HTML report
const htmlReport = `
<h2>Weekly Sales Report - ${reportDate}</h2>
<h3>Summary</h3>
<ul>
    <li>Total Sales: ${totalSales}</li>
    <li>Total Revenue: $${totalRevenue.toFixed(2)}</li>
    <li>Average Order Value: $${(totalRevenue / totalSales).toFixed(2)}</li>
</ul>
<h3>Daily Breakdown</h3>
<table border="1">
    <tr><th>Date</th><th>Sales</th><th>Revenue</th><th>AOV</th></tr>
    ${reportData.map(day => `
        <tr>
            <td>${day.date}</td>
            <td>${day.total_sales}</td>
            <td>$${parseFloat(day.revenue).toFixed(2)}</td>
            <td>$${parseFloat(day.avg_order_value).toFixed(2)}</td>
        </tr>
    `).join('')}
</table>
`;

return [{
    json: {
        reportDate,
        totalSales,
        totalRevenue,
        htmlReport,
        rawData: reportData
    }
}];
"""
                    }
                },
                {
                    "id": "send_email",
                    "name": "Email Report",
                    "type": "n8n-nodes-base.emailSend",
                    "typeVersion": 2.1,
                    "position": [850, 200],
                    "parameters": {
                        "sendTo": "={{$vars.report_recipients}}",
                        "subject": "Weekly Sales Report - {{$json.reportDate}}",
                        "message": "={{$json.htmlReport}}",
                        "options": {
                            "allowUnauthorizedCerts": True
                        }
                    }
                },
                {
                    "id": "post_slack",
                    "name": "Post to Slack",
                    "type": "n8n-nodes-base.slack",
                    "typeVersion": 2.1,
                    "position": [850, 400],
                    "parameters": {
                        "operation": "post",
                        "channel": "#sales-reports",
                        "text": "Weekly Sales Report Generated",
                        "otherOptions": {
                            "attachments": [
                                {
                                    "color": "#36a64f",
                                    "title": "Sales Performance",
                                    "fields": [
                                        {
                                            "title": "Total Sales",
                                            "value": "{{$json.totalSales}}",
                                            "short": True
                                        },
                                        {
                                            "title": "Total Revenue",
                                            "value": "${{$json.totalRevenue}}",
                                            "short": True
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            ],
            "connections": {
                "Weekly Schedule": {"main": [[{"node": "Fetch Metrics", "type": "main", "index": 0}]]},
                "Fetch Metrics": {"main": [[{"node": "Generate Report", "type": "main", "index": 0}]]},
                "Generate Report": {
                    "main": [[
                        {"node": "Email Report", "type": "main", "index": 0},
                        {"node": "Post to Slack", "type": "main", "index": 0}
                    ]]
                }
            }
        }


def get_template(category: str, template_name: str) -> Dict[str, Any]:
    """Get a specific template by category and name"""
    
    templates = {
        "data-pipeline": {
            "etl": WorkflowTemplates.data_pipeline_etl()
        },
        "integration": {
            "crm-sync": WorkflowTemplates.crm_sync_integration()
        },
        "approval": {
            "multi-step": WorkflowTemplates.approval_workflow()
        },
        "automation": {
            "report-generator": WorkflowTemplates.report_generator()
        }
    }
    
    if category in templates and template_name in templates[category]:
        return templates[category][template_name]
    
    raise ValueError(f"Template '{template_name}' not found in category '{category}'")


def list_templates() -> Dict[str, List[str]]:
    """List all available templates by category"""
    
    return {
        "data-pipeline": ["etl"],
        "integration": ["crm-sync"],
        "approval": ["multi-step"],
        "automation": ["report-generator"]
    }