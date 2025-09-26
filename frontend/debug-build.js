#!/usr/bin/env node

/**
 * Debug script for Render deployment issues
 * This script helps diagnose common build problems
 */

const fs = require('fs')
const path = require('path')

console.log('🔍 SCRIBE Frontend Build Debug Report')
console.log('=====================================')

// Check Node version
console.log(`📦 Node.js version: ${process.version}`)
console.log(`🔧 Platform: ${process.platform}`)
console.log(`🏗️  Architecture: ${process.arch}`)

// Check if components exist
const componentsPath = path.join(__dirname, 'components', 'ui')
console.log(`\n🎨 UI Components Status:`)

const expectedComponents = [
  'button.tsx',
  'card.tsx',
  'textarea.tsx',
  'input.tsx',
  'badge.tsx',
  'label.tsx',
  'switch.tsx',
  'index.ts'
]

expectedComponents.forEach(component => {
  const componentPath = path.join(componentsPath, component)
  const exists = fs.existsSync(componentPath)
  console.log(`   ${exists ? '✅' : '❌'} ${component}`)

  if (exists && component.endsWith('.tsx')) {
    const content = fs.readFileSync(componentPath, 'utf8')
    const hasExport = content.includes('export')
    const hasForwardRef = content.includes('forwardRef')
    console.log(`      - Has exports: ${hasExport ? '✅' : '❌'}`)
    console.log(`      - Uses forwardRef: ${hasForwardRef ? '✅' : '❌'}`)
  }
})

// Check lib/utils
const utilsPath = path.join(__dirname, 'lib', 'utils.ts')
const utilsExists = fs.existsSync(utilsPath)
console.log(`\n🛠️  Utils Status:`)
console.log(`   ${utilsExists ? '✅' : '❌'} lib/utils.ts`)

if (utilsExists) {
  const utilsContent = fs.readFileSync(utilsPath, 'utf8')
  const hasCn = utilsContent.includes('export function cn')
  console.log(`   ${hasCn ? '✅' : '❌'} cn function exported`)
}

// Check dependencies
const packagePath = path.join(__dirname, 'package.json')
const packageExists = fs.existsSync(packagePath)
console.log(`\n📦 Dependencies Status:`)
console.log(`   ${packageExists ? '✅' : '❌'} package.json`)

if (packageExists) {
  const packageContent = JSON.parse(fs.readFileSync(packagePath, 'utf8'))
  const deps = packageContent.dependencies || {}

  const criticalDeps = [
    'class-variance-authority',
    'clsx',
    'tailwind-merge',
    'react',
    'next',
    'lucide-react'
  ]

  criticalDeps.forEach(dep => {
    const exists = deps[dep]
    console.log(`   ${exists ? '✅' : '❌'} ${dep}: ${exists || 'MISSING'}`)
  })
}

// Check tsconfig
const tsconfigPath = path.join(__dirname, 'tsconfig.json')
const tsconfigExists = fs.existsSync(tsconfigPath)
console.log(`\n⚙️  TypeScript Config:`)
console.log(`   ${tsconfigExists ? '✅' : '❌'} tsconfig.json`)

if (tsconfigExists) {
  const tsconfigContent = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'))
  const hasBaseUrl = tsconfigContent.compilerOptions?.baseUrl
  const hasPaths = tsconfigContent.compilerOptions?.paths
  console.log(`   ${hasBaseUrl ? '✅' : '❌'} baseUrl configured`)
  console.log(`   ${hasPaths ? '✅' : '❌'} paths configured`)

  if (hasPaths) {
    const hasAtSlash = hasPaths['@/*']
    console.log(`   ${hasAtSlash ? '✅' : '❌'} @/* path mapping`)
  }
}

// Environment check
console.log(`\n🌍 Environment:`)
console.log(`   NODE_ENV: ${process.env.NODE_ENV || 'not set'}`)
console.log(`   RENDER: ${process.env.RENDER || 'not set'}`)

console.log('\n🚀 Build Debug Complete!')
console.log('If components show ✅ but build still fails on Render:')
console.log('1. Check Render build logs for specific error messages')
console.log('2. Ensure Node.js version matches between local and Render')
console.log('3. Clear Render build cache and retry')
console.log('4. Check if environment variables are properly set')