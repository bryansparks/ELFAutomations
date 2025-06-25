#!/usr/bin/env node

import { Command } from 'commander'
import { create } from './commands/create-simple'
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
  .action(create)

console.log(chalk.cyan('ELF UI Development System'))

program.parse()
