/**
 * Test Configuration
 * Adjust these values to change test behavior
 */
export const TestConfig = {
  /**
   * SUCCESS_THRESHOLD: Overall test suite success rate
   *
   * This is the MINIMUM percentage of test cases that must PASS
   * for the entire test suite to be considered successful.
   *
   * Examples:
   * - 90: At least 90% of 844 tests must PASS (760 tests)
   * - 85: At least 85% of 844 tests must PASS (717 tests)
   * - 80: At least 80% of 844 tests must PASS (676 tests)
   *
   * Note: Each individual test case must find ALL expected fields to PASS.
   * Fields with "-" in CSV are considered N/A and auto-pass.
   *
   * Recommended: 90 for production, 80-85 for development
   */
  SUCCESS_THRESHOLD: 90,

  /**
   * Wait time after search (milliseconds)
   * Increase if results load slowly
   */
  SEARCH_WAIT_TIME: 10000, // Tăng từ 2.5s lên 5s để đợi kết quả search

  /**
   * Highlight duration (milliseconds)
   * How long to keep the green highlight before screenshot
   */
  HIGHLIGHT_DURATION: 500,

  /**
   * Screenshot settings
   */
  SCREENSHOT: {
    enabled: true,
    fullPage: true,
  },

  /**
   * Step-by-step screenshots (like TestCafe)
   * Chụp màn hình từng step thao tác
   */
  STEP_SCREENSHOTS: {
    enabled: true, // Bật/tắt step screenshots
    fullPage: true, // Chụp toàn bộ trang hay chỉ viewport
    outputDir: './test-screenshots-steps', // Thư mục lưu screenshots
    attachToReport: true, // ✅ Attach screenshots vào Playwright HTML Report
  },
};
