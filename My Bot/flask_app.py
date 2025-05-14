from flask import Flask, render_template_string

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
                    <div class="feature-icon">🚀</div>
                    <h3>Easy to Use</h3>
                    <p>Just send a voice message to the bot and select from a menu of effects</p>
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)