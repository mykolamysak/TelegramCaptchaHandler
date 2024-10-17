# Telegram Bot Captcha Handler

This Python script uses the Telethon library to connect to Telegram and handle various types of captcha challenges presented by bots in a specified chat. The script also saves information about these bots and their associated captcha types into an SQLite database.

## Features

- **Telegram Client**: Connects to Telegram using user session credentials stored in a configuration file (`config.ini`).
- **Database Integration**: Uses SQLite to store information about captcha messages, including:
  - Chat ID
  - Chat Name
  - Bot ID
  - Bot Username
  - Captcha Type
- **Captcha Handling**: Listens for new messages in the specified chat and handles different types of captchas based on the content of the messages or the buttons available.
- **Dynamic Bot Identification**: The bot recognizes messages from other bots and processes captchas based on their characteristics.

## Captcha Types Handled

The script supports the following captcha types:

1. **Text Captcha**:
   - Triggered by messages containing requests for the user to send any message (e.g., "send any message").
   - The bot responds with a predefined message to pass the captcha.
   - Example check: `if "send any message" in event.message.message.lower():`

2. **Math Captcha**:
   - Recognizes captchas that require solving a mathematical expression within parentheses in the message.
   - The solution is calculated and sent back as a response.
   - Example extraction: `match = re.search(r'\((.*?)\)', event.message.message)`

3. **Button Captcha**:
   - Engaged when buttons are present in the message.
   - If there is only one button without a URL, it automatically clicks the button to pass the captcha.
   - It also checks for specific keywords in button texts and clicks the relevant button if keywords are found.
   - Example check for button text: `if not button.url and any(keyword in button_text for keyword in KEYWORDS):`

4. **Button Link Captcha**:
   - Activated when buttons are present with URLs.
   - Opens the URL in a web browser and sends a `/start` command to the bot linked to the URL after a short delay.
   - Example action: `webbrowser.open(button.url)`
