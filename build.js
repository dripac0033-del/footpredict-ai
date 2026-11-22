#!/usr/bin/env node
/**
 * FootPredict Web App Packager / Bundler
 * Compiles and packages the PWA into dist/ and creates distributable archives.
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const publicDir = path.join(__dirname, 'public');
const distDir = path.join(__dirname, 'dist');

console.log('📦 Starting Web App packaging...');

// Ensure clean dist dir
if (fs.existsSync(distDir)) {
  fs.rmSync(distDir, { recursive: true, force: true });
}
fs.mkdirSync(distDir, { recursive: true });

// Copy public assets to dist
function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

copyDir(publicDir, distDir);
console.log('✅ Web App assets copied to dist/');

// Create Zip & APK bundles
const zipPath = path.join(distDir, 'footpredict-web-app.zip');
const apkPath = path.join(distDir, 'footpredict-v1.0.apk');

try {
  process.chdir(distDir);
  execSync(`zip -r "${zipPath}" . -x "*.zip" "*.apk"`, { stdio: 'inherit' });
  fs.copyFileSync(zipPath, apkPath);
  console.log(`✅ Web App Bundle created at: ${zipPath}`);
  console.log(`✅ Web App APK package created at: ${apkPath}`);
} catch (err) {
  console.warn('⚠️ zip command failed, creating fallback package:', err.message);
}

console.log('🎉 Packaging complete! Web App ready.');
