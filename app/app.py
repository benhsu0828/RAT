from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json

# Import core modules
from core.config import (
    get_available_model,
    generate_response,
    check_model_config,
    chatgpt_system_prompt,
    OpenAI_Model,
    openai_client
)

from core.search import (
    get_search,
    get_page_content,
    check_search_config
)

from core.file_processing import (
    process_uploaded_file,
    extract_course_info
)

from core.chunk import (
    num_tokens_from_string,
    chunk_texts
)

# Import main pipeline functions
from gradio_app import (
    process_course_generation,
    extract_course_info_chunked,
    combine_extracted_info,
    generate_course_outline_with_rat
)

app = Flask(__name__)
app.secret_key = 'HSU, PAO-HUA'  # Please change to a secure secret key

# Upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# Routes
# =============================================================================

@app.context_processor
def inject_model_info():
    model_info = {
        'current_model': get_available_model().upper(),
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'google_configured': bool(os.getenv('GOOGLE_API_KEY'))
    }
    return dict(model_info=model_info)


@app.route('/')
def index():
    """Home page"""
    model_info = {
        'current_model': get_available_model().upper(),
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'google_configured': bool(os.getenv('GOOGLE_API_KEY'))
    }
    return render_template('index.html', model_info=model_info)

@app.route('/course')
def course_page():
    """Course outline generation page"""
    return render_template('course.html')

@app.route('/api/generate_course', methods=['POST'])
def api_generate_course():
    """Course outline generation API"""
    try:
        # Get form data
        requirements = request.form.get('requirements', '').strip()
        # enable_search = request.form.get('enable_search') == 'true'
        enable_search = True  # Always enable search

        # Handle file upload
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
        
        # Validate input
        if not file_path and not requirements:
            return jsonify({
                'success': False,
                'error': 'Please upload a file or enter course requirements.'
            })
        
        # Process file if provided
        course_info = ""
        if file_path:
            print(f"[INFO] Processing uploaded file: {file_path}")
            
            # Create a temporary file object to simulate Gradio's file interface
            class TempFile:
                def __init__(self, path):
                    self.name = path
            
            temp_file = TempFile(file_path)
            file_content = process_uploaded_file(temp_file)
            
            if file_content and "錯誤" not in file_content:
                file_tokens = num_tokens_from_string(file_content)
                print(f"[INFO] File content tokens: {file_tokens}")
                
                if file_tokens > 4000:
                    print(f"[INFO] Large file, chunking...")
                    course_info = extract_course_info_chunked(file_content)
                else:
                    course_info = extract_course_info(file_content)
            else:
                return jsonify({
                    'success': False,
                    'error': f'File processing failed: {file_content}'
                })
            
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass
        
        # If no file was provided, use user requirements
        if not course_info and requirements:
            course_info = requirements
        
        # Generate course outline
        print(f"[INFO] Starting course outline generation with RAT...")
        base_outline, final_outline = generate_course_outline_with_rat(
            course_info, 
            requirements, 
            search_enabled=enable_search
        )
        
        # Ensure final_outline is not empty
        if not final_outline or final_outline.strip() == '':
            final_outline = base_outline  # Fallback
        
        return jsonify({
            'success': True,
            'final_outline': final_outline,  # Return only the final result
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"[ERROR] Course generation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/system_status')
def api_system_status():
    """System status API"""
    try:
        # Import model config from core.config
        try:
            from core.config import OpenAI_Model
            openai_model = OpenAI_Model
        except ImportError as e:
            print(f"[WARNING] Could not import from core.config: {e}")
            openai_model = 'gpt-3.5-turbo'  # Default value
        
        # Get current model type
        model_type = get_available_model()
        
        # Determine current model version by type
        if model_type == 'openai':
            current_model_version = openai_model
        else:
            current_model_version = 'Unknown'
        
        status = {
            'model_type': model_type,
            'current_model_version': current_model_version,   # Current model in use
            'openai_model': openai_model,                     # Configured OpenAI model
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
            'google_configured': bool(os.getenv('GOOGLE_API_KEY')),
            'google_cse_configured': bool(os.getenv('GOOGLE_CSE_ID')),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(status)
        
    except Exception as e:
        print(f"[ERROR] System status failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/system')
def system_page():
    """System info page"""
    return render_template('system.html')

@app.route('/user-manual')
def user_manual():
    return render_template('user_manual.html')

@app.context_processor
def inject_model_info():
    # Note: This overrides the earlier context_processor and only provides 'current_model'
    return dict(model_info={'current_model': 'OpenAI'})

@app.route('/test')
def test_route():
    """Test route"""
    return jsonify({'message': 'Flask is working!', 'timestamp': datetime.now().isoformat()})

# Route list viewer
@app.route('/debug/routes')
def show_routes():
    """Show all available routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
        routes.append(f"{rule.rule} [{methods}] -> {rule.endpoint}")
    return '<br>'.join(routes)


# =============================================================================
# Error handlers
# =============================================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('course_page'))

# =============================================================================
# App initialization and startup
# =============================================================================

def initialize_app():
    """Initialize the application"""
    print(f"{datetime.now()} [INFO] Initializing Flask RAT application...")
    print(f"{datetime.now()} [INFO] Checking model config...")
    check_model_config()
    print(f"{datetime.now()} [INFO] Checking Google Search API key...")
    check_search_config()
    print(f"{datetime.now()} [INFO] Flask app initialized successfully")

if __name__ == '__main__':
    initialize_app()
    app.run(
        host='0.0.0.0',
        port=7860,
        debug=True
    )