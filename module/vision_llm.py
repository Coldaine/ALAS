import logging
import threading
import time
import cv2
import base64
import os
import numpy as np
from datetime import datetime

# Import configuration - try ollama first, fallback to gemini
USING_OLLAMA = False
try:
    from config.vision_ollama_config import *
    USING_OLLAMA = ENABLE_OLLAMA_VISION
except ImportError:
    pass

if not USING_OLLAMA:
    try:
        from config.vision_llm_config import *
    except ImportError:
        # Fallback configuration if config file not available
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        GEMINI_MODEL = "gemini-2.5-flash"
        VISION_LOG_FILE = "logs/vision_llm.log"
        LOG_LEVEL = "DEBUG"
        LOG_ONLY_MATCHES = True
        API_TIMEOUT = 10
        MAX_IMAGE_SIZE = (800, 600)
        ENABLE_LLM_LOGGING = True
        ENABLE_JSON_PARSING = True
        ENABLE_FALLBACK_PARSING = True
        TEMPLATE_MATCHING_PROMPT = """You are analyzing a screenshot from the Azur Lane mobile game to find a specific UI element.

TASK: Determine if the template image (second image) appears in the screenshot (first image).

Template name: {template_name}

Please analyze both images and respond with:
1. Whether the template is found (true/false)
2. If found, the approximate bounding box coordinates [x1, y1, x2, y2]
3. Confidence level (0.0 to 1.0)
4. Brief explanation of what you see

Format your response as JSON:
{{"found": boolean, "bounding_box": [x1, y1, x2, y2], "confidence": float, "explanation": "string"}}"""
        ERROR_NO_API_KEY = "GOOGLE_API_KEY not found in environment variables"
        ERROR_MISSING_DEPS = "google-generativeai package not installed. Run: pip install google-generativeai"

def preload_ollama_model():
    """Pre-load the ollama model to avoid cold start delays."""
    if not USING_OLLAMA:
        return
    
    try:
        import requests
        vision_logger.info(f"Pre-loading ollama model: {VISION_MODEL}")
        
        # Simple test prompt to warm up the model
        payload = {
            "model": VISION_MODEL,
            "prompt": "Ready",
            "stream": False
        }
        
        response = requests.post(f"{OLLAMA_API_BASE}/api/generate", json=payload, timeout=60)
        if response.status_code == 200:
            vision_logger.info(f"Ollama model {VISION_MODEL} pre-loaded successfully")
        else:
            vision_logger.warning(f"Failed to pre-load ollama model: {response.status_code}")
    except Exception as e:
        vision_logger.warning(f"Error pre-loading ollama model: {e}")

# Set consistent template matching prompt for ollama
if USING_OLLAMA:
    TEMPLATE_MATCHING_PROMPT = """You are an expert computer vision system specialized in analyzing Azur Lane mobile game UI elements.

CONTEXT: Azur Lane is a mobile game with anime-style graphics featuring naval combat. UI elements include buttons, menus, ship portraits, resource counters, battle indicators, and navigation elements. The interface uses blue/white color schemes with stylized fonts and icons.

TASK: Analyze the screenshot (first image) to locate the template UI element (second image).

Template name: {template_name}

ANALYSIS REQUIREMENTS:
1. Compare the template against all regions of the screenshot
2. Look for visual similarities in shape, color, text, and iconography
3. Account for slight variations in lighting, scaling, or UI state changes
4. Consider that UI elements may have hover effects or different states
5. Be precise with bounding box coordinates if found

RESPONSE FORMAT (JSON only):
{{"found": boolean, "bounding_box": [x1, y1, x2, y2], "confidence": float, "explanation": "string"}}

Where:
- found: true if template is clearly visible in screenshot
- bounding_box: [left, top, right, bottom] coordinates as ratios (0.0-1.0), null if not found
- confidence: 0.0-1.0 based on visual similarity and certainty
- explanation: Brief description of what you identified and location

Focus on accuracy over speed. If uncertain, err on the side of caution with lower confidence."""

# --- Logger Configuration ---
# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# A dedicated logger for the vision model's analysis
vision_logger = logging.getLogger('vision_llm')
vision_logger.setLevel(getattr(logging, LOG_LEVEL))
# Create file handler
fh = logging.FileHandler(VISION_LOG_FILE)
fh.setLevel(getattr(logging, LOG_LEVEL))
# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(message)s')
fh.setFormatter(formatter)
vision_logger.addHandler(fh)

# --- Ollama Vision Model ---
def call_ollama_vision(screen_b64, template_b64, template_name):
    """
    Call Ollama vision model (llava-phi3) to analyze template matching.
    """
    try:
        import requests
        import json
        
        # Decode base64 images
        screen_bytes = base64.b64decode(screen_b64)
        template_bytes = base64.b64decode(template_b64)
        
        # Resize images if too large
        screen_img = cv2.imdecode(np.frombuffer(screen_bytes, np.uint8), cv2.IMREAD_COLOR)
        max_size = MAX_IMAGE_SIZE if isinstance(MAX_IMAGE_SIZE, int) else MAX_IMAGE_SIZE[0]
        if screen_img.shape[1] > max_size or screen_img.shape[0] > max_size:
            height, width = screen_img.shape[:2]
            if width > height:
                new_width = max_size
                new_height = int((height * max_size) / width)
            else:
                new_height = max_size
                new_width = int((width * max_size) / height)
            screen_img = cv2.resize(screen_img, (new_width, new_height))
            _, screen_buffer = cv2.imencode('.png', screen_img)
            screen_b64 = base64.b64encode(screen_buffer).decode('utf-8')
        
        template_img = cv2.imdecode(np.frombuffer(template_bytes, np.uint8), cv2.IMREAD_COLOR)
        if template_img.shape[1] > max_size or template_img.shape[0] > max_size:
            height, width = template_img.shape[:2]
            if width > height:
                new_width = max_size
                new_height = int((height * max_size) / width)
            else:
                new_height = max_size
                new_width = int((width * max_size) / height)
            template_img = cv2.resize(template_img, (new_width, new_height))
            _, template_buffer = cv2.imencode('.png', template_img)
            template_b64 = base64.b64encode(template_buffer).decode('utf-8')
        
        # Prepare prompt
        prompt = TEMPLATE_MATCHING_PROMPT.format(template_name=template_name)
        
        # Prepare request for ollama
        payload = {
            "model": VISION_MODEL,
            "prompt": prompt,
            "images": [screen_b64, template_b64],
            "stream": False
        }
        
        # Make API call
        response = requests.post(
            f"{OLLAMA_API_BASE}/api/generate",
            json=payload,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        
        result_text = response.json()["response"]
        
        # Parse JSON response
        try:
            # Try direct JSON parse first
            result = json.loads(result_text.strip())
            result['model'] = VISION_MODEL
            return result
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                    result['model'] = VISION_MODEL
                    return result
                except json.JSONDecodeError:
                    pass
            
            # Fallback parsing
            return {
                'found': 'found' in result_text.lower() or 'detected' in result_text.lower(),
                'bounding_box': None,
                'confidence': 0.5,
                'explanation': result_text[:200],
                'model': VISION_MODEL
            }
            
    except Exception as e:
        vision_logger.error(f"Ollama API call failed for template '{template_name}': {e}")
        return {'error': str(e), 'model': VISION_MODEL}

def call_vision_model(screen_b64, template_b64, template_name):
    """
    Dispatcher function that calls the appropriate vision model based on configuration.
    """
    if USING_OLLAMA:
        return call_ollama_vision(screen_b64, template_b64, template_name)
    else:
        return call_gemini_vision(screen_b64, template_b64, template_name)

# --- LLM Interaction (Gemini Flash 2.5) ---
def call_gemini_vision(screen_b64, template_b64, template_name):
    """
    Call Gemini Flash 2.5 vision model to analyze template matching.
    """
    try:
        import google.generativeai as genai

        # Check API key
        if not GOOGLE_API_KEY:
            vision_logger.warning(ERROR_NO_API_KEY)
            return {'error': 'No API key', 'model': GEMINI_MODEL}

        # Configure API key
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Decode base64 images
        screen_bytes = base64.b64decode(screen_b64)
        template_bytes = base64.b64decode(template_b64)
        
        # Resize images if too large (to reduce API costs)
        screen_img = cv2.imdecode(np.frombuffer(screen_bytes, np.uint8), cv2.IMREAD_COLOR)
        if screen_img.shape[1] > MAX_IMAGE_SIZE[0] or screen_img.shape[0] > MAX_IMAGE_SIZE[1]:
            screen_img = cv2.resize(screen_img, MAX_IMAGE_SIZE)
            _, screen_buffer = cv2.imencode('.png', screen_img)
            screen_bytes = screen_buffer.tobytes()
        
        template_img = cv2.imdecode(np.frombuffer(template_bytes, np.uint8), cv2.IMREAD_COLOR)
        if template_img.shape[1] > MAX_IMAGE_SIZE[0] or template_img.shape[0] > MAX_IMAGE_SIZE[1]:
            template_img = cv2.resize(template_img, MAX_IMAGE_SIZE)
            _, template_buffer = cv2.imencode('.png', template_img)
            template_bytes = template_buffer.tobytes()
        
        # Create PIL Images from bytes for Gemini
        import io
        from PIL import Image
        
        screen_image = Image.open(io.BytesIO(screen_bytes))
        template_image = Image.open(io.BytesIO(template_bytes))
        
        # Use configured prompt template
        prompt = TEMPLATE_MATCHING_PROMPT.format(template_name=template_name)
        
        # Create model instance
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Make API call
        response = model.generate_content([prompt, screen_image, template_image])
        
        # Parse response
        if ENABLE_JSON_PARSING:
            try:
                import json
                result = json.loads(response.text.strip())
                result['model'] = GEMINI_MODEL
                return result
            except json.JSONDecodeError:
                if not ENABLE_FALLBACK_PARSING:
                    return {'error': 'JSON parsing failed', 'model': GEMINI_MODEL}
        
        # Fallback parsing if JSON fails or is disabled
        return {
            'found': 'found' in response.text.lower() or 'detected' in response.text.lower(),
            'bounding_box': None,
            'confidence': 0.5,
            'explanation': response.text[:200],
            'model': GEMINI_MODEL
        }
            
    except ImportError:
        vision_logger.warning(ERROR_MISSING_DEPS)
        return {'error': 'Missing dependencies', 'model': GEMINI_MODEL}
    except Exception as e:
        vision_logger.error(f"Gemini API call failed for template '{template_name}': {e}")
        return {'error': str(e), 'model': GEMINI_MODEL}

# --- Screenshot Saving Function ---
def save_vision_screenshots(screen_image, template_image, template_name, matched=False):
    """Save vision input screenshots for offline analysis."""
    try:
        # Import main logger for visibility
        from module.logger import logger
        
        # Create filename with result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        result_str = "matched" if matched else "not_matched"
        filename = f"{timestamp}_{template_name}_{result_str}"
        
        # Create directory structure
        vision_dir = os.path.join("logs", "vision_screenshots")
        os.makedirs(vision_dir, exist_ok=True)
        
        # Resize screen image to optimal size for Gemini 2.5 Flash (768x768)
        screen_resized = cv2.resize(screen_image, (768, 768), interpolation=cv2.INTER_AREA)
        screen_path = os.path.join(vision_dir, f"{filename}_screen.png")
        cv2.imwrite(screen_path, screen_resized)
        
        # Resize template image (max 384x384 to save tokens)
        h, w = template_image.shape[:2]
        if h > 384 or w > 384:
            scale = min(384/h, 384/w)
            new_h, new_w = int(h*scale), int(w*scale)
            template_resized = cv2.resize(template_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            template_resized = template_image
        template_path = os.path.join(vision_dir, f"{filename}_template.png")
        cv2.imwrite(template_path, template_resized)
        
        # Log to main ALAS logger for visibility
        logger.info(f"Vision screenshot saved: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to save vision screenshots: {e}")

# --- Core Logging Function ---
def _log_vision_task(screen_image, template_image, template_name, traditional_result):
    """
    The core task that runs in a separate thread.
    """
    try:
        # Determine if it was a match
        matched = traditional_result.get('matched', False)
        
        # Save screenshots with descriptive names for offline analysis
        save_vision_screenshots(screen_image, template_image, template_name, matched)

    except Exception as e:
        from module.logger import logger
        logger.error(f"Failed to save vision screenshots: {e}")

def log_vision_comparison(screen_image, template_image, template_name, traditional_result):
    """
    Public function to be called from the main application.
    Starts the logging task in a new thread to avoid blocking.
    """
    # Check if LLM logging is enabled
    if not ENABLE_LLM_LOGGING:
        return
    
    # Check if we should only log matches
    if LOG_ONLY_MATCHES and not traditional_result.get('matched', False):
        return
    
    thread = threading.Thread(
        target=_log_vision_task,
        args=(screen_image, template_image, template_name, traditional_result)
    )
    thread.daemon = True # Allows main program to exit even if threads are running
    thread.start()
