import gradio as gr
from langchain.tools import Tool
import os 
import requests
import json
from datetime import datetime
import PyPDF2
import docx
from io import BytesIO

# =============================================================================
###new###
# =============================================================================

# from langchain_community.utilities import GoogleSearchAPIWrapper
# from langchain_community.document_loaders import AsyncHtmlLoader
# from langchain_community.document_transformers import Html2TextTransformer

try:
    # 嘗試使用新版本
    from langchain_google_community import GoogleSearchAPIWrapper
except ImportError:
    # 備用方案：使用舊版本但忽略警告
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from langchain_community.utilities import GoogleSearchAPIWrapper

import ssl
import certifi
import nest_asyncio

# 修復異步事件循環
nest_asyncio.apply()

# 配置 SSL 設定
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # 注意：這會降低安全性

# 設定環境變數
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''

# =============================================================================

os.environ["USER_AGENT"] = "RAT-App/1.0 (Retrieval-Augmented-Thoughts)"

# 模型配置
MODEL_TYPE = os.getenv('MODEL_TYPE', 'ollama')  # 可選: openai, ollama
OpenAI_Model = "gpt-4o"  # OpenAI 模型名稱
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
DEFAULT_OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')

# chatgpt_system_prompt = f'''
# You are ChatGPT, a large language model trained by OpenAI, based on the GPT-4 architecture.
# Knowledge cutoff: 2023-04
# Current date: {datetime.now().strftime('%Y-%m-%d')}
# '''

chatgpt_system_prompt = f'''
You are a Senior Course Designer and Educational Consultant with over 15 years of experience in curriculum development across various academic disciplines. You have:

**Professional Background:**
- Ph.D. in Education with specialization in Curriculum and Instruction
- Extensive experience in designing courses for universities, colleges, and professional training
- Expert knowledge in learning theories, assessment methods, and instructional design
- Published researcher in educational methodology and course effectiveness

**Core Competencies:**
- Bloom's Taxonomy application for learning objectives
- Backward design methodology for curriculum planning
- Multi-modal teaching strategies and active learning techniques
- Assessment design and rubric development
- Technology integration in education
- Cross-cultural and inclusive education practices

**Current Role:**
- Design comprehensive course outlines with clear learning progressions
- Integrate industry best practices and current trends
- Ensure alignment between objectives, content, activities, and assessments
- Provide practical teaching strategies and resource recommendations

**Communication Style:**
- Professional yet accessible language
- Evidence-based recommendations
- Structured and logical presentation
- Focus on practical implementation

Knowledge cutoff: 2023-04
Current date: {datetime.now().strftime('%Y-%m-%d')}

When designing courses, always consider:
1. **Create a well-paced course outline that balances learning speed with content depth, ensuring students have adequate time to master each concept before progressing to more complex topics
2. **Learning Pace Optimization**: Design content delivery that matches student cognitive capacity and allows for different learning speeds
3. **Progressive Difficulty**: Structure topics from foundational concepts to advanced applications with logical scaffolding
4. **Clear learning outcomes mapped to appropriate cognitive levels**
5. **Authentic assessment opportunities that align with learning pace**
6. **Real-world application and relevance**
7. **Resource accessibility and variety**
8. **Regular knowledge consolidation and review periods**
'''

# =============================================================================
# 統一的模型調用介面
# =============================================================================

def call_ollama(model_name, messages, temperature=1.0, max_tokens=1000):
    """調用 Ollama API"""
    try:
        # 構建提示
        if len(messages) >= 2:
            prompt = f"System: {messages[0]['content']}\nUser: {messages[1]['content']}\nAssistant:"
        else:
            prompt = messages[0]['content']
        
        url = f"{OLLAMA_BASE_URL}/api/generate"
        data = {
            "model": model_name,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
            "options": {
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(url, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    except Exception as e:
        raise Exception(f"Ollama error: {str(e)}")

def call_openai(messages, temperature=1.0, max_tokens=1000):
    """調用 OpenAI API"""
    try:
        from openai import OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("OPENAI_API_KEY not set")
        
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OpenAI_Model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI error: {str(e)}")

def get_available_model():
    """根據環境變數和可用性決定使用哪個模型"""
    # 檢查環境變數設定
    model_preference = os.getenv('MODEL_TYPE', '').lower()
    
    if model_preference == 'openai' and os.getenv('OPENAI_API_KEY'):
        return 'openai'
    elif model_preference == 'ollama':
        return 'ollama'
    
    # 自動檢測可用模型
    if os.getenv('OPENAI_API_KEY'):
        return 'openai'
    else:
        return 'ollama'  # 預設使用 Ollama

def generate_response(messages, temperature=1.0, max_tokens=1000, model_type=None):
    """統一的回應生成函數"""
    if model_type is None:
        model_type = get_available_model()
    
    print(f"[INFO] Using model: {model_type}")
    if model_type == 'openai':
            return call_openai(messages, temperature, max_tokens)
    elif model_type == 'ollama':
        return call_ollama(DEFAULT_OLLAMA_MODEL, messages, temperature, max_tokens)
    else:
        raise Exception(f"Unsupported model type: {model_type}")
    
def check_model_config():
    """檢查模型配置"""
    print("=== 模型配置檢查 ===")
    print(f"環境變數 MODEL_TYPE: {os.getenv('MODEL_TYPE', 'None')}")
    print(f"程式中的 MODEL_TYPE: {MODEL_TYPE}")
    print(f"實際使用的模型: {get_available_model()} {OpenAI_Model}")
    print(f"OpenAI API Key: {'已設定' if os.getenv('OPENAI_API_KEY') else '未設定'}")
    print("==================")

    """檢查 Google 搜尋 API 配置"""
    print("\n=== Google 搜尋 API 配置檢查 ===")
    
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')

    print(f"GOOGLE_API_KEY: {'✅ 已設定' if google_api_key else '❌ 未設定'}")
    print(f"GOOGLE_CSE_ID: {'✅ 已設定' if google_cse_id else '❌ 未設定'}")
    
    if google_api_key:
        print(f"API Key 前綴: {google_api_key[:15]}...")
    
    if google_cse_id:
        print(f"CSE ID: {google_cse_id}")
    
    # 檢查 GoogleSearchAPIWrapper 是否可用
    try:
        from langchain_google_community import GoogleSearchAPIWrapper
        print("✅ 新版 GoogleSearchAPIWrapper 可用")
        wrapper_available = True
    except ImportError:
        try:
            from langchain_community.utilities import GoogleSearchAPIWrapper
            print("⚠️ 使用舊版 GoogleSearchAPIWrapper")
            wrapper_available = True
        except ImportError:
            print("❌ GoogleSearchAPIWrapper 不可用")
            wrapper_available = False
    
    # 如果 API 配置完整且 wrapper 可用，進行簡單測試
    if google_api_key and google_cse_id and wrapper_available:
        print("🔍 測試 Google 搜尋功能...")
        try:
            # 進行測試
            search = GoogleSearchAPIWrapper(
                google_api_key=google_api_key,
                google_cse_id=google_cse_id,
                k=1
            )
            
            test_query = "python programming"
            results = search.results(test_query, 1)
            
            if results and len(results) > 0:
                print("✅ Google 搜尋功能測試成功")
            else:
                print("⚠️ Google 搜尋測試無結果，但 API 配置正確")
                
        except Exception as e:
            print(f"❌ Google 搜尋測試失敗: {str(e)}")
            print("   可能原因：API 金鑰無效、CSE ID 錯誤或網路問題")
    else:
        print("❌ Google 搜尋功能不可用")
        if not google_api_key:
            print("   - 缺少 GOOGLE_API_KEY 環境變數")
        if not google_cse_id:
            print("   - 缺少 GOOGLE_CSE_ID 環境變數")
        if not wrapper_available:
            print("   - GoogleSearchAPIWrapper 套件不可用")
    
    print("===============================\n")
# 在程式開始時呼叫
check_model_config()
# =============================================================================
# 原有的工具函數保持不變
# =============================================================================

from langchain.tools import Tool
from langchain_community.utilities import GoogleSearchAPIWrapper

# =============================================================================
# 檔案處理和課程資訊提取
# =============================================================================
def process_uploaded_file(file):
    #"""處理上傳的檔案"""
    if file is None:
        return ""
    
    file_content = ""
    file_name = file.name.lower()
    
    try:
        if file_name.endswith('.pdf'):
            # 處理 PDF 檔案
            with open(file.name, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    file_content += page.extract_text() + "\n"
                    
        elif file_name.endswith('.docx'):
            # 處理 Word 檔案
            doc = docx.Document(file.name)
            for paragraph in doc.paragraphs:
                file_content += paragraph.text + "\n"
                
        elif file_name.endswith('.txt'):
            # 處理文字檔案
            with open(file.name, 'r', encoding='utf-8') as txt_file:
                file_content = txt_file.read()
                
        else:
            return "不支援的檔案格式。請上傳 PDF、DOCX 或 TXT 檔案。"
            
    except Exception as e:
        return f"讀取檔案時發生錯誤: {str(e)}"
    
    return file_content

def extract_course_info(file_content):
    """從檔案內容中提取課程關鍵資訊"""
    extract_prompt = '''
    Analyze the following course document content and extract key course information:
    1. Course name and subject
    2. Learning objectives
    3. Main content areas
    4. Target learners
    5. Course level (beginner/intermediate/advanced)
    6. Any special requirements or prerequisites

    Please organize this information in a structured way for subsequent course outline generation.
    '''
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Course document content：\n{file_content}\n\n{extract_prompt}"
        }
    ]
    
    try:
        return generate_response(messages, temperature=0.3, max_tokens=1000)
    except Exception as e:
        return f"提取課程資訊失敗: {str(e)}"
    
def process_course_content_with_chunking(course_info, user_requirements):
    """處理過長的課程內容，進行分塊處理"""
    
    # 檢查總 token 數
    total_content = f"Course info：\n{course_info}\n\nUser requirements：\n{user_requirements}"
    total_tokens = num_tokens_from_string(total_content)
    
    print(f"[INFO] 總輸入 tokens: {total_tokens}")
    
    # 如果超過限制，進行分塊處理
    if total_tokens > 3000:  # 保留空間給 prompt 和輸出
        print(f"[INFO] 內容過長，進行分塊處理...")
        
        # 分塊處理課程資訊
        if num_tokens_from_string(course_info) > 2000:
            course_chunks = chunk_texts(course_info, 1500)
            
            # 對每個塊提取關鍵資訊
            extracted_info = []
            for i, chunk in enumerate(course_chunks):
                print(f"[INFO] 處理課程資訊塊 {i+1}/{len(course_chunks)}")
                chunk_info = extract_course_info(chunk)
                extracted_info.append(chunk_info)
            
            # 合併提取的資訊
            course_info = combine_extracted_info(extracted_info)
    
    return course_info, user_requirements

def combine_extracted_info(extracted_info_list):
    """合併多個提取的課程資訊"""
    combine_prompt = '''
    Merge the following multiple course information fragments into a complete, structured course description:
    
    Please integrate and remove duplicate information, retaining the most important course characteristics.
    '''
    
    combined_content = "\n\n".join([f"Fragment {i+1}:\n{info}" for i, info in enumerate(extracted_info_list)])
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"{combined_content}\n\n{combine_prompt}"
        }
    ]
    
    try:
        return generate_response(messages, temperature=0.3, max_tokens=1500)
    except Exception as e:
        print(f"合併資訊失敗: {str(e)}")
        return "\n".join(extracted_info_list)

def enhance_section_wrapper(q, course_info, section, search_content):
    """enhance_section_with_content 的 wrapper 函數"""
    result = enhance_section_with_content(course_info, section, search_content)
    q.put(result)

def format_final_outline_wrapper(q, course_info, outline):
    """format_course_outline 的 wrapper 函數"""
    result = format_course_outline(course_info, outline)
    q.put(result)

def generate_course_outline_with_rat(course_info, user_requirements, search_enabled=True):
    """使用完整 RAT 技術生成課程大綱"""
    
    # 步驟1: 處理過長內容
    processed_course_info, processed_requirements = process_course_content_with_chunking(
        course_info, user_requirements
    )
    
    # 步驟2: 生成初始大綱
    print(f"{datetime.now()} [INFO] 生成初始課程大綱...")
    initial_outline = get_course_draft(processed_course_info, processed_requirements)
    
    if not search_enabled:
        return initial_outline, initial_outline
    
    # 步驟3: RAT 式分段處理
    print(f"{datetime.now()} [INFO] 對課程大綱進行 RAT 分段處理...")
    outline_sections = split_course_outline(initial_outline)
    print(f"{datetime.now()} [INFO] 大綱分為 {len(outline_sections)} 個段落")
    
    enhanced_outline = ""
    
    # 步驟4: 逐段搜尋和優化 (RAT 核心技術)
    for i, section in enumerate(outline_sections):
        print(f"{datetime.now()} [INFO] 處理段落 {i+1}/{len(outline_sections)}...")
        enhanced_outline += "\n\n" + section
        
        # 為當前段落生成專門的搜尋查詢
        print(f"{datetime.now()} [INFO] 為段落生成搜尋查詢...")
        section_query = generate_section_query(processed_course_info, section)
        print(f">>> 段落 {i+1} 查詢: {section_query}")
        
        # 搜尋相關資源
        print(f"{datetime.now()} [INFO] 搜尋段落相關資源...")
        search_results = run_with_timeout(get_content_wrapper, 30, section_query)
        
        if search_results:
            # 使用搜尋結果優化當前段落
            LIMIT = 4
            for j, content in enumerate(search_results[:LIMIT]):
                print(f"{datetime.now()} [INFO] 使用搜尋結果優化段落 [{j+1}/{LIMIT}]...")
                
                optimized_section = run_with_timeout(
                    enhance_section_wrapper, 30,
                    processed_course_info, section, content
                )
                
                if optimized_section:
                    enhanced_outline = enhanced_outline.replace(section, optimized_section)
                    section = optimized_section  # 更新段落用於下次優化
                    print(f"{datetime.now()} [INFO] 段落優化完成 [{j+1}/{LIMIT}]")
    
    # 步驟5: 最終整合和格式化
    print(f"{datetime.now()} [INFO] 最終整合課程大綱...")
    final_outline = run_with_timeout(
        format_final_outline_wrapper, 30,
        processed_course_info, enhanced_outline
    )
    
    if not final_outline:
        final_outline = enhanced_outline
    
    print(f"{datetime.now()} [INFO] 課程大綱生成完成")
    return initial_outline, final_outline

def split_course_outline(outline):
    """智能分割課程大綱為邏輯段落"""
    split_prompt = '''
    Split the course outline into logical sections, where each section should contain a complete concept or topic.
    Use ## as a separator to divide sections.
    Keep the original content unchanged, just add separator symbols.
    '''
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Course outline：\n{outline}\n\n{split_prompt}"
        }
    ]
    
    try:
        split_result = generate_response(messages, temperature=0.3, max_tokens=2000)
        sections = [section.strip() for section in split_result.split('##') if section.strip()]
        return sections
    except Exception as e:
        print(f"智能分割失敗，使用預設分割: {str(e)}")
        # 預設分割方式
        return outline.split('\n\n')

def generate_section_query(course_info, section):
    """為特定段落生成搜尋查詢"""
    query_prompt = '''
    Based on the course information and current section content, generate a precise search query.
    The query should be able to find teaching resources, best practices, or case studies related to this section.
    
    Only output the search query, do not add other explanations.
    '''
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Course information：\n{course_info}\n\nCurrent section：\n{section}\n\n{query_prompt}"
        }
    ]
    
    try:
        return generate_response(messages, temperature=0.5, max_tokens=200)
    except Exception as e:
        return f"teaching methods {section[:50]}"

def enhance_section_with_content(course_info, section, search_content):
    """使用搜尋內容優化段落"""
    enhance_prompt = '''
    Based on the searched relevant teaching resources, improve and enrich the current course outline section.
    
    Improvement focus:
    1. Add specific teaching activities and methods
    2. Supplement relevant learning resources
    3. Include practical cases or exercises
    4. Optimize learning objective descriptions
    
    Maintain the core structure of the section while significantly improving content quality.
    '''
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Course information：\n{course_info}\n\nCurrent section：\n{section}\n\nSearch resources：\n{search_content}\n\n{enhance_prompt}"
        }
    ]
    
    try:
        return generate_response(messages, temperature=0.6, max_tokens=1500)
    except Exception as e:
        print(f"段落優化失敗: {str(e)}")
        return section

def get_course_draft(course_info, user_requirements):
    """生成基礎課程大綱"""
    course_prompt = '''
    Based on the provided course information and user requirements, generate a detailed WEEKLY course outline for a 16-week semester. Please structure it as follows:

    **IMPORTANT WEEKLY FORMAT REQUIREMENTS:**
    - Organize content by weeks (Week 1, Week 2, etc.)
    - Each week should have specific learning topics and activities
    - Complex topics can span multiple weeks (e.g., arrays taught across Week 1 and Week 2)
    - Include both theoretical concepts and practical implementations
    - Provide specific subtopics and activities for each week

    **WEEKLY STRUCTURE TEMPLATE:**
    
    ## Week X: [Main Topic/Chapter]
    **Learning Objectives:**
    - [Specific learning goal 1]
    - [Specific learning goal 2]
    
    **Content Coverage:**
    - [Subtopic 1]: [Brief description]
    - [Subtopic 2]: [Brief description]
    - [Subtopic 3]: [Brief description]
    
    **Activities & Practice:**
    - [Lab exercise or coding practice]
    - [Assignment or project work]
    
    **Assessment:**
    - [Quiz, assignment, or evaluation method]

    **Example Format:**
    
    ## Week 1: Arrays - Fundamentals
    **Learning Objectives:**
    - Understand array concepts and memory allocation
    - Learn array declaration and initialization
    
    **Content Coverage:**
    - Array definition and characteristics
    - One-dimensional array syntax
    - Memory layout and indexing
    - Basic array operations (input/output)
    
    **Activities & Practice:**
    - Lab: Basic array exercises
    - Practice: Array input and display programs
    
    **Assessment:**
    - Programming Quiz 1: Array basics
    
    ## Week 2: Arrays - Advanced Operations
    **Learning Objectives:**
    - Master array manipulation techniques
    - Implement array algorithms
    
    **Content Coverage:**
    - Array searching algorithms (linear search)
    - Array sorting basics (bubble sort)
    - Multi-dimensional arrays introduction
    - Array functions and parameter passing
    
    **Activities & Practice:**
    - Lab: Implement search and sort algorithms
    - Assignment 1: Array processing program
    
    **Assessment:**
    - Programming Assignment 1 due

    Please generate a complete 16-week outline following this format, ensuring:
    1. **Logical Progression**: Topics build upon each other
    2. **Practical Focus**: Each week includes hands-on coding
    3. **Flexible Pacing**: Complex topics can span multiple weeks
    4. **Regular Assessment**: Include quizzes, assignments, and projects
    5. **Real Application**: Connect theory to practical programming
    '''
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Course information：\n{course_info}\n\nUser requirements：\n{user_requirements}\n\n{course_prompt}"
        }
    ]
    
    try:
        return generate_response(messages, temperature=0.7, max_tokens=3500)  # 增加 token 數
    except Exception as e:
        return f"生成基礎大綱失敗: {str(e)}"

def generate_course_search_query(course_info, user_requirements):
    """生成課程相關的搜尋查詢"""
    query_prompt = '''
    Based on the course information and user requirements, generate an effective search query to find relevant course design resources, teaching syllabi, or similar course information.
    The query should be concise but specific, able to find high-quality educational resources.

    Only output the search query, do not add other explanations.
    '''
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Course information：\n{course_info}\n\nUser requirements：\n{user_requirements}\n\n{query_prompt}"
        }
    ]
    
    try:
        return generate_response(messages, temperature=0.5, max_tokens=200)
    except Exception as e:
        return f"course curriculum syllabus {course_info[:100]}"

def generate_additional_search_queries(course_info):
    """生成額外的搜尋查詢"""
    additional_prompt = '''
    Based on the course information, generate 2 additional search queries to find relevant:
    1. Teaching methods and best practices
    2. Learning resources and reference materials

    One query per line, do not add numbering or other formatting.
    '''
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Course information：\n{course_info}\n\n{additional_prompt}"
        }
    ]
    
    try:
        result = generate_response(messages, temperature=0.6, max_tokens=300)
        return [query.strip() for query in result.split('\n') if query.strip()]
    except Exception as e:
        return []

def enhance_course_outline(course_info, base_outline, search_results):
    """使用搜尋結果增強課程大綱"""
    enhance_prompt = '''
    Based on the searched relevant educational resources and course information, improve and enhance the existing course outline. Please:

    1. **Content Enrichment**: Add excellent teaching concepts and methods from search results
    2. **Structure Optimization**: Reference structural designs from similar courses
    3. **Resource Supplementation**: Add relevant learning resources and reference materials
    4. **Practical Activities**: Integrate real cases and exercise activities
    5. **Assessment Improvement**: Improve evaluation methods and standards

    Maintain the core structure of the original outline while significantly enhancing content depth and breadth.
    Output in Markdown format.
    '''
    
    # 整合搜尋結果
    search_content = "\n\n".join([f"Reference material {i+1}:\n{content}" for i, content in enumerate(search_results)])
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Original course information：\n{course_info}\n\nBase outline：\n{base_outline}\n\nSearched reference materials：\n{search_content}\n\n{enhance_prompt}"
        }
    ]
    
    try:
        return generate_response(messages, temperature=0.6, max_tokens=3000)
    except Exception as e:
        print(f"增強大綱失敗: {str(e)}")
        return base_outline

def format_course_outline(course_info, outline):
    """最終格式化課程大綱"""
    format_prompt = '''
    Perform final formatting and structural adjustment of the course outline, ensuring:

    1. **Clear Title Hierarchy**: Use appropriate Markdown headings
    2. **Logical Sequence**: Ensure content flows smoothly and progressively
    3. **Practical Details**: Include specific learning activities and time arrangements
    4. **Professional Presentation**: Suitable for teaching and learning use

    Output a complete, professional course outline.
    '''
    
    messages = [
        {
            "role": "system",
            "content": chatgpt_system_prompt
        },
        {
            "role": "user",
            "content": f"Course information：\n{course_info}\n\nCourse outline：\n{outline}\n\n{format_prompt}"
        }
    ]
    
    try:
        return generate_response(messages, temperature=0.4, max_tokens=3000)
    except Exception as e:
        print(f"格式化失敗: {str(e)}")
        return outline
# =============================================================================
# Google 搜索工具
# =============================================================================

def get_search(query:str="", k:int=1):
    search = GoogleSearchAPIWrapper(k=k)
    def search_results(query):
        return search.results(query, k)
    tool = Tool(
        name="Google Search Snippets",
        description="Search Google for recent results.",
        func=search_results,
    )
    ref_text = tool.run(query)
    if 'Result' not in ref_text[0].keys():
        return ref_text
    else:
        return None

def get_page_content(link:str):
    """安全的網頁內容抓取函數"""
    try:
        # 方法1: 使用 requests 替代 AsyncHtmlLoader
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # 使用 requests 抓取，忽略 SSL 驗證
        response = requests.get(
            link, 
            headers=headers, 
            timeout=10,
            verify=False,  # 忽略 SSL 驗證
            allow_redirects=True
        )
        
        if response.status_code == 200:
            # 簡單的 HTML 清理
            content = response.text
            
            # 移除 HTML 標籤的簡單方法
            import re
            # 移除 script 和 style 標籤
            content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
            # 移除 HTML 標籤
            content = re.sub(r'<[^>]+>', '', content)
            # 清理多餘的空白
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content[:5000]  # 限制長度
        else:
            print(f"HTTP Error: {response.status_code} for {link}")
            return None
            
    except Exception as e:
        print(f"Error fetching {link}: {str(e)}")
        
        # 備用方案：使用更簡單的方法
        try:
            import urllib.request
            import urllib.error
            
            # 創建忽略 SSL 的上下文
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(
                link,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; RAT-Bot/1.0)'}
            )
            
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                # 簡單清理
                import re
                content = re.sub(r'<[^>]+>', '', content)
                content = re.sub(r'\s+', ' ', content).strip()
                return content[:5000]
                
        except Exception as e2:
            print(f"Backup method also failed for {link}: {str(e2)}")
            return None
    #舊的
    # loader = AsyncHtmlLoader([link])
    # docs = loader.load()
    # html2text = Html2TextTransformer()
    # docs_transformed = html2text.transform_documents(docs)
    # if len(docs_transformed) > 0:
    #     return docs_transformed[0].page_content
    # else:
    #     return None

import tiktoken
def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def chunk_text_by_sentence(text, chunk_size=2048):
    """Chunk the $text into sentences with less than 2k tokens."""
    sentences = text.split('. ')
    chunked_text = []
    curr_chunk = []
    # 逐句添加文本片段，确保每个段落都小于2k个token
    for sentence in sentences:
        if num_tokens_from_string(". ".join(curr_chunk)) + num_tokens_from_string(sentence) + 2 <= chunk_size:
            curr_chunk.append(sentence)
        else:
            chunked_text.append(". ".join(curr_chunk))
            curr_chunk = [sentence]
    # 添加最后一个片段
    if curr_chunk:
        chunked_text.append(". ".join(curr_chunk))
    return chunked_text[0]

def chunk_text_front(text, chunk_size = 2048):
    '''
    get the first `trunk_size` token of text
    '''
    chunked_text = ""
    tokens = num_tokens_from_string(text)
    if tokens < chunk_size:
        return text
    else:
        ratio = float(chunk_size) / tokens
        char_num = int(len(text) * ratio)
        return text[:char_num]

def chunk_texts(text, chunk_size = 2048):
    '''
    trunk the text into n parts, return a list of text
    [text, text, text]
    '''
    tokens = num_tokens_from_string(text)
    if tokens < chunk_size:
        return [text]
    else:
        texts = []
        n = int(tokens/chunk_size) + 1
        # 计算每个部分的长度
        part_length = len(text) // n
        # 如果不能整除，则最后一个部分会包含额外的字符
        extra = len(text) % n
        parts = []
        start = 0

        for i in range(n):
            # 对于前extra个部分，每个部分多分配一个字符
            end = start + part_length + (1 if i < extra else 0)
            parts.append(text[start:end])
            start = end
        return parts
    
from datetime import datetime

from openai import OpenAI
import openai
import os

chatgpt_system_prompt = f'''
You are ChatGPT, a large language model trained by OpenAI, based on the GPT-4 architecture.
Knowledge cutoff: 2023-04
Current date: {datetime.now().strftime('%Y-%m-%d')}
'''

def get_draft(question):
    # Getting the draft answer
    draft_prompt = '''
IMPORTANT:
Try to answer this question/instruction with step-by-step thoughts and make the answer more structural.
Use `\n\n` to split the answer into several paragraphs.
Just respond to the instruction directly. DO NOT add additional explanations or introducement in the answer unless you are asked to.
'''
    # openai_client = OpenAI(api_key=openai.api_key)
    openai_client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
    draft = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": chatgpt_system_prompt
            },
            {
                "role": "user",
                "content": f"{question}" + draft_prompt
            }
        ],
        temperature = 1.0
    ).choices[0].message.content
    return draft

def split_draft(draft, split_char = '\n\n'):
    # 将draft切分为多个段落
    # split_char: '\n\n'
    paragraphs = draft.split(split_char)
    draft_paragraphs = [para for para in paragraphs if len(para)>5]
    # print(f"The draft answer has {len(draft_paragraphs)}")
    return draft_paragraphs

def split_draft_openai(question, answer, NUM_PARAGRAPHS = 4):
    split_prompt = f'''
Split the answer of the question into multiple paragraphs with each paragraph containing a complete thought.
The answer should be splited into less than {NUM_PARAGRAPHS} paragraphs.
Use ## as splitting char to seperate the paragraphs.
So you should output the answer with ## to split the paragraphs.
**IMPORTANT**
Just output the query directly. DO NOT add additional explanations or introducement in the answer unless you are asked to.
'''
    openai_client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
    splited_answer = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": chatgpt_system_prompt
            },
            {
                "role": "user",
                "content": f"##Question: {question}\n\n##Response: {answer}\n\n##Instruction: {split_prompt}"
            }
        ],
        temperature = 1.0
    ).choices[0].message.content
    split_draft_paragraphs = split_draft(splited_answer, split_char = '##')
    return split_draft_paragraphs

def get_query(question, answer):
    query_prompt = '''
I want to verify the content correctness of the given question, especially the last sentences.
Please summarize the content with the corresponding question.
This summarization will be used as a query to search with Bing search engine.
The query should be short but need to be specific to promise Bing can find related knowledge or pages.
Try to make the query as relevant as possible to the last few sentences in the content.
**IMPORTANT**
Just output the query directly. DO NOT add additional explanations or introducement in the answer unless you are asked to.
'''
    # openai_client = OpenAI(api_key = openai.api_key)
    openai_client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
    query = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": chatgpt_system_prompt
            },
            {
                "role": "user",
                "content": f"##Question: {question}\n\n##Content: {answer}\n\n##Instruction: {query_prompt}"
            }
        ],
        temperature = 1.0
    ).choices[0].message.content
    return query

def get_content(query):
    """獲取網頁內容"""
    try:
        # 搜尋結果
        res = get_search(query, 5)
        if not res:
            print(">>> No Google Search Result found")
            return None
        
        search_results = res[0]
        link = search_results['link']
        print(f">>> Fetching content from: {link}")
        
        # 使用安全的內容抓取
        content = get_page_content(link)
        
        if not content:
            print(f">>> No content found for {link}")
            return None
        
        # 分塊處理
        chunked_texts = chunk_texts(content, 1500)
        cleaned_texts = [text.replace('\n', ' ').strip() for text in chunked_texts if text.strip()]
        
        return cleaned_texts[:3]  # 限制返回數量
        
    except Exception as e:
        print(f">>> Content retrieval error: {str(e)}")
        return None
    # res = get_search(query, 1)
    # if not res:
    #     print(">>> No good Google Search Result was found")
    #     return None
    # search_results = res[0]
    # link = search_results['link'] # title, snippet
    # res = get_page_content(link)
    # if not res:
    #     print(f">>> No content was found in {link}")
    #     return None
    # retrieved_text = res
    # trunked_texts = chunk_texts(retrieved_text, 1500)
    # trunked_texts = [trunked_text.replace('\n', " ") for trunked_text in trunked_texts]
    # return trunked_texts

def get_revise_answer(question, answer, content):
    revise_prompt = '''
I want to revise the answer according to retrieved related text of the question in WIKI pages.
You need to check whether the answer is correct.
If you find some errors in the answer, revise the answer to make it better.
If you find some necessary details are ignored, add it to make the answer more plausible according to the related text.
If you find the answer is right and do not need to add more details, just output the original answer directly.
**IMPORTANT**
Try to keep the structure (multiple paragraphs with its subtitles) in the revised answer and make it more structual for understanding.
Add more details from retrieved text to the answer.
Split the paragraphs with \n\n characters.
Just output the revised answer directly. DO NOT add additional explanations or annoucement in the revised answer unless you are asked to.
'''
    # openai_client = OpenAI(api_key = openai.api_key)
    openai_client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
    revised_answer = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
                {
                    "role": "system",
                    "content": chatgpt_system_prompt
                },
                {
                    "role": "user",
                    "content": f"##Existing Text in Wiki Web: {content}\n\n##Question: {question}\n\n##Answer: {answer}\n\n##Instruction: {revise_prompt}"
                }
            ],
            temperature = 1.0
    ).choices[0].message.content
    return revised_answer

def get_reflect_answer(question, answer):
    reflect_prompt = '''
Give a title for the answer of the question.
And add a subtitle to each paragraph in the answer and output the final answer using markdown format. 
This will make the answer to this question look more structured for better understanding.
**IMPORTANT**
Try to keep the structure (multiple paragraphs with its subtitles) in the response and make it more structual for understanding.
Split the paragraphs with \n\n characters.
Just output the revised answer directly. DO NOT add additional explanations or annoucement in the revised answer unless you are asked to.
'''
    openai_client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
    reflected_answer = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
                {
                    "role": "system",
                    "content": chatgpt_system_prompt
                },
                {
                    "role": "user",
                    "content": f"##Question:\n{question}\n\n##Answer:\n{answer}\n\n##Instruction:\n{reflect_prompt}"
                }
            ],
            temperature = 1.0
    ).choices[0].message.content
    return reflected_answer

def get_query_wrapper(q, question, answer):
    result = get_query(question, answer)
    q.put(result)  # 将结果放入队列

def get_content_wrapper(q, query):
    result = get_content(query)
    q.put(result)  # 将结果放入队列

def get_revise_answer_wrapper(q, question, answer, content):
    result = get_revise_answer(question, answer, content)
    q.put(result)

def get_reflect_answer_wrapper(q, question, answer):
    result = get_reflect_answer(question, answer)
    q.put(result)

from multiprocessing import Process, Queue
def run_with_timeout(func, timeout, *args, **kwargs):
    q = Queue()  # 创建一个Queue对象用于进程间通信
    # 创建一个进程来执行传入的函数，将Queue和其他*args、**kwargs作为参数传递
    p = Process(target=func, args=(q, *args), kwargs=kwargs)
    p.start()
    # 等待进程完成或超时
    p.join(timeout)
    if p.is_alive():
        print(f"{datetime.now()} [INFO] Function {str(func)} running timeout ({timeout}s), terminating...")
        p.terminate()  # 终止进程
        p.join()  # 确保进程已经终止
        result = None  # 超时情况下，我们没有结果
    else:
        print(f"{datetime.now()} [INFO] Function {str(func)} executed successfully.")
        result = q.get()  # 从队列中获取结果
    return result

from difflib import unified_diff
from IPython.display import display, HTML

def generate_diff_html(text1, text2):
    diff = unified_diff(text1.splitlines(keepends=True),
                        text2.splitlines(keepends=True),
                        fromfile='text1', tofile='text2')

    diff_html = ""
    for line in diff:
        if line.startswith('+'):
            diff_html += f"<div style='color:green;'>{line.rstrip()}</div>"
        elif line.startswith('-'):
            diff_html += f"<div style='color:red;'>{line.rstrip()}</div>"
        elif line.startswith('@'):
            diff_html += f"<div style='color:blue;'>{line.rstrip()}</div>"
        else:
            diff_html += f"{line.rstrip()}<br>"
    return diff_html

newline_char = '\n'

def rat(question):
    print(f"{datetime.now()} [INFO] Generating draft...")
    draft = get_draft(question)
    print(f"{datetime.now()} [INFO] Return draft.")
    # print(f"##################### DRAFT #######################")
    # print(draft)
    # print(f"#####################  END  #######################")

    print(f"{datetime.now()} [INFO] Processing draft ...")
    # draft_paragraphs = split_draft(draft)
    draft_paragraphs = split_draft_openai(question, draft)
    print(f"{datetime.now()} [INFO] Draft is splitted into {len(draft_paragraphs)} sections.")
    answer = ""
    for i, p in enumerate(draft_paragraphs):
        # print(str(i)*80)
        print(f"{datetime.now()} [INFO] Revising {i+1}/{len(draft_paragraphs)} sections ...")
        answer = answer + '\n\n' + p
        # print(f"[{i}/{len(draft_paragraphs)}] Original Answer:\n{answer.replace(newline_char, ' ')}")

        # query = get_query(question, answer)
        print(f"{datetime.now()} [INFO] Generating query ...")
        res = run_with_timeout(get_query_wrapper, 30, question, answer)
        if not res:
            print(f"{datetime.now()} [INFO] Generating query timeout, skipping...")
            continue
        else:
            query = res
        print(f">>> {i}/{len(draft_paragraphs)} Query: {query.replace(newline_char, ' ')}")

        print(f"{datetime.now()} [INFO] Crawling network pages ...")
        # content = get_content(query)
        res = run_with_timeout(get_content_wrapper, 30, query)
        if not res:
            print(f"{datetime.now()} [INFO] Parsing network pages timeout, skipping ...")
            continue
        else:
            content = res

        LIMIT = 2
        for j, c in enumerate(content):
            if  j >= LIMIT: # limit rge number of network pages
                break
            print(f"{datetime.now()} [INFO] Revising answers with retrieved network pages...[{j}/{min(len(content),LIMIT)}]")
            # answer = get_revise_answer(question, answer, c)
            res = run_with_timeout(get_revise_answer_wrapper, 30, question, answer, c)
            if not res:
                print(f"{datetime.now()} [INFO] Revising answers timeout, skipping ...")
                continue
            else:
                diff_html = generate_diff_html(answer, res)
                display(HTML(diff_html))
                answer = res
            print(f"{datetime.now()} [INFO] Answer revised [{j}/{min(len(content),3)}]")
        # print(f"[{i}/{len(draft_paragraphs)}] REVISED ANSWER:\n {answer.replace(newline_char, ' ')}")
        # print()
    res = run_with_timeout(get_reflect_answer_wrapper, 30, question, answer)
    if not res:
        print(f"{datetime.now()} [INFO] Reflecting answers timeout, skipping next steps...")
    else:
        answer = res
    return draft, answer

# =============================================================================
# 在原有程式碼後添加清除函數
# =============================================================================

def clear_func():
    return "", "", ""

def clear_course_func():
    return None, "", "", ""

# =============================================================================
# Gradio 介面
# =============================================================================

page_title = "RAT: AI Course Outline Generation System"
page_md = """
# RAT: AI Course Outline Generation System

With google search and file analysis, automatically generate professional course outlines.

Now model is: """ + get_available_model().upper() + """

---

## 📋 System Features

### 🎯 **General Q&A (RAT)**
- Intelligent draft generation
- Web information retrieval
- Multi-round answer optimization
- Structured responses

### 📚 **Course Outline Generation**
- File analysis (PDF/DOCX/TXT)
- Web resource search
- Professional outline design
- Multi-stage optimization

---
"""

def process_course_generation(file, requirements, enable_search):
    """增強版課程大綱生成主函數"""
    if file is None and not requirements.strip():
        return "⚠️ Please upload a course document or enter course requirements.", ""
    
    # 處理上傳的檔案（支援大檔案）
    course_info = ""
    if file is not None:
        print(f"[INFO] 處理上傳檔案: {file.name}")
        file_content = process_uploaded_file(file)
        
        if file_content and "錯誤" not in file_content:
            # 檢查檔案大小，如果太大則分塊處理
            file_tokens = num_tokens_from_string(file_content)
            print(f"[INFO] 檔案內容 tokens: {file_tokens}")
            
            if file_tokens > 4000:
                print(f"[INFO] 檔案內容過長，進行分塊提取...")
                course_info = extract_course_info_chunked(file_content)
            else:
                course_info = extract_course_info(file_content)
        else:
            return f"❌ File processing failed: {file_content}", ""

    # 如果沒有檔案，使用用戶需求作為課程資訊
    if not course_info and requirements.strip():
        course_info = requirements
    
    # 使用增強的 RAT 技術生成課程大綱
    try:
        print(f"[INFO] 開始使用 RAT 技術生成課程大綱...")
        base_outline, final_outline = generate_course_outline_with_rat(
            course_info, 
            requirements, 
            search_enabled=enable_search
        )
        return base_outline, final_outline
    except Exception as e:
        return f"❌ Error occurred: {str(e)}", ""

def extract_course_info_chunked(file_content):
    """分塊提取課程資訊"""
    chunks = chunk_texts(file_content, 2000)
    extracted_parts = []
    
    for i, chunk in enumerate(chunks):
        print(f"[INFO] 提取塊 {i+1}/{len(chunks)} 的課程資訊...")
        part_info = extract_course_info(chunk)
        extracted_parts.append(part_info)
    
    # 合併所有提取的資訊
    return combine_extracted_info(extracted_parts)

# =============================================================================
# Main Gradio Interface - English Version
# =============================================================================

with gr.Blocks(
    title=page_title,
    theme=gr.themes.Soft(),
    css="""
    /* 導入專業字體 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap');
    
    /* 全域字體設定 - 使用更銳利的商務字體 */
    * {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* Gradio 容器整體字體 */
    .gradio-container {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* 標題字體 - 使用更銳利的字體 */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
    }
    
    /* 按鈕字體 */
    button {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0 !important;
    }
    
    /* 輸入框和文字框字體 */
    input, textarea {
        font-family: 'Roboto', 'Consolas', 'Monaco', 'Courier New', monospace !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
    }
    
    /* 標籤字體 */
    label {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* Markdown 內容字體 */
    .markdown {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* 程式碼字體 */
    code, pre {
        font-family: 'Consolas', 'Monaco', 'Courier New', 'Roboto Mono', monospace !important;
        font-size: 13px !important;
    }
    
    /* 主要標題區域 */
    .main-header { 
        text-align: center; 
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    .main-header h1 {
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    
    /* 功能區塊 */
    .feature-box {
        border: 1px solid #e1e5eb;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* 狀態顏色 */
    .status-success { 
        color: #28a745; 
        font-weight: bold;
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    .status-error { 
        color: #dc3545; 
        font-weight: bold;
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    .status-warning { 
        color: #ffc107; 
        font-weight: bold;
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* Tab 標籤字體 */
    .tab-nav button {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* 側邊欄字體 */
    .gr-box {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* 範例區域字體 */
    .gr-examples {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* 資訊框字體 */
    .gr-info {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    
    /* 頁腳字體 */
    .footer {
        font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }
    """
) as demo:
    
    gr.HTML(f"""
    <div class="main-header">
        <h1>🧠 RAT: Retrieval-Augmented Thoughts</h1>
        <p>Intelligent Retrieval-Augmented Thinking System | Current Model: <strong>{get_available_model().upper()}</strong></p>
    </div>
    """)
    
    with gr.Tabs():
        
        # =============================================================================
        # Tab 1: Course Outline Generation
        # =============================================================================
        with gr.Tab("📚 Course Outline Generation", elem_id="course-tab"):
            gr.Markdown("""
            ### 🎯 Feature Description
            Upload course-related documents or input requirements, the system will automatically search web resources and generate professional course outlines
            """)
            
            with gr.Row():
                with gr.Column(scale=1, elem_classes="feature-box"):
                    gr.Markdown("#### 📁 Input Settings")
                    
                    file_upload = gr.File(
                        label="📎 Upload Course Document",
                        file_types=[".pdf", ".docx", ".txt"],
                        type="filepath",
                        height=100
                    )
                    
                    requirements_box = gr.Textbox(
                        label="📝 Course Requirements Description",
                        placeholder="Please describe your course objectives, audience, duration, key content and other requirements in detail...\n\nExample:\n• Python Programming Fundamentals Course\n• For first-year university students\n• 16-week course including basic syntax, data structures, project implementation",
                        lines=6,
                        max_lines=10
                    )
                    
                    with gr.Row():
                        enable_search = gr.Checkbox(
                            label="🌐 Enable Web Search Enhancement",
                            value=True,
                            info="Search relevant teaching resources to enrich course content"
                        )
                        
                    with gr.Row():
                        generate_course_btn = gr.Button(
                            "🚀 Generate Course Outline",
                            variant="primary",
                            size="lg"
                        )
                        clear_course_btn = gr.Button(
                            "🗑️ Clear",
                            variant="secondary"
                        )
                
                with gr.Column(scale=2):
                    with gr.Tabs():
                        with gr.Tab("📋 Basic Outline"):
                            gr.Markdown("#### 📋 Basic Course Outline")
                            base_outline_box = gr.Textbox(
                                placeholder="Basic weekly course outline will be displayed here...",
                                lines=20,
                                max_lines=25,
                                interactive=True,  # 允許用戶選取文字
                                show_copy_button=False, 
                            )
                        
                        with gr.Tab("✨ Enhanced Outline"):
                            gr.Markdown("#### ✨ Enhanced Course Outline")
                            final_outline_box = gr.Textbox(
                                placeholder="Enhanced weekly course outline with web resources will be displayed here...",
                                lines=20,
                                max_lines=25,
                                interactive=True,
                                show_copy_button=False,
                            )
            
            # Course Examples
            with gr.Accordion("💡 Usage Examples", open=False):
                course_examples = gr.Examples(
                    examples=[
                        ["Python Programming Fundamentals Course for first-year university students, 16-week course including basic syntax, data structures, algorithms, GUI programming and project implementation"],
                        ["Machine Learning Fundamentals Course for professionals with programming background, 12-week online course covering supervised learning, unsupervised learning and deep learning"],
                        ["Digital Marketing Strategy Course for business executives, 8-week practical course including SEO, social media, content marketing and data analytics"],
                        ["Data Science Project Implementation, graduate level, combining theory and practice, including data collection, cleaning, analysis, visualization and model construction"],
                        ["Full-Stack Web Development Course, 16-week course from HTML/CSS basics to React frontend and Node.js backend development"],
                    ],
                    inputs=[requirements_box],
                    label="Click examples to get started quickly"
                )
            
            generate_course_btn.click(
                fn=process_course_generation,
                inputs=[file_upload, requirements_box, enable_search],
                outputs=[base_outline_box, final_outline_box],
                show_progress=True
            )
            
            clear_course_btn.click(
                fn=clear_course_func,
                outputs=[file_upload, requirements_box, base_outline_box, final_outline_box]
            )
        
        # =============================================================================
        # Tab 2: System Information
        # =============================================================================
        with gr.Tab("⚙️ System Information", elem_id="info-tab"):
            gr.Markdown("""
            ### 📊 System Status
            """)
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown(f"""
                    #### 🤖 Model Configuration
                    - **Current Model**: {get_available_model().upper()}
                    - **OpenAI API**: {'✅ Configured' if os.getenv('OPENAI_API_KEY') else '❌ Not Configured'}
                    - **Google Search API**: {'✅ Configured' if os.getenv('GOOGLE_API_KEY') else '❌ Not Configured'}
                    
                    #### 🔍 RAT Processing Flow
                    1. **Draft Generation**: Generate initial response based on the question
                    2. **Smart Segmentation**: Break down answers into logical paragraphs
                    3. **Query Generation**: Generate search queries for each segment
                    4. **Web Retrieval**: Search relevant information for verification
                    5. **Answer Optimization**: Integrate retrieved information to improve answers
                    6. **Final Formatting**: Present final results in structured format
                    """)
                
                with gr.Column():
                    gr.Markdown("""
                    #### 📚 Course Outline Generation Flow
                    1. **File Analysis**: Extract key information from uploaded documents
                    2. **Requirements Understanding**: Analyze user's course requirements
                    3. **Basic Outline**: Generate initial course structure
                    4. **Resource Search**: Find relevant teaching resources
                    5. **Content Enhancement**: Optimize outline by integrating search results
                    6. **Professional Formatting**: Generate standardized course outline
                    
                    #### 📁 Supported File Formats
                    - **PDF** (.pdf) - Academic papers, course syllabi
                    - **Word** (.docx) - Course plans, teaching documents
                    - **Text Files** (.txt) - Plain text course materials
                    """)
            
            with gr.Accordion("🔧 Advanced Settings", open=False):
                gr.Markdown("""
                #### Environment Variables Configuration
                ```bash
                # Model Settings
                export MODEL_TYPE=openai  # or ollama
                export OPENAI_API_KEY="your-openai-key"
                
                # Google Search Settings
                export GOOGLE_API_KEY="your-google-key"
                export GOOGLE_CSE_ID="your-cse-id"
                
                # System Parameter Adjustments
                export RAT_TIMEOUT=30
                export RAT_CONTENT_LIMIT=2
                ```
                
                #### Performance Optimization Recommendations
                - **Memory**: Recommended 8GB+ (if using Ollama)
                - **Network**: Stable internet connection for API calls
                - **Concurrency**: System supports timeout handling and error recovery
                """)

    # =============================================================================
    # 頁腳資訊
    # =============================================================================
    gr.HTML("""
    <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
        <p><strong>🧠 RAT: Retrieval-Augmented Thoughts System</strong></p>
        <p>Intelligent Retrieval-Augmented Thinking System - Powerful tool combining AI reasoning with web search</p>
        <p><small>Version 2.0 | Supports Course Outline Generation & Intelligent Q&A</small></p>
    </div>
    """)

# =============================================================================
# 啟動應用
# =============================================================================

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )
