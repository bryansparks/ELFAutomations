import { select, input, confirm } from '@inquirer/prompts'
import chalk from 'chalk'
import ora from 'ora'
import fs from 'fs-extra'
import path from 'path'
import prettier from 'prettier'

const componentTemplate = (name: string, options: any) => `import * as React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
${options.crud ? "import { Button, Card, CardContent, CardHeader, CardTitle } from '@elf/ui'" : ''}

interface ${name}Props extends React.HTMLAttributes<HTMLDivElement> {
  // Add your props here
}

export const ${name} = React.forwardRef<HTMLDivElement, ${name}Props>(
  ({ className, ...props }, ref) => {
    ${options.crud ? `const [items, setItems] = React.useState([])
    const [loading, setLoading] = React.useState(false)

    const handleCreate = async () => {
      // Implement create logic
    }

    const handleUpdate = async (id: string) => {
      // Implement update logic
    }

    const handleDelete = async (id: string) => {
      // Implement delete logic
    }` : ''}

    return (
      ${options.animate ? `<motion.div
        ref={ref}
        className={cn('', className)}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
        {...props}
      >` : `<div ref={ref} className={cn('', className)} {...props}>`}
        ${options.crud ? `<Card>
          <CardHeader>
            <CardTitle>${name}</CardTitle>
            <Button onClick={handleCreate} variant="gradient">
              Create New
            </Button>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div>Loading...</div>
            ) : (
              <div>
                {/* Render your items here */}
              </div>
            )}
          </CardContent>
        </Card>` : `{/* Your component content */}`}
      ${options.animate ? '</motion.div>' : '</div>'}
    )
  }
)

${name}.displayName = '${name}'
`

const hookTemplate = (name: string, options: any) => `import { useState, useEffect, useCallback } from 'react'
${options.api ? "import { useQuery, useMutation } from '@tanstack/react-query'" : ''}

export function ${name}() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  ${options.api ? `const { data: queryData, isLoading, error: queryError } = useQuery({
    queryKey: ['${name.replace('use', '').toLowerCase()}'],
    queryFn: async () => {
      // Implement your API call here
      const response = await fetch('/api/${name.replace('use', '').toLowerCase()}')
      if (!response.ok) throw new Error('Failed to fetch')
      return response.json()
    }
  })` : ''}

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      // Implement your data fetching logic
      setData(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    data: ${options.api ? 'queryData || data' : 'data'},
    loading: ${options.api ? 'isLoading || loading' : 'loading'},
    error: ${options.api ? 'queryError || error' : 'error'},
    refetch: fetchData
  }
}
`

const pageTemplate = (name: string, options: any) => `'use client'

import { PageTransition, Button, Card } from '@elf/ui'
${options.api ? "import { use${name}Data } from '@/hooks/use${name}Data'" : ''}

export default function ${name}Page() {
  ${options.api ? 'const { data, loading, error } = use' + name + 'Data()' : ''}

  return (
    <PageTransition variant="fade">
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">${name}</h1>

        ${options.crud ? `<div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Manage ${name}</h2>
            <Button variant="gradient">Create New</Button>
          </div>

          <Card>
            {/* Your CRUD interface here */}
          </Card>
        </div>` : `<Card>
          {/* Your page content here */}
        </Card>`}
      </div>
    </PageTransition>
  )
}
`

export async function generate(type: string, name: string, options: any) {
  const spinner = ora()

  try {
    // Validate type
    const validTypes = ['component', 'page', 'hook']
    if (!validTypes.includes(type)) {
      console.error(chalk.red(`Invalid type: ${type}. Must be one of: ${validTypes.join(', ')}`))
      process.exit(1)
    }

    // Ensure we're in a Next.js project
    const packageJsonPath = path.join(process.cwd(), 'package.json')
    if (!fs.existsSync(packageJsonPath)) {
      console.error(chalk.red('Error: Not in a Node.js project directory'))
      process.exit(1)
    }

    spinner.start(`Generating ${type}: ${name}...`)

    let content = ''
    let filePath = ''

    switch (type) {
      case 'component':
        content = componentTemplate(name, options)
        filePath = path.join(process.cwd(), 'src/components', `${name}.tsx`)
        break

      case 'hook':
        if (!name.startsWith('use')) {
          name = `use${name}`
        }
        content = hookTemplate(name, options)
        filePath = path.join(process.cwd(), 'src/hooks', `${name}.ts`)
        break

      case 'page':
        content = pageTemplate(name, options)
        const pageName = name.toLowerCase().replace(/page$/i, '')
        filePath = path.join(process.cwd(), 'src/app', pageName, 'page.tsx')
        await fs.ensureDir(path.dirname(filePath))
        break
    }

    // Format with prettier
    const formatted = await prettier.format(content, {
      parser: 'typescript',
      semi: false,
      singleQuote: true,
      tabWidth: 2
    })

    // Write file
    await fs.writeFile(filePath, formatted)

    spinner.succeed(`Generated ${type}: ${name}`)
    console.log(chalk.green(`✨ Created: ${filePath}`))

    // Generate API route if needed
    if (options.api && (type === 'page' || type === 'hook')) {
      spinner.start('Generating API route...')

      const apiContent = `import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    // Implement your API logic here
    const data = {
      message: 'Success',
      timestamp: new Date().toISOString()
    }

    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Implement your API logic here

    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    )
  }
}
`

      const apiName = name.toLowerCase().replace(/page$/i, '')
      const apiPath = path.join(process.cwd(), 'src/app/api', apiName, 'route.ts')
      await fs.ensureDir(path.dirname(apiPath))
      await fs.writeFile(apiPath, apiContent)

      spinner.succeed('Generated API route')
      console.log(chalk.green(`✨ Created: ${apiPath}`))
    }

  } catch (error) {
    spinner.fail(`Failed to generate ${type}`)
    console.error(error)
    process.exit(1)
  }
}
