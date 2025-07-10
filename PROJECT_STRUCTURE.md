# ELFAutomations Project Structure

## Directory Layout

```
ELFAutomations/
├── src/                    # Main source code
│   ├── elf_automations/    # Core Python package
│   ├── teams/             # AI team implementations
│   └── mcps/              # MCP servers
│
├── infrastructure/         # Deployment and configuration
│   ├── k8s/               # Kubernetes manifests
│   ├── docker/            # Dockerfiles
│   └── terraform/         # Infrastructure as Code
│
├── scripts/               # Organized operational scripts
│   ├── setup/             # Installation and setup
│   ├── deployment/        # Deployment scripts
│   ├── testing/           # Test scripts
│   ├── utilities/         # Helper utilities
│   └── demos/             # Demo scripts
│
├── database/              # Database related files
│   ├── schemas/           # Current schema definitions
│   ├── migrations/        # Migration scripts
│   └── seeds/             # Seed data
│
├── docs/                  # Documentation
│   ├── architecture/      # System design docs
│   ├── guides/            # How-to guides
│   ├── api/               # API documentation
│   ├── sessions/          # Development session notes
│   └── planning/          # Planning documents
│
├── tests/                 # Test files
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
│
├── tools/                 # Development tools
├── examples/              # Example configurations
└── archive/               # Deprecated/old files
```

## Key Files Locations

- Python source: `src/elf_automations/`
- Team definitions: `src/teams/`
- MCP servers: `src/mcps/`
- Kubernetes configs: `infrastructure/k8s/`
- Database schemas: `database/schemas/`
- Setup instructions: `docs/guides/`
- Session notes: `docs/sessions/`

## Migration Notes

Files have been reorganized from the flat structure to this hierarchical layout.
Update your import paths and script references accordingly.
