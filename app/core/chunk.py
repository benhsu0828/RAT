import tiktoken
from multiprocessing import Process, Queue
from datetime import datetime

def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

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
