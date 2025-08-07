from langchain.tools import Tool
import os 
import requests
import json
from datetime import datetime
import PyPDF2
import docx
from io import BytesIO
from openai import OpenAI

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
MODEL_TYPE = os.getenv('MODEL_TYPE', 'openai')
OpenAI_Model = "gpt-4o"  # OpenAI 模型名稱
openai_client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))


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
        return 'ollama'

def generate_response(messages, temperature=1.0, max_tokens=1000, model_type=None):
    """統一的回應生成函數"""
    if model_type is None:
        model_type = get_available_model()
    
    print(f"[INFO] Using model: {model_type}")
    if model_type == 'openai':
            return call_openai(messages, temperature, max_tokens)
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


# 在程式開始時呼叫
if __name__ == "__main__":
    print("=== 應用程式啟動 ===")
    print(f"當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"使用的模型類型: {MODEL_TYPE}")
    print(f"OpenAI 模型: {OpenAI_Model}")
    check_model_config()