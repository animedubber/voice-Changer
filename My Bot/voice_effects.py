"""
This module contains the available voice effects for the Telegram bot.
Each effect is mapped to its corresponding FFmpeg filter command.
"""

# Basic voice effects
VOICE_EFFECTS = {
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
    "underwater": "aecho=0.6:0.9:900:0.3,asetrate=48000*0.8,aresample=48000",
    "telephone": "highpass=f=500,lowpass=f=2000,aphaser=type=t:speed=0.8:decay=0.6",
    "megaphone": "highpass=f=400,lowpass=f=4000,compand=0.4:0.8:0:-7:-14:-90:5:5",
    "tremolo": "tremolo=f=6:d=0.8",
    "vibrato": "vibrato=f=7:d=0.5",
    "whisper": "highpass=f=200,lowpass=f=3000,acompressor=threshold=0.1:ratio=4",
    "evil": "asetrate=44100*0.75,aresample=44100,aecho=0.8:0.88:30:0.5",
    "helium": "asetrate=44100*1.8,aresample=44100",
    "old_radio": "highpass=f=500,lowpass=f=3000,aphaser=speed=0.5:decay=0.3,areverse",
    "metallic": "afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)',aecho=0.8:0.88:6:0.4"
}

# Function to get a subset of effects for pagination
def get_effect_page(page_num=0, effects_per_page=8):
    """
    Get a subset of effects for pagination
    
    Args:
        page_num (int): The page number (0-indexed)
        effects_per_page (int): Number of effects per page
        
    Returns:
        dict: A dictionary containing a subset of effects
    """
    effect_items = list(VOICE_EFFECTS.items())
    start_idx = page_num * effects_per_page
    end_idx = start_idx + effects_per_page
    
    # Get a slice of the effects dictionary
    if start_idx >= len(effect_items):
        return {}
    
    return dict(effect_items[start_idx:min(end_idx, len(effect_items))])

# Function to get total number of pages
def get_total_pages(effects_per_page=8):
    """
    Calculate the total number of pages needed to display all effects
    
    Args:
        effects_per_page (int): Number of effects per page
        
    Returns:
        int: Total number of pages
    """
    return (len(VOICE_EFFECTS) + effects_per_page - 1) // effects_per_page
