// API Configuration
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000' 
    : `http://${window.location.hostname}:5000`;

// Generate a new activity ID (UUID v4)
function generateActivityId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// State
let deleteSourceId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUpload();
    initSearch();
    initChat();
    initModal();
    checkHealth();
    loadSources();
    
    // Refresh health every 30 seconds
    setInterval(checkHealth, 30000);
});

// ============== Health Check ==============

async function checkHealth() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusDot.className = 'status-dot healthy';
            statusText.textContent = 'All systems operational';
        } else {
            statusDot.className = 'status-dot';
            statusText.textContent = 'Some services degraded';
        }
    } catch (error) {
        statusDot.className = 'status-dot error';
        statusText.textContent = 'Connection error';
    }
}

// ============== Tabs ==============

function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active content
            const tabId = tab.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}

// ============== Upload ==============

function initUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
    
    // Refresh button
    document.getElementById('refresh-sources').addEventListener('click', loadSources);
}

async function handleFiles(files) {
    const progressDiv = document.getElementById('upload-progress');
    const progressFill = progressDiv.querySelector('.progress-fill');
    const progressText = progressDiv.querySelector('.progress-text');
    
    progressDiv.classList.remove('hidden');
    
    let uploaded = 0;
    let failed = 0;
    const total = files.length;
    
    for (const file of files) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        progressText.textContent = `Indexing ${file.name} (${sizeMB} MB)... (${uploaded + 1}/${total})`;
        progressText.innerHTML += '<br><small style="color: var(--text-muted);">Large files may take a while to process...</small>';
        progressFill.style.width = `${(uploaded / total) * 100}%`;
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 min timeout
            const activityId = generateActivityId();
            
            const response = await fetch(`${API_URL}/index/upload`, {
                method: 'POST',
                headers: { 'X-Activity-ID': activityId },
                body: formData,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            const result = await response.json();
            
            if (response.ok) {
                uploaded++;
                progressText.innerHTML = `✓ Indexed ${file.name} (${result.chunks_indexed} chunks)`;
            } else {
                failed++;
                console.error(`Error uploading ${file.name}:`, result.error);
                progressText.innerHTML = `✗ Failed: ${file.name} - ${result.error}`;
            }
        } catch (error) {
            failed++;
            if (error.name === 'AbortError') {
                progressText.innerHTML = `✗ Timeout: ${file.name} (file too large)`;
            } else {
                progressText.innerHTML = `✗ Error: ${file.name} - ${error.message}`;
            }
            console.error(`Error uploading ${file.name}:`, error);
        }
        
        // Small delay between files to let UI update
        await new Promise(r => setTimeout(r, 100));
    }
    
    progressFill.style.width = '100%';
    if (failed > 0) {
        progressText.innerHTML = `Completed: ${uploaded} uploaded, ${failed} failed`;
    } else {
        progressText.textContent = `✓ Successfully indexed ${uploaded} file(s)`;
    }
    
    // Reset after 3 seconds
    setTimeout(() => {
        progressDiv.classList.add('hidden');
        progressFill.style.width = '0%';
        document.getElementById('file-input').value = '';
    }, 3000);
    
    // Refresh sources list
    loadSources();
}

// ============== Sources ==============

async function loadSources() {
    const tbody = document.getElementById('sources-body');
    const totalSourcesEl = document.getElementById('total-sources');
    const totalChunksEl = document.getElementById('total-chunks');
    
    try {
        const response = await fetch(`${API_URL}/sources`);
        const data = await response.json();
        
        totalSourcesEl.textContent = data.total_sources;
        totalChunksEl.textContent = data.total_chunks;
        
        if (data.sources.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No files indexed yet. Upload some files to get started!</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.sources.map(source => `
            <tr>
                <td><strong>${escapeHtml(source.source)}</strong></td>
                <td>${source.chunks}</td>
                <td>${formatBytes(source.size_bytes)}</td>
                <td>${formatDate(source.indexed_at)}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="showDeleteModal('${escapeHtml(source.source)}')">
                        Delete
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Error loading sources</td></tr>';
    }
}

// ============== Delete Modal ==============

function initModal() {
    document.getElementById('cancel-delete').addEventListener('click', hideDeleteModal);
    document.getElementById('confirm-delete').addEventListener('click', confirmDelete);
    
    // Close on background click
    document.getElementById('delete-modal').addEventListener('click', (e) => {
        if (e.target.id === 'delete-modal') {
            hideDeleteModal();
        }
    });
}

function showDeleteModal(sourceId) {
    deleteSourceId = sourceId;
    document.getElementById('delete-source-name').textContent = sourceId;
    document.getElementById('delete-modal').classList.remove('hidden');
}

function hideDeleteModal() {
    deleteSourceId = null;
    document.getElementById('delete-modal').classList.add('hidden');
}

async function confirmDelete() {
    if (!deleteSourceId) return;
    
    try {
        const response = await fetch(`${API_URL}/sources/${encodeURIComponent(deleteSourceId)}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadSources();
        } else {
            const data = await response.json();
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
    
    hideDeleteModal();
}

// ============== Search ==============

function initSearch() {
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');
    
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });
}

async function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    
    const resultsCard = document.getElementById('search-results-card');
    const resultsDiv = document.getElementById('search-results');
    
    resultsCard.style.display = 'block';
    resultsDiv.innerHTML = '<p>Generating AI response...</p>';
    
    try {
        // Let API auto-determine optimal settings based on query complexity
        const requestBody = { query };
        const activityId = generateActivityId();
        const response = await fetch(`${API_URL}/search/rag`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Activity-ID': activityId
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        // Show just query time
        const queryTime = data.timings ? `${(data.timings.total_ms/1000).toFixed(1)}s` : '';
        
        resultsDiv.innerHTML = `
            <div class="rag-response">
                <h3>🤖 AI Response</h3>
                <div class="ai-content">${formatAIResponse(data.response)}</div>
                ${queryTime ? `<p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 12px;">Query time: ${queryTime}</p>` : ''}
            </div>
        `;
    } catch (error) {
        resultsDiv.innerHTML = `<p class="empty-state">Error: ${error.message}</p>`;
    }
}

// ============== Chat ==============

function initChat() {
    const sendBtn = document.getElementById('chat-send');
    const chatInput = document.getElementById('chat-input');
    
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

const chatHistory = [];

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    const messagesDiv = document.getElementById('chat-messages');
    
    // Add user message to UI
    messagesDiv.innerHTML += `
        <div class="message user">
            <div class="message-content">${escapeHtml(message)}</div>
        </div>
    `;
    
    // Add to history
    chatHistory.push({ role: 'user', content: message });
    
    input.value = '';
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // Add loading indicator
    messagesDiv.innerHTML += `
        <div class="message assistant" id="loading-message">
            <div class="message-content">Thinking...</div>
        </div>
    `;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    try {
        const activityId = generateActivityId();
        
        // Use RAG endpoint to get context-aware response
        const response = await fetch(`${API_URL}/search/rag`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Activity-ID': activityId
            },
            body: JSON.stringify({ query: message })
        });
        
        const data = await response.json();
        const assistantMessage = data.response || data.error || 'No response';
        
        // Remove loading and add real response with formatted markdown
        document.getElementById('loading-message').remove();
        messagesDiv.innerHTML += `
            <div class="message assistant">
                <div class="message-content">${formatAIResponse(assistantMessage)}</div>
            </div>
        `;
        
        // Add to history (for context in future messages)
        chatHistory.push({ role: 'assistant', content: assistantMessage });
        
    } catch (error) {
        document.getElementById('loading-message').remove();
        messagesDiv.innerHTML += `
            <div class="message assistant">
                <div class="message-content">Error: ${escapeHtml(error.message)}</div>
            </div>
        `;
    }
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// ============== Utilities ==============

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatAIResponse(text) {
    // Escape HTML first
    let formatted = escapeHtml(text);
    
    // Convert markdown-style formatting
    // Bold: **text** or __text__
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/__(.+?)__/g, '<strong>$1</strong>');
    
    // Italic: *text* or _text_
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/_([^_]+)_/g, '<em>$1</em>');
    
    // Code: `text`
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Split into lines for list/paragraph processing
    const lines = formatted.split('\n');
    let html = '';
    let inList = false;
    
    for (const line of lines) {
        const trimmed = line.trim();
        
        // Numbered list: 1. or 1)
        if (/^\d+[.)\s]/.test(trimmed)) {
            if (!inList) {
                html += '<ol>';
                inList = 'ol';
            }
            html += `<li>${trimmed.replace(/^\d+[.)\s]+/, '')}</li>`;
        }
        // Bullet list: - or * or •
        else if (/^[-*•]\s/.test(trimmed)) {
            if (!inList) {
                html += '<ul>';
                inList = 'ul';
            }
            html += `<li>${trimmed.replace(/^[-*•]\s+/, '')}</li>`;
        }
        // Empty line
        else if (trimmed === '') {
            if (inList) {
                html += inList === 'ol' ? '</ol>' : '</ul>';
                inList = false;
            }
            html += '<br>';
        }
        // Regular paragraph
        else {
            if (inList) {
                html += inList === 'ol' ? '</ol>' : '</ul>';
                inList = false;
            }
            html += `<p>${trimmed}</p>`;
        }
    }
    
    // Close any open list
    if (inList) {
        html += inList === 'ol' ? '</ol>' : '</ul>';
    }
    
    return html;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
