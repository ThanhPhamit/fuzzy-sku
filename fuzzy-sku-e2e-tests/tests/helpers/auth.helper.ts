import { Page, expect } from '@playwright/test';
import process from 'process';

/**
 * Login helper function
 * Performs login and waits for navigation to search page
 */
export async function login(page: Page) {
  const username = process.env.TEST_USERNAME;
  const password = process.env.TEST_PASSWORD;

  if (!username || !password) {
    throw new Error(
      'TEST_USERNAME and TEST_PASSWORD must be set in .env file.\n' +
        'Please update the .env file with your credentials.',
    );
  }

  console.log(`🔐 Attempting login for user: ${username}`);

  // Navigate to login page
  await page.goto('/');

  // Wait for login form to be visible
  await page.waitForSelector('input[type="text"]', { timeout: 10000 });

  // Fill in credentials
  await page.fill('input[type="text"]', username);
  await page.fill('input[type="password"]', password);

  // Click login button
  await page.click('button[type="submit"]');

  // Wait for navigation to search page
  await page.waitForURL('**/search', { timeout: 15000 });

  console.log('✅ Login successful');
}

/**
 * Check if user is already logged in
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  try {
    // Check if we're on the search page and can see the search input
    const currentUrl = page.url();
    if (!currentUrl.includes('/search')) {
      return false;
    }

    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.waitFor({ state: 'visible', timeout: 2000 });
    return true;
  } catch {
    return false;
  }
}
