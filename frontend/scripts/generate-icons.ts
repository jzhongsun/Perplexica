import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

const ICON_SIZES = {
  favicon: 32,
  'apple-touch-icon': 180,
  'icon-192x192': 192,
  'icon-512x512': 512,
  'icon-maskable-192x192': 192,
  'icon-maskable-512x512': 512,
};

async function waitForServer(retries = 30, interval = 1000): Promise<boolean> {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch('http://localhost:3000/api/icon?size=32');
      if (response.ok) {
        return true;
      }
    } catch (e) {
      // Server not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  return false;
}

async function generateIcon(name: string, size: number, maskable: boolean = false) {
  const outputDir = path.join(process.cwd(), 'public', 'icons');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const url = `http://localhost:3000/api/icon?size=${size}${maskable ? '&maskable=true' : ''}`;
  const outputPath = path.join(outputDir, `${name}.png`);

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to generate icon: ${response.statusText}`);
    }
    
    const buffer = await response.arrayBuffer();
    fs.writeFileSync(outputPath, Buffer.from(buffer));
    console.log(`Generated ${name}.png (${size}x${size})`);
  } catch (error) {
    console.error(`Error generating ${name}.png:`, error);
    throw error;
  }
}

async function generateIcons() {
  console.log('Starting icon generation...');
  
  // Start the development server
  const nextDev = spawn('pnpm', ['dev'], {
    stdio: 'inherit',
  });

  try {
    // Wait for the server to be ready
    console.log('Waiting for Next.js server to start...');
    const serverReady = await waitForServer();
    if (!serverReady) {
      throw new Error('Server failed to start after 30 seconds');
    }
    console.log('Server is ready, generating icons...');

    // Generate all icons
    for (const [name, size] of Object.entries(ICON_SIZES)) {
      const isMaskable = name.includes('maskable');
      await generateIcon(name, size, isMaskable);
    }

    // Generate favicon.ico
    const faviconPath = path.join(process.cwd(), 'public', 'favicon.ico');
    await generateIcon('favicon', 32);
    fs.renameSync(
      path.join(process.cwd(), 'public', 'icons', 'favicon.png'),
      faviconPath
    );

    console.log('Icon generation complete!');
  } catch (error) {
    console.error('Error during icon generation:', error);
    process.exit(1);
  } finally {
    // Kill the development server
    nextDev.kill();
  }
}

generateIcons(); 