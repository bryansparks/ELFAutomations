import chalk from 'chalk'
import ora from 'ora'
import fs from 'fs-extra'
import path from 'path'

export async function create(name: string, options: any) {
  const spinner = ora()

  try {
    const projectPath = path.join(process.cwd(), name)

    if (fs.existsSync(projectPath)) {
      console.error(chalk.red(`Error: Directory ${name} already exists`))
      process.exit(1)
    }

    console.log(chalk.cyan(`\nCreating ${name}...\n`))
    spinner.start('Creating project structure...')

    await fs.ensureDir(projectPath)

    // Create a simple package.json
    const packageJson = {
      name,
      version: '0.1.0',
      private: true,
      scripts: {
        dev: 'next dev',
        build: 'next build',
        start: 'next start',
      },
      dependencies: {
        '@elf/ui': 'file:../../packages/ui',
        'next': '^14.1.0',
        'react': '^18.2.0',
        'react-dom': '^18.2.0',
      }
    }

    await fs.writeJson(path.join(projectPath, 'package.json'), packageJson, { spaces: 2 })
    spinner.succeed('Project created')

    console.log(chalk.green('\n✨ Project created successfully!\n'))
    console.log(chalk.cyan('To get started:'))
    console.log(chalk.white(`  cd ${name}`))
    console.log(chalk.white('  npm install'))
    console.log(chalk.white('  npm run dev'))
    console.log()

  } catch (error) {
    spinner.fail('Failed to create project')
    console.error(error)
    process.exit(1)
  }
}
