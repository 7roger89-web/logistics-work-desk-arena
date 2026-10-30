// Isolated trial only: no repo dependency added.
module.exports = {
  testDir: './specs',
  timeout: 90000,
  retries: 0,
  workers: 1,
  reporter: [['json', { outputFile: 'result.json' }], ['line']],
  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:9502',
    headless: true,
    launchOptions: { executablePath: '/tmp/chromium', args: ['--no-sandbox'] },
    viewport: { width: 1440, height: 900 },
    trace: 'on',
    screenshot: 'only-on-failure',
  },
};
