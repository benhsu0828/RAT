import PyPDF2
import docx
from .config import generate_response, chatgpt_system_prompt

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
    