const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    const logs = [];
    page.on('console', msg => logs.push(`[${msg.type()}] ${msg.text()}`));
    page.on('pageerror', error => logs.push(`[pageerror] ${error.message}\n${error.stack}`));

    console.log("Navigating to http://localhost:5174 to set localStorage...");
    await page.goto('http://localhost:5174', { waitUntil: 'domcontentloaded' });

    await page.evaluate(() => {
        localStorage.setItem('auth_token', 'fake_token_for_test');
        localStorage.setItem('current_user', JSON.stringify({
            id: "23-A-01617",
            name: "Lady Joy Borja",
            email: "joyborjacom6@gmail.com",
            role: "student",
            college: "College of Engineering",
            faceScanRegistered: false
        }));
    });

    console.log("Navigating to dashboard...");
    await page.goto('http://localhost:5174/#/student/dashboard', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const html = await page.content();
    fs.writeFileSync('browser_errors.log', 'LOGS:\n' + logs.join('\n') + '\n\nHTML:\n' + html);
    console.log("Dumped browser console logs to browser_errors.log");

    await browser.close();
})();
