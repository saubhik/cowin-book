# cowin-book

Automated booking of COWIN vaccination slots for multiple beneficiaries. This work is
based on work of 
1. https://github.com/sudeepg95/cowin-public
2. https://github.com/bhattbhavesh91/cowin-vaccination-slot-availability

This is tested in MacOS. Can run on Linux with minimal changes.

### Steps

- Use Google Messages as default SMS app.
- Open https://messages.google.com/web/conversations/<SOME-NUMBER> in Google Chrome.
  (Replace <SOME-NUMBER> with your OTP sender's conversation number.)
- Use https://www.tampermonkey.net/ extension in Google Chrome and setup
  `tampermonkey.js` (in this repository) to work on the above conversation.
  (You need to change just the `@match` field in this file to match the right
  conversation)
- Setup `config.json` with the correct field values. You don't need to care about `auth`
  field. It gets updated automatically.
- Make sure you have VLC installed. Life is better with it, anyways.
- Run the following in project root directory:
  ```bash
  python3.9 -m venv ./venv
  source venv/bin/activate
  pip install -r requirements.txt
  npm install # For node server (updates tokens every 15 minutes)
  python src/book.py --filename config1.json
  python src/book.py --filename config2.json
  ```
  Each config is associated with a single mobile number. Each mobile number can
  accommodate at most 4 beneficiaries.
