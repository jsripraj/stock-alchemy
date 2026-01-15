const {By, Builder, Browser} = require('selenium-webdriver');
const assert = require("assert");

describe('End-to-end tests', async function e2eTests() {
    let driver;

    before(async function() {
        driver = await new Builder().forBrowser(Browser.CHROME).build();
        await driver.manage().setTimeouts({ implicit: 5000 });
    });

    it("[Market Cap] > 0", async function() {
        await driver.get('http://localhost:3000/');

        const editor = await driver.findElement(By.id('formula-editor'));
        await editor.clear();
        const formula = "[Market Cap] > 0";
        await editor.sendKeys(formula);

        await driver.findElement(By.id('find-stocks-btn')).click();

        const label = await driver.findElement(By.id('results-label')).getText();
        assert.equal(label, 'Results (65)');
    })

    after(async () => await driver.quit());
});