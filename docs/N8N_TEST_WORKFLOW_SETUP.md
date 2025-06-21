# N8N Test Workflow Setup Guide

## Creating the Test Webhook Workflow

### Option 1: Import the Workflow (Recommended)

1. In n8n, click the menu (☰) in the top left
2. Select "Import from File"
3. Navigate to: `/examples/n8n_workflows/test-webhook-workflow.json`
4. Click "Import"

### Option 2: Create Manually

1. **Create a new workflow**
   - Click "+ Add workflow" or "New" button

2. **Add Webhook Node**
   - Click "+" to add a node
   - Search for "Webhook"
   - Add it to the canvas
   - Configure:
     - HTTP Method: `POST`
     - Path: `test`
     - Response Mode: `Using 'Respond to Webhook' Node`

3. **Add Set Node**
   - Click "+" after the Webhook node
   - Search for "Set"
   - Connect it to the Webhook
   - Configure to add fields:
     - `result`: `Workflow executed successfully at {{new Date().toISOString()}}`
     - `input_message`: `={{$json["message"]}}`
     - `processed_by`: `n8n-test-workflow`

4. **Add Respond to Webhook Node**
   - Click "+" after the Set node
   - Search for "Respond to Webhook"
   - Connect it to the Set node

5. **Save and Activate**
   - Click "Save" (top right)
   - Toggle the "Active" switch to ON
   - Note the workflow ID from the URL (e.g., `workflow/7`)

## Testing the Webhook

Once activated, you'll see the webhook URL. It should be something like:
- Production URL: `http://[your-domain]/webhook/test`
- Test URL: `http://[your-domain]/webhook-test/test`

For our setup, the internal URL will be:
`http://n8n.n8n.svc.cluster.local:5678/webhook/test`

## Next Steps

After creating and activating the workflow:

1. Note the workflow ID from the URL
2. Update the registry with the actual ID
3. Test the integration

The webhook is now ready to receive requests from ELF teams!
