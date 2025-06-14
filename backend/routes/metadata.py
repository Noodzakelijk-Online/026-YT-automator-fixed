"""
Metadata generation routes using OpenAI
"""

from flask import Blueprint, request, jsonify, current_app
import openai
import logging
import json
from services.transcription_service import transcribe_video
from services.thumbnail_service import generate_thumbnail

logger = logging.getLogger(__name__)

metadata_bp = Blueprint('metadata', __name__)

@metadata_bp.route('/generate', methods=['POST'])
def generate_metadata():
    """Generate video metadata using AI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get input text (could be transcription, summary, or user input)
        input_text = data.get('text', '')
        video_topic = data.get('topic', '')
        target_audience = data.get('audience', 'general')
        video_style = data.get('style', 'informative')
        
        if not input_text and not video_topic:
            return jsonify({'error': 'Either text or topic must be provided'}), 400
        
        # Combine inputs for better context
        context = f"Topic: {video_topic}\n" if video_topic else ""
        context += f"Content: {input_text}\n" if input_text else ""
        context += f"Target Audience: {target_audience}\n"
        context += f"Style: {video_style}"
        
        # Generate title
        title_prompt = f"""
        Generate a compelling YouTube video title based on the following information:
        {context}
        
        Requirements:
        - Maximum 60 characters
        - Engaging and click-worthy
        - SEO-friendly
        - No quotation marks
        - Appropriate for the target audience
        """
        
        title_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": title_prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        title = title_response.choices[0].message.content.strip()
        
        # Generate description
        description_prompt = f"""
        Create a detailed YouTube video description based on the following information:
        {context}
        
        Requirements:
        - Engaging introduction
        - Key points covered in the video
        - Call to action (like, subscribe, comment)
        - 200-500 words
        - No timestamps or external links
        - SEO-optimized
        - Professional tone
        """
        
        description_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": description_prompt}],
            max_tokens=800,
            temperature=0.7
        )
        
        description = description_response.choices[0].message.content.strip()
        
        # Generate tags
        tags_prompt = f"""
        Generate relevant YouTube tags for a video with the following information:
        {context}
        
        Requirements:
        - 10-15 tags
        - Mix of broad and specific tags
        - SEO-optimized
        - Relevant to content
        - Return as comma-separated list
        """
        
        tags_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": tags_prompt}],
            max_tokens=200,
            temperature=0.5
        )
        
        tags_text = tags_response.choices[0].message.content.strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        
        # Generate category suggestion
        category_prompt = f"""
        Based on the following video information, suggest the most appropriate YouTube category:
        {context}
        
        Choose from these categories and return only the category ID number:
        1 - Film & Animation
        2 - Autos & Vehicles
        10 - Music
        15 - Pets & Animals
        17 - Sports
        19 - Travel & Events
        20 - Gaming
        22 - People & Blogs
        23 - Comedy
        24 - Entertainment
        25 - News & Politics
        26 - Howto & Style
        27 - Education
        28 - Science & Technology
        
        Return only the number.
        """
        
        category_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": category_prompt}],
            max_tokens=10,
            temperature=0.3
        )
        
        category_id = category_response.choices[0].message.content.strip()
        
        # Validate category ID
        valid_categories = ['1', '2', '10', '15', '17', '19', '20', '22', '23', '24', '25', '26', '27', '28']
        if category_id not in valid_categories:
            category_id = '22'  # Default to People & Blogs
        
        return jsonify({
            'title': title,
            'description': description,
            'tags': tags,
            'category_id': category_id,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Metadata generation error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@metadata_bp.route('/title', methods=['POST'])
def generate_title_only():
    """Generate only video title"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        prompt = f"""
        Generate a compelling YouTube video title based on this content:
        {text}
        
        Requirements:
        - Maximum 60 characters
        - Engaging and click-worthy
        - No quotation marks
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        title = response.choices[0].message.content.strip()
        
        return jsonify({
            'title': title,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Title generation error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@metadata_bp.route('/description', methods=['POST'])
def generate_description_only():
    """Generate only video description"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        prompt = f"""
        Create a YouTube video description based on this content:
        {text}
        
        Requirements:
        - Engaging and informative
        - 200-300 words
        - Include call to action
        - No timestamps or external links
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        
        description = response.choices[0].message.content.strip()
        
        return jsonify({
            'description': description,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Description generation error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@metadata_bp.route('/keywords', methods=['POST'])
def generate_keywords():
    """Generate SEO keywords for video"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        prompt = f"""
        Generate SEO-optimized keywords for a YouTube video based on this content:
        {text}
        
        Requirements:
        - 15-20 relevant keywords
        - Mix of broad and specific terms
        - Good for YouTube SEO
        - Return as comma-separated list
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5
        )
        
        keywords_text = response.choices[0].message.content.strip()
        keywords = [keyword.strip() for keyword in keywords_text.split(',') if keyword.strip()]
        
        return jsonify({
            'keywords': keywords,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Keywords generation error: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

