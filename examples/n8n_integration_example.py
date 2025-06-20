"""
Example: How ELF Teams Can Use N8N Integration

This example shows how a team can leverage n8n workflows for automation.
"""

import asyncio
from elf_automations.shared.n8n import N8NClient, WorkflowCategory

async def marketing_team_example():
    """Example: Marketing team using n8n for competitor analysis"""
    
    async with N8NClient() as client:
        # Execute a competitor analysis workflow
        result = await client.execute_workflow(
            workflow_name="competitor-analysis-pipeline",
            data={
                "competitors": ["company-a", "company-b", "company-c"],
                "metrics": ["social_media", "content", "pricing"],
                "date_range": "last_7_days"
            },
            team_name="marketing-team"
        )
        
        print(f"Analysis completed: {result.status.value}")
        if result.output_data:
            print(f"Report URL: {result.output_data.get('report_url')}")
            print(f"Key insights: {result.output_data.get('insights')}")

async def devops_team_example():
    """Example: DevOps team using n8n for deployment notifications"""
    
    async with N8NClient() as client:
        # Trigger deployment notification workflow
        result = await client.execute_workflow(
            workflow_name="deployment-notification",
            data={
                "service": "user-api",
                "version": "v2.1.0",
                "environment": "production",
                "deployed_by": "devops-team",
                "commit_sha": "abc123def",
                "changes": [
                    "Added user profile API",
                    "Fixed authentication bug",
                    "Improved performance"
                ]
            },
            team_name="devops-team"
        )
        
        print(f"Notifications sent: {result.status.value}")

async def executive_team_example():
    """Example: Executive team using n8n for weekly reports"""
    
    async with N8NClient() as client:
        # First, check what workflows are available
        workflows = await client.list_workflows(
            owner_team="executive-team",
            category=WorkflowCategory.DATA_PIPELINE
        )
        
        print("Available executive workflows:")
        for wf in workflows:
            print(f"- {wf.name}: {wf.description}")
        
        # Get execution history
        history = await client.get_execution_history(
            team_name="executive-team",
            limit=5
        )
        
        print("\nRecent workflow executions:")
        for exec in history:
            print(f"- {exec.workflow_name}: {exec.status.value} "
                  f"(took {exec.duration:.2f}s)" if exec.duration else "")

async def integration_example():
    """Example: Integrating with CrewAI team"""
    
    from crewai import Agent, Task, Crew
    
    # Create an agent that can use n8n workflows
    class WorkflowAgent(Agent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.n8n_client = None
        
        async def execute_workflow(self, workflow_name: str, data: dict):
            """Execute an n8n workflow as part of agent task"""
            if not self.n8n_client:
                self.n8n_client = N8NClient()
            
            async with self.n8n_client as client:
                result = await client.execute_workflow(
                    workflow_name=workflow_name,
                    data=data,
                    team_name=self.role
                )
                return result.output_data
    
    # Example agent that uses workflows
    data_analyst = WorkflowAgent(
        role="data-analyst",
        goal="Analyze data using n8n pipelines",
        backstory="Expert in leveraging automated workflows for data analysis"
    )
    
    # In a task, the agent can call workflows
    async def analyze_task():
        result = await data_analyst.execute_workflow(
            "customer-sentiment-analysis",
            {"time_period": "last_month", "channels": ["twitter", "reviews"]}
        )
        return result

if __name__ == "__main__":
    # Run examples
    print("Marketing Team Example:")
    print("-" * 50)
    # asyncio.run(marketing_team_example())
    
    print("\nDevOps Team Example:")
    print("-" * 50)
    # asyncio.run(devops_team_example())
    
    print("\nExecutive Team Example:")
    print("-" * 50)
    # asyncio.run(executive_team_example())
    
    print("\nNote: Uncomment the asyncio.run() lines to execute examples")
    print("Make sure you have workflows registered in the system first!")