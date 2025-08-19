# 🧠 RAT: Retrieval-Augmented Thoughts System
[中文](./README.md) | [English](./README.en.md)

**Intelligent Retrieval-Augmented Thinking System** - Combining OpenAI ChatGPT and Web Search for Course Outline Generation and Intelligent Q&A System

## 📋 Project Overview

RAT is an AI-based course design and Q&A system that leverages Retrieval-Augmented Generation (RAG) technology to provide more accurate and enriched content generation services.

### 🎯 Key Features

- **📚 Course Outline Generation**: Upload documents or input requirements to automatically generate professional course outlines
- **🔍 Intelligent Q&A**: AI Q&A system enhanced with web search capabilities
- **📄 Multi-format Support**: Support for PDF, DOCX, TXT file processing
- **🌐 Web Enhancement**: Integration with Google Search to improve content quality
- **📊 System Monitoring**: Real-time system status and configuration monitoring

## 🚀 Quick Start

### 1. Create Conda Virtual Environment

```bash
# Create new conda environment
conda create -n RAT python=3.10 -y

# Activate environment
conda activate RAT
```

### 2. Install Dependencies

```bash
# Navigate to project directory
cd /path/to/RAT

# Install required packages
pip install -r requirements.txt
```

## 3. Environment Variables Configuration (English)

### Method 1: Create a setup script (recommended)
1. Create the script file
```bash
cd /path/to/RAT/app
touch setup_env.sh
```

2. Edit setup_env.sh (add your own keys; do NOT commit secrets)
```bash
#!/bin/bash
# Environment variables for RAT (do NOT commit real keys)

# OpenAI API (required)
export OPENAI_API_KEY="your-openai-api-key"

# Google Search API (optional but recommended)
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CSE_ID="your-custom-search-engine-id"

# System configuration
export MODEL_TYPE="openai"

echo "[RAT] Environment variables loaded."
```

3. Make it executable and load it
```bash
chmod +x setup_env.sh
source ./setup_env.sh
```

4. (Optional) Auto-load on shell startup by adding to ~/.zshrc or ~/.bashrc
```bash
source /path/to/RAT/app/setup_env.sh
```

### Method 2: Manually set environment variables each time
```bash
# OpenAI (required)
export OPENAI_API_KEY="your-openai-api-key"

# Google Search (optional)
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CSE_ID="your-custom-search-engine-id"

# System configuration
export MODEL_TYPE="openai"
```

---

#### Obtaining API Keys

1. **OpenAI API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Create an account and obtain an API Key

2. **Google Search API**:
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Custom Search API
   - Create a Custom Search Engine and obtain the CSE ID

### 4. Launch Application

#### Web Interface (Flask)

```bash
# Launch Flask Web Application
python app.py
```

The app will run at `http://localhost:7860`

#### Gradio Interface

```bash
# Launch Gradio Interface
python gradio_app.py
```

#### Using Launch Script

```bash
# Grant execution permission
chmod +x start_rat.sh

# One-click launch
./start_rat.sh
```

## 📁 Project Structure

```
RAT/app/
├── 📄 app.py
├── 📄 gradio_app.py
├── 📄 README.md
├── 📄 setup.sh
├── 📄 start_rat.sh
├── 📄 requirements.txt
├── 📁 __pycache__/
├── 📁 core/
│   ├── 📄 chunk.py
│   ├── 📄 config.py
│   ├── 📄 file_processing.py
│   ├── 📄 search.py
│   └── 📁 __pycache__/
├── 📁 static/
│   ├── 📁 css/
│   │   └── 📄 style.css
│   └── 📁 js/
│       ├── 📄 app.js
│       └── 📄 course.js
├── 📁 templates/
│   ├── 📄 404.html
│   ├── 📄 500.html
│   ├── 📄 base.html
│   ├── 📄 course.html
│   ├── 📄 index.html
│   ├── 📄 system.html
│   └── 📄 test.html
└── 📁 uploads/
```

## 🔧 Core Modules

### `core/config.py`
- **OpenAI API Integration**: ChatGPT model invocation
- **System Configuration Management**: Model selection and parameter settings
- **Unified Response Generation**: Standardized AI response interface

### `core/file_processing.py`
- **Multi-format File Support**: PDF, DOCX, TXT parsing
- **Course Information Extraction**: Extract key course information from documents
- **Intelligent Content Analysis**: Automatically understand document structure and content

### `core/search.py`
- **Google Search Integration**: Web information retrieval
- **Content Quality Filtering**: Relevance and credibility assessment
- **Search Result Optimization**: Smart query generation and result processing

### `core/chunk.py`
- **Text Chunking**: Smart segmentation of large documents
- **Token Calculation**: Accurate text length calculation
- **Memory Optimization**: Efficient text processing strategies

## 🌐 Web Interface Features

### Main Pages

1. **Homepage** (`/`)
2. **Course Generator** (`/course`)
3. **System Information** (`/system`)

### API Endpoints

- `POST /api/generate_course`: Course outline generation API
- `GET /api/system_status`: System status query API

## ⚙️ System Requirements

### API Requirements
- **OpenAI API Key**: Required (for ChatGPT)
- **Google Search API**: Optional (enhanced search functionality)
- **Google CSE ID**: Optional (custom search engine)

## 🔍 Usage

### Course Outline Generation

1. **Method 1**: Upload course-related documents (PDF/DOCX/TXT)
2. **Method 2**: Directly input course requirement descriptions
3. **Method 3**: Provide both documents and requirement descriptions

### The system will automatically:
- Analyze document content or requirements
- Generate the initial course outline
- Search for relevant teaching resources (if enabled)
- Enhance and optimize the course content
- Produce a professionally formatted course outline

## 🛠️ Troubleshooting

### Common Issues

1. **OpenAI API Error**:
   ```bash
   # Check if API Key is correctly configured
   echo $OPENAI_API_KEY
   ```

2. **Module Import Error**:
   ```bash
   # Confirm you're in the correct virtual environment
   conda activate RAT
   pip list | grep flask
   ```

3. **File Upload Failure**:
   ```bash
   # Check uploads directory permissions
   chmod 755 uploads/
   ```

### Debug Mode

```bash
# Enable Flask debug mode
export FLASK_DEBUG=1
python app.py
```

## 👥 Project Information

### Author
**HSU, PAO-HUA (徐保華)**

### Institution
**Feng Chia University (逢甲大學)**

### Project Type
**Study Abroad Dream Project (學海築夢計畫)**

### Technical Features
- **Retrieval-Augmented Generation** (RAG)
- **Multi-modal Content Processing**
- **Intelligent Course Design**
- **Web Resource Integration**

## 📄 License

This project is an academic research project. Please cite the source when using.

## 🔗 Related Links

- [OpenAI Platform](https://platform.openai.com/)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gradio Documentation](https://gradio.app/docs/)

---

**Version 2.0** | **Flask Web Interface** | **OpenAI ChatGPT Integration**

💡 If you have any questions or suggestions, please contact the project team or check the system information page for more technical details.