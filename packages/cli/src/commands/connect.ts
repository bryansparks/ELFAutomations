import { input, confirm } from '@inquirer/prompts'
import chalk from 'chalk'
import ora from 'ora'
import fs from 'fs-extra'
import path from 'path'
import { execa } from 'execa'

export async function connect(type: string, options: any) {
  const spinner = ora()

  try {
    if (type !== 'api') {
      console.error(chalk.red(`Invalid connection type: ${type}`))
      process.exit(1)
    }

    console.log(chalk.cyan('\nConnecting to API...\n'))

    if (options.swagger) {
      await connectSwagger(options.swagger, options, spinner)
    } else if (options.graphql) {
      await connectGraphQL(options.graphql, options, spinner)
    } else {
      // Interactive mode
      const apiType = await input({
        message: 'Enter your API type:',
        default: 'rest'
      })

      if (apiType === 'graphql') {
        const endpoint = await input({
          message: 'Enter GraphQL endpoint URL:'
        })
        await connectGraphQL(endpoint, options, spinner)
      } else {
        const specPath = await input({
          message: 'Enter path to OpenAPI/Swagger spec:'
        })
        await connectSwagger(specPath, options, spinner)
      }
    }

  } catch (error) {
    spinner.fail('Failed to connect API')
    console.error(error)
    process.exit(1)
  }
}

async function connectSwagger(specPath: string, options: any, spinner: ora.Ora) {
  spinner.start('Reading OpenAPI specification...')

  // Check if spec file exists
  const absolutePath = path.resolve(specPath)
  if (!fs.existsSync(absolutePath)) {
    spinner.fail(`OpenAPI spec not found: ${specPath}`)
    process.exit(1)
  }

  const spec = await fs.readJson(absolutePath)
  spinner.succeed('OpenAPI spec loaded')

  // Generate TypeScript types
  if (options.generateTypes !== false) {
    spinner.start('Generating TypeScript types...')

    const typesContent = generateTypesFromOpenAPI(spec)
    const typesPath = path.join(process.cwd(), 'src/types/api.ts')
    await fs.ensureDir(path.dirname(typesPath))
    await fs.writeFile(typesPath, typesContent)

    spinner.succeed('TypeScript types generated')
  }

  // Generate React hooks
  if (options.generateHooks) {
    spinner.start('Generating React hooks...')

    const hooksContent = generateHooksFromOpenAPI(spec)
    const hooksPath = path.join(process.cwd(), 'src/hooks/api.ts')
    await fs.ensureDir(path.dirname(hooksPath))
    await fs.writeFile(hooksPath, hooksContent)

    spinner.succeed('React hooks generated')
  }

  // Create API client
  spinner.start('Creating API client...')

  const clientContent = generateAPIClient(spec)
  const clientPath = path.join(process.cwd(), 'src/lib/api-client.ts')
  await fs.ensureDir(path.dirname(clientPath))
  await fs.writeFile(clientPath, clientContent)

  spinner.succeed('API client created')

  console.log(chalk.green('\n✨ API connection established!\n'))
  console.log(chalk.cyan('Generated files:'))
  if (options.generateTypes !== false) {
    console.log(chalk.white('  - src/types/api.ts'))
  }
  if (options.generateHooks) {
    console.log(chalk.white('  - src/hooks/api.ts'))
  }
  console.log(chalk.white('  - src/lib/api-client.ts'))
}

async function connectGraphQL(endpoint: string, options: any, spinner: ora.Ora) {
  spinner.start('Connecting to GraphQL endpoint...')

  // Here you would implement GraphQL introspection and code generation
  // For now, we'll create a basic setup

  const clientContent = `import { GraphQLClient } from 'graphql-request'

const endpoint = '${endpoint}'

export const graphqlClient = new GraphQLClient(endpoint, {
  headers: {
    // Add your headers here
  },
})

// Example query
export const exampleQuery = async () => {
  const query = `
    query {
      # Your query here
    }
  `

  return graphqlClient.request(query)
}
`

  const clientPath = path.join(process.cwd(), 'src/lib/graphql-client.ts')
  await fs.ensureDir(path.dirname(clientPath))
  await fs.writeFile(clientPath, clientContent)

  spinner.succeed('GraphQL client created')

  // Install required dependencies
  spinner.start('Installing GraphQL dependencies...')
  await execa('npm', ['install', 'graphql-request', 'graphql'], { cwd: process.cwd() })
  spinner.succeed('Dependencies installed')

  console.log(chalk.green('\n✨ GraphQL connection established!\n'))
}

function generateTypesFromOpenAPI(spec: any): string {
  let types = `// Auto-generated API types from OpenAPI spec\n\n`

  // Generate types from schemas
  if (spec.components?.schemas) {
    for (const [name, schema] of Object.entries(spec.components.schemas)) {
      types += `export interface ${name} {\n`

      if ((schema as any).properties) {
        for (const [prop, propSchema] of Object.entries((schema as any).properties)) {
          const required = (schema as any).required?.includes(prop) || false
          const type = openAPITypeToTS((propSchema as any).type)
          types += `  ${prop}${required ? '' : '?'}: ${type}\n`
        }
      }

      types += `}\n\n`
    }
  }

  return types
}

function generateHooksFromOpenAPI(spec: any): string {
  let hooks = `// Auto-generated React hooks from OpenAPI spec\n\n`
  hooks += `import { useQuery, useMutation } from '@tanstack/react-query'\n`
  hooks += `import { apiClient } from '@/lib/api-client'\n\n`

  // Generate hooks for each endpoint
  if (spec.paths) {
    for (const [path, methods] of Object.entries(spec.paths)) {
      for (const [method, operation] of Object.entries(methods as any)) {
        if (['get', 'post', 'put', 'delete', 'patch'].includes(method)) {
          const operationId = (operation as any).operationId ||
            `${method}${path.split('/').map((p: string) => p.charAt(0).toUpperCase() + p.slice(1)).join('')}`

          const hookName = `use${operationId.charAt(0).toUpperCase() + operationId.slice(1)}`

          if (method === 'get') {
            hooks += `export function ${hookName}(params?: any) {
  return useQuery({
    queryKey: ['\${operationId}', params],
    queryFn: () => apiClient.\${operationId}(params)
  })
}

`
          } else {
            hooks += `export function ${hookName}() {
  return useMutation({
    mutationFn: (data: any) => apiClient.\${operationId}(data)
  })
}

`
          }
        }
      }
    }
  }

  return hooks
}

function generateAPIClient(spec: any): string {
  let client = `// Auto-generated API client from OpenAPI spec\n\n`
  client += `const baseURL = '\${spec.servers?.[0]?.url || '/api'}'\n\n`

  client += `class APIClient {
  private async request(path: string, options: RequestInit = {}) {
    const response = await fetch(`${baseURL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return response.json()
  }\n\n`

  // Generate methods for each endpoint
  if (spec.paths) {
    for (const [path, methods] of Object.entries(spec.paths)) {
      for (const [method, operation] of Object.entries(methods as any)) {
        if (['get', 'post', 'put', 'delete', 'patch'].includes(method)) {
          const operationId = (operation as any).operationId ||
            `${method}${path.split('/').map((p: string) => p.charAt(0).toUpperCase() + p.slice(1)).join('')}`

          client += `  async ${operationId}(data?: any) {
    return this.request('\${path}', {
      method: '\${method.toUpperCase()}',
      \${method !== 'get' ? 'body: JSON.stringify(data),' : ''}
    })
  }

`
        }
      }
    }
  }

  client += `}\n\nexport const apiClient = new APIClient()\n`

  return client
}

function openAPITypeToTS(type: string): string {
  const typeMap: Record<string, string> = {
    'string': 'string',
    'integer': 'number',
    'number': 'number',
    'boolean': 'boolean',
    'array': 'any[]',
    'object': 'Record<string, any>'
  }

  return typeMap[type] || 'any'
}
