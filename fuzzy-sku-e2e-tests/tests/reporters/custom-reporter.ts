import {
  Reporter,
  FullConfig,
  Suite,
  FullResult,
} from '@playwright/test/reporter';
import { stringify } from 'csv-stringify/sync';
import { parse } from 'csv-parse/sync';
import * as fs from 'fs';
import * as path from 'path';
import { HTMLReportGenerator } from '../utils/html-report-generator';

// Inline TestConfig to avoid importing from test files (causes circular dependency)
const SUCCESS_THRESHOLD = 90;

/**
 * Custom Playwright Reporter
 *
 * This reporter runs AFTER all workers complete, ensuring:
 * - No race conditions when writing files
 * - All test results are collected from shared JSON file
 * - CSV and HTML reports are generated once
 *
 * ⚠️ CRITICAL: This runs AFTER test.afterAll() hooks from ALL workers
 */
class CustomTestReporter implements Reporter {
  private testResults: Array<{
    test_number: number;
    status: 'PASS' | 'FAIL' | 'NOT_RUN';
    aitehinmei: string;
    hinban: string;
    skname1: string;
    colorcd: string;
    colornm: string;
    sizecd: string;
    sizename: string;
    found_count?: number;
    total_count?: number;
    error_message?: string;
    screenshot_path?: string;
    result_position?: number;
    result_rank_range?: string;
  }> = [];

  private totalTests = 0;
  private passCount = 0;
  private failCount = 0;
  private notRunCount = 0;

  onBegin(config: FullConfig, suite: Suite) {
    console.log('\n' + '='.repeat(80));
    console.log('🚀 STARTING TEST SUITE');
    console.log('='.repeat(80));
    console.log(`   Workers: ${config.workers || 'auto'}`);
    console.log(
      `   Projects: ${config.projects.map((p) => p.name).join(', ')}`,
    );
    console.log('='.repeat(80) + '\n');
  }

  // We don't track individual test results here anymore
  // All results are saved to shared JSON file by tests themselves

  async onEnd(result: FullResult) {
    console.log('\n' + '='.repeat(80));
    console.log('📊 GENERATING FINAL REPORTS (AFTER ALL WORKERS COMPLETE)');
    console.log('='.repeat(80) + '\n');

    const basePath = path.dirname(path.dirname(__dirname));
    const sharedResultsPath = path.join(basePath, '.test-results-shared.json');
    const csvPath = path.join(basePath, 'fuzzy-sku-jpoc-testcases.csv');
    const resultsPath = path.join(basePath, 'fuzzy-sku-test-results.csv');

    // === 0. LOAD TEST RESULTS FROM SHARED FILE ===
    console.log('📂 Loading test results from shared file...');

    let allResults: any[] = [];
    if (fs.existsSync(sharedResultsPath)) {
      try {
        const content = fs.readFileSync(sharedResultsPath, 'utf-8');
        if (content.trim()) {
          allResults = JSON.parse(content);
          console.log(
            `   ✅ Loaded ${allResults.length} test results from shared file`,
          );
        }
      } catch (error) {
        console.error('   ❌ Failed to load shared results:', error);
      }
    } else {
      console.warn(
        '   ⚠️  No shared results file found - tests may not have run',
      );
    }

    // Load original CSV to get all test cases
    let testCases: any[] = [];
    if (fs.existsSync(csvPath)) {
      const csvContent = fs.readFileSync(csvPath, 'utf-8');
      testCases = parse(csvContent, {
        columns: true,
        skip_empty_lines: true,
        trim: true,
        bom: true,
      });
    }

    // === MERGE WITH PREVIOUS RESULTS ===
    // Load previous results from CSV to preserve old test results
    let previousResults: Map<number, any> = new Map();
    if (fs.existsSync(resultsPath)) {
      console.log('   📂 Loading previous results to merge...');
      try {
        const prevCsvContent = fs.readFileSync(resultsPath, 'utf-8');
        const prevResults = parse(prevCsvContent, {
          columns: true,
          skip_empty_lines: true,
          trim: true,
          bom: true,
        });

        prevResults.forEach((r: any) => {
          const testNum = parseInt(r.test_number);
          if (!isNaN(testNum)) {
            previousResults.set(testNum, r);
          }
        });

        console.log(
          `   ✅ Loaded ${previousResults.size} previous results for merging`,
        );

        // 🐛 DEBUG: Log previous results
        previousResults.forEach((r, testNum) => {
          console.log(
            `   🔍 Previous TC${String(testNum).padStart(3, '0')}: ${
              r.status
            } (found: ${r.found_count || 'N/A'}, total: ${
              r.total_count || 'N/A'
            })`,
          );
        });
      } catch (error) {
        console.warn('   ⚠️  Could not load previous results:', error);
      }
    }

    // Merge results: Priority = Current Run > Previous Results > CSV Template
    this.testResults = testCases.map((tc, idx) => {
      const testNumber = idx + 1;

      // 1st priority: Results from current run (from shared file)
      // ✅ ONLY override if test was ACTUALLY run in this execution
      const currentRun = allResults.find((r: any) => r._testIndex === idx);
      if (currentRun) {
        const { _testIndex, ...cleanResult } = currentRun;
        return {
          test_number: testNumber,
          ...cleanResult,
        };
      }

      // 2nd priority: Results from previous runs (from old CSV)
      // ✅ Preserve ALL previous results (PASS/FAIL/NOT_RUN) if test was NOT run this time
      const previousRun = previousResults.get(testNumber);
      if (previousRun) {
        // Parse numeric fields safely (CSV returns strings)
        const foundCount =
          previousRun.found_count && String(previousRun.found_count).trim();
        const totalCount =
          previousRun.total_count && String(previousRun.total_count).trim();
        const resultPosition =
          previousRun.result_position &&
          String(previousRun.result_position).trim();

        return {
          test_number: testNumber,
          status: previousRun.status, // Keep previous status (PASS/FAIL/NOT_RUN)
          aitehinmei: tc.aitehinmei,
          hinban: tc.hinban,
          skname1: tc.skname1,
          colorcd: tc.colorcd,
          colornm: tc.colornm,
          sizecd: tc.sizecd,
          sizename: tc.sizename,
          found_count: foundCount ? parseInt(foundCount) : undefined,
          total_count: totalCount ? parseInt(totalCount) : undefined,
          error_message: previousRun.error_message || '',
          screenshot_path: previousRun.screenshot_path || '',
          result_position: resultPosition
            ? parseInt(resultPosition)
            : undefined,
          result_rank_range: previousRun.result_rank_range || '',
        };
      }

      // 3rd priority: Default NOT_RUN from CSV template (first time ever)
      return {
        test_number: testNumber,
        status: 'NOT_RUN' as const,
        aitehinmei: tc.aitehinmei,
        hinban: tc.hinban,
        skname1: tc.skname1,
        colorcd: tc.colorcd,
        colornm: tc.colornm,
        sizecd: tc.sizecd,
        sizename: tc.sizename,
      };
    });

    // Debug: Log merged results to verify
    console.log('\n🔍 MERGED RESULTS:');
    this.testResults.forEach((r, idx) => {
      if (idx < 5) {
        // Only log first 5
        console.log(
          `   TC${String(r.test_number).padStart(3, '0')}: ${
            r.status
          } (found: ${r.found_count || 'N/A'}, total: ${
            r.total_count || 'N/A'
          })`,
        );
      }
    });
    console.log('');

    this.totalTests = this.testResults.length;

    // Count results
    this.passCount = this.testResults.filter((r) => r.status === 'PASS').length;
    this.failCount = this.testResults.filter((r) => r.status === 'FAIL').length;
    this.notRunCount = this.testResults.filter(
      (r) => r.status === 'NOT_RUN',
    ).length;

    // === 1. GENERATE CSV REPORT ===
    console.log('\n📄 Generating CSV report...');

    try {
      const csvOutput = stringify(this.testResults, {
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
          'result_position',
          'result_rank_range',
          'error_message',
          'screenshot_path',
        ],
        bom: true,
      });

      fs.writeFileSync(resultsPath, csvOutput, 'utf-8');
      console.log(`   ✅ CSV saved: ${resultsPath}`);
    } catch (error) {
      console.error(`   ❌ CSV generation failed:`, error);
    }

    // === 2. PRINT SUMMARY ===
    const passRate =
      this.totalTests > 0
        ? ((this.passCount / this.totalTests) * 100).toFixed(1)
        : '0.0';

    console.log('\n📈 TEST SUMMARY:');
    console.log('─'.repeat(80));
    console.log(
      `   ✅ PASS:    ${this.passCount.toString().padStart(4)} (${passRate}%)`,
    );
    console.log(`   ❌ FAIL:    ${this.failCount.toString().padStart(4)}`);
    console.log(`   ⏭️  NOT RUN: ${this.notRunCount.toString().padStart(4)}`);
    console.log(`   📊 TOTAL:   ${this.totalTests.toString().padStart(4)}`);
    console.log('─'.repeat(80));

    // Check overall success threshold
    const passRateNum = parseFloat(passRate);
    const overallSuccess = passRateNum >= SUCCESS_THRESHOLD;
    const requiredPasses = Math.ceil(
      (SUCCESS_THRESHOLD / 100) * this.totalTests,
    );

    console.log('\n📊 OVERALL TEST SUITE STATUS:');
    console.log('─'.repeat(80));
    console.log(
      `   Success Threshold: ${SUCCESS_THRESHOLD}% (${requiredPasses}/${this.totalTests} tests must pass)`,
    );
    console.log(
      `   Actual Pass Rate:  ${passRate}% (${this.passCount}/${this.totalTests} tests passed)`,
    );
    console.log(
      `   Result: ${overallSuccess ? '✅ SUITE PASSED' : '❌ SUITE FAILED'}`,
    );
    console.log('─'.repeat(80) + '\n');

    if (!overallSuccess) {
      console.log(
        `⚠️  Warning: Test suite did not meet ${SUCCESS_THRESHOLD}% success threshold.`,
      );
      console.log(
        `   Need ${requiredPasses - this.passCount} more test(s) to pass.\n`,
      );
    }

    // === 3. GENERATE HTML REPORT IN DEPLOY FOLDER ===
    console.log('📄 Generating HTML report in deploy folder...');
    console.log('─'.repeat(80));

    try {
      const reportSummary = {
        totalTests: this.totalTests,
        passCount: this.passCount,
        failCount: this.failCount,
        notRunCount: this.notRunCount,
        passRate: passRateNum,
        successThreshold: SUCCESS_THRESHOLD,
        suiteStatus: (overallSuccess ? 'PASSED' : 'FAILED') as
          | 'PASSED'
          | 'FAILED',
        timestamp: new Date().toLocaleString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }),
      };

      // === 3.1. PREPARE SCREENSHOTS ===
      const stepScreenshotsDir = path.join(basePath, 'test-screenshots-steps');

      // === 3.2. CREATE DEPLOY FOLDER FOR S3/CloudFront ===
      const deployFolder = path.join(basePath, 'custom-report-dist');
      const deployScreenshotsFolder = path.join(deployFolder, 'screenshots');
      const deployIndexPath = path.join(deployFolder, 'index.html');

      // Create deploy folder structure
      if (!fs.existsSync(deployFolder)) {
        fs.mkdirSync(deployFolder, { recursive: true });
      }
      if (!fs.existsSync(deployScreenshotsFolder)) {
        fs.mkdirSync(deployScreenshotsFolder, { recursive: true });
      }

      // 🗑️ Clean old screenshots in deploy folder first
      if (fs.existsSync(deployScreenshotsFolder)) {
        const oldDeployScreenshots = fs.readdirSync(deployScreenshotsFolder);
        if (oldDeployScreenshots.length > 0) {
          console.log(
            `   🗑️  Cleaning ${oldDeployScreenshots.length} old screenshot(s) from deploy folder...`,
          );
          oldDeployScreenshots.forEach((file) => {
            fs.unlinkSync(path.join(deployScreenshotsFolder, file));
          });
        }
      }

      // Copy step screenshots to deploy folder
      if (fs.existsSync(stepScreenshotsDir)) {
        const screenshots = fs.readdirSync(stepScreenshotsDir);
        screenshots.forEach((screenshot) => {
          const srcPath = path.join(stepScreenshotsDir, screenshot);
          const destPath = path.join(deployScreenshotsFolder, screenshot);
          fs.copyFileSync(srcPath, destPath);
        });
        console.log(
          `   📸 Copied ${screenshots.length} step screenshots to deploy folder`,
        );
      } else {
        console.warn('   ⚠️  No step screenshots found');
      }

      // Update results for DEPLOY report (use screenshots/ path)
      const resultsForDeploy = this.testResults.map((result) => {
        const testId = `TC${String(result.test_number).padStart(3, '0')}`;
        const stepScreenshots: string[] = [];

        if (fs.existsSync(stepScreenshotsDir)) {
          const allScreenshots = fs.readdirSync(stepScreenshotsDir);
          const testScreenshots = allScreenshots
            .filter((file) => file.startsWith(testId))
            .sort();

          testScreenshots.forEach((file) => {
            stepScreenshots.push(`screenshots/${file}`); // Relative to deploy folder
          });
        }

        return {
          ...result,
          step_screenshots: stepScreenshots,
          screenshot_path: stepScreenshots.join('|'),
        };
      });

      // Generate index.html in deploy folder
      HTMLReportGenerator.generate(
        resultsForDeploy,
        reportSummary,
        deployIndexPath,
      );

      console.log(`   ✅ HTML report generated: ${deployIndexPath}`);
      console.log(`   🌐 Open in browser: file://${deployIndexPath}`);
      console.log(`   📦 Ready to deploy to S3/CloudFront`);
      console.log(`   📂 Structure:`);
      console.log(`      - custom-report-dist/`);
      console.log(`        ├── index.html`);
      console.log(`        └── screenshots/`);
      console.log('─'.repeat(80) + '\n');
    } catch (error) {
      console.error('   ❌ HTML report generation failed:', error);
    }

    // === 4. CLEANUP SHARED FILE ===
    if (fs.existsSync(sharedResultsPath)) {
      try {
        fs.unlinkSync(sharedResultsPath);
        console.log('🧹 Cleaned up shared results file\n');
      } catch (error) {
        console.error('⚠️  Failed to cleanup shared results file:', error);
      }
    }

    // === 5. FINAL STATUS ===
    console.log('='.repeat(80));
    console.log(
      `${
        overallSuccess
          ? '✅ TEST SUITE COMPLETED SUCCESSFULLY'
          : '❌ TEST SUITE FAILED'
      }`,
    );
    console.log('='.repeat(80) + '\n');
  }
}

export default CustomTestReporter;
