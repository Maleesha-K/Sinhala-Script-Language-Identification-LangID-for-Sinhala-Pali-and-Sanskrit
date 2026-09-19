import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  // Replace with the actual URL or relative path based on playwright.config.ts baseURL
  await page.goto('/');

  // Expect a title "to contain" a substring.
  // This will fail initially if the title isn't 'Create Next App' (default Next.js title)
  // Feel free to update the title assertion to match your app's title
  await expect(page).toHaveTitle(/Next/i);
});
