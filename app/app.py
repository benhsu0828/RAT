from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json

# 導入您現有的核心模組
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

# 導入您的主要函數
from gradio_app import (
    process_course_generation,
    extract_course_info_chunked,
    combine_extracted_info,
    generate_course_outline_with_rat
)

app = Flask(__name__)
app.secret_key = 'HSU, PAO-HUA'  # 請更改為安全的密鑰

# 設定檔案上傳
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 限制

# 確保上傳目錄存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# 路由定義
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
    """主頁面"""
    model_info = {
        'current_model': get_available_model().upper(),
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'google_configured': bool(os.getenv('GOOGLE_API_KEY'))
    }
    return render_template('index.html', model_info=model_info)

@app.route('/course')
def course_page():
    """課程大綱生成頁面"""
    return render_template('course.html')

@app.route('/api/generate_course', methods=['POST'])
def api_generate_course():
    """課程大綱生成 API"""
    try:
        # 獲取表單資料
        requirements = request.form.get('requirements', '').strip()
        enable_search = request.form.get('enable_search') == 'true'
        
        # 處理檔案上傳
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
        
        # 檢查輸入
        if not file_path and not requirements:
            return jsonify({
                'success': False,
                'error': 'Please upload a file or enter course requirements.'
            })
        
        # 處理檔案
        course_info = ""
        if file_path:
            print(f"[INFO] Processing uploaded file: {file_path}")
            
            # 創建臨時檔案物件來模擬 Gradio 的檔案格式
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
            
            # 清理上傳的檔案
            try:
                os.remove(file_path)
            except:
                pass
        
        # 如果沒有檔案，使用用戶需求
        if not course_info and requirements:
            course_info = requirements
        
        # 生成課程大綱
        print(f"[INFO] Starting course outline generation with RAT...")
        base_outline, final_outline = generate_course_outline_with_rat(
            course_info, 
            requirements, 
            search_enabled=enable_search
        )
        
        # 🔥 確保 final_outline 不為空
        if not final_outline or final_outline.strip() == '':
            final_outline = base_outline  # 備用方案
        
        return jsonify({
            'success': True,
            'final_outline': final_outline,  # 🔥 只返回最終結果
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
    """系統狀態 API"""
    try:
        #從 core.config 導入模型配置
        try:
            from core.config import OpenAI_Model
            openai_model = OpenAI_Model
        except ImportError as e:
            print(f"[WARNING] Could not import from core.config: {e}")
            openai_model = 'gpt-3.5-turbo'  # 默認值
        
        # 獲取當前使用的模型類型
        model_type = get_available_model()
        
        # 根據模型類型確定當前使用的模型版本
        if model_type == 'openai':
            current_model_version = openai_model
        else:
            current_model_version = 'Unknown'
        
        status = {
            'model_type': model_type,
            'current_model_version': current_model_version,  # 🔥 當前使用的模型
            'openai_model': openai_model,  # 🔥 配置的 OpenAI 模型
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
    """系統資訊頁面"""
    return render_template('system.html')

@app.route('/test')
def test_route():
    """測試路由"""
    return jsonify({'message': 'Flask is working!', 'timestamp': datetime.now().isoformat()})

# 添加路由列表查看器
@app.route('/debug/routes')
def show_routes():
    """顯示所有可用路由"""
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
        routes.append(f"{rule.rule} [{methods}] -> {rule.endpoint}")
    return '<br>'.join(routes)


# =============================================================================
# 錯誤處理
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
# 應用初始化和啟動
# =============================================================================

def initialize_app():
    """初始化應用"""
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