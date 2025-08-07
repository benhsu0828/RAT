import gradio as gr
from langchain.tools import Tool
import os 
import requests
import json
from datetime import datetime
import PyPDF2
import docx
from io import BytesIO
import ssl
import certifi
import nest_asyncio
from langchain_community.utilities import GoogleSearchAPIWrapper

# =============================================================================
# 導入自定義模組
# =============================================================================

# 模型相關函數
from core.config import (
    get_available_model,
    generate_response,
    check_model_config,
    chatgpt_system_prompt,
    OpenAI_Model,
    openai_client
)

# 搜尋相關函數
from core.search import (
    get_search,
    get_page_content,
    check_search_config
)

# 檔案處理相關函數
from core.file_processing import (
    process_uploaded_file,
    extract_course_info
)

# 工具函數
from core.chunk import (
    num_tokens_from_string,
    chunk_texts
)

# =============================================================================
# 檔案處理和課程資訊提取
# =============================================================================


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
    - Consider that students need time to absorb and practice
    - Start with basic concepts and slowly build complexity

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

    Just output the revised answer directly. DO NOT add additional explanations or annoucement in the revised answer unless you are asked to.
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

import tiktoken


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
    draft = openai_client.chat.completions.create(
        model=OpenAI_Model,
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
    splited_answer = openai_client.chat.completions.create(
        model=OpenAI_Model,
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
    query = openai_client.chat.completions.create(
        model=OpenAI_Model,
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
        res = get_search(query, 3)
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

    revised_answer = openai_client.chat.completions.create(
        model=OpenAI_Model,
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
    reflected_answer = openai_client.chat.completions.create(
        model=OpenAI_Model,
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

# def get_revise_answer_wrapper(q, question, answer, content):
#     result = get_revise_answer(question, answer, content)
#     q.put(result)

# def get_reflect_answer_wrapper(q, question, answer):
#     result = get_reflect_answer(question, answer)
#     q.put(result)

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
                export MODEL_TYPE=openai
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
    print(f"{datetime.now()} [INFO] Checking model config...")
    check_model_config()
    print(f"{datetime.now()} [INFO] Checking Google Search API key...")
    check_search_config()
    print(f"{datetime.now()} [INFO] Starting Gradio app...")
    # 啟動 Gradio 應用
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )
