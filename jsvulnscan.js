#!/usr/bin/env node

// ========== IMPORTS (ESM) ==========
import fs from 'fs/promises';
import path from 'path';
import { Command } from 'commander';
import inquirer from 'inquirer';
import ora from 'ora';
import * as parser from '@babel/parser';
import traverse from '@babel/traverse';
import chalk from 'chalk';

const program = new Command();

// ========== VULNERABILITY RULES ==========
const VULNERABILITIES = [
  {
    id: 'EVAL',
    name: 'Use of eval()',
    description: 'Allows arbitrary code execution. Highly dangerous.',
    severity: 'CRITICAL',
    match: (node) => node.type === 'CallExpression' && 
                     node.callee.type === 'Identifier' && 
                     node.callee.name === 'eval',
    remediation: 'Replace with JSON.parse() or specific functions. Never use eval on untrusted input.'
  },
  {
    id: 'DOCUMENT_WRITE',
    name: 'document.write()',
    description: 'Can cause XSS if used with user input.',
    severity: 'HIGH',
    match: (node) => node.type === 'MemberExpression' &&
                     node.object.name === 'document' &&
                     node.property.name === 'write',
    remediation: 'Use DOM methods like createElement, textContent, or sanitization libraries.'
  },
  {
    id: 'INNER_HTML',
    name: 'Assignment to .innerHTML',
    description: 'Can enable HTML/JS injection attacks.',
    severity: 'MEDIUM',
    match: (node) => node.type === 'AssignmentExpression' &&
                     node.left.type === 'MemberExpression' &&
                     node.left.property.name === 'innerHTML',
    remediation: 'Prefer .textContent or sanitize with DOMPurify.'
  },
  {
    id: 'SET_TIMEOUT_STRING',
    name: 'setTimeout/setInterval with string',
    description: 'String-based timeout is equivalent to eval.',
    severity: 'HIGH',
    match: (node) => node.type === 'CallExpression' &&
                     ['setTimeout', 'setInterval'].includes(node.callee.name) &&
                     node.arguments[0]?.type === 'StringLiteral',
    remediation: 'Pass a function, never a string.'
  },
  {
    id: 'CONSOLE_LOG',
    name: 'console.log/debug in production',
    description: 'May leak sensitive or debug information.',
    severity: 'LOW',
    match: (node) => node.type === 'MemberExpression' &&
                     node.object.name === 'console' &&
                     ['log', 'debug', 'info', 'warn', 'error'].includes(node.property.name),
    remediation: 'Remove logs in production or use conditional logging tools.'
  },
  {
    id: 'LOCAL_STORAGE_SENSITIVE',
    name: 'localStorage.setItem with sensitive data',
    description: 'Sensitive data should not be stored in localStorage.',
    severity: 'MEDIUM',
    match: (node) => node.type === 'CallExpression' &&
                     node.callee.type === 'MemberExpression' &&
                     node.callee.object.name === 'localStorage' &&
                     node.callee.property.name === 'setItem',
    remediation: 'Avoid storing tokens, passwords, or PII in localStorage. Use httpOnly cookies.'
  }
];

// ========== CORE: FILE ANALYZER ==========
async function analyzeFile(filePath) {
  let content;
  try {
    content = await fs.readFile(filePath, 'utf8');
  } catch (err) {
    return { error: `Failed to read file: ${err.message}` };
  }

  let ast;
  try {
    ast = parser.parse(content, {
      sourceType: 'module',
      plugins: ['jsx']
    });
  } catch (err) {
    return { error: `Failed to parse JS: ${err.message}` };
  }

  const issues = [];

  traverse.default(ast, {
    enter(path) {
      for (const vuln of VULNERABILITIES) {
        if (vuln.match(path.node)) {
          issues.push({
            id: vuln.id,
            name: vuln.name,
            description: vuln.description,
            severity: vuln.severity,
            line: path.node.loc?.start.line || 0,
            column: path.node.loc?.start.column || 0,
            remediation: vuln.remediation
          });
        }
      }
    }
  });

  return { filePath, issues, content };
}

// ========== REPORTING ==========
function getSeverityColor(severity) {
  switch (severity) {
    case 'CRITICAL': return chalk.red.bold;
    case 'HIGH': return chalk.red;
    case 'MEDIUM': return chalk.yellow;
    case 'LOW': return chalk.blue;
    default: return chalk.white;
  }
}

function printReport(results) {
  console.log('\n');
  console.log(chalk.bold.white.bgBlue(' 🛡️  JAVASCRIPT VULNERABILITY SCAN REPORT '));
  console.log('\n');

  let totalIssues = 0;
  let criticalCount = 0, highCount = 0, mediumCount = 0, lowCount = 0;

  for (const result of results) {
    if (result.error) {
      console.log(chalk.red(`❌ ${result.filePath}: ${result.error}`));
      continue;
    }

    if (result.issues.length === 0) {
      console.log(chalk.green(`✅ ${result.filePath} - No vulnerabilities found.`));
      continue;
    }

    console.log(chalk.bold.underline(`📄 File: ${result.filePath}`));
    console.log('');

    for (const issue of result.issues) {
      totalIssues++;
      switch (issue.severity) {
        case 'CRITICAL': criticalCount++; break;
        case 'HIGH': highCount++; break;
        case 'MEDIUM': mediumCount++; break;
        case 'LOW': lowCount++; break;
      }

      const color = getSeverityColor(issue.severity);
      console.log(`${color('●')} ${color(issue.name)} [${issue.severity}]`);
      console.log(`  📍 Line: ${issue.line}:${issue.column}`);
      console.log(`  📖 ${issue.description}`);
      console.log(`  💡 Fix: ${issue.remediation}`);
      console.log('');
    }
    console.log('─'.repeat(80));
  }

  // Summary
  console.log('\n📊 SCAN SUMMARY:');
  console.log(chalk.red.bold(`   ● CRITICAL: ${criticalCount}`));
  console.log(chalk.red(`   ● HIGH: ${highCount}`));
  console.log(chalk.yellow(`   ● MEDIUM: ${mediumCount}`));
  console.log(chalk.blue(`   ● LOW: ${lowCount}`));
  console.log(chalk.bold(`   📌 TOTAL: ${totalIssues} issues found`));

  if (totalIssues === 0) {
    console.log(chalk.green.bold('\n🎉 Great job! No vulnerabilities detected.'));
  } else {
    console.log(chalk.red.bold('\n⚠️  We recommend fixing the above issues.'));
  }
}

// ========== INTERACTIVE MODE ==========
async function interactiveMode() {
  console.clear();
  console.log(chalk.bold.blue.bgWhite('🛡️  JS VULNERABILITY SCANNER — INTERACTIVE MODE'));
  console.log('');

  const answers = await inquirer.prompt([
    {
      type: 'list',
      name: 'targetType',
      message: 'What would you like to scan?',
      choices: [
        { name: 'Single file (.js)', value: 'file' },
        { name: 'Directory (all .js files)', value: 'dir' },
        { name: 'Exit', value: 'exit' }
      ]
    }
  ]);

  if (answers.targetType === 'exit') {
    console.log(chalk.gray('Goodbye! 👋'));
    process.exit(0);
  }

  let targetPath;
  if (answers.targetType === 'file') {
    const answer = await inquirer.prompt([{
      type: 'input',
      name: 'filePath',
      message: 'Enter the path to the .js file:',
      validate: input => {
        if (!input.endsWith('.js')) return 'Please select a .js file';
        if (!fs.existsSync(input)) return 'File not found';
        return true;
      }
    }]);
    targetPath = answer.filePath;
  } else {
    const answer = await inquirer.prompt([{
      type: 'input',
      name: 'dirPath',
      message: 'Enter directory path:',
      default: './',
      validate: input => {
        if (!fs.existsSync(input)) return 'Directory not found';
        return true;
      }
    }]);
    targetPath = answer.dirPath;
  }

  await runAnalysis(targetPath, answers.targetType === 'dir');
}

// ========== RUN ANALYSIS ==========
async function runAnalysis(target, isDirectory = false) {
  const spinner = ora('Scanning files...').start();
  let files = [];

  try {
    if (isDirectory) {
      const entries = await fs.readdir(target, { recursive: true });
      files = entries
        .filter(e => e.endsWith('.js'))
        .map(e => path.join(target, e));
    } else {
      files = [target];
    }

    if (files.length === 0) {
      spinner.fail('No .js files found.');
      return;
    }

    const results = [];
    for (const file of files) {
      const result = await analyzeFile(file);
      results.push(result);
    }

    spinner.stop();
    printReport(results);

  } catch (err) {
    spinner.fail(`Error: ${err.message}`);
  }
}

// ========== CLI FLAGS ==========
program
  .name('jsvulnscan')
  .description('JavaScript vulnerability scanner for GitHub projects')
  .version('1.0.0');

program
  .command('scan')
  .description('Scan file or directory for vulnerabilities')
  .argument('[path]', 'file or directory path to scan')
  .option('-f, --file <file>', 'scan specific file')
  .option('-d, --dir <dir>', 'scan all .js files in directory')
  .option('-i, --interactive', 'launch interactive mode')
  .action(async (path, options) => {
    if (options.interactive) {
      await interactiveMode();
      return;
    }

    if (options.file) {
      await runAnalysis(options.file, false);
    } else if (options.dir) {
      await runAnalysis(options.dir, true);
    } else if (path) {
      const stat = await fs.stat(path);
      if (stat.isDirectory()) {
        await runAnalysis(path, true);
      } else {
        await runAnalysis(path, false);
      }
    } else {
      console.log(chalk.red('❌ Error: Please specify a file, directory, or use --interactive'));
      program.help();
    }
  });

// ========== ENTRY POINT ==========
if (import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.length <= 2) {
    await interactiveMode();
  } else {
    program.parse();
  }
}
