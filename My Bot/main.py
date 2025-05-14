import os
import logging
import threading
from flask import Flask, render_template_string

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create Flask app for the web interface
app = Flask(__name__)

@app.route('/')
def home():
    """Render a simple homepage with information about the bot."""
    html = """
    <!DOCTYPE html>
    <html data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Voice Effects Bot</title>
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        <style>
            .container {
                max-width: 800px;
                margin-top: 3rem;
            }
            .features {
                margin-top: 2rem;
            }
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row">
                <div class="col-12 text-center">
                    <h1 class="display-4">🎙️ Telegram Voice Effects Bot</h1>
                    <p class="lead">A bot that processes voice messages and applies various audio effects using FFmpeg</p>
                </div>
            </div>
            
            <div class="row features">
                <div class="col-md-4 text-center">
                    <div class="feature-icon">🔊</div>
                    <h3>20+ Voice Effects</h3>
                    <p>Apply various effects like chipmunk, robot, echo, and more to your voice messages</p>
                </div>
                <div class="col-md-4 text-center">
                    <div class="feature-icon">🧬</div>
                    <h3>Voice Cloning</h3>
                    <p>Clone your voice and use it when applying effects to any incoming voice messages</p>
                </div>
                <div class="col-md-4 text-center">
                    <div class="feature-icon">🎛️</div>
                    <h3>Powered by FFmpeg</h3>
                    <p>Professional audio processing capabilities using FFmpeg technology</p>
                </div>
            </div>
            
            <div class="row mt-5">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h2 class="card-title">How to Use the Bot</h2>
                            <ol>
                                <li>Find the bot on Telegram by searching for it</li>
                                <li>Start a conversation with the bot by sending the /start command</li>
                                <li>Use /clone to record and clone your voice (optional)</li>
                                <li>Send or forward a voice message to the bot</li>
                                <li>Select an effect from the menu that appears</li>
                                <li>Receive your processed voice message with the applied effect</li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12 text-center">
                    <p class="alert alert-success">
                        <strong>Status:</strong> The bot is currently running in the background. Visit Telegram to interact with it!
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

def run_flask():
    """Run the Flask web application."""
    try:
        app.run(host='0.0.0.0', port=5000)
    except OSError as e:
        logger.warning(f"Could not start Flask server: {e}")
        logger.info("Web interface is already running in another process")

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Import and run the bot in the main thread
    from simple_bot import main
    main()
