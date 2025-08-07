class CourseGenerator {
    constructor() {
        // 元素初始化 - 🔥 移除 preview 相關元素
        this.formContainer = document.getElementById('courseForm');
        this.generateBtn = document.getElementById('generateBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.progressSection = document.getElementById('progressSection');
        this.progressText = document.getElementById('progressText');
        this.generatedResult = document.getElementById('generatedResult');
        
        // 檢查關鍵元素
        if (!this.formContainer || !this.generateBtn) {
            console.error('ERROR: Required elements not found!');
            return;
        }
        
        this.initializeEventListeners();
        console.log('CourseGenerator initialized successfully');
    }
    
    initializeEventListeners() {
        // 生成按鈕點擊事件
        this.generateBtn.addEventListener('click', () => {
            console.log('🚀 Generate button clicked');
            this.generateCourse();
        });
        
        // 清除按鈕點擊事件
        this.clearBtn.addEventListener('click', () => {
            this.clearForm();
        });
        
        // 🔥 移除所有 preview 相關的事件監聽器
    }
    
    async generateCourse() {
        console.log('🚀 === generateCourse() called ===');
        
        try {
            // 顯示載入狀態
            this.setLoading(true);
            
            // 構建請求數據
            const formData = new FormData();
            
            // 獲取檔案
            const fileInput = document.getElementById('fileInput');
            if (fileInput.files.length > 0) {
                formData.append('file', fileInput.files[0]);
                console.log('📎 File attached:', fileInput.files[0].name);
            }
            
            // 構建結構化需求
            const structuredRequirements = this.buildCourseRequirements();
            formData.append('requirements', structuredRequirements);
            
            // 搜尋選項
            const enableSearch = document.getElementById('enableSearch').checked;
            formData.append('enable_search', enableSearch);
            
            console.log('📝 Requirements built:', structuredRequirements);
            console.log('🔍 Search enabled:', enableSearch);
            
            // 發送請求
            const response = await fetch('/api/generate_course', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            console.log('📊 API Response:', data);
            
            if (data.success) {
                // 更新結果
                this.updateResult(data.final_outline);
                this.showAlert('Course outline generated successfully!', 'success');
            } else {
                this.showAlert(`Error: ${data.error}`, 'danger');
            }
            
        } catch (error) {
            console.error('❌ Generation error:', error);
            this.showAlert(`Error: ${error.message}`, 'danger');
        } finally {
            this.setLoading(false);
        }
    }
    
    buildCourseRequirements() {
        // 獲取結構化輸入
        const courseTitle = document.getElementById('courseTitle')?.value?.trim() || '';
        const targetAudience = document.getElementById('targetAudience')?.value?.trim() || '';
        const courseDuration = document.getElementById('courseDuration')?.value?.trim() || '';
        const classHours = document.getElementById('classHours')?.value?.trim() || '';
        const coreRequirements = document.getElementById('coreRequirements')?.value?.trim() || '';
        const additionalRequirements = document.getElementById('requirementsInput')?.value?.trim() || '';
        
        // 構建完整需求
        let requirements = [];
        
        if (courseTitle) requirements.push(`Course Title: ${courseTitle}`);
        if (targetAudience) requirements.push(`Target Audience: ${targetAudience}`);
        if (courseDuration) requirements.push(`Course Duration: ${courseDuration}`);
        if (classHours) requirements.push(`Class Hours: ${classHours}`);
        if (coreRequirements) requirements.push(`Core Learning Requirements: ${coreRequirements}`);
        if (additionalRequirements) requirements.push(`Additional Requirements: ${additionalRequirements}`);
        
        return requirements.join('\n');
    }
    
    updateResult(generatedOutline) {
        console.log('📋 Updating result...');
        console.log('Generated outline length:', generatedOutline?.length || 0);
        
        // 更新生成結果
        if (this.generatedResult) {
            this.generatedResult.innerHTML = this.formatContent(generatedOutline || 'No course outline generated');
        }
        
        console.log('✅ Result updated successfully');
    }
    
    formatContent(content) {
        if (!content || content.trim() === '') {
            return `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-exclamation-circle fa-2x mb-3"></i>
                    <p>No content available</p>
                    <small>Please check your input and try again</small>
                </div>
            `;
        }
        
        // 基本的 Markdown 轉 HTML
        let formatted = content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^# (.*$)/gm, '<h1 class="text-primary">$1</h1>')
            .replace(/^## (.*$)/gm, '<h2 class="text-secondary">$1</h2>')
            .replace(/^### (.*$)/gm, '<h3 class="text-dark">$1</h3>')
            .replace(/^#### (.*$)/gm, '<h4 class="text-muted">$1</h4>')
            .replace(/^- (.*$)/gm, '<li class="mb-1">$1</li>');
        
        // 包裝列表項目
        formatted = formatted.replace(/(<li>.*?<\/li>)/gs, '<ul class="list-unstyled ps-3">$1</ul>');
        
        // 添加功能按鈕
        const actionButtons = `
            <div class="mt-4 d-flex gap-2">
                <button class="btn btn-outline-primary copy-content-btn" onclick="copyContentToClipboard(this)">
                    <i class="fas fa-copy me-1"></i>Copy Content
                </button>
                <button class="btn btn-outline-success download-btn" onclick="downloadContent(this)">
                    <i class="fas fa-download me-1"></i>Download as Text
                </button>
                <button class="btn btn-outline-info share-btn" onclick="shareContent(this)">
                    <i class="fas fa-share me-1"></i>Share
                </button>
            </div>
        `;
        
        return `
            <div class="content-wrapper">
                <div class="generated-content p-3 bg-light rounded">
                    ${formatted}
                </div>
                ${actionButtons}
            </div>
        `;
    }
    
    setLoading(isLoading) {
        if (isLoading) {
            this.progressSection.classList.remove('d-none');
            this.generateBtn.disabled = true;
            this.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating...';
            
            // 更新進度文字
            const messages = [
                'Analyzing requirements...',
                'Generating initial outline...',
                'Searching web resources...',
                'Enhancing content...',
                'Finalizing course outline...'
            ];
            
            let index = 0;
            this.progressInterval = setInterval(() => {
                if (index < messages.length) {
                    this.progressText.textContent = messages[index];
                    index++;
                } else {
                    index = 0; // 循環顯示
                }
            }, 2000);
            
        } else {
            this.progressSection.classList.add('d-none');
            this.generateBtn.disabled = false;
            this.generateBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Generate Course Outline';
            
            if (this.progressInterval) {
                clearInterval(this.progressInterval);
            }
        }
    }
    
    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // 自動移除警告
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    clearForm() {
        // 清除所有輸入欄位
        document.getElementById('fileInput').value = '';
        document.getElementById('courseTitle').value = '';
        document.getElementById('targetAudience').value = '';
        document.getElementById('courseDuration').value = '';
        document.getElementById('classHours').value = '';
        document.getElementById('coreRequirements').value = '';
        document.getElementById('requirementsInput').value = '';
        
        // 清除結果
        this.generatedResult.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-graduation-cap fa-3x mb-3"></i>
                <p>Your generated course outline will appear here</p>
                <small>Fill in the course details and click "Generate Course Outline" to start</small>
            </div>
        `;
        
        console.log('✅ Form cleared');
    }
    
    // 🔥 移除所有 preview 相關方法：
    // - showPreview()
    // - copyPreviewContent()
}

// 保留全域功能函數
function copyContentToClipboard(button) {
    const contentWrapper = button.closest('.content-wrapper');
    const generatedContent = contentWrapper.querySelector('.generated-content');
    const content = generatedContent.textContent.trim();
    
    navigator.clipboard.writeText(content).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-success');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-primary');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

function downloadContent(button) {
    const contentWrapper = button.closest('.content-wrapper');
    const generatedContent = contentWrapper.querySelector('.generated-content');
    const content = generatedContent.textContent.trim();
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `course-outline-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // 更新按鈕狀態
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check me-1"></i>Downloaded!';
    button.classList.remove('btn-outline-success');
    button.classList.add('btn-success');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.remove('btn-success');
        button.classList.add('btn-outline-success');
    }, 2000);
}

function shareContent(button) {
    const contentWrapper = button.closest('.content-wrapper');
    const generatedContent = contentWrapper.querySelector('.generated-content');
    const content = generatedContent.textContent.trim();
    
    if (navigator.share) {
        navigator.share({
            title: 'Generated Course Outline',
            text: content,
        }).then(() => {
            console.log('Content shared successfully');
        }).catch(err => {
            console.error('Error sharing:', err);
        });
    } else {
        // 備用方案：複製到剪貼簿
        navigator.clipboard.writeText(content).then(() => {
            alert('Content copied to clipboard for sharing!');
        });
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Course.js DOM loaded');
    window.courseGenerator = new CourseGenerator();
});