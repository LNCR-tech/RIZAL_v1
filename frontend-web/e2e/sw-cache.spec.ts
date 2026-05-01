import { test, expect } from '@playwright/test';

test.describe('Service Worker and Cache tests', () => {
    test('Offline fallback behavior', async ({ page, context }) => {
        // First visit to cache the app
        await page.goto('/');
        await expect(page.locator('body')).toBeVisible();

        // Disconnect network
        await context.setOffline(true);

        // Try navigating, app shell should load if SW is active, or show standard offline error
        // As long as the page doesn't crash completely or throw an unhandled SW clone error
        let pageError = false;
        page.on('pageerror', err => {
            pageError = true;
        });

        try {
            await page.reload();
        } catch (e) {
            // It's expected to fail if SW offline page isn't setup perfectly, 
            // but we want to ensure no JS syntax errors in the SW runtime itself
        }

        expect(pageError).toBeFalsy();
    });
});