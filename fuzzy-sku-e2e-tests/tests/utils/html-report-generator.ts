import * as fs from 'fs';
import * as path from 'path';

interface TestResult {
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
  step_screenshots?: string[]; // Array of step screenshot paths
}

interface ReportSummary {
  totalTests: number;
  passCount: number;
  failCount: number;
  notRunCount: number;
  passRate: number;
  successThreshold: number;
  suiteStatus: 'PASSED' | 'FAILED';
  timestamp: string;
}

export class HTMLReportGenerator {
  private static generateCSS(): string {
    return `
      * { margin: 0; padding: 0; box-sizing: border-box; }
      
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 20px;
        min-height: 100vh;
      }
      
      .container {
        max-width: 1600px;
        margin: 0 auto;
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        overflow: hidden;
      }
      
      .header {
        background: linear-gradient(135deg, #3C9D04 0%, #2d7603 100%);
        color: white;
        padding: 40px;
        text-align: center;
      }
      
      .header h1 {
        font-size: 2.5rem;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
      }
      
      .header p {
        font-size: 1.1rem;
        opacity: 0.9;
      }
      
      .summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
        padding: 40px;
        background: #f8f9fa;
      }
      
      .summary-card {
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        text-align: center;
        transition: transform 0.3s;
      }
      
      .summary-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
      }
      
      .summary-card h3 {
        font-size: 0.85rem;
        color: #6c757d;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
      }
      
      .summary-card .value {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 5px;
      }
      
      .summary-card .subtitle {
        font-size: 0.9rem;
        color: #6c757d;
      }
      
      .summary-card.pass .value { color: #28a745; }
      .summary-card.fail .value { color: #dc3545; }
      .summary-card.total .value { color: #007bff; }
      .summary-card.rate .value { color: #17a2b8; }
      
      .suite-status {
        padding: 25px 40px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        border-bottom: 3px solid #dee2e6;
      }
      
      .suite-status.passed {
        background: #d4edda;
        color: #155724;
        border-bottom-color: #28a745;
      }
      
      .suite-status.failed {
        background: #f8d7da;
        color: #721c24;
        border-bottom-color: #dc3545;
      }
      
      .filters {
        padding: 20px 40px;
        background: white;
        border-bottom: 2px solid #dee2e6;
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
        align-items: center;
      }
      
      .filters label {
        font-weight: 600;
        color: #495057;
      }
      
      .filter-btn {
        padding: 12px 24px;
        border: 2px solid #dee2e6;
        background: white;
        border-radius: 8px;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 600;
        transition: all 0.3s;
      }
      
      .filter-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }
      
      .filter-btn.active {
        background: #3C9D04;
        color: white;
        border-color: #3C9D04;
      }
      
      .filter-btn.all { border-color: #007bff; }
      .filter-btn.all.active { background: #007bff; border-color: #007bff; }
      
      .filter-btn.pass { border-color: #28a745; }
      .filter-btn.pass.active { background: #28a745; border-color: #28a745; }
      
      .filter-btn.fail { border-color: #dc3545; }
      .filter-btn.fail.active { background: #dc3545; border-color: #dc3545; }
      
      .test-cases {
        padding: 40px;
        background: #f8f9fa;
      }
      
      .test-case {
        background: white;
        border: 2px solid #dee2e6;
        border-radius: 12px;
        margin-bottom: 20px;
        overflow: hidden;
        transition: all 0.3s;
      }
      
      .test-case:hover {
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        transform: translateY(-3px);
      }
      
      .test-case-header {
        padding: 20px 25px;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        user-select: none;
      }
      
      .test-case-header.pass {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 6px solid #28a745;
      }
      
      .test-case-header.fail {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 6px solid #dc3545;
      }
      
      .test-case-header.not-run {
        background: linear-gradient(135deg, #e2e3e5 0%, #d6d8db 100%);
        border-left: 6px solid #6c757d;
      }
      
      .test-case-title {
        flex: 1;
      }
      
      .test-case-title h3 {
        font-size: 1.1rem;
        margin-bottom: 5px;
      }
      
      .test-case-title p {
        font-size: 0.9rem;
        color: #6c757d;
      }
      
      .test-case-status {
        display: flex;
        align-items: center;
        gap: 15px;
      }
      
      .status-badge {
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
      }
      
      .status-badge.pass {
        background: #28a745;
        color: white;
      }
      
      .status-badge.fail {
        background: #dc3545;
        color: white;
      }
      
      .status-badge.not-run {
        background: #6c757d;
        color: white;
      }
      
      .toggle-icon {
        font-size: 1.5rem;
        transition: transform 0.3s;
      }
      
      .toggle-icon.open {
        transform: rotate(90deg);
      }
      
      .test-case-body {
        display: none;
        padding: 25px;
        background: #f8f9fa;
        border-top: 2px solid #dee2e6;
      }
      
      .test-case-body.open {
        display: block;
      }
      
      .test-details {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 25px;
      }
      
      .detail-group {
        background: white;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #3C9D04;
      }
      
      .detail-group h4 {
        font-size: 0.85rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
      }
      
      .detail-group p {
        font-size: 1rem;
        color: #212529;
        word-break: break-word;
      }
      
      .detail-group.error {
        border-left-color: #dc3545;
      }
      
      .detail-group.error p {
        color: #dc3545;
        font-weight: 500;
      }
      
      .screenshot-section {
        margin-top: 25px;
      }
      
      .screenshot-section h4 {
        font-size: 1.1rem;
        margin-bottom: 15px;
        color: #495057;
      }
      
      .screenshot-container {
        background: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
      }
      
      .screenshot-container img {
        max-width: 100%;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        cursor: pointer;
        transition: transform 0.3s;
      }
      
      .screenshot-container img:hover {
        transform: scale(1.02);
      }
      
      .no-screenshot {
        padding: 40px;
        text-align: center;
        color: #6c757d;
        font-style: italic;
      }
      
      .footer {
        padding: 30px;
        text-align: center;
        background: #343a40;
        color: white;
      }
      
      .footer p {
        margin: 5px 0;
      }
      
      /* Modal for full-size screenshot */
      .modal {
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.9);
        align-items: center;
        justify-content: center;
      }
      
      .modal.open {
        display: flex;
      }
      
      .modal-content {
        max-width: 95%;
        max-height: 95%;
      }
      
      .close-modal {
        position: absolute;
        top: 20px;
        right: 35px;
        color: #f1f1f1;
        font-size: 40px;
        font-weight: bold;
        cursor: pointer;
      }
      
      .close-modal:hover {
        color: #bbb;
      }
      
      @media print {
        .filters, .toggle-icon { display: none; }
        .test-case-body { display: block !important; }
        body { background: white; padding: 0; }
        .container { box-shadow: none; }
      }
    `;
  }

  private static generateJS(): string {
    return `
      // Toggle test case details
      function toggleTestCase(testNumber) {
        const body = document.getElementById('test-body-' + testNumber);
        const icon = document.getElementById('icon-' + testNumber);
        
        body.classList.toggle('open');
        icon.classList.toggle('open');
      }
      
      // Filter tests
      let currentFilter = 'all';
      
      function filterTests(status) {
        currentFilter = status;
        const testCases = document.querySelectorAll('.test-case');
        
        // Update button states
        document.querySelectorAll('.filter-btn').forEach(btn => {
          btn.classList.remove('active');
        });
        document.getElementById('filter-' + status).classList.add('active');
        
        // Filter test cases
        testCases.forEach(testCase => {
          if (status === 'all') {
            testCase.style.display = 'block';
          } else {
            const testStatus = testCase.dataset.status.toLowerCase();
            testCase.style.display = testStatus === status ? 'block' : 'none';
          }
        });
      }
      
      // Modal for screenshots
      function openScreenshot(imgSrc) {
        const modal = document.getElementById('screenshot-modal');
        const modalImg = document.getElementById('modal-img');
        modal.classList.add('open');
        modalImg.src = imgSrc;
      }
      
      function closeModal() {
        document.getElementById('screenshot-modal').classList.remove('open');
      }
      
      // Close modal on click outside
      document.addEventListener('click', function(event) {
        const modal = document.getElementById('screenshot-modal');
        if (event.target === modal) {
          closeModal();
        }
      });
      
      // Keyboard shortcuts
      document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
          closeModal();
        }
      });
    `;
  }

  public static generate(
    testResults: TestResult[],
    summary: ReportSummary,
    outputPath: string,
  ): void {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fuzzy SKU Test Report - ${summary.timestamp}</title>
  <style>${this.generateCSS()}</style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <h1>🧪 Fuzzy SKU Search Test Report</h1>
      <p>Generated on ${summary.timestamp}</p>
    </div>
    
    <!-- Summary Cards -->
    <div class="summary">
      <div class="summary-card total">
        <h3>Total Tests</h3>
        <div class="value">${summary.totalTests}</div>
        <div class="subtitle">Test Cases</div>
      </div>
      
      <div class="summary-card pass">
        <h3>Passed</h3>
        <div class="value">${summary.passCount}</div>
        <div class="subtitle">${summary.passRate.toFixed(1)}%</div>
      </div>
      
      <div class="summary-card fail">
        <h3>Failed</h3>
        <div class="value">${summary.failCount}</div>
        <div class="subtitle">${(
          (summary.failCount / summary.totalTests) *
          100
        ).toFixed(1)}%</div>
      </div>
      
      <div class="summary-card rate">
        <h3>Success Threshold</h3>
        <div class="value">${summary.successThreshold}%</div>
        <div class="subtitle">Required</div>
      </div>
    </div>
    
    <!-- Suite Status -->
    <div class="suite-status ${
      summary.suiteStatus === 'PASSED' ? 'passed' : 'failed'
    }">
      ${summary.suiteStatus === 'PASSED' ? '✅' : '❌'} Test Suite ${
      summary.suiteStatus
    }
      ${
        summary.suiteStatus === 'PASSED'
          ? `(${summary.passRate.toFixed(1)}% >= ${summary.successThreshold}%)`
          : `(${summary.passRate.toFixed(1)}% < ${summary.successThreshold}%)`
      }
    </div>
    
    <!-- Filters -->
    <div class="filters">
      <label>Filter:</label>
      <button id="filter-all" class="filter-btn all active" onclick="filterTests('all')">
        All (${summary.totalTests})
      </button>
      <button id="filter-pass" class="filter-btn pass" onclick="filterTests('pass')">
        ✅ Pass (${summary.passCount})
      </button>
      <button id="filter-fail" class="filter-btn fail" onclick="filterTests('fail')">
        ❌ Fail (${summary.failCount})
      </button>
      ${
        summary.notRunCount > 0
          ? `
      <button id="filter-not_run" class="filter-btn" onclick="filterTests('not_run')">
        ⏭️ Not Run (${summary.notRunCount})
      </button>
      `
          : ''
      }
    </div>
    
    <!-- Test Cases -->
    <div class="test-cases">
      ${testResults.map((test) => this.generateTestCaseHTML(test)).join('')}
    </div>
    
    <!-- Footer -->
    <div class="footer">
      <p><strong>Fuzzy SKU POC - E2E Test Report</strong></p>
      <p>${summary.timestamp}</p>
    </div>
  </div>
  
  <!-- Screenshot Modal -->
  <div id="screenshot-modal" class="modal" onclick="closeModal()">
    <span class="close-modal">&times;</span>
    <img class="modal-content" id="modal-img" alt="Screenshot">
  </div>
  
  <script>${this.generateJS()}</script>
</body>
</html>
    `;

    fs.writeFileSync(outputPath, html, 'utf-8');
  }

  private static generateScreenshotsHTML(test: TestResult): string {
    if (!test.step_screenshots || test.step_screenshots.length === 0) {
      return `
          <div class="screenshot-section">
            <div class="no-screenshot">No screenshots available for this test case</div>
          </div>
      `;
    }

    const screenshotsHTML = test.step_screenshots
      .map((path, idx) => {
        // Extract step name from filename
        const filename = path.split('/').pop() || '';
        const stepMatch = filename.match(/step\d+_(.+)\.png$/);
        const stepName = stepMatch
          ? stepMatch[1].replace(/-/g, ' ').replace(/^\d+-/, '')
          : `Step ${idx + 1}`;
        const stepLabel = stepName.charAt(0).toUpperCase() + stepName.slice(1);

        return `
        <div class="screenshot-container">
          <p style="margin-bottom: 10px; color: #6c757d; font-weight: 600;">
            📍 Step ${String(idx + 1).padStart(2, '0')}: ${stepLabel}
          </p>
          <img 
            src="${path}" 
            alt="Test ${test.test_number} - ${stepLabel}"
            onclick="openScreenshot(this.src)"
            loading="lazy"
          />
        </div>
      `;
      })
      .join('');

    return `
          <div class="screenshot-section">
            <h4>📸 Step-by-Step Screenshots (${test.step_screenshots.length} steps)</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
              ${screenshotsHTML}
            </div>
          </div>
    `;
  }

  private static generateTestCaseHTML(test: TestResult): string {
    const statusClass = test.status.toLowerCase().replace('_', '-');
    const statusText =
      test.status === 'PASS'
        ? '✅ PASS'
        : test.status === 'FAIL'
        ? '❌ FAIL'
        : '⏭️ NOT RUN';

    return `
      <div class="test-case" data-status="${test.status}">
        <div class="test-case-header ${statusClass}" onclick="toggleTestCase(${
      test.test_number
    })">
          <div class="test-case-title">
            <h3>TC${String(test.test_number).padStart(
              3,
              '0',
            )}: ${this.escapeHtml(test.aitehinmei)}</h3>
            <p>Expected Hinban: ${test.hinban}</p>
          </div>
          <div class="test-case-status">
            <span class="status-badge ${statusClass}">${statusText}</span>
            ${
              test.found_count !== undefined
                ? `
              <span class="status-badge" style="background: #6c757d;">
                ${test.found_count}/${test.total_count} fields
              </span>
            `
                : ''
            }
            <span id="icon-${test.test_number}" class="toggle-icon">▶</span>
          </div>
        </div>
        
        <div id="test-body-${test.test_number}" class="test-case-body">
          <div class="test-details">
            <div class="detail-group">
              <h4>📝 Input Query</h4>
              <p>${this.escapeHtml(test.aitehinmei)}</p>
            </div>
            
            <div class="detail-group">
              <h4>🎯 Expected Hinban</h4>
              <p>${test.hinban}</p>
            </div>
            
            <div class="detail-group">
              <h4>📦 Expected SKU Name</h4>
              <p>${test.skname1}</p>
            </div>
            
            <div class="detail-group">
              <h4>🎨 Color Info</h4>
              <p>${test.colornm} (${test.colorcd})</p>
            </div>
            
            <div class="detail-group">
              <h4>📏 Size Info</h4>
              <p>${test.sizename} (${test.sizecd})</p>
            </div>
            
            <div class="detail-group">
              <h4>📊 Match Result</h4>
              <p>${test.found_count}/${test.total_count} fields found</p>
            </div>
            
            ${
              test.error_message
                ? `
            <div class="detail-group error">
              <h4>❌ Error Details</h4>
              <p>${this.escapeHtml(test.error_message)}</p>
            </div>
            `
                : ''
            }
          </div>
          
          ${this.generateScreenshotsHTML(test)}
        </div>
      </div>
    `;
  }

  private static escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }
}
