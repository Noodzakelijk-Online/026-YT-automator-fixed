"""
Thumbnail generation service
"""

import logging
import tempfile
import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

def generate_thumbnail(video_path=None, title=None, template_style='modern'):
    """
    Generate thumbnail for video
    
    Args:
        video_path (str): Path to video file (optional)
        title (str): Video title for thumbnail text
        template_style (str): Style template to use
    
    Returns:
        str: Path to generated thumbnail or None if failed
    """
    try:
        logger.info(f"Generating thumbnail with style: {template_style}")
        
        # Create a basic thumbnail using PIL
        width, height = 1280, 720  # YouTube recommended size
        
        # Create base image
        if template_style == 'modern':
            bg_color = (45, 45, 45)  # Dark gray
            text_color = (255, 255, 255)  # White
            accent_color = (255, 0, 0)  # YouTube red
        elif template_style == 'bright':
            bg_color = (255, 255, 255)  # White
            text_color = (0, 0, 0)  # Black
            accent_color = (0, 123, 255)  # Blue
        else:
            bg_color = (30, 30, 30)  # Very dark
            text_color = (255, 255, 255)  # White
            accent_color = (255, 165, 0)  # Orange
        
        # Create image
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add gradient effect (simple version)
        for y in range(height):
            alpha = int(255 * (1 - y / height) * 0.3)
            overlay_color = tuple(min(255, c + alpha) for c in bg_color)
            draw.line([(0, y), (width, y)], fill=overlay_color)
        
        # Add title text if provided
        if title:
            try:
                # Try to use a better font, fall back to default
                font_size = 72
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # Wrap text to fit
                words = title.split()
                lines = []
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    if bbox[2] - bbox[0] <= width - 100:  # Leave margin
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                        else:
                            lines.append(word)
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Draw text lines
                total_height = len(lines) * (font_size + 10)
                start_y = (height - total_height) // 2
                
                for i, line in enumerate(lines):
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (width - text_width) // 2
                    y = start_y + i * (font_size + 10)
                    
                    # Draw text shadow
                    draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 128))
                    # Draw main text
                    draw.text((x, y), line, font=font, fill=text_color)
                
            except Exception as e:
                logger.warning(f"Error adding text to thumbnail: {e}")
        
        # Add decorative elements
        # Corner accent
        draw.rectangle([0, 0, 50, height], fill=accent_color)
        draw.rectangle([width-50, 0, width, height], fill=accent_color)
        
        # Save thumbnail
        temp_dir = tempfile.mkdtemp()
        thumbnail_path = os.path.join(temp_dir, 'thumbnail.jpg')
        img.save(thumbnail_path, 'JPEG', quality=95)
        
        logger.info(f"Thumbnail generated: {thumbnail_path}")
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"Thumbnail generation error: {e}")
        return None

def extract_frame_from_video(video_path, timestamp=None):
    """
    Extract a frame from video to use as thumbnail base
    
    Args:
        video_path (str): Path to video file
        timestamp (float): Time in seconds to extract frame (default: middle)
    
    Returns:
        str: Path to extracted frame or None if failed
    """
    try:
        # This would use FFmpeg to extract a frame
        # Example: ffmpeg -i video.mp4 -ss 00:00:30 -vframes 1 frame.jpg
        
        logger.info(f"Extracting frame from video: {video_path}")
        
        # Placeholder implementation
        # In real implementation:
        # import subprocess
        # if timestamp is None:
        #     timestamp = get_video_duration(video_path) / 2  # Middle of video
        # 
        # temp_dir = tempfile.mkdtemp()
        # frame_path = os.path.join(temp_dir, 'frame.jpg')
        # 
        # cmd = ['ffmpeg', '-i', video_path, '-ss', str(timestamp), '-vframes', '1', frame_path]
        # result = subprocess.run(cmd, capture_output=True, text=True)
        # 
        # if result.returncode == 0:
        #     return frame_path
        
        return None
        
    except Exception as e:
        logger.error(f"Frame extraction error: {e}")
        return None

def create_custom_thumbnail(background_image=None, title=None, subtitle=None, style_config=None):
    """
    Create custom thumbnail with advanced options
    
    Args:
        background_image (str): Path to background image
        title (str): Main title text
        subtitle (str): Subtitle text
        style_config (dict): Style configuration
    
    Returns:
        str: Path to generated thumbnail or None if failed
    """
    try:
        if style_config is None:
            style_config = {
                'width': 1280,
                'height': 720,
                'title_font_size': 72,
                'subtitle_font_size': 36,
                'title_color': (255, 255, 255),
                'subtitle_color': (200, 200, 200),
                'background_color': (45, 45, 45),
                'overlay_opacity': 0.7
            }
        
        width = style_config['width']
        height = style_config['height']
        
        # Create base image
        if background_image and os.path.exists(background_image):
            img = Image.open(background_image)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Add overlay for text readability
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, int(255 * style_config['overlay_opacity'])))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        else:
            img = Image.new('RGB', (width, height), style_config['background_color'])
        
        draw = ImageDraw.Draw(img)
        
        # Add title and subtitle
        if title:
            # Implementation for custom text rendering
            pass
        
        # Save thumbnail
        temp_dir = tempfile.mkdtemp()
        thumbnail_path = os.path.join(temp_dir, 'custom_thumbnail.jpg')
        img.save(thumbnail_path, 'JPEG', quality=95)
        
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"Custom thumbnail creation error: {e}")
        return None

