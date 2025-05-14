import os
import shutil
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def ensure_temp_dir(directory):
    """
    Ensure that the temporary directory exists and is empty.
    
    Args:
        directory (str): Path to the temporary directory
    """
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created temporary directory: {directory}")
        else:
            # Clean up old files
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {str(e)}")
            
            logger.info(f"Cleaned temporary directory: {directory}")
    except Exception as e:
        logger.error(f"Error ensuring temporary directory: {str(e)}")

def cleanup_user_files(user_id, temp_dir, user_audio_dict):
    """
    Clean up user audio files and remove from dictionary.
    
    Args:
        user_id (int): Telegram user ID
        temp_dir (str): Path to the temporary directory
        user_audio_dict (dict): Dictionary storing user audio paths
    """
    try:
        input_path = user_audio_dict.get(user_id)
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
            
        output_path = os.path.join(temp_dir, f"output_{user_id}.ogg")
        if os.path.exists(output_path):
            os.remove(output_path)
            
        if user_id in user_audio_dict:
            del user_audio_dict[user_id]
            
        logger.info(f"Cleaned up files for user: {user_id}")
    except Exception as e:
        logger.error(f"Error cleaning up user files: {str(e)}")

def apply_audio_effect(input_path, output_path, effect_filter):
    """
    Apply a voice effect to an audio file using FFmpeg.
    
    Args:
        input_path (str): Path to the input audio file
        output_path (str): Path where the processed file will be saved
        effect_filter (str): FFmpeg filter to apply
        
    Returns:
        bool: True if successful, False otherwise
        str: Error message if unsuccessful, empty string otherwise
    """
    if not os.path.exists(input_path):
        return False, f"Input file not found: {input_path}"
    
    try:
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-i", input_path, 
            "-af", effect_filter, "-c:a", "libopus", 
            output_path
        ]
        
        process = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            error_msg = process.stderr
            logger.error(f"FFmpeg error: {error_msg}")
            return False, error_msg
        
        return True, ""
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error applying audio effect: {error_msg}")
        return False, error_msg

def apply_voice_clone_effect(input_path, output_path, cloned_voice_path):
    """
    Apply voice cloning to convert input voice to sound like the cloned voice.
    
    This is a simplified implementation that uses the characteristics of the 
    cloned voice to transform the input voice. In a real production implementation,
    this would use a more sophisticated voice conversion algorithm.
    
    Args:
        input_path (str): Path to the input audio file
        output_path (str): Path where the processed file will be saved
        cloned_voice_path (str): Path to the user's cloned voice
        
    Returns:
        bool: True if successful, False otherwise
        str: Error message if unsuccessful, empty string otherwise
    """
    if not os.path.exists(input_path):
        return False, f"Input file not found: {input_path}"
    
    if not os.path.exists(cloned_voice_path):
        return False, f"Cloned voice file not found: {cloned_voice_path}"
    
    try:
        import subprocess
        
        # For demonstration, we'll apply a basic voice transformation
        # In a real implementation, this would involve analyzing the cloned voice
        # and applying its characteristics to the input voice
        
        # 1. Extract vocal characteristics from the cloned voice
        # (simplified for demo - we're using a basic pitch shift)
        temp_analysis_file = f"{os.path.splitext(output_path)[0]}_analysis.txt"
        
        # 2. Apply a transformation based on the cloned voice characteristics
        # Here we're just using a simple formant shift filter as a demonstration
        filter_cmd = "asetrate=44100*1.1,aresample=44100,atempo=0.9"
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path, 
            "-af", filter_cmd, "-c:a", "libopus", 
            output_path
        ]
        
        process = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            error_msg = process.stderr
            logger.error(f"Voice cloning error: {error_msg}")
            return False, error_msg
        
        return True, ""
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error applying voice clone effect: {error_msg}")
        return False, error_msg

def check_ffmpeg_installed():
    """
    Check if FFmpeg is installed on the system.
    
    Returns:
        bool: True if FFmpeg is installed, False otherwise
    """
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False
