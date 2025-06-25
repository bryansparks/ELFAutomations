import { select, input, confirm } from '@inquirer/prompts'
import chalk from 'chalk'
import ora from 'ora'
import fs from 'fs-extra'
import path from 'path'
import { execa } from 'execa'

const templates = {
  dashboard: {
    name: 'Dashboard',
    description: 'Admin dashboard with charts, metrics, and real-time data',
    dependencies: ['recharts', '@tanstack/react-query', 'zustand', 'socket.io-client']
  },
  admin: {
    name: 'Admin Panel',
    description: 'Full-featured admin panel with CRUD operations',
    dependencies: ['@tanstack/react-table', 'react-hook-form', 'zod']
  },
  workflow: {
    name: 'Workflow Builder',
    description: 'Visual workflow builder with drag-and-drop',
    dependencies: ['@dnd-kit/sortable', 'reactflow', 'immer']
  },
  analytics: {
    name: 'Analytics',
    description: 'Analytics dashboard with reports and data exploration',
    dependencies: ['recharts', 'd3', '@visx/visx', 'date-fns']
  },
  communication: {
    name: 'Communication Hub',
    description: 'Real-time chat and notification system',
    dependencies: ['socket.io-client', 'date-fns', '@tanstack/react-virtual']
  }
}

export async function create(name: string, options: any) {
  const spinner = ora()

  try {
    // Get project details
    const projectPath = path.join(process.cwd(), name)

    if (fs.existsSync(projectPath)) {
      console.error(chalk.red(`Error: Directory ${name} already exists`))
      process.exit(1)
    }

    // Select template if not provided
    let template = options.template
    if (!templates[template]) {
      template = await select({
        message: 'Select a template:',
        choices: Object.entries(templates).map(([key, value]) => ({
          value: key,
          title: value.name,
          description: value.description
        }))
      })
    }

    console.log(chalk.cyan(`\nCreating ${name} with ${templates[template].name} template...\n`))

    // Create project structure
    spinner.start('Creating project structure...')

    await fs.ensureDir(projectPath)
    await fs.ensureDir(path.join(projectPath, 'src'))
    await fs.ensureDir(path.join(projectPath, 'src/components'))
    await fs.ensureDir(path.join(projectPath, 'src/pages'))
    await fs.ensureDir(path.join(projectPath, 'src/hooks'))
    await fs.ensureDir(path.join(projectPath, 'src/lib'))
    await fs.ensureDir(path.join(projectPath, 'src/styles'))
    await fs.ensureDir(path.join(projectPath, 'public'))

    // Create package.json
    const packageJson = {
      name,
      version: '0.1.0',
      private: true,
      scripts: {
        dev: 'next dev',
        build: 'next build',
        start: 'next start',
        lint: 'next lint',
        'type-check': 'tsc --noEmit',
        format: 'prettier --write .',
        test: 'jest'
      },
      dependencies: {
        '@elf/ui': 'workspace:*',
        'next': '^14.1.0',
        'react': '^18.2.0',
        'react-dom': '^18.2.0',
        ...templates[template].dependencies.reduce((acc, dep) => {
          acc[dep] = 'latest'
          return acc
        }, {})
      },
      devDependencies: {
        '@types/node': '^20.11.17',
        '@types/react': '^18.2.55',
        '@types/react-dom': '^18.2.19',
        'autoprefixer': '^10.4.17',
        'eslint': '^8.56.0',
        'eslint-config-next': '^14.1.0',
        'postcss': '^8.4.35',
        'prettier': '^3.2.5',
        'tailwindcss': '^3.4.1',
        'typescript': '^5.3.3'
      }
    }

    await fs.writeJson(path.join(projectPath, 'package.json'), packageJson, { spaces: 2 })

    // Create Next.js config
    const nextConfig = `/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@elf/ui'],
}

module.exports = nextConfig
`
    await fs.writeFile(path.join(projectPath, 'next.config.js'), nextConfig)

    // Create TypeScript config
    const tsConfig = {
      compilerOptions: {
        target: 'es5',
        lib: ['dom', 'dom.iterable', 'esnext'],
        allowJs: true,
        skipLibCheck: true,
        strict: true,
        forceConsistentCasingInFileNames: true,
        noEmit: true,
        esModuleInterop: true,
        module: 'esnext',
        moduleResolution: 'bundler',
        resolveJsonModule: true,
        isolatedModules: true,
        jsx: 'preserve',
        incremental: true,
        paths: {
          '@/*': ['./src/*']
        }
      },
      include: ['next-env.d.ts', '**/*.ts', '**/*.tsx'],
      exclude: ['node_modules']
    }

    await fs.writeJson(path.join(projectPath, 'tsconfig.json'), tsConfig, { spaces: 2 })

    // Create Tailwind config
    const tailwindConfig = `/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './node_modules/@elf/ui/dist/**/*.{js,ts,jsx,tsx}'
  ],
  presets: [
    require('@elf/ui/tailwind.config')
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
`
    await fs.writeFile(path.join(projectPath, 'tailwind.config.js'), tailwindConfig)

    // Create PostCSS config
    const postcssConfig = `module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
`
    await fs.writeFile(path.join(projectPath, 'postcss.config.js'), postcssConfig)

    // Create main CSS file
    const mainCss = `@import '@elf/ui/themes/index.css';

/* Your custom styles here */
`
    await fs.writeFile(path.join(projectPath, 'src/styles/globals.css'), mainCss)

    // Create layout
    const layout = `import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '${name}',
  description: 'Built with ELF UI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
`
    await fs.ensureDir(path.join(projectPath, 'src/app'))
    await fs.writeFile(path.join(projectPath, 'src/app/layout.tsx'), layout)

    // Create template-specific files
    await createTemplateFiles(projectPath, template)

    spinner.succeed('Project structure created')

    // Initialize git
    if (options.git) {
      spinner.start('Initializing git repository...')
      await execa('git', ['init'], { cwd: projectPath })

      // Create .gitignore
      const gitignore = `# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
`
      await fs.writeFile(path.join(projectPath, '.gitignore'), gitignore)
      spinner.succeed('Git repository initialized')
    }

    // Install dependencies
    if (options.install) {
      spinner.start('Installing dependencies...')
      await execa('npm', ['install'], { cwd: projectPath })
      spinner.succeed('Dependencies installed')
    }

    // Success message
    console.log(chalk.green('\n✨ Project created successfully!\n'))
    console.log(chalk.cyan('To get started:'))
    console.log(chalk.white(`  cd ${name}`))
    if (!options.install) {
      console.log(chalk.white('  npm install'))
    }
    console.log(chalk.white('  npm run dev'))
    console.log()

  } catch (error) {
    spinner.fail('Failed to create project')
    console.error(error)
    process.exit(1)
  }
}

async function createTemplateFiles(projectPath: string, template: string) {
  // Create a sample page based on template
  let pageContent = ''

  switch (template) {
    case 'dashboard':
      pageContent = `'use client'

import { Button, Card, CardContent, CardHeader, CardTitle, MetricCard, Loading, PageTransition } from '@elf/ui'
import { Users, DollarSign, Activity, CreditCard } from 'lucide-react'

export default function DashboardPage() {
  return (
    <PageTransition variant="fade">
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gradient">Dashboard</h1>
          <Button variant="gradient">
            New Report
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Users"
            value={2350}
            change={12}
            changeLabel="from last month"
            icon={<Users className="h-4 w-4" />}
            color="info"
            animate
          />
          <MetricCard
            title="Revenue"
            value={45231}
            prefix="$"
            change={20.1}
            changeLabel="from last month"
            icon={<DollarSign className="h-4 w-4" />}
            color="success"
            animate
          />
          <MetricCard
            title="Active Now"
            value={573}
            change={-5}
            icon={<Activity className="h-4 w-4" />}
            color="warning"
            animate
          />
          <MetricCard
            title="Transactions"
            value={89}
            change={3}
            icon={<CreditCard className="h-4 w-4" />}
            animate
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card variant="glass" hover="lift">
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <Loading variant="wave" />
            </CardContent>
          </Card>

          <Card variant="gradient" hover="glow">
            <CardHeader>
              <CardTitle>Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <Loading variant="orbit" color="gradient" />
            </CardContent>
          </Card>
        </div>
      </div>
    </PageTransition>
  )
}
`
      break

    default:
      pageContent = `'use client'

import { Button, Card, CardContent, CardHeader, CardTitle, PageTransition } from '@elf/ui'

export default function HomePage() {
  return (
    <PageTransition variant="slide" direction="up">
      <div className="container mx-auto p-6">
        <Card variant="glass" hover="lift" className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="text-gradient">Welcome to ${template}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Your ${templates[template].name} application is ready!
            </p>
            <div className="flex gap-2">
              <Button variant="gradient">Get Started</Button>
              <Button variant="outline">Learn More</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
`
  }

  await fs.writeFile(path.join(projectPath, 'src/app/page.tsx'), pageContent)
}
