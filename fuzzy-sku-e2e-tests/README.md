# 🎯 Fuzzy SKU Search - E2E Tests với Playwright

Test tự động cho tính năng tìm kiếm sản phẩm tại https://fuzzy-sku-poc.welfan-welink.biz

---

## 🚀 QUICK START

### 1️⃣ Cập nhật Credentials (BẮT BUỘC!)

```bash
# Mở file .env
nano .env
```

Thay đổi:

```env
TEST_USERNAME=your_actual_username_here
TEST_PASSWORD=your_actual_password_here
```

### 2️⃣ Chạy Tests

```bash
# Chạy tất cả tests với UI mode (RECOMMENDED)
pnpm run test:ui

# Hoặc chạy headless (nền, không hiển thị browser)
pnpm test

# Hoặc chạy với browser visible
pnpm run test:headed
```

### 3️⃣ Xem Kết Quả

```bash
# Xem HTML report
pnpm run test:report
```

---

## 📊 Test Data

Tests sử dụng data từ file **`fuzzy-sku-jpoc-testcases.csv`**:

| Column       | Purpose                            |
| ------------ | ---------------------------------- |
| `aitehinmei` | **INPUT** - Search query           |
| `hinban`     | **OUTPUT** - Expected product code |
| `skname1`    | **OUTPUT** - Expected SKU name     |
| `colorcd`    | **OUTPUT** - Expected color code   |
| `colornm`    | **OUTPUT** - Expected color name   |
| `sizecd`     | **OUTPUT** - Expected size code    |
| `sizename`   | **OUTPUT** - Expected size name    |

**Mỗi dòng trong CSV = 1 test case tự động!**

---

## ✅ Test Logic

Với mỗi test case, Playwright sẽ:

1. ✅ **Login** tự động (sử dụng credentials từ `.env`)
2. ✅ **Navigate** đến `/search`
3. ✅ **Input** `aitehinmei` vào search box
4. ✅ **Click** button "🔍 Search"
5. ✅ **Wait** cho results load
6. ✅ **Verify** results table chứa:
   - Hinban (Product Code) - **Critical**
   - SKU Name - **Critical**
   - Color Code & Name
   - Size Code & Name
7. ✅ **Log** chi tiết kết quả (pass/fail cho từng field)
8. ✅ **Assert** ít nhất 1 critical field được tìm thấy

---

## 📁 Project Structure

```
fuzzy-sku-e2e-tests/
├── .env                              ← ⚠️ CẬP NHẬT CREDENTIALS TẠI ĐÂY
├── .env.example
├── playwright.config.ts              ← Cấu hình Playwright
├── package.json
├── fuzzy-sku-jpoc-testcases.csv     ← Test data (symlink)
├── tests/
│   ├── fuzzy-sku-search.spec.ts     ← 🎯 MAIN TEST FILE
│   └── helpers/
│       └── auth.helper.ts            ← Login helper
├── test-results/                     ← Test artifacts (screenshots, videos)
└── playwright-report/                ← HTML report
```

---

## 💻 Available Commands

| Command                | Description                               |
| ---------------------- | ----------------------------------------- |
| `pnpm test`            | Chạy tất cả tests (headless)              |
| `pnpm run test:headed` | Chạy tests với browser visible            |
| `pnpm run test:ui`     | Chạy với Playwright UI mode (interactive) |
| `pnpm run test:debug`  | Debug mode (từng bước)                    |
| `pnpm run test:report` | Xem HTML report                           |
| `pnpm run codegen`     | Record tests tự động                      |

---

## 🎨 Test Output Example

```
🔍 Test Case 1/500
   📝 Input (aitehinmei): "211282/快歩主義M035/ブラック/25.5//"
   🎯 Expected Results:
      - Hinban: 211282
      - SKU Name: 快歩主義M035
      - Color: ﾌﾞﾗｯｸｽﾑｰｽ (784)
      - Size: 25.5 (255)
   ⌨️  Entered search query: "211282/快歩主義M035/ブラック/25.5//"
   🔎 Clicked search button
   ✅ Results table is visible
   ✅ Hinban: 211282
   ✅ SKU Name: 快歩主義M035
   ✅ Color Code: 784
   ✅ Color Name: ﾌﾞﾗｯｸｽﾑｰｽ
   ✅ Size Code: 255
   ✅ Size Name: 25.5

   📊 Results: 6/6 fields found (100.0%)
   ✅ Test passed!
```

---

## 🐛 Troubleshooting

### ❌ "TEST_USERNAME must be set"

**Fix:** Cập nhật `.env` file với credentials thật

### ❌ "Login failed"

**Fix:**

- Check username/password trong `.env`
- Thử login thủ công vào website
- Verify website accessible

### ❌ "CSV file not found"

**Fix:**

```bash
ln -sf ../fuzzy-sku-jpoc-testcases.csv .
```

### ❌ "No results found"

**Possible reasons:**

- Search query không match với dữ liệu trong database
- API có vấn đề
- Network timeout

**Debug:**

```bash
pnpm run test:debug
```

### ❌ Tests timeout

**Fix:**

- Tăng timeout trong `playwright.config.ts`
- Check internet connection
- Verify API endpoint hoạt động

---

## 🔧 Configuration

### Thay đổi timeouts

Edit `playwright.config.ts`:

```typescript
export default defineConfig({
  timeout: 120000, // Test timeout (default: 60s)
  use: {
    actionTimeout: 30000, // Action timeout (default: 15s)
    navigationTimeout: 60000, // Navigation timeout (default: 30s)
  },
});
```

### Thay đổi số workers

```typescript
export default defineConfig({
  workers: 1, // Run tests sequentially (prevent rate limiting)
});
```

### Thêm browsers khác

```typescript
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },  // Uncomment to test on Firefox
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },    // Uncomment to test on Safari
],
```

---

## 📈 Expected Results

Với **~500 test cases** từ CSV:

- ⏱️ Mỗi test: **~3-5 giây**
- ⏱️ Total time: **~25-40 phút**
- 📊 HTML report with:
  - ✅ Pass/Fail counts
  - 📸 Screenshots (on failure)
  - 🎬 Videos (on failure)
  - 📝 Detailed logs
  - 📊 Success rate

---

## 🎯 Test Validation Strategy

**Mỗi test sẽ PASS nếu:**

- ✅ Tìm thấy ít nhất **Hinban** HOẶC **SKU Name** trong results

**Mỗi test sẽ FAIL nếu:**

- ❌ Không tìm thấy bất kỳ expected field nào
- ❌ API trả về error
- ❌ Timeout
- ❌ Login failed

---

## 💡 Tips & Tricks

### Chạy 1 test case cụ thể:

```bash
# Chạy test case đầu tiên
pnpm exec playwright test --grep "TC001"

# Chạy test cases từ TC001 đến TC010
pnpm exec playwright test --grep "TC00[1-9]|TC010"
```

### Debug 1 test case:

```bash
pnpm exec playwright test --grep "TC001" --debug
```

### Chạy tests slow motion:

```bash
pnpm exec playwright test --headed --slow-mo=1000
```

### Xem trace của test failed:

```bash
pnpm exec playwright show-trace test-results/.../trace.zip
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        run: |
          cd fuzzy-sku-e2e-tests
          pnpm install

      - name: Install Playwright browsers
        run: |
          cd fuzzy-sku-e2e-tests
          pnpm exec playwright install --with-deps chromium

      - name: Run tests
        env:
          TEST_USERNAME: ${{ secrets.TEST_USERNAME }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: |
          cd fuzzy-sku-e2e-tests
          pnpm test

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: fuzzy-sku-e2e-tests/playwright-report/
```

---

## 📚 Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Test API](https://playwright.dev/docs/api/class-test)
- [Selectors Guide](https://playwright.dev/docs/selectors)
- [Test Assertions](https://playwright.dev/docs/test-assertions)

---

## ✨ Thêm Test Cases Mới

**Cực kỳ đơn giản:**

1. Mở file `fuzzy-sku-jpoc-testcases.csv`
2. Thêm dòng mới với data
3. Chạy lại tests → Test mới tự động được thêm vào! 🎉

**Không cần code gì thêm!**

---

## 🎉 Success Checklist

- [x] ✅ Setup Playwright
- [x] ✅ Tạo test suite tự động từ CSV
- [x] ✅ Login helper
- [x] ✅ Search logic matching frontend
- [x] ✅ Validation cho tất cả expected outputs
- [x] ✅ Chi tiết logging
- [x] ✅ Screenshots/videos on failure
- [x] ✅ HTML reporting
- [x] ✅ Documentation đầy đủ

---

**Happy Testing! 🚀**

Nếu có vấn đề, check lại:

1. `.env` file có credentials đúng?
2. Website accessible?
3. CSV file exists?
4. Internet stable?
