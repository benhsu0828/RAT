class CourseGenerator {
    constructor() {
        // Elements
        this.formContainer = document.getElementById('courseForm');
        this.generateBtn = document.getElementById('generateBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.progressSection = document.getElementById('progressSection');
        this.progressText = document.getElementById('progressText');
        this.generatedResult = document.getElementById('generatedResult');
        // New: actions toolbar
        this.resultActions = document.getElementById('resultActions');
        this.copyResultBtn = document.getElementById('copyResultBtn');
        this.downloadResultBtn = document.getElementById('downloadResultBtn');

        // Guard
        if (!this.formContainer || !this.generateBtn) {
            console.error('ERROR: Required elements not found!');
            return;
        }

        this.initializeEventListeners();
        console.log('CourseGenerator initialized successfully');
    }

    initializeEventListeners() {
        // Generate outline
        this.generateBtn.addEventListener('click', () => {
            this.generateCourse();
        });

        // Clear form
        this.clearBtn.addEventListener('click', () => {
            this.clearForm();
        });

        // Result actions (outside toolbar)
        if (this.copyResultBtn) {
            this.copyResultBtn.addEventListener('click', () => this.copyResult());
        }
        if (this.downloadResultBtn) {
            this.downloadResultBtn.addEventListener('click', () => this.downloadResult());
        }
    }

    async generateCourse() {
        console.log('🚀 === generateCourse() called ===');
        try {
            this.setLoading(true);

            const formData = new FormData();

            // Optional file
            const fileInput = document.getElementById('fileInput');
            if (fileInput?.files?.length > 0) {
                formData.append('file', fileInput.files[0]);
                console.log('📎 File attached:', fileInput.files[0].name);
            }

            // Structured requirements
            const structuredRequirements = this.buildCourseRequirements();
            formData.append('requirements', structuredRequirements);

            // Search option
            const enableSearch = document.getElementById('enableSearch').checked;
            formData.append('enable_search', enableSearch);

            const response = await fetch('/api/generate_course', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.success) {
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
        // Read inputs and build a structured string
        const courseTitle = document.getElementById('courseTitle')?.value?.trim() || '';
        const targetAudience = document.getElementById('targetAudience')?.value?.trim() || '';
        const courseDuration = document.getElementById('courseDuration')?.value?.trim() || '';
        const classHours = document.getElementById('classHours')?.value?.trim() || '';
        const coreRequirements = document.getElementById('coreRequirements')?.value?.trim() || '';
        const additionalRequirements = document.getElementById('requirementsInput')?.value?.trim() || '';

        const parts = [];
        if (courseTitle) parts.push(`Course Title: ${courseTitle}`);
        if (targetAudience) parts.push(`Target Audience: ${targetAudience}`);
        if (courseDuration) parts.push(`Course Duration: ${courseDuration}`);
        if (classHours) parts.push(`Class Hours: ${classHours}`);
        if (coreRequirements) parts.push(`Core Learning Requirements: ${coreRequirements}`);
        if (additionalRequirements) parts.push(`Additional Requirements: ${additionalRequirements}`);

        return parts.join('\n');
    }

    updateResult(generatedOutline) {
        console.log('📋 Updating result...');
        const content = generatedOutline || 'No course outline generated';
        if (this.generatedResult) {
            const html = this.markdownToHtml(content); // Use improved markdown parser
            this.generatedResult.innerHTML = `
                <div class="content-wrapper">
                    <div class="generated-content p-3 bg-light rounded">
                        ${html}
                    </div>
                </div>
            `;
        }
        // Show actions toolbar once result is available
        if (this.resultActions) {
            this.resultActions.classList.remove('d-none');
        }
        console.log('✅ Result updated successfully');
    }

    // Simple Markdown parser: handles headings, unordered lists, bold/italic, paragraphs
    markdownToHtml(markdown) {
        // Normalize line breaks
        const lines = (markdown || '').replace(/\r\n/g, '\n').split('\n');

        // Inline formatting helper (bold/italic)
        const inline = (text) =>
            text
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>');

        let html = '';
        let inUl = false;

        for (let raw of lines) {
            const line = raw.trimEnd();

            // Empty line -> break paragraph / close current list
            if (line.trim() === '') {
                if (inUl) {
                    html += '</ul>';
                    inUl = false;
                }
                html += '<br>';
                continue;
            }

            // Headings (close list before heading)
            let m;
            if ((m = line.match(/^####\s+(.*)/))) {
                if (inUl) { html += '</ul>'; inUl = false; }
                html += `<h4>${inline(m[1])}</h4>`;
                continue;
            }
            if ((m = line.match(/^###\s+(.*)/))) {
                if (inUl) { html += '</ul>'; inUl = false; }
                html += `<h3>${inline(m[1])}</h3>`;
                continue;
            }
            if ((m = line.match(/^##\s+(.*)/))) {
                if (inUl) { html += '</ul>'; inUl = false; }
                html += `<h2>${inline(m[1])}</h2>`;
                continue;
            }
            if ((m = line.match(/^#\s+(.*)/))) {
                if (inUl) { html += '</ul>'; inUl = false; }
                html += `<h1>${inline(m[1])}</h1>`;
                continue;
            }

            // Unordered list items (- or *)
            if ((m = line.match(/^[-*]\s+(.*)/))) {
                if (!inUl) {
                    html += '<ul>';
                    inUl = true;
                }
                html += `<li>${inline(m[1])}</li>`;
                continue;
            }

            // Normal paragraph line
            if (inUl) {
                html += '</ul>';
                inUl = false;
            }
            html += `<p>${inline(line)}</p>`;
        }

        // Close a trailing list
        if (inUl) html += '</ul>';

        return html;
    }

    setLoading(isLoading) {
        if (isLoading) {
            this.progressSection.classList.remove('d-none');
            this.generateBtn.disabled = true;
            this.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating...';

            // Rotate progress messages
            const messages = [
                'Analyzing requirements...',
                'Generating initial outline...',
                'Searching web resources...',
                'Enhancing content...',
                'Finalizing course outline...'
            ];
            let index = 0;
            this.progressInterval = setInterval(() => {
                this.progressText.textContent = messages[index];
                index = (index + 1) % messages.length;
            }, 2000);
        } else {
            this.progressSection.classList.add('d-none');
            this.generateBtn.disabled = false;
            this.generateBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Generate Course Outline';
            if (this.progressInterval) clearInterval(this.progressInterval);
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
        setTimeout(() => { if (alertDiv.parentNode) alertDiv.remove(); }, 5000);
    }

    clearForm() {
        // Clear inputs
        document.getElementById('fileInput').value = '';
        document.getElementById('courseTitle').value = '';
        document.getElementById('targetAudience').value = '';
        document.getElementById('courseDuration').value = '';
        document.getElementById('classHours').value = '';
        document.getElementById('coreRequirements').value = '';
        document.getElementById('requirementsInput').value = '';

        // Reset result
        this.generatedResult.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-graduation-cap fa-3x mb-3"></i>
                <p>Your generated course outline will appear here</p>
                <small>Fill in the course details and click "Generate Course Outline" to start</small>
            </div>
        `;
        // Hide actions toolbar until next result
        if (this.resultActions) {
            this.resultActions.classList.add('d-none');
        }
        console.log('✅ Form cleared');
    }

    // Copy result text (outside toolbar button)
    copyResult() {
        // Read plain text from the rendered result
        const text = this.generatedResult?.innerText?.trim() || '';
        if (!text) return;

        // Success UI feedback
        const onSuccess = () => {
            const btn = this.copyResultBtn;
            if (!btn) return;
            const orig = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
            btn.classList.remove('btn-outline-primary');
            btn.classList.add('btn-success');
            setTimeout(() => {
                btn.innerHTML = orig;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-primary');
            }, 1500);
        };

        // Prefer Async Clipboard API in secure contexts
        if (window.isSecureContext && navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text)
                .then(onSuccess)
                .catch(() => this.fallbackCopyText(text, onSuccess));
        } else {
            // Fallback for non-secure origins and older browsers
            this.fallbackCopyText(text, onSuccess);
        }
    }

    // Fallback copy using a hidden textarea (works on HTTP)
    fallbackCopyText(text, onDone) {
        try {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.setAttribute('readonly', '');
            ta.style.position = 'fixed';
            ta.style.top = '-1000px';
            ta.style.left = '-1000px';
            document.body.appendChild(ta);
            ta.select();
            const ok = document.execCommand('copy');
            document.body.removeChild(ta);
            if (ok) {
                onDone && onDone();
            } else {
                throw new Error('execCommand("copy") returned false');
            }
        } catch (e) {
            console.error('Copy fallback failed:', e);
            this.showAlert('Copy failed. Please select the text and press Cmd/Ctrl+C.', 'danger');
        }
    }

    // Download result as .txt (outside toolbar button)
    downloadResult() {
        const text = this.generatedResult?.innerText?.trim() || '';
        if (!text) return;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `course-outline-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        const btn = this.downloadResultBtn;
        if (btn) {
            const orig = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check me-1"></i>Downloaded!';
            btn.classList.remove('btn-outline-success');
            btn.classList.add('btn-success');
            setTimeout(() => {
                btn.innerHTML = orig;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-success');
            }, 1500);
        }
    }
}

// Init
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Course.js DOM loaded');
    window.courseGenerator = new CourseGenerator();
});