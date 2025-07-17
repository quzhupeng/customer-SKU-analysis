const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000'); // Adjust the URL if needed

  // Set different viewports to test responsiveness
  const viewports = [
    { width: 1920, height: 1080 }, // Desktop
    { width: 768, height: 1024 },  // Tablet
    { width: 375, height: 667 },  // Mobile
  ];

  for (const viewport of viewports) {
    await page.setViewport(viewport);

    // Test for no text or number overlap
    const cards = await page.$$('.strategy-card');
    for (const card of cards) {
      const text = await card.evaluate(node => node.innerText);
      if (text.includes('...')) {
        console.error('Text overlap found in card:', text);
      }
    }

    // Test KPI section 2:1 ratio
    const kpiPrimaryValue = await page.$eval('.kpi-card.primary-value .kpi-number', el => el.innerText);
    const kpiContribution = await page.$eval('.kpi-card.secondary-percentage .kpi-number', el => el.innerText);
    console.assert(parseFloat(kpiPrimaryValue) / parseFloat(kpiContribution) === 2, 'KPI section is not in 2:1 ratio');

    // Test metrics section 1:1 ratio
    const projectStats = await page.$eval('.metric-card.stats-card .metric-value', el => el.innerText);
    const boundaryPosition = await page.$eval('.metric-card.boundary-card .metric-value', el => el.innerText);
    console.assert(parseFloat(projectStats) === parseFloat(boundaryPosition), 'Metrics section is not in 1:1 ratio');

    // Check clean visual hierarchy
    const hierarchyCheck = await page.evaluate(() => {
      // Implement a heuristic check for visual hierarchy
      const headers = document.querySelectorAll('.header-title');
      return Array.from(headers).every(h => window.getComputedStyle(h).fontSize === '14px');
    });
    console.assert(hierarchyCheck, 'Visual hierarchy is not clean');
  }

  await browser.close();
})();

