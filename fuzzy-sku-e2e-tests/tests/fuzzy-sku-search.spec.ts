import { test, expect, Page } from '@playwright/test';
import { parse } from 'csv-parse/sync';
import { stringify } from 'csv-stringify/sync';
import * as fs from 'fs';
import * as path from 'path';
import { login } from './helpers/auth.helper';
import { TestConfig } from './config/test-config';
import { HTMLReportGenerator } from './utils/html-report-generator';
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
}

/**
 * Load test cases from CSV file - MUST BE DONE BEFORE test.describe()
 */
// Path to CSV file (now in the same directory as e2e-tests folder)
const csvPath = path.join(__dirname, '../fuzzy-sku-jpoc-testcases.csv');
const resultsPath = path.join(__dirname, '../fuzzy-sku-test-results.csv');

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

// Initialize shared results file
if (!fs.existsSync(sharedResultsPath)) {
  fs.writeFileSync(sharedResultsPath, JSON.stringify([]), 'utf-8');
}

console.log(`✅ Successfully loaded ${testCases.length} test cases from CSV\n`);

/**
 * Save individual test result to shared file (thread-safe with file locking)
 */
function saveTestResult(index: number, result: TestResult) {
  try {
    // Read current results
    let allResults: TestResult[] = [];
    if (fs.existsSync(sharedResultsPath)) {
      const content = fs.readFileSync(sharedResultsPath, 'utf-8');
      if (content.trim()) {
        allResults = JSON.parse(content);
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

    // Write back (atomic write)
    const tempPath = sharedResultsPath + '.tmp';
    fs.writeFileSync(tempPath, JSON.stringify(allResults, null, 2), 'utf-8');
    fs.renameSync(tempPath, sharedResultsPath);
  } catch (error) {
    console.error(`⚠️  Failed to save test result ${index}:`, error);
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
      const screenshotter = createScreenshotter(
        page,
        testId,
        TestConfig.STEP_SCREENSHOTS.outputDir,
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
   * Final reports are generated by custom-reporter.ts after ALL workers complete
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

    // Merge with original test cases to get all fields
    const mergedResults = testCases.map((tc, idx) => {
      const saved = allResults.find((r: any) => r._testIndex === idx);
      return saved || { ...tc, status: 'NOT_RUN' as const };
    });

    // Prepare CSV data
    const csvData = mergedResults.map((result, index) => ({
      test_number: index + 1,
      status: result.status || 'NOT_RUN',
      aitehinmei: result.aitehinmei,
      hinban: result.hinban,
      skname1: result.skname1,
      colorcd: result.colorcd,
      colornm: result.colornm,
      sizecd: result.sizecd,
      sizename: result.sizename,
      found_count: result.found_count ?? '',
      total_count: result.total_count ?? '',
      error_message: result.error_message || '',
      screenshot_path: result.screenshot_path || '',
    }));

    // Convert to CSV string
    const csvOutput = stringify(csvData, {
      header: true,
      columns: [
        'test_number',
        'status',
        'aitehinmei',
        'hinban',
        'skname1',
        'colorcd',
        'colornm',
        'sizecd',
        'sizename',
        'found_count',
        'total_count',
        'error_message',
        'screenshot_path',
      ],
      bom: true,
    });

    // Write to file (this will be overwritten by custom reporter)
    fs.writeFileSync(resultsPath, csvOutput, 'utf-8');

    // Count results
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

    console.log(
      '⏳ Waiting for custom reporter to generate final reports...\n',
    );
  });
});
