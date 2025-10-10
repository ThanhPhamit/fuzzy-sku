import { Page, test } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Screenshot Helper - Chụp màn hình từng step như TestCafe
 *
 * Usage:
 * ```typescript
 * const screenshotter = new ScreenshotHelper(page, 'TC001', './screenshots');
 * await screenshotter.capture('step1-login');
 * await screenshotter.capture('step2-search');
 * await screenshotter.capture('step3-results');
 * ```
 */
export class ScreenshotHelper {
  private page: Page;
  private testId: string;
  private outputDir: string;
  private stepCounter: number = 0;
  private enabled: boolean;
  private attachToReport: boolean;

  constructor(
    page: Page,
    testId: string,
    outputDir: string,
    enabled: boolean = true,
    attachToReport: boolean = true,
  ) {
    this.page = page;
    this.testId = testId;
    this.outputDir = outputDir;
    this.enabled = enabled;
    this.attachToReport = attachToReport;

    // Tạo thư mục nếu chưa có
    if (this.enabled && !fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
  }

  /**
   * Chụp màn hình một step cụ thể
   * @param stepName - Tên của step (ví dụ: 'fill-search-input', 'click-search-button')
   * @param options - Tùy chọn screenshot (fullPage, clip, etc.)
   */
  async capture(
    stepName: string,
    options?: {
      fullPage?: boolean;
      clip?: { x: number; y: number; width: number; height: number };
    },
  ): Promise<string | null> {
    if (!this.enabled) {
      return null;
    }

    try {
      this.stepCounter++;
      const paddedStep = String(this.stepCounter).padStart(2, '0');
      const filename = `${this.testId}_step${paddedStep}_${stepName}.png`;
      const filepath = path.join(this.outputDir, filename);

      // Chụp screenshot
      const screenshotBuffer = await this.page.screenshot({
        fullPage: options?.fullPage ?? true,
        clip: options?.clip,
      });

      // Lưu vào file
      fs.writeFileSync(filepath, screenshotBuffer);

      console.log(`   📸 Screenshot saved: ${filename}`);

      // ✅ Attach screenshot vào Playwright HTML Report
      if (this.attachToReport) {
        await test.info().attach(`Step ${paddedStep}: ${stepName}`, {
          body: screenshotBuffer,
          contentType: 'image/png',
        });
      }

      return filepath;
    } catch (error) {
      console.error(
        `   ⚠️  Failed to capture screenshot for ${stepName}:`,
        error,
      );
      return null;
    }
  }

  /**
   * Chụp màn hình và highlight một element cụ thể
   * @param stepName - Tên của step
   * @param selector - Selector của element cần highlight
   * @param highlightColor - Màu highlight (default: green)
   */
  async captureWithHighlight(
    stepName: string,
    selector: string,
    highlightColor: string = '#86efac',
    options?: { fullPage?: boolean },
  ): Promise<string | null> {
    if (!this.enabled) {
      return null;
    }

    try {
      // Highlight element
      const element = this.page.locator(selector).first();
      if (await element.isVisible().catch(() => false)) {
        await element.evaluate((el, color) => {
          el.style.backgroundColor = color;
          el.style.border = '3px solid #22c55e';
          el.style.transition = 'all 0.3s ease';
        }, highlightColor);

        await this.page.waitForTimeout(300); // Đợi animation
      }

      return await this.capture(stepName, options);
    } catch (error) {
      console.error(
        `   ⚠️  Failed to capture screenshot with highlight for ${stepName}:`,
        error,
      );
      return null;
    }
  }

  /**
   * Reset step counter (dùng khi bắt đầu test case mới)
   */
  reset(): void {
    this.stepCounter = 0;
  }

  /**
   * Get current step counter
   */
  getStepCount(): number {
    return this.stepCounter;
  }

  /**
   * Enable/disable screenshots
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }
}

/**
 * Factory function để tạo ScreenshotHelper dễ dàng hơn
 */
export function createScreenshotter(
  page: Page,
  testId: string,
  outputDir: string = './test-screenshots-steps',
  enabled: boolean = true,
  attachToReport: boolean = true,
): ScreenshotHelper {
  return new ScreenshotHelper(page, testId, outputDir, enabled, attachToReport);
}
