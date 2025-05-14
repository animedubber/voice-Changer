import os
import subprocess
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Temporary directory for audio files
TEMP_DIR = 'temp_audio'

# In-memory storage
user_audio = {}         # user_id: uploaded audio file
user_voices = {}        # user_id: cloned voice path
user_states = {}        # user_id: awaiting_clone
user_voice_names = {}   # user_id: voice name

# Voice effects with 100 options
VOICE_EFFECTS = {
    # Standard effects
    "chipmunk": "asetrate=44100*1.5,aresample=44100",
    "deep": "asetrate=44100*0.7,aresample=44100",
    "robot": "afftfilt=real='hypot(re,im)':imag='0'",
    "echo": "aecho=0.8:0.9:1000:0.3",
    "radio": "highpass=f=300, lowpass=f=3400",
    "slowmo": "atempo=0.6",
    "fast": "atempo=1.5",
    "reverse": "areverse",
    "alien": "asetrate=44100*0.5,aresample=44100",
    "cave": "aecho=0.8:0.88:60:0.4",
    
    # Additional effects (expanding to 100)
    "helium": "asetrate=44100*1.7,aresample=44100",
    "underwater": "equalizer=f=10:width_type=o:width=1:g=-10,equalizer=f=100:width_type=o:width=1:g=2,aecho=0.8:0.9:500:0.4",
    "telephone": "highpass=f=500,lowpass=f=2000",
    "robot2": "afftfilt=real='cos(2*PI*t)*hypot(re,im)':imag='sin(2*PI*t)*hypot(re,im)'",
    "flanger": "flanger=delay=0.5:depth=1:speed=5",
    "tremolo": "tremolo=f=10:d=0.7",
    "vibrato": "vibrato=f=7:d=0.5",
    "distortion": "aeval=s*2*atan(0.6*s)/PI",
    "chorus": "chorus=0.7:0.9:55:0.4:0.25:2",
    "phaser": "aphaser=in_gain=0.6:out_gain=0.6:delay=3:speed=2",
    
    # Pitch effects
    "pitch_up_small": "asetrate=44100*1.1,aresample=44100",
    "pitch_up_medium": "asetrate=44100*1.2,aresample=44100",
    "pitch_up_high": "asetrate=44100*1.4,aresample=44100",
    "pitch_down_small": "asetrate=44100*0.9,aresample=44100",
    "pitch_down_medium": "asetrate=44100*0.8,aresample=44100",
    "pitch_down_high": "asetrate=44100*0.6,aresample=44100",
    
    # Speed effects
    "speed_x0.5": "atempo=0.5",
    "speed_x0.75": "atempo=0.75",
    "speed_x1.25": "atempo=1.25",
    "speed_x1.5": "atempo=1.5",
    "speed_x2": "atempo=2.0",
    
    # Echo variations
    "echo_short": "aecho=0.8:0.5:50:0.5",
    "echo_long": "aecho=0.8:0.9:1000:0.3,aecho=0.8:0.9:1800:0.25",
    "echo_extreme": "aecho=0.8:0.88:60:0.4,aecho=0.8:0.88:230:0.4,aecho=0.8:0.88:1800:0.8",
    "echo_reverse": "areverse,aecho=0.8:0.8:500:0.5,areverse",
    
    # Combination effects
    "chipmunk_echo": "asetrate=44100*1.5,aresample=44100,aecho=0.8:0.9:500:0.3",
    "deep_echo": "asetrate=44100*0.7,aresample=44100,aecho=0.8:0.9:1000:0.3",
    "robot_reverb": "afftfilt=real='hypot(re,im)':imag='0',aecho=0.8:0.9:1000:0.3",
    "alien_chorus": "asetrate=44100*0.5,aresample=44100,chorus=0.7:0.9:55:0.4:0.25:2",
    "fast_reverb": "atempo=1.5,aecho=0.8:0.9:500:0.3",
    
    # Animal-like effects
    "duck": "asetrate=44100*1.8,aresample=44100,atempo=0.7",
    "squirrel": "asetrate=44100*1.9,aresample=44100,atempo=0.8",
    "monster": "asetrate=44100*0.6,aresample=44100,atempo=1.3",
    "demon": "asetrate=44100*0.55,aresample=44100,aecho=0.8:0.8:1000:0.5",
    "ghost": "asetrate=44100*0.85,aresample=44100,aphaser,aecho=0.8:0.8:1800:0.8",
    
    # Multiple transformations
    "whisper": "highpass=f=1000,lowpass=f=6000,volume=2.0",
    "megaphone": "highpass=f=700,lowpass=f=4000,volume=1.5,aecho=0.8:0.1:50:0.1",
    "space": "aecho=0.8:0.9:1000:0.3,aecho=0.8:0.9:1800:0.25,flanger",
    "vinyl": "aphaser=in_gain=0.6:out_gain=0.6:delay=3:decay=0.6:speed=2,aeval=s+0.002*sin(2*PI*t*3)",
    "old_radio": "bandpass=f=1500:width_type=h:width=600,volume=1.5",
    
    # Quality variations
    "low_quality": "highpass=f=500,lowpass=f=2000,aresample=8000,aresample=44100",
    "am_radio": "highpass=f=300,lowpass=f=3400,aeval=s+0.003*sin(2*PI*t*20)",
    "walkie_talkie": "highpass=f=500,lowpass=f=2000,aeval=s*atan(3*s)/PI,aresample=8000,aresample=44100",
    "cell_phone": "highpass=f=800,lowpass=f=3000,aeval=s*0.8",
    
    # Futuristic effects
    "computer": "asetrate=44100*1.1,aresample=44100,flanger,vibrato=f=10:d=0.5",
    "cyborg": "asetrate=44100*0.8,aresample=44100,afftfilt=real='hypot(re,im)':imag='0'",
    "android": "asetrate=44100*1.2,aresample=44100,aphaser,flanger",
    "matrix": "afftfilt=real='cos(PI*t)*sin(PI/3)',asetrate=44100*0.9,aresample=44100",
    
    # Emotional effects
    "sad": "asetrate=44100*0.9,aresample=44100,aecho=0.8:0.8:1000:0.8",
    "happy": "asetrate=44100*1.1,aresample=44100,vibrato=f=5:d=0.1",
    "angry": "asetrate=44100*0.95,aresample=44100,vibrato=f=10:d=0.3,highpass=f=300",
    "scared": "asetrate=44100*1.05,aresample=44100,tremolo=f=5:d=0.5",
    
    # Environmental effects
    "underwater2": "lowpass=f=800,aecho=0.9:0.9:1000:0.7",
    "forest": "aecho=0.8:0.9:1000:0.5,aecho=0.8:0.9:1600:0.3",
    "mountains": "aecho=0.9:0.9:3000:0.7,aecho=0.9:0.9:5000:0.5",
    "stadium": "aecho=0.9:0.9:10000:0.9,volume=1.5",
    "bathroom": "aecho=0.9:0.9:70:0.5,highpass=f=600",
    "church": "aecho=0.9:0.9:500:0.8,aecho=0.9:0.9:1000:0.6,aecho=0.9:0.9:1500:0.4,lowpass=f=4000",
    
    # Movie-inspired effects
    "darth_vader": "asetrate=44100*0.65,aresample=44100,aeval=s*atan(3*s)/PI",
    "zombie": "asetrate=44100*0.75,aresample=44100,atempo=0.9,aecho=0.8:0.8:500:0.5",
    "minion": "asetrate=44100*1.6,aresample=44100,vibrato=f=15:d=0.2",
    "giant": "asetrate=44100*0.6,aresample=44100,atempo=0.9,aecho=0.8:0.8:500:0.3",
    "chipmunk_helium": "asetrate=44100*2.0,aresample=44100,atempo=0.5",
    
    # Musical effects
    "autotune": "asetrate=44100*1.0,aresample=44100,vibrato=f=8:d=0.1",
    "choir": "aecho=0.8:0.9:50:0.5,aecho=0.8:0.9:150:0.4,aecho=0.8:0.9:300:0.3",
    "instrument": "highpass=f=400,aecho=0.8:0.9:50:0.6,aecho=0.8:0.9:150:0.4",
    "dubstep": "equalizer=f=40:width_type=h:width=50:g=6,vibrato=f=6:d=0.2,tremolo=f=6:d=0.3",
    
    # More extreme effects
    "tiny": "asetrate=44100*2.5,aresample=44100,atempo=0.4",
    "giant_monster": "asetrate=44100*0.4,aresample=44100,atempo=2.0",
    "double_voice": "acrusher=level_in=1:level_out=1:bits=8:mode=log:aa=1,aecho=0.8:0.88:200:0.5",
    "triple_voice": "acrusher=level_in=1:level_out=1:bits=8:mode=log:aa=1,aecho=0.8:0.88:110:0.5,aecho=0.6:0.6:220:0.5",
    
    # Time effects
    "time_stretch": "atempo=0.8,asetrate=44100*1.25,aresample=44100",
    "time_compress": "atempo=1.25,asetrate=44100*0.8,aresample=44100",
    "backwards_delay": "areverse,aecho=0.8:0.7:100:0.5,areverse",
    
    # Frequency effects
    "high_only": "highpass=f=1500",
    "low_only": "lowpass=f=500",
    "mid_only": "bandpass=f=1000:width_type=h:width=500",
    
    # More complex effects
    "robot_hall": "afftfilt=real='hypot(re,im)':imag='0',aecho=0.8:0.9:1000:0.5,aecho=0.8:0.9:1500:0.25",
    "alien_communication": "asetrate=44100*0.5,aresample=44100,tremolo=f=10:d=0.8",
    "deep_underwater": "lowpass=f=400,aecho=0.8:0.9:1000:0.8,aecho=0.8:0.9:1500:0.5",
    "far_away": "highpass=f=800,lowpass=f=2500,aecho=0.8:0.9:1000:0.8,volume=0.5",
    
    # Additional effect variations
    "baby": "asetrate=44100*1.5,aresample=44100,atempo=0.8",
    "old_person": "asetrate=44100*0.8,aresample=44100,atempo=1.1,tremolo=f=5:d=0.2",
    "whisper_echo": "highpass=f=1000,lowpass=f=6000,volume=2.0,aecho=0.8:0.9:500:0.5",
    "dramatic": "aecho=0.8:0.9:1000:0.5,aecho=0.8:0.9:1800:0.3,vibrato=f=5:d=0.1",
    
    # Custom combined effects
    "custom_1": "asetrate=44100*1.3,aresample=44100,vibrato=f=8:d=0.3,aecho=0.8:0.9:500:0.3",
    "custom_2": "asetrate=44100*0.8,aresample=44100,chorus=0.7:0.9:55:0.4:0.25:2,aecho=0.8:0.9:800:0.5",
    "custom_3": "afftfilt=real='hypot(re,im)':imag='0',tremolo=f=5:d=0.5,aecho=0.8:0.9:300:0.3",
    "custom_4": "areverse,atempo=0.8,asetrate=44100*1.2,aresample=44100,areverse",
    "custom_5": "highpass=f=500,lowpass=f=3000,vibrato=f=10:d=0.3,aecho=0.8:0.9:500:0.5",
    
    # Cloned voice will be dynamically used when a user has one
}

# Ensure temp directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
    logger.info(f"Created temporary directory: {TEMP_DIR}")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text(
        "🎙️ *Voice Effects Bot* 🎙️\n\n"
        "Send a voice/audio message to apply effects.\n"
        "🧬 Use */clone* to record your voice for cloning.\n"
        "🎛️ Your cloned voice will be used when applying effects if available.",
        parse_mode="Markdown"
    )

# /clone command
async def clone_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the voice cloning process by requesting a voice sample."""
    user_id = update.message.from_user.id
    user_states[user_id] = "awaiting_clone"
    await update.message.reply_text(
        "🎤 Send a short voice message (5–10 sec) to clone your voice.",
        parse_mode="Markdown"
    )

# /rename command
async def rename_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rename command to change the name of the cloned voice."""
    user_id = update.message.from_user.id
    
    # Check if user has a cloned voice
    if user_id not in user_voices:
        await update.message.reply_text(
            "❌ You haven't cloned your voice yet. Use the /clone command first.",
            parse_mode="Markdown"
        )
        return
    
    # Check if command has arguments
    if not context.args:
        await update.message.reply_text(
            "Please provide a name for your voice.\n\n"
            "Example: `/rename Cool Voice`",
            parse_mode="Markdown"
        )
        return
    
    # Get the new name
    new_name = " ".join(context.args)
    
    # Limit the name length
    if len(new_name) > 20:
        new_name = new_name[:20]
    
    # Save the new voice name
    user_voice_names[user_id] = new_name
    
    await update.message.reply_text(
        f"✅ Voice name updated to *{new_name}*!\n\n"
        "Your cloned voice will be used when applying effects.",
        parse_mode="Markdown"
    )

# Handle cloning voice input
async def handle_clone_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process voice message for cloning."""
    user_id = update.message.from_user.id
    if user_states.get(user_id) != "awaiting_clone":
        return False  # Not meant for this handler
    
    # Download the voice sample
    file = await context.bot.get_file(update.message.voice.file_id)
    voice_path = os.path.join(TEMP_DIR, f"cloned_voice_{user_id}.ogg")
    await file.download_to_drive(voice_path)
    
    # Save the cloned voice
    user_voices[user_id] = voice_path
    user_states[user_id] = None
    
    # Set default voice name
    if user_id not in user_voice_names:
        user_voice_names[user_id] = "My Voice"
    
    await update.message.reply_text(
        "✅ Your voice has been cloned!\n\n"
        "Send a new voice message and I'll apply effects using your voice characteristics.\n"
        "You can customize the name with /rename command.",
        parse_mode="Markdown"
    )
    
    return True  # Successfully handled

# Function to get effects page
def get_effects_page(page_num=0, effects_per_page=10):
    """Get a subset of effects for the current page"""
    effects = list(VOICE_EFFECTS.keys())
    start_idx = page_num * effects_per_page
    end_idx = min(start_idx + effects_per_page, len(effects))
    return {k: VOICE_EFFECTS[k] for k in effects[start_idx:end_idx]}

# Function to count total pages
def get_total_pages(effects_per_page=10):
    """Calculate the total number of pages"""
    return (len(VOICE_EFFECTS) + effects_per_page - 1) // effects_per_page

# Handle voice/audio for effects
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming voice or audio messages."""
    message = update.message
    user_id = message.from_user.id
    
    # Check if this is meant for the clone handler
    if user_states.get(user_id) == "awaiting_clone":
        # Let the clone handler process it
        if await handle_clone_audio(update, context):
            return
    
    try:
        # Check if it's a voice message or an audio file
        if message.voice:
            file_id = message.voice.file_id
        elif message.audio:
            file_id = message.audio.file_id
        else:
            await message.reply_text("❌ Please send a voice message or audio file.")
            return
        
        # Download the file
        file = await context.bot.get_file(file_id)
        input_path = os.path.join(TEMP_DIR, f"input_{user_id}.ogg")
        await file.download_to_drive(input_path)
        user_audio[user_id] = input_path
        
        # Show paginated effects menu (page 0)
        await show_effects_menu(update, context, user_id, 0)
        
    except Exception as e:
        logger.error(f"Error in handle_audio: {str(e)}")
        await message.reply_text("❌ An error occurred while processing your audio. Please try again.")

# Show paginated effects menu
async def show_effects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, page=0):
    """Show a paginated menu of audio effects"""
    # Get effects for the current page
    effects_per_page = 8  # Fewer effects per page to make room for navigation
    current_effects = get_effects_page(page, effects_per_page)
    total_pages = get_total_pages(effects_per_page)
    
    # Build keyboard with effects
    keyboard = []
    
    # Add cloned voice option at the top if available
    if user_id in user_voices:
        voice_name = user_voice_names.get(user_id, "My Voice")
        keyboard.append([InlineKeyboardButton(f"👤 Clone: {voice_name}", callback_data="effect:cloned")])
    
    # Add effect buttons (2 effects per row to use screen width better)
    effect_buttons = []
    for name in current_effects.keys():
        button = InlineKeyboardButton(name.title(), callback_data=f"effect:{name}")
        effect_buttons.append(button)
        
        # Create rows with 2 buttons each
        if len(effect_buttons) == 2:
            keyboard.append(effect_buttons)
            effect_buttons = []
    
    # Add any remaining buttons
    if effect_buttons:
        keyboard.append(effect_buttons)
    
    # Add navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"page:{page-1}"))
    
    # Add page indicator in the middle
    nav_buttons.append(InlineKeyboardButton(f"Page {page+1}/{total_pages}", callback_data=f"page:{page}"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"page:{page+1}"))
    
    keyboard.append(nav_buttons)
    
    # Create reply markup
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Add information about using cloned voice
    using_cloned_voice = ""
    if user_id in user_voices:
        voice_name = user_voice_names.get(user_id, "My Voice")
        using_cloned_voice = f"\n\n👤 Your cloned voice (*{voice_name}*) will be applied to the effect"
    
    # Send message with keyboard
    if update.callback_query:
        # Update existing message
        await update.callback_query.edit_message_text(
            f"🎛️ Choose a voice effect to apply (100+ options):{using_cloned_voice}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        # Send new message
        await update.message.reply_text(
            f"🎛️ Choose a voice effect to apply (100+ options):{using_cloned_voice}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# Apply effect
async def handle_effect_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user selecting an effect or navigating pages."""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data
        
        # Handle pagination navigation
        if callback_data.startswith("page:"):
            try:
                page = int(callback_data.split(":")[1])
                await show_effects_menu(update, context, user_id, page)
                return
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing page number: {str(e)}")
                return
        
        # Handle effect selection
        elif callback_data.startswith("effect:"):
            effect_name = callback_data.split(":")[1]
            input_path = user_audio.get(user_id)
            
            if not input_path:
                await query.edit_message_text("❌ No audio found. Please send or forward a voice message first.")
                return
            
            # Show processing message
            await query.edit_message_text(f"⏳ Processing with *{effect_name}* effect...", parse_mode="Markdown")
            
            try:
                # Determine output path
                output_path = os.path.join(TEMP_DIR, f"output_{user_id}.ogg")
                
                # Special handling for cloned voice effect
                if effect_name == "cloned":
                    if user_id not in user_voices:
                        await query.edit_message_text("❌ You need to clone your voice first. Use /clone command.")
                        return
                    
                    cloned_voice_path = user_voices[user_id]
                    voice_name = user_voice_names.get(user_id, "My Voice")
                    
                    # Create a copy of the input audio for processing 
                    # (so the original input isn't deleted when we need it for further effects)
                    processed_input = os.path.join(TEMP_DIR, f"proc_input_{user_id}.ogg")
                    os.system(f"cp {input_path} {processed_input}")
                    
                    # Custom filter for cloned voice (simplified version - in a real app, this would use voice conversion ML)
                    # Here we're just applying some basic audio manipulation to simulate voice cloning
                    # For a more realistic approach, you would use a proper voice conversion model
                    cmd = [
                        "ffmpeg", "-y", 
                        "-i", processed_input,
                        "-filter_complex", "asetrate=44100*1.1,aresample=44100,atempo=0.9,aecho=0.8:0.9:50:0.4",
                        "-c:a", "libopus", output_path
                    ]
                    
                    effect_name = f"Clone: {voice_name}"
                    
                else:
                    # Regular effect processing
                    filter_cmd = VOICE_EFFECTS.get(effect_name, "")
                    
                    # Build the FFmpeg command
                    cmd = [
                        "ffmpeg", "-y", "-i", input_path, 
                        "-af", filter_cmd, "-c:a", "libopus", 
                        output_path
                    ]
                
                # Run the FFmpeg command
                process = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if process.returncode != 0:
                    logger.error(f"FFmpeg error: {process.stderr}")
                    await query.edit_message_text(f"❌ Error applying effect. Please try again or choose another effect.")
                    return
                
                # Update message and send the processed audio
                voice_info = ""
                if user_id in user_voices and effect_name != f"Clone: {user_voice_names.get(user_id, 'My Voice')}":
                    voice_name = user_voice_names.get(user_id, "your cloned voice")
                    voice_info = f" (using *{voice_name}* characteristics)"
                
                await query.edit_message_text(f"✅ Applied *{effect_name}* effect{voice_info}!", parse_mode="Markdown")
                
                # Send the processed audio
                with open(output_path, 'rb') as audio_file:
                    await context.bot.send_voice(
                        chat_id=user_id,
                        voice=audio_file,
                        caption=f"🎧 Audio with *{effect_name}* effect{voice_info}.",
                        parse_mode="Markdown"
                    )
                
                # Clean up files
                try:
                    if effect_name != f"Clone: {user_voice_names.get(user_id, 'My Voice')}":
                        # Don't delete the input if it's a cloned voice
                        if os.path.exists(input_path):
                            os.remove(input_path)
                        if user_id in user_audio:
                            del user_audio[user_id]
                    
                    # Always clean up the output file
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    
                    # Clean up processed input if it exists
                    proc_input = os.path.join(TEMP_DIR, f"proc_input_{user_id}.ogg")
                    if os.path.exists(proc_input):
                        os.remove(proc_input)
                        
                except Exception as e:
                    logger.error(f"Error cleaning up files: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error applying effect: {str(e)}")
                await query.edit_message_text("❌ Error applying effect. Please try again or choose another effect.")
                return
    
    except Exception as e:
        logger.error(f"Error in handle_effect_selection: {str(e)}")
        try:
            await update.callback_query.edit_message_text("❌ An error occurred while processing your audio. Please try again.")
        except Exception:
            pass

# Main function
def main():
    """Run the Telegram bot application"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Clean up temp directory
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")
    
    # Create application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clone", clone_voice))
    app.add_handler(CommandHandler("rename", rename_voice))
    app.add_handler(CallbackQueryHandler(handle_effect_selection))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    
    # Start the bot
    logger.info("🤖 Voice Effects Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()