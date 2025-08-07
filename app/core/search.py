import os
import requests
import ssl
import certifi
from langchain.tools import Tool

try:
    from langchain_google_community import GoogleSearchAPIWrapper
except ImportError:
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from langchain_community.utilities import GoogleSearchAPIWrapper



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

def check_search_config():
    """檢查搜尋配置"""
    print("\n=== Google 搜尋 API 配置檢查 ===")
    
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')

    print(f"GOOGLE_API_KEY: {'✅ 已設定' if google_api_key else '❌ 未設定'}")
    print(f"GOOGLE_CSE_ID: {'✅ 已設定' if google_cse_id else '❌ 未設定'}")
    
    if google_api_key:
        print(f"API Key 前綴: {google_api_key[:15]}...")
    
    if google_cse_id:
        print(f"CSE ID: {google_cse_id}")
    
    try:
        search = GoogleSearchAPIWrapper(k=1)
        results = search.results("test", 1)
        print(f"✅ 測試成功: {results}")
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
    finally:
        print("===============================\n")

