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
    const htmlReportPath = path.join(basePath, 'custom-report.html');

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

    // Merge results with original test cases
    this.testResults = testCases.map((tc, idx) => {
      const saved = allResults.find((r: any) => r._testIndex === idx);
      if (saved) {
        // Remove internal _testIndex field
        const { _testIndex, ...cleanResult } = saved;
        return {
          test_number: idx + 1,
          ...cleanResult,
        };
      }
      return {
        test_number: idx + 1,
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

    // === 3. GENERATE HTML REPORT & DEPLOY FOLDER ===
    console.log('📄 Generating custom HTML report & deploy folder...');
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

      // === 3.1. PREPARE SCREENSHOTS FIRST ===
      const stepScreenshotsDir = path.join(basePath, 'test-screenshots-steps');

      // Update all results for ROOT report (use test-screenshots-steps/ path)
      const resultsForRoot = this.testResults.map((result) => {
        const testId = `TC${String(result.test_number).padStart(3, '0')}`;
        const stepScreenshots: string[] = [];

        if (fs.existsSync(stepScreenshotsDir)) {
          const allScreenshots = fs.readdirSync(stepScreenshotsDir);
          const testScreenshots = allScreenshots
            .filter((file) => file.startsWith(testId))
            .sort();

          testScreenshots.forEach((file) => {
            stepScreenshots.push(`test-screenshots-steps/${file}`); // Relative to root
          });
        }

        return {
          ...result,
          step_screenshots: stepScreenshots,
          screenshot_path: stepScreenshots.join('|'),
        };
      });

      // Generate custom-report.html in root (for local viewing)
      HTMLReportGenerator.generate(
        resultsForRoot,
        reportSummary,
        htmlReportPath,
      );

      console.log(`   ✅ HTML report generated: ${htmlReportPath}`);
      console.log(`   🌐 Open in browser: file://${htmlReportPath}`);

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

      // Debug: Verify screenshots are included
      if (resultsForDeploy.length > 0) {
        console.log(`   🔍 Sample test result with screenshots:`, {
          test_number: resultsForDeploy[0].test_number,
          screenshot_count: resultsForDeploy[0].step_screenshots?.length || 0,
          screenshots: resultsForDeploy[0].step_screenshots,
        });
      }

      // Generate index.html in deploy folder
      HTMLReportGenerator.generate(
        resultsForDeploy,
        reportSummary,
        deployIndexPath,
      );

      console.log(`   ✅ Deploy folder created: ${deployFolder}`);
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
