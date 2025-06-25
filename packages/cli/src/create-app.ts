#!/usr/bin/env node

import { Command } from 'commander'
import { execSync } from 'child_process'
import * as fs from 'fs'
import * as path from 'path'
import chalk from 'chalk'
import inquirer from 'inquirer'

const program = new Command()

program
  .name('create-elf-app')
  .description('Create a new app using the ELF UI template')
  .version('1.0.0')
  .argument('<app-name>', 'Name of your new app')
  .option('-t, --template <template>', 'Template to use', 'default')
  .option('-d, --directory <directory>', 'Directory to create app in', '.')
  .action(async (appName, options) => {
    console.log(chalk.blue.bold('\n🚀 ELF App Creator\n'))

    // Ask configuration questions
    const answers = await inquirer.prompt([
      {
        type: 'list',
        name: 'framework',
        message: 'Which framework features do you need?',
        choices: [
          { name: 'Basic (UI components only)', value: 'basic' },
          { name: 'Dashboard (with charts and metrics)', value: 'dashboard' },
          { name: 'Full (all features)', value: 'full' }
        ],
        default: 'dashboard'
      },
      {
        type: 'list',
        name: 'primaryColor',
        message: 'Choose a primary color scheme:',
        choices: [
          { name: '🔵 ELF Blue (default)', value: 'blue' },
          { name: '🟣 Purple', value: 'purple' },
          { name: '🟢 Green', value: 'green' },
          { name: '🔴 Red', value: 'red' },
          { name: '⚫ Neutral', value: 'neutral' }
        ],
        default: 'blue'
      },
      {
        type: 'confirm',
        name: 'includeApi',
        message: 'Include API integration setup?',
        default: true
      },
      {
        type: 'confirm',
        name: 'includeSamplePages',
        message: 'Include sample pages?',
        default: true
      }
    ])

    const appDir = path.join(options.directory, appName)

    console.log(chalk.yellow(`\n📁 Creating ${appName}...\n`))

    try {
      // Create app using the bash script
      execSync(`${__dirname}/../../../scripts/create-elf-app.sh ${appName}`, {
        stdio: 'inherit',
        cwd: options.directory
      })

      // Apply customizations based on answers
      if (answers.primaryColor !== 'blue') {
        console.log(chalk.yellow('🎨 Applying color scheme...'))
        // Update CSS variables
        updateColorScheme(appDir, answers.primaryColor)
      }

      if (!answers.includeApi) {
        console.log(chalk.yellow('🔌 Removing API integration...'))
        // Remove API-related files
        removeApiFiles(appDir)
      }

      if (answers.includeSamplePages) {
        console.log(chalk.yellow('📄 Adding sample pages...'))
        // Add sample pages
        addSamplePages(appDir, answers.framework)
      }

      console.log(chalk.green.bold('\n✅ Success! Your app is ready.\n'))
      console.log(chalk.white('To get started:'))
      console.log(chalk.cyan(`  cd ${appName}`))
      console.log(chalk.cyan('  npm install'))
      console.log(chalk.cyan('  npm run dev\n'))

      console.log(chalk.white('Available commands:'))
      console.log(chalk.gray('  npm run dev      - Start development server'))
      console.log(chalk.gray('  npm run build    - Build for production'))
      console.log(chalk.gray('  npm run lint     - Run linter'))
      console.log(chalk.gray('  npm run preview  - Preview production build\n'))

    } catch (error) {
      console.error(chalk.red('\n❌ Error creating app:'), error.message)
      process.exit(1)
    }
  })

function updateColorScheme(appDir: string, color: string) {
  const colors = {
    purple: { primary: '280 87% 65%', start: '280 87% 65%', end: '260 90% 70%' },
    green: { primary: '142 76% 36%', start: '142 76% 36%', end: '160 80% 40%' },
    red: { primary: '0 84% 60%', start: '0 84% 60%', end: '15 85% 65%' },
    neutral: { primary: '220 9% 46%', start: '220 9% 46%', end: '220 9% 56%' }
  }

  if (colors[color]) {
    const cssPath = path.join(appDir, 'src/styles/globals.css')
    let css = fs.readFileSync(cssPath, 'utf-8')

    css = css.replace(/--primary: .+;/g, `--primary: ${colors[color].primary};`)
    css = css.replace(/--gradient-start: .+;/g, `--gradient-start: ${colors[color].start};`)
    css = css.replace(/--gradient-end: .+;/g, `--gradient-end: ${colors[color].end};`)

    fs.writeFileSync(cssPath, css)
  }
}

function removeApiFiles(appDir: string) {
  const apiFiles = [
    'src/services/api.ts',
    'src/hooks/useSystemStats.ts'
  ]

  apiFiles.forEach(file => {
    const filePath = path.join(appDir, file)
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath)
    }
  })
}

function addSamplePages(appDir: string, framework: string) {
  // Add sample pages based on framework choice
  const pages = {
    basic: ['about', 'contact'],
    dashboard: ['analytics', 'users', 'reports'],
    full: ['analytics', 'users', 'reports', 'admin', 'profile']
  }

  const pagesToCreate = pages[framework] || pages.basic

  pagesToCreate.forEach(page => {
    const pageDir = path.join(appDir, `src/app/${page}`)
    fs.mkdirSync(pageDir, { recursive: true })

    const pageContent = generatePageContent(page)
    fs.writeFileSync(path.join(pageDir, 'page.tsx'), pageContent)
  })
}

function generatePageContent(pageName: string): string {
  const title = pageName.charAt(0).toUpperCase() + pageName.slice(1)

  return `'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function ${title}Page() {
  return (
    <PageTransition variant="fade">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gradient">${title}</h1>
          <p className="text-muted-foreground mt-1">
            Welcome to the ${pageName} page
          </p>
        </div>

        <Card variant="glass">
          <CardHeader>
            <CardTitle>Content Area</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Your ${pageName} content goes here.</p>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  )
}
`
}

program.parse()
