#!/usr/bin/env node

// Test script to verify workflow import functionality
// Run this after creating the workflows tables in Supabase

const testWorkflowImport = async () => {
  const controlCenterUrl = 'http://localhost:3003';

  const testWorkflow = {
    name: "Test Webhook Workflow",
    description: "A simple test workflow for import verification",
    nodes: [
      {
        id: "1",
        name: "Webhook",
        type: "n8n-nodes-base.webhook",
        position: [250, 300],
        parameters: {
          path: "test-webhook",
          httpMethod: "POST"
        }
      },
      {
        id: "2",
        name: "Set",
        type: "n8n-nodes-base.set",
        position: [450, 300],
        parameters: {
          values: {
            string: [
              {
                name: "status",
                value: "received"
              }
            ]
          }
        }
      }
    ],
    connections: {
      "Webhook": {
        "main": [
          [
            {
              "node": "Set",
              "type": "main",
              "index": 0
            }
          ]
        ]
      }
    }
  };

  console.log('Testing workflow import...');
  console.log('Target URL:', `${controlCenterUrl}/api/workflows/import`);
  console.log('Workflow:', JSON.stringify(testWorkflow, null, 2));

  try {
    const response = await fetch(`${controlCenterUrl}/api/workflows/import`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        source: JSON.stringify(testWorkflow),
        sourceType: 'json',
        ownerTeam: 'test-team',
        category: 'testing',
        validate: true,
        process: true,
        autoFix: false
      })
    });

    console.log('Response status:', response.status);

    const responseText = await response.text();
    console.log('Response body:', responseText);

    if (response.ok) {
      const result = JSON.parse(responseText);
      console.log('\n✅ Import successful!');
      console.log('Workflow ID:', result.workflow?.id);
      console.log('Workflow Name:', result.workflow?.name);
      console.log('Validation Status:', result.validationReport?.status);
    } else {
      console.error('\n❌ Import failed');
      try {
        const error = JSON.parse(responseText);
        console.error('Error:', error.error);
        console.error('Details:', error.details);
        console.error('Code:', error.code);
      } catch {
        console.error('Raw error:', responseText);
      }
    }
  } catch (error) {
    console.error('\n❌ Request failed:', error.message);
  }
};

// Run the test
testWorkflowImport();
