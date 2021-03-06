const fs = require('fs');
const puppeteer = require('puppeteer');
const fastify = require('fastify');
const cors = require('fastify-cors');

const configPath = __dirname + "/../" + process.argv.slice(2)[0]
const locationConfigPath = __dirname + "/../location.json"
const selectors = {
    mobileInput: 'input[appmobilenumber=true]',
    getOtp: 'ion-button',
    otpInput: '#mat-input-1',
    verifyOtpButton: 'ion-button',
};

function waitForSms() {
    return new Promise((resolve) => {
        const server = fastify();
        const config = require(configPath);

        server.register(cors, {
            origin: true,
        });

        server.post('/otp', async (request, response) => {
            const query = new URLSearchParams(request.query);

            if (query.has('otp')) {
                response.send();
                setTimeout(() => {
                    server.close();
                    resolve(query.get('otp'));
                });
            }
        });

        server.listen(config.port);
    });
}

function sleep(time) {
    return new Promise((resolve) => {
        setTimeout(resolve, time);
    });
}

(async () => {
    const config = require(configPath);
    const locationConfig = require(locationConfigPath);

    const browser = await puppeteer.launch({
        headless: false,
    });
    const page = await browser.newPage();
    await page.goto('https://selfregistration.cowin.gov.in/');
    await page.waitForSelector(selectors.mobileInput);
    await sleep(2000);
    await page.type(selectors.mobileInput, config.phone);
    await page.click(selectors.getOtp);
    const otp = await waitForSms();

    await page.type(selectors.otpInput, otp);

    page.on('response', async (interceptedResponse) => {
        const request = interceptedResponse.request();

        if (
            request.url().endsWith('/beneficiaries') &&
            request.method() === 'GET'
        ) {
            const headers = request.headers();
            config.auth = headers['authorization'];
            locationConfig.auth = headers['authorization'];
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
            fs.writeFileSync(locationConfigPath, JSON.stringify(locationConfig, null, 2));
            await browser.close();
        }
    });

    await Promise.all([
        page.waitForNavigation(),
        page.click(selectors.verifyOtpButton),
    ]);

    await sleep(5000);
})();
