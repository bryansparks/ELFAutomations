#!/usr/bin/env node

import { Command } from 'commander'
import { create } from './commands/create'
import { generate } from './commands/generate'
import { connect } from './commands/connect'
import chalk from 'chalk'

const program = new Command()

program
  .name('elf-ui')
  .description('ELF UI CLI - Rapid development tool for ELF applications')
  .version('1.0.0')

program
  .command('create <name>')
  .description('Create a new ELF application')
  .option('-t, --template <template>', 'Use a specific template', 'dashboard')
  .option('--ts, --typescript', 'Use TypeScript (default)', true)
  .option('--js, --javascript', 'Use JavaScript')
  .option('--auth <provider>', 'Add authentication', 'supabase')
  .option('--git', 'Initialize git repository', true)
  .option('--install', 'Install dependencies', true)
  .action(create)

program
  .command('generate <type> <name>')
  .alias('g')
  .description('Generate a new component, page, or hook')
  .option('--crud', 'Generate CRUD operations')
  .option('--animate', 'Add animations')
  .option('--api', 'Include API integration')
  .action(generate)

program
  .command('connect api')
  .description('Connect to an API and generate types/hooks')
  .option('--swagger <path>', 'Path to OpenAPI/Swagger spec')
  .option('--graphql <url>', 'GraphQL endpoint URL')
  .option('--generate-hooks', 'Generate React hooks')
  .option('--generate-types', 'Generate TypeScript types')
  .action(connect)

// ASCII art logo
console.log(chalk.cyan(`
╔═══════════════════════════════════════╗
║                                       ║
║   ███████╗██╗     ███████╗            ║
║   ██╔════╝██║     ██╔════╝            ║
║   █████╗  ██║     █████╗              ║
║   ██╔══╝  ██║     ██╔══╝              ║
║   ███████╗███████╗██║                 ║
║   ╚══════╝╚══════╝╚═╝                 ║
║                                       ║
║         UI Development System         ║
║                                       ║
╚═══════════════════════════════════════╝
`))

program.parse()
