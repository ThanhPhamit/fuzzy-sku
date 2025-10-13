import { test, expect, Page } from '@playwright/test';
import { parse } from 'csv-parse/sync';
import * as fs from 'fs';
import * as path from 'path';
import { login } from './helpers/auth.helper';
import { TestConfig } from './config/test-config';
import {
  createScreenshotter,
  ScreenshotHelper,
} from './helpers/screenshot.helper';

/**
 * Test Case Interface based on CSV structure
 */
interface TestCase {
  aitehinmei: string; // Input: Search query
  hinban: string; // Expected output: Product code
  skname1: string; // Expected output: SKU name
  colorcd: string; // Expected output: Color code
  colornm: string; // Expected output: Color name
  sizecd: string; // Expected output: Size code
  sizename: string; // Expected output: Size name
}

/**
 * Test Result Interface - extended with status and screenshot
 */
interface TestResult extends TestCase {
  status?: 'PASS' | 'FAIL' | 'NOT_RUN';
  error_message?: string;
  found_count?: number;
  total_count?: number;
  screenshot_path?: string;
  result_position?: number; // Vị trí của expected result trong danh sách (1-based)
  result_rank_range?: string; // Khoảng ranking: 'Top 1-5', 'Top 6-10', etc.
}

/**
 * Load test cases from CSV file - MUST BE DONE BEFORE test.describe()
 */
// Path to CSV file (now in the same directory as e2e-tests folder)
const csvPath = path.join(__dirname, '../fuzzy-sku-jpoc-testcases.csv');

console.log(`📁 Loading test cases from: ${csvPath}`);

if (!fs.existsSync(csvPath)) {
  throw new Error(`CSV file not found at: ${csvPath}`);
}

const csvContent = fs.readFileSync(csvPath, 'utf-8');

const testCases: TestCase[] = parse(csvContent, {
  columns: true,
  skip_empty_lines: true,
  trim: true,
  bom: true, // Handle BOM (Byte Order Mark) for UTF-8 files with Japanese characters
});

// Initialize results array
const testResults: TestResult[] = testCases.map((tc) => ({
  ...tc,
  status: 'NOT_RUN',
}));

// Path to shared results file (for parallel workers)
const sharedResultsPath = path.join(__dirname, '../.test-results-shared.json');

// ✅ MERGE MODE: Preserve existing results when rerunning specific tests
// This allows you to rerun only failed/specific tests and merge with previous results
if (!fs.existsSync(sharedResultsPath)) {
  console.log('📝 Creating new shared results file (first run)...');
  fs.writeFileSync(sharedResultsPath, JSON.stringify([]), 'utf-8');
} else {
  console.log(
    '📝 Found existing results - will merge new results (rerun mode)...',
  );
}

console.log(`✅ Successfully loaded ${testCases.length} test cases from CSV\n`);

/**
 * Save individual test result to shared file with retry logic
 */
function saveTestResult(index: number, result: TestResult) {
  const maxRetries = 5;
  const baseDelay = 50; // ms

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      // Add exponential backoff with jitter
      if (attempt > 0) {
        const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 100;
        const start = Date.now();
        while (Date.now() - start < delay) {
          /* busy wait */
        }
      }

      // Read current results with validation
      let allResults: TestResult[] = [];
      if (fs.existsSync(sharedResultsPath)) {
        const content = fs.readFileSync(sharedResultsPath, 'utf-8');
        if (content.trim()) {
          try {
            allResults = JSON.parse(content);
            if (!Array.isArray(allResults)) {
              console.warn(`   ⚠️  Invalid JSON, resetting...`);
              allResults = [];
            }
          } catch (parseError) {
            if (attempt < maxRetries - 1) {
              continue; // Retry on parse error
            }
            console.warn(
              `   ⚠️  Corrupt JSON after ${maxRetries} attempts, resetting...`,
            );
            allResults = [];
          }
        }
      }

      // Update or add result
      const existingIndex = allResults.findIndex(
        (r: any) => r._testIndex === index,
      );
      const resultWithIndex = { ...result, _testIndex: index };

      if (existingIndex >= 0) {
        allResults[existingIndex] = resultWithIndex;
      } else {
        allResults.push(resultWithIndex);
      }

      // Atomic write with unique temp file
      const tempPath = `${sharedResultsPath}.tmp.${process.pid}.${Date.now()}`;
      fs.writeFileSync(tempPath, JSON.stringify(allResults, null, 2), 'utf-8');
      fs.renameSync(tempPath, sharedResultsPath);

      return; // Success!
    } catch (error) {
      if (attempt === maxRetries - 1) {
        console.error(
          `⚠️  Failed to save test result ${index} after ${maxRetries} attempts:`,
          error,
        );
      }
    }
  }
}

/**
 * Main test suite for Fuzzy SKU Search
 */
test.describe('Fuzzy SKU Search - CSV Test Cases', () => {
  let page: Page;

  /**
   * Setup: Login before each test
   */
  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;

    // Login before each test
    await login(page);

    // Ensure we're on the search page
    await page.goto('/search');
    await page.waitForSelector('input[type="text"]', { timeout: 5000 });

    console.log('---');
  });

  /**
   * Generate a test for each row in the CSV
   */
  testCases.forEach((testCase, index) => {
    test(`TC${String(index + 1).padStart(3, '0')}: "${testCase.aitehinmei}" → ${
      testCase.hinban
    }`, async () => {
      console.log(`\n🔍 Test Case ${index + 1}/${testCases.length}`);
      console.log(`   📝 Input (aitehinmei): "${testCase.aitehinmei}"`);
      console.log(`   🎯 Expected Results:`);
      console.log(`      - Hinban: ${testCase.hinban}`);
      console.log(`      - SKU Name: ${testCase.skname1}`);
      console.log(`      - Color: ${testCase.colornm} (${testCase.colorcd})`);
      console.log(`      - Size: ${testCase.sizename} (${testCase.sizecd})`);

      // 🎬 Initialize Screenshot Helper cho test case này
      const testId = `TC${String(index + 1).padStart(3, '0')}`;

      // 🗑️ Delete old screenshots for this test case before rerun
      const screenshotDir = TestConfig.STEP_SCREENSHOTS.outputDir;
      if (fs.existsSync(screenshotDir)) {
        const oldScreenshots = fs
          .readdirSync(screenshotDir)
          .filter((file) => file.startsWith(testId));

        if (oldScreenshots.length > 0) {
          console.log(
            `   🗑️  Deleting ${oldScreenshots.length} old screenshot(s)...`,
          );
          oldScreenshots.forEach((file) => {
            fs.unlinkSync(path.join(screenshotDir, file));
          });
        }
      }

      const screenshotter = createScreenshotter(
        page,
        testId,
        screenshotDir,
        TestConfig.STEP_SCREENSHOTS.enabled,
        TestConfig.STEP_SCREENSHOTS.attachToReport, // ✅ Attach vào HTML report
      );

      // 📸 Step 1: Chụp màn hình trang search ban đầu
      await screenshotter.capture('01-initial-search-page');

      // Get the search input (placeholder: "Enter aitehinmei")
      const searchInput = page.locator('input[placeholder="Enter aitehinmei"]');

      // Clear any existing value
      await searchInput.clear();
      await page.waitForTimeout(300);

      // Enter search query
      await searchInput.fill(testCase.aitehinmei);
      console.log(`   ⌨️  Entered search query: "${testCase.aitehinmei}"`);

      // 📸 Step 2: Chụp màn hình sau khi nhập search query (highlight input)
      await screenshotter.captureWithHighlight(
        '02-filled-search-query',
        'input[placeholder="Enter aitehinmei"]',
        '#fef08a', // Yellow highlight cho input
      );

      // Find and click search button (text: "🔍 Search")
      const searchButton = page.locator(
        'button[type="submit"]:has-text("Search")',
      );

      await searchButton.click();
      console.log(`   🔎 Clicked search button`);

      // Wait for results to load (wait for either table or "no results" message)
      await page.waitForTimeout(TestConfig.SEARCH_WAIT_TIME);

      // Check if we have results or no results message
      const noResultsMessage = page.locator('text=No results found');
      const hasNoResults = await noResultsMessage
        .isVisible()
        .catch(() => false);

      if (hasNoResults) {
        console.log(`   ❌ No results found for this query`);
        // 📸 Step 3: Chụp màn hình khi không có kết quả
        await screenshotter.capture('03-no-results-found');
        throw new Error(`No results found for query: "${testCase.aitehinmei}"`);
      }

      // Get the search results table
      const resultsTable = page.locator('table.min-w-full');

      // Verify results are visible
      try {
        await expect(resultsTable).toBeVisible({ timeout: 10000 });
        console.log(`   ✅ Results table is visible`);
      } catch (error) {
        console.log(`   ❌ No results table found`);

        // Check for "no results" message
        const noResultsMsg = page.locator(
          'text=/no results|結果が見つかりません/i',
        );
        const hasNoResults = await noResultsMsg.isVisible().catch(() => false);

        if (hasNoResults) {
          console.log(`   ℹ️  "No results" message displayed`);
        }

        // 📸 Step 3: Chụp màn hình khi không tìm thấy results table
        await screenshotter.capture('03-results-table-not-found');

        throw new Error('Results table not visible');
      }

      // Get all text content from results (không cần screenshot ở đây nữa)
      const resultText = (await resultsTable.textContent()) || '';

      // 🎯 Find the position of expected result in the table
      let resultPosition = -1; // -1 means not found
      try {
        // Get all rows in the table
        const rows = page.locator('table tbody tr');
        const rowCount = await rows.count();

        console.log(`   📋 Total rows in result: ${rowCount}`);

        // Search for the row containing the expected hinban
        for (let i = 0; i < rowCount; i++) {
          const row = rows.nth(i);
          const rowText = await row.textContent();

          if (rowText && rowText.includes(testCase.hinban)) {
            resultPosition = i + 1; // 1-based position
            console.log(
              `   🎯 Found expected result at position: ${resultPosition}`,
            );
            break;
          }
        }

        if (resultPosition === -1) {
          console.log(
            `   ⚠️  Expected result (${testCase.hinban}) not found in results`,
          );
        }
      } catch (error) {
        console.log(`   ⚠️  Could not determine result position: ${error}`);
      }

      // Determine rank range based on position
      let rankRange = 'Not Found';
      if (resultPosition > 0) {
        if (resultPosition <= 5) {
          rankRange = 'Top 1-5';
        } else if (resultPosition <= 10) {
          rankRange = 'Top 6-10';
        } else if (resultPosition <= 20) {
          rankRange = 'Top 11-20';
        } else if (resultPosition <= 30) {
          rankRange = 'Top 21-30';
        } else if (resultPosition <= 50) {
          rankRange = 'Top 31-50';
        } else {
          rankRange = `Below Top 50 (Position ${resultPosition})`;
        }
      }

      console.log(`   📊 Rank Range: ${rankRange}`);

      // Save position info to test results
      testResults[index].result_position =
        resultPosition > 0 ? resultPosition : undefined;
      testResults[index].result_rank_range = rankRange;

      // Track which expected values are found
      const foundFields: { field: string; value: string; found: boolean }[] =
        [];

      // Check Hinban (Product Code) - REQUIRED
      if (testCase.hinban && testCase.hinban.trim() !== '') {
        const found = resultText.includes(testCase.hinban);
        foundFields.push({
          field: 'Hinban',
          value: testCase.hinban,
          found,
        });
        console.log(`   ${found ? '✅' : '❌'} Hinban: ${testCase.hinban}`);
      }

      // Check SKU Name - REQUIRED
      if (testCase.skname1 && testCase.skname1.trim() !== '') {
        const found = resultText.includes(testCase.skname1);
        foundFields.push({
          field: 'SKU Name',
          value: testCase.skname1,
          found,
        });
        console.log(`   ${found ? '✅' : '❌'} SKU Name: ${testCase.skname1}`);
      }

      // Check Color Code
      if (
        testCase.colorcd &&
        testCase.colorcd.trim() !== '' &&
        testCase.colorcd !== '-'
      ) {
        const found = resultText.includes(testCase.colorcd);
        foundFields.push({
          field: 'Color Code',
          value: testCase.colorcd,
          found,
        });
        console.log(
          `   ${found ? '✅' : '❌'} Color Code: ${testCase.colorcd}`,
        );
      }

      // Check Color Name
      if (
        testCase.colornm &&
        testCase.colornm.trim() !== '' &&
        testCase.colornm !== '-'
      ) {
        const found = resultText.includes(testCase.colornm);
        foundFields.push({
          field: 'Color Name',
          value: testCase.colornm,
          found,
        });
        console.log(
          `   ${found ? '✅' : '❌'} Color Name: ${testCase.colornm}`,
        );
      }

      // Check Size Code
      if (
        testCase.sizecd &&
        testCase.sizecd.trim() !== '' &&
        testCase.sizecd !== '-'
      ) {
        const found = resultText.includes(testCase.sizecd);
        foundFields.push({
          field: 'Size Code',
          value: testCase.sizecd,
          found,
        });
        console.log(`   ${found ? '✅' : '❌'} Size Code: ${testCase.sizecd}`);
      }

      // Check Size Name
      if (
        testCase.sizename &&
        testCase.sizename.trim() !== '' &&
        testCase.sizename !== '-'
      ) {
        const found = resultText.includes(testCase.sizename);
        foundFields.push({
          field: 'Size Name',
          value: testCase.sizename,
          found,
        });
        console.log(
          `   ${found ? '✅' : '❌'} Size Name: ${testCase.sizename}`,
        );
      }

      // Calculate success rate for this individual test case
      const foundCount = foundFields.filter((f) => f.found).length;
      const totalCount = foundFields.length;
      const successRate = totalCount > 0 ? (foundCount / totalCount) * 100 : 0;

      console.log(
        `\n   📊 Results: ${foundCount}/${totalCount} fields found (${successRate.toFixed(
          1,
        )}%)`,
      );

      // Update test results
      testResults[index].found_count = foundCount;
      testResults[index].total_count = totalCount;

      // ⚠️ IMPORTANT: Each test case must find ALL expected fields
      // SUCCESS_THRESHOLD in config is for overall suite success rate, not individual tests
      const allFieldsFound = foundCount === totalCount;
      const missingFields = foundFields.filter((f) => !f.found);

      try {
        expect(
          allFieldsFound,
          `Expected to find ALL ${totalCount} fields in search results.\n` +
            `   Found: ${foundCount}/${totalCount} fields (${successRate.toFixed(
              1,
            )}%)\n\n` +
            `✅ Found (${foundCount}): ${foundFields
              .filter((f) => f.found)
              .map((f) => `${f.field}`)
              .join(', ')}\n` +
            `❌ Missing (${missingFields.length}): ${missingFields
              .map((f) => `${f.field}`)
              .join(', ')}`,
        ).toBeTruthy();

        // ✅ TEST PASSED - All expected fields found
        testResults[index].status = 'PASS';
        testResults[index].error_message = '';
        console.log(
          `   ✅ Test passed! All ${totalCount} fields found (100%)\n`,
        );

        // Find and highlight the matching row in the table
        if (TestConfig.SCREENSHOT.enabled) {
          try {
            // Find the row containing the hinban
            const matchingRow = page
              .locator('table tbody tr', {
                has: page.locator(`text="${testCase.hinban}"`),
              })
              .first();

            if (await matchingRow.isVisible().catch(() => false)) {
              // Highlight the row with green background
              await matchingRow.evaluate((el) => {
                el.style.backgroundColor = '#86efac'; // Green-300
                el.style.border = '3px solid #22c55e'; // Green-600
                el.style.transition = 'all 0.3s ease';
              });

              console.log(`   🎨 Highlighted matching row`);

              // Wait for highlight to be visible
              await page.waitForTimeout(TestConfig.HIGHLIGHT_DURATION);

              // 📸 Step 3: Chụp màn hình kết quả cuối cùng với highlight
              await screenshotter.capture('03-final-result-highlighted');
            }
          } catch (highlightError) {
            console.log(`   ⚠️  Could not highlight row: ${highlightError}`);
          }

          // ✅ Test PASSED - Lưu thông tin
          testResults[index].screenshot_path = '';
          console.log(`   ✅ Test completed successfully!\n`);
        }

        // ⚠️ IMPORTANT: Save to shared file AFTER screenshot is taken
        saveTestResult(index, testResults[index]);
      } catch (error) {
        // ❌ TEST FAILED - Not all fields found
        testResults[index].status = 'FAIL';
        testResults[index].error_message = `Missing ${
          missingFields.length
        }/${totalCount} fields: ${missingFields
          .map((f) => f.field)
          .join(', ')}`;

        console.log(
          `   ❌ Test failed! Found ${foundCount}/${totalCount} fields (${successRate.toFixed(
            1,
          )}%)\n`,
        );

        // 📸 Step 3: Chụp màn hình kết quả thất bại
        if (TestConfig.SCREENSHOT.enabled) {
          await screenshotter.capture('03-final-result-failed');
        }

        // ❌ Test FAILED - Lưu thông tin
        testResults[index].screenshot_path = '';
        console.log(`   ❌ Test failed!\n`);

        // ⚠️ IMPORTANT: Save to shared file AFTER screenshot is taken
        saveTestResult(index, testResults[index]);

        throw error;
      }
    });
  });

  /**
   * After all tests complete, save results to CSV
   * NOTE: This runs PER WORKER, so we don't write final reports here
   */
  test.afterAll(async () => {
    console.log('\n' + '='.repeat(80));
    console.log('📊 WORKER COMPLETED - Waiting for other workers...');
    console.log('='.repeat(80) + '\n');

    // Load all results from shared file
    let allResults: TestResult[] = [];
    if (fs.existsSync(sharedResultsPath)) {
      const content = fs.readFileSync(sharedResultsPath, 'utf-8');
      if (content.trim()) {
        allResults = JSON.parse(content);
      }
    }

    // Sort by test index
    allResults.sort(
      (a: any, b: any) => (a._testIndex || 0) - (b._testIndex || 0),
    );

    // Merge with original test cases to get all fields (for summary only)
    const mergedResults = testCases.map((tc, idx) => {
      const saved = allResults.find((r: any) => r._testIndex === idx);
      return saved || { ...tc, status: 'NOT_RUN' as const };
    });

    // ⚠️ DO NOT write CSV here - let custom reporter handle it
    // Custom reporter has better merge logic with previous results
    // This avoids race conditions and ensures single source of truth

    // Count results for worker summary only
    const passCount = mergedResults.filter((r) => r.status === 'PASS').length;
    const failCount = mergedResults.filter((r) => r.status === 'FAIL').length;
    const notRunCount = mergedResults.filter(
      (r) => r.status === 'NOT_RUN',
    ).length;

    console.log('📈 WORKER TEST SUMMARY:');
    console.log('─'.repeat(80));
    console.log(`   ✅ PASS:    ${passCount.toString().padStart(4)}`);
    console.log(`   ❌ FAIL:    ${failCount.toString().padStart(4)}`);
    console.log(`   ⏭️  NOT RUN: ${notRunCount.toString().padStart(4)}`);
    console.log(`   📊 TOTAL:   ${testCases.length.toString().padStart(4)}`);
    console.log('─'.repeat(80) + '\n');
  });
});
