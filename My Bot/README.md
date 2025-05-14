# Telegram Voice Effects Bot

A Telegram bot that processes voice messages and applies various audio effects using FFmpeg. It also includes a voice cloning feature that allows users to clone their voice and use it for text-to-speech.

## Features

- Processes voice messages sent by users
- Applies 20+ different voice effects using FFmpeg
- Pagination system to browse through all available effects
- Handles error cases gracefully
- Allows users to apply multiple effects to the same audio file
- Voice cloning feature to record and clone user's voice
- Text-to-speech functionality with the cloned voice

## Requirements

- Python 3.7+
- python-telegram-bot (v20.0+)
- FFmpeg installed on the system

## Setup

1. Install required dependencies:
   ```bash
   pip install python-telegram-bot
   ```

2. Make sure FFmpeg is installed:
   ```bash
   # On Ubuntu/Debian
   apt-get install ffmpeg
   
   # On MacOS with Homebrew
   brew install ffmpeg
   
   # On Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. Set your Telegram Bot Token as an environment variable:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

## Available Voice Effects

The bot includes 20+ different voice effects including:

- Chipmunk: High-pitched voice
- Deep: Low-pitched voice
- Robot: Mechanical voice
- Echo: Adds echo effect
- Radio: Makes voice sound like it's coming through a radio
- SlowMo: Slows down the audio
- Fast: Speeds up the audio
- Reverse: Plays the audio backwards
- Alien: Spooky alien-like voice
- Cave: Adds cave-like echo
- Underwater: Makes voice sound like it's underwater
- Telephone: Old telephone effect
- And many more!

## How It Works

### Voice Effects
1. User sends a voice message to the bot
2. Bot downloads the voice message
3. Bot presents a menu of available effects
4. User selects an effect
5. Bot processes the audio with FFmpeg
6. Bot sends the processed audio back to the user

### Voice Cloning & Text-to-Speech
1. User sends the /clone command
2. Bot asks for a voice sample
3. User sends a short voice message
4. Bot stores the voice sample as the user's cloned voice
5. User can customize the voice name with /rename (e.g., /rename Cool Voice)
6. The cloned voice appears at the top of the effects menu with the custom name
7. When any voice message is sent to the bot, the user can select their cloned voice from the effects menu to transform the message using their voice characteristics
8. User can also use /say command followed by text
9. Bot converts the text to speech with the user's cloned voice

## License

This project is open-source and available under the MIT License.
