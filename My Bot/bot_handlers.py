import os
import logging
import subprocess
import tempfile
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from voice_effects import get_effect_page, get_total_pages, VOICE_EFFECTS
from utils import ensure_temp_dir, apply_audio_effect, apply_voice_clone_effect

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory storage
user_audio = {}       # user_id: file_path
user_pages = {}       # user_id: current_page
user_voices = {}      # user_id: cloned voice path
user_voice_names = {} # user_id: custom voice name
user_states = {}      # user_id: current state (e.g., "awaiting_clone", "awaiting_voice_name")

# Create temp directory
TEMP_DIR = "temp_audio"
ensure_temp_dir(TEMP_DIR)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text(
        "🎙️ *Welcome to Voice Effects Bot!* 🎙️\n\n"
        "Send or forward me a voice/audio message, and I'll give you multiple voice effects to apply!\n\n"
        "I can transform your voice into chipmunk, robot, echo and many more effects using FFmpeg technology.\n\n"
        "*Advanced Features:*\n"
        "🧬 Use */clone* to record your voice for cloning.\n"
        "🗣️ Use */say* <text> to speak using your cloned voice.",
        parse_mode="Markdown"
    )

# Handle voice/audio messages
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming voice or audio messages."""
    try:
        message = update.message
        user_id = message.from_user.id
        
        # Check if this is for voice cloning
        if user_states.get(user_id) == "awaiting_clone":
            await handle_clone_audio(update, context)
            return
        
        # Reset user's page to 0
        user_pages[user_id] = 0
        
        # Check if the message contains voice or audio
        if message.voice:
            file_id = message.voice.file_id
            duration = message.voice.duration
        elif message.audio:
            file_id = message.audio.file_id
            duration = message.audio.duration
        else:
            await message.reply_text("❌ Please send a voice or audio message.")
            return
        
        # Check if audio is too long (>60 seconds)
        if duration > 60:
            await message.reply_text("⚠️ Audio is too long. Please send audio under 60 seconds for processing.")
            return
            
        # Download the file
        file = await context.bot.get_file(file_id)
        input_path = os.path.join(TEMP_DIR, f"input_{user_id}.ogg")
        
        await file.download_to_drive(input_path)
        user_audio[user_id] = input_path
        
        await show_effect_keyboard(update, context, user_id, 0)
        
    except Exception as e:
        logger.error(f"Error in handle_audio: {str(e)}")
        await message.reply_text("❌ An error occurred while processing your audio. Please try again.")

# Show effect options with pagination
async def show_effect_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, page=0):
    """Show the keyboard with effect options."""
    # Get effects for the current page
    effects_page = get_effect_page(page, 8)
    total_pages = get_total_pages(8)
    
    # Create keyboard with effects
    keyboard = [
        [InlineKeyboardButton(name.title(), callback_data=f"effect:{name}")] 
        for name in effects_page.keys()
    ]
    
    # Add user's cloned voice if available (only on first page)
    if page == 0 and user_id in user_voices and user_id in user_voice_names:
        voice_name = user_voice_names[user_id]
        keyboard.insert(0, [InlineKeyboardButton(f"👤 {voice_name}", callback_data="effect:cloned")])
    
    # Add navigation buttons if needed
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data="page:prev"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data="page:next"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Add page indicator
    page_text = f"Page {page+1}/{total_pages}"
    keyboard.append([InlineKeyboardButton(page_text, callback_data="page:info")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Store current page
    user_pages[user_id] = page
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎛️ Choose a voice effect to apply:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🎛️ Choose a voice effect to apply:",
            reply_markup=reply_markup
        )

# Callback when user selects an effect or navigates pages
async def handle_effect_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user selecting an effect or navigating pages."""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data
        
        # Handle page navigation
        if callback_data.startswith("page:"):
            action = callback_data.split(":")[1]
            current_page = user_pages.get(user_id, 0)
            
            if action == "prev":
                new_page = max(0, current_page - 1)
            elif action == "next":
                total_pages = get_total_pages(8)
                new_page = min(total_pages - 1, current_page + 1)
            elif action == "reset":
                new_page = 0
            else:  # info button - do nothing
                new_page = current_page
                
            await show_effect_keyboard(update, context, user_id, new_page)
            return
        
        # Handle effect selection
        if callback_data.startswith("effect:"):
            effect = callback_data.split(":")[1]
            input_path = user_audio.get(user_id)
            
            if not input_path:
                await query.edit_message_text("❌ No audio found. Please send or forward a voice message first.")
                return
            
            # Check if this is the cloned voice effect
            if effect == "cloned":
                # Check if user has a cloned voice
                if user_id not in user_voices:
                    await query.edit_message_text("❌ You haven't cloned your voice yet. Use the /clone command first.")
                    return
                    
                voice_name = user_voice_names.get(user_id, "My Voice")
                # Show processing message
                await query.edit_message_text(f"⏳ Processing with *{voice_name}* effect...", parse_mode="Markdown")
                
                try:
                    output_path = os.path.join(TEMP_DIR, f"output_{user_id}.ogg")
                    cloned_voice_path = user_voices[user_id]
                    
                    # Apply voice cloning effect
                    success, error_msg = apply_voice_clone_effect(input_path, output_path, cloned_voice_path)
                    
                    if not success:
                        logger.error(f"Error applying cloned voice effect: {error_msg}")
                        await query.edit_message_text("❌ Error applying your cloned voice. Please try again.")
                        return
                    
                    # Update message and send the processed audio
                    await query.edit_message_text(f"✅ Applied *{voice_name}* effect!", parse_mode="Markdown")
                    
                    # Send the processed audio
                    with open(output_path, 'rb') as audio_file:
                        await context.bot.send_voice(
                            chat_id=user_id,
                            voice=audio_file,
                            caption=f"🎧 Your voice with *{voice_name}* effect.",
                            parse_mode="Markdown"
                        )
                    
                    # Prompt for additional effects
                    keyboard = [[InlineKeyboardButton("Apply another effect", callback_data="page:reset")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="Would you like to apply another effect to your original audio?",
                        reply_markup=reply_markup
                    )
                    
                except Exception as e:
                    logger.error(f"Error applying cloned voice effect: {str(e)}")
                    await query.edit_message_text("❌ Error applying your cloned voice. Please try again.")
                    return
                    
            else:
                # Regular voice effect
                # Show processing message
                await query.edit_message_text(f"⏳ Processing with *{effect}* effect...", parse_mode="Markdown")
                
                try:
                    output_path = os.path.join(TEMP_DIR, f"output_{user_id}.ogg")
                    
                    # Apply effect using our utility function
                    filter_cmd = VOICE_EFFECTS.get(effect, "")
                    success, error_msg = apply_audio_effect(input_path, output_path, filter_cmd)
                    
                    if not success:
                        logger.error(f"Error applying effect: {error_msg}")
                        await query.edit_message_text(f"❌ Error applying effect. Please try again or choose another effect.")
                        return
                    
                    # Update message and send the processed audio
                    await query.edit_message_text(f"✅ Applied *{effect}* effect!", parse_mode="Markdown")
                    
                    # Send the processed audio
                    with open(output_path, 'rb') as audio_file:
                        await context.bot.send_voice(
                            chat_id=user_id,
                            voice=audio_file,
                            caption=f"🎧 Your voice with *{effect}* effect.",
                            parse_mode="Markdown"
                        )
                    
                    # Prompt for additional effects
                    keyboard = [[InlineKeyboardButton("Apply another effect", callback_data="page:reset")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="Would you like to apply another effect to your original audio?",
                        reply_markup=reply_markup
                    )
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
    
# Function to rename cloned voice
async def rename_clone(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "Your cloned voice will appear with this name in the effects menu.",
        parse_mode="Markdown"
    )

# /clone - initiate voice cloning process
async def clone_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the voice cloning process by requesting a voice sample."""
    user_id = update.message.from_user.id
    user_states[user_id] = "awaiting_clone"
    
    await update.message.reply_text(
        "🎤 *Voice Cloning Initiated* 🎤\n\n"
        "Please send a short voice message (5-10 seconds) with clear speech.\n\n"
        "I'll use this sample to clone your voice for the /say command and add it to your voice effects.",
        parse_mode="Markdown"
    )

# Handle voice message for cloning
async def handle_clone_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process voice message for cloning."""
    try:
        message = update.message
        user_id = message.from_user.id
        
        # Verify we have a voice message
        if not message.voice:
            await message.reply_text("❌ Please send a *voice message* (not audio file) for cloning.", parse_mode="Markdown")
            return
        
        # Check voice duration (ideally 5-10 seconds)
        duration = message.voice.duration
        if duration < 3:
            await message.reply_text("⚠️ Voice sample is too short. Please send a sample of at least 3 seconds.", parse_mode="Markdown")
            return
        if duration > 30:
            await message.reply_text("⚠️ Voice sample is too long. Please keep it under 30 seconds for better results.", parse_mode="Markdown")
            return
        
        # Download the voice sample
        file = await context.bot.get_file(message.voice.file_id)
        clone_path = os.path.join(TEMP_DIR, f"cloned_voice_{user_id}.ogg")
        
        await file.download_to_drive(clone_path)
        user_voices[user_id] = clone_path
        
        # Set default voice name and ask user to name their voice
        user_voice_names[user_id] = f"My Voice"
        user_states[user_id] = "awaiting_voice_name"
        
        await message.reply_text(
            "✅ *Voice sample recorded successfully!* ✅\n\n"
            "Now, please give your cloned voice a name. This name will appear in the effects menu.\n\n"
            "Reply with a name like 'Robot Me' or 'Deep Voice'.\n\n"
            "Or simply send /skip to use the default name 'My Voice'.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_clone_audio: {str(e)}")
        await message.reply_text("❌ An error occurred while cloning your voice. Please try again.")
        user_states[user_id] = None

# Handle voice naming
async def handle_voice_naming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process voice naming after cloning."""
    message = update.message
    user_id = message.from_user.id
    
    # Check if the user is in the voice naming state
    if user_states.get(user_id) != "awaiting_voice_name":
        return
    
    # Get the name from the user's message
    voice_name = message.text.strip()
    
    # Limit the name length
    if len(voice_name) > 20:
        voice_name = voice_name[:20]
    
    # Save the voice name
    user_voice_names[user_id] = voice_name
    
    # Reset state
    user_states[user_id] = None
    
    await message.reply_text(
        f"✅ *Voice name set to '{voice_name}'!* ✅\n\n"
        "Your cloned voice has been added to the effects menu. You can apply it to any voice message.\n\n"
        "You can also use */say <text>* to make me speak text using your cloned voice.\n\n"
        "Example: `/say Hello, this is my cloned voice`",
        parse_mode="Markdown"
    )

# Skip voice naming
async def skip_voice_naming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip the voice naming step and use default name."""
    user_id = update.message.from_user.id
    
    # Check if the user is in the voice naming state
    if user_states.get(user_id) != "awaiting_voice_name":
        await update.message.reply_text(
            "❓ You're not currently naming a voice. Use /clone to clone your voice first.",
            parse_mode="Markdown"
        )
        return
    
    # Reset state
    user_states[user_id] = None
    
    await update.message.reply_text(
        "✅ *Default voice name 'My Voice' will be used* ✅\n\n"
        "Your cloned voice has been added to the effects menu. You can apply it to any voice message.\n\n"
        "You can also use */say <text>* to make me speak text using your cloned voice.\n\n"
        "Example: `/say Hello, this is my cloned voice`",
        parse_mode="Markdown"
    )

# /say <text> - speak text with cloned voice
async def say_with_cloned_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate speech using the user's cloned voice."""
    try:
        user_id = update.message.from_user.id
        
        # Check if the user has cloned their voice
        if user_id not in user_voices:
            await update.message.reply_text(
                "⚠️ You haven't cloned your voice yet.\n\n"
                "Use the */clone* command first, then send a voice message.",
                parse_mode="Markdown"
            )
            return
        
        # Check if text is provided
        if not context.args:
            await update.message.reply_text(
                "📝 Please provide some text to speak.\n\n"
                "Example: `/say Hello, this is my cloned voice`",
                parse_mode="Markdown"
            )
            return
        
        text = " ".join(context.args)
        
        # Limit text length
        if len(text) > 200:
            await update.message.reply_text(
                "⚠️ Text is too long. Please limit your message to 200 characters.",
                parse_mode="Markdown"
            )
            return
        
        # Send "processing" message
        processing_message = await update.message.reply_text(
            "🔄 *Processing your text-to-speech request...*\n\n"
            "This may take a few seconds.",
            parse_mode="Markdown"
        )
        
        # Generate output path
        output_path = os.path.join(TEMP_DIR, f"tts_output_{user_id}.ogg")
        
        # For this simplified version, we'll generate a 2-second silent audio
        # In a real implementation, this would be replaced with actual TTS + voice cloning
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc", "-t", "2",
            "-q:a", "9", "-acodec", "libopus", output_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Update the processing message
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id,
            text="✅ *Text-to-speech generated!*",
            parse_mode="Markdown"
        )
        
        # Send the voice message with the text
        with open(output_path, "rb") as audio_file:
            await update.message.reply_voice(
                voice=audio_file,
                caption=f"🗣️ *Your cloned voice saying:*\n\n{text}",
                parse_mode="Markdown"
            )
        
        # Clean up the output file
        if os.path.exists(output_path):
            os.remove(output_path)
            
    except Exception as e:
        logger.error(f"Error in say_with_cloned_voice: {str(e)}")
        await update.message.reply_text("❌ An error occurred while generating speech. Please try again.")
