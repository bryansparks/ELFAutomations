# ELF Automations - Virtual AI Company Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

ELF Automations is a revolutionary **Virtual AI Company Platform** that creates fully functional organizational structures using autonomous AI agents. This platform simulates a real company with hierarchical management, department specialization, cross-functional workflows, and measurable business outcomes - all powered by AI agents.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Human Execs   │    │  Chief AI Agent │    │   Dashboard     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│                   Department Layer                                │
├─────────────┬─────────────┬─────────────┬─────────────┬──────────┤
│Sales & Admin│  Marketing  │   Product   │Back Office  │Customer  │
│   Head      │    Head     │    Head     │    Head     │ Success  │
└─────────────┴─────────────┴─────────────┴─────────────┴──────────┘
         │           │           │           │           │
┌─────────────────────────────────┼─────────────────────────────────┐
│                Individual Agents Layer                           │
└─────────────────────────────────┼─────────────────────────────────┘
         │           │           │           │           │
┌─────────────────────────────────┼─────────────────────────────────┐
│                     Tools Layer                                   │
└─────────────────────────────────┼─────────────────────────────────┘
```

## Technology Stack

- **Agent Orchestration**: LangGraph for stateful, graph-based workflows
- **Kubernetes Management**: kagent for cloud-native agent deployment
- **Tool Integration**: Model Context Protocol (MCP) for standardized tool access
- **Communication**: agentgateway.dev for agent-MCP communication
- **Infrastructure**: Kubernetes for container orchestration and scaling
- **Observability**: LangSmith for agent monitoring and performance tracking

## Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop
- Kubernetes cluster (minikube recommended for local development)
- Conda environment manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ELFAutomations
   ```

2. **Set up conda environment**
   ```bash
   conda activate ElfAutomations
   pip install -r requirements.txt
   ```

3. **Start local Kubernetes cluster**
   ```bash
   minikube start --driver=docker --memory=8192 --cpus=4
   ```

4. **Install kagent**
   ```bash
   # Installation instructions will be added once kagent is available
   ```

5. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Project Structure

```
ELFAutomations/
├── agents/                 # Agent definitions and workflows
│   ├── executive/         # Executive layer agents
│   ├── departments/       # Department-specific agents
│   └── individual/        # Individual contributor agents
├── mcp-servers/           # Custom MCP server implementations
│   ├── business-tools/    # Business-specific tools
│   ├── integrations/      # Third-party integrations
│   └── utilities/         # Common utility tools
├── k8s/                   # Kubernetes manifests
│   ├── base/              # Base configurations
│   ├── overlays/          # Environment-specific overlays
│   └── operators/         # Custom operators
├── workflows/             # LangGraph workflow definitions
│   ├── cross-department/  # Inter-department workflows
│   └── department/        # Department-specific workflows
├── apis/                  # REST/GraphQL API implementations
├── tests/                 # Test suites
├── docs/                  # Documentation
└── tools/                 # Development and deployment tools
```

## Development

### Running Tests
```bash
pytest tests/ -v --cov=agents --cov=workflows
```

### Code Formatting
```bash
black .
flake8 .
mypy .
```

### Local Development
```bash
# Start local services
docker-compose up -d

# Run the platform
python -m agents.executive.chief_ai_agent
```

## Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# LLM Configuration
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
LANGSMITH_API_KEY=your_langsmith_key

# Database Configuration
POSTGRES_URL=postgresql://user:pass@localhost:5432/elfautomations
REDIS_URL=redis://localhost:6379

# Kubernetes Configuration
KUBECONFIG=~/.kube/config

# Agent Gateway Configuration
AGENT_GATEWAY_URL=https://agentgateway.dev
```

## Success Metrics

- **Agent Productivity**: 95%+ task completion rate across all departments
- **Inter-Agent Collaboration**: <2 second average response time for cross-department requests
- **System Reliability**: 99.9% uptime for critical business workflows
- **Scalability**: Support for 100+ concurrent agents without performance degradation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

- [Product Requirements Document](docs/PRD.md)
- [Technology Stack](docs/TECH-STACK.md)
- [Engineering Principles](docs/ENGINEERING-PRINCIPLES.md)
- [Development Tasks](docs/TASKS.md)

## Support

For questions and support, please open an issue in the GitHub repository.
