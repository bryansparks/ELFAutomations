const http = require('http');
const url = require('url');

const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  
  console.log(`${req.method} ${pathname}`);
  
  if (pathname === '/api/version') {
    res.writeHead(200);
    res.end(JSON.stringify({ version: '1.0.0-mock' }));
  } else if (pathname === '/api/validate' && req.method === 'POST') {
    // Handle validation requests - always return valid
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      console.log('Validation request body:', body);
      res.writeHead(200);
      res.end(JSON.stringify({ 
        isValid: true,
        message: 'Validation successful'
      }));
    });
    return;
  } else if (pathname.startsWith('/api/teams/')) {
    // Handle team validation - return success for any team
    const teamName = pathname.split('/')[3];
    res.writeHead(200);
    res.end(JSON.stringify({ 
      name: teamName, 
      status: 'active',
      description: `Mock team ${teamName}` 
    }));
  } else if (pathname.startsWith('/api/agents/')) {
    // Handle agent operations
    const agentName = pathname.split('/')[3];
    if (req.method === 'POST' || req.method === 'PUT') {
      res.writeHead(200);
      res.end(JSON.stringify({ 
        name: agentName, 
        status: 'created',
        message: 'Agent processed successfully' 
      }));
    } else {
      res.writeHead(200);
      res.end(JSON.stringify({ 
        name: agentName, 
        status: 'active' 
      }));
    }
  } else if (pathname === '/api/health') {
    res.writeHead(200);
    res.end(JSON.stringify({ status: 'healthy' }));
  } else {
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found', path: pathname }));
  }
});

const port = 8081;
server.listen(port, () => {
  console.log('Mock Autogen Studio running on port ' + port);
});
