import { test, expect } from '@playwright/test';

// Use deterministic CI seed users
const USERS = {
    campus_admin: { email: 'campus_admin@test.com', password: 'TestPass123!' },
    student: { email: 'student@test.com', password: 'TestPass123!' },
    ssg: { email: 'ssg@test.com', password: 'TestPass123!' }
};

test.describe('RBAC Frontend Tests', () => {
    
    // Fail test if console errors are encountered
    test.beforeEach(({ page }) => {
        page.on('pageerror', err => {
            expect(err.message).not.toContain('Failed to load resource');
            expect(err.message).not.toContain('404');
        });
    });

    test('Student login sees correct dashboard and restricted menus are hidden', async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[type="email"]', USERS.student.email);
        await page.fill('input[type="password"]', USERS.student.password);
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL(/\/dashboard|\/student/);
        
        // Assert student dashboard visible
        await expect(page.locator('text=My Events')).toBeVisible();
        
        // Assert Admin elements are HIDDEN
        await expect(page.locator('text=School Settings')).not.toBeVisible();
        await expect(page.locator('text=User Management')).not.toBeVisible();
    });

    test('Campus Admin login sees admin dashboard and restricted routes', async ({ page }) => {
        await page.goto('/login');
        await page.fill('input[type="email"]', USERS.campus_admin.email);
        await page.fill('input[type="password"]', USERS.campus_admin.password);
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL(/\/dashboard|\/admin/);
        
        // Assert admin dashboard visible
        await expect(page.locator('text=User Management')).toBeVisible();
    });
    
    test('Direct URL Privilege Escalation Blocked', async ({ page }) => {
        // Login as student
        await page.goto('/login');
        await page.fill('input[type="email"]', USERS.student.email);
        await page.fill('input[type="password"]', USERS.student.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL(/\/dashboard|\/student/);
        
        // Try to access admin users page
        await page.goto('/admin/users');
        
        // Should redirect back to dashboard or show 403 Unauhtorized
        await expect(page).not.toHaveURL(/\/admin\/users/);
    });
});