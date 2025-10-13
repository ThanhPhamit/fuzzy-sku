import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
dotenv.config({ path: path.resolve(__dirname, '.env') });

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests',
  /*
   * Run tests in parallel within files
   * Set to true to enable parallel execution
   * WARNING: May cause rate limiting issues with API
   */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /*
   * Configure number of parallel workers
   *
   * Options:
   * - 1: Sequential (safest, no rate limiting)
   * - 2-4: Moderate parallelism (recommended)
   * - 6-8: Fast (may hit rate limits)
   * - undefined: Use all CPU cores (fastest, high risk)
   */
  workers: undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['./tests/reporters/custom-reporter.ts'], // Custom reporter for CSV and HTML generation
  ],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('')`. */
    baseURL: process.env.BASE_URL || 'https://fuzzy-sku-poc.welfan-welink.biz',

    /*
     * Trace Viewer - Tự động record TẤT CẢ actions, screenshots, network requests
     * Options:
     * - 'on': Record trace cho TẤT CẢ tests (tốn disk space nhưng debug dễ nhất)
     * - 'on-first-retry': Chỉ record khi test retry (mặc định)
     * - 'retain-on-failure': Chỉ giữ trace của tests bị FAIL
     * - 'off': Tắt trace (nhanh nhất)
     *
     * Xem trace: npx playwright show-trace trace.zip
     */
    trace: 'retain-on-failure', // ✅ Giữ trace cho tests FAIL (có thể đổi sang 'on' để debug)

    /*
     * Screenshot settings - Playwright tự động chụp
     * Options:
     * - 'on': Chụp screenshot cho TẤT CẢ tests (PASS & FAIL)
     * - 'only-on-failure': Chỉ chụp khi test FAIL
     * - 'off': Tắt screenshot tự động
     *
     * ❌ TẮT vì đã có custom step screenshots (tránh trùng lặp)
     */
    screenshot: 'off', // ❌ Tắt Playwright auto screenshot (dùng custom screenshots thay thế)

    /* Video on failure - Record video khi test bị FAIL */
    video: 'retain-on-failure',

    /* Timeouts */
    actionTimeout: 30000, // Tăng từ 15s lên 30s cho mỗi action
    navigationTimeout: 60000, // Tăng từ 30s lên 60s cho navigation
  },

  /* Global timeout for each test */
  timeout: 120000, // Tăng từ 60s lên 120s (2 phút) cho mỗi test case

  /* Expect timeout */
  expect: {
    timeout: 20000, // Tăng từ 10s lên 20s cho expect assertions
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment to test on other browsers
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },

    /* Test against mobile viewports. */
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },

    /* Test against branded browsers. */
    // {
    //   name: 'Microsoft Edge',
    //   use: { ...devices['Desktop Edge'], channel: 'msedge' },
    // },
    // {
    //   name: 'Google Chrome',
    //   use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    // },
  ],

  /* Run your local dev server before starting the tests */
  // webServer: {
  //   command: 'npm run start',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: !process.env.CI,
  // },
});
