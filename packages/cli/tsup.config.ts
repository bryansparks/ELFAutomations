import { defineConfig } from 'tsup'

export default defineConfig({
  entry: ['src/index-simple.ts'],
  format: ['cjs'],
  banner: {
    js: '#!/usr/bin/env node'
  },
  clean: true,
})
