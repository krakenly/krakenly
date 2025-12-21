// API Configuration
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000' 
    : `http://${window.location.hostname}:5000`;

// Feature flags
const STREAMING_ENABLED = true;

// Generate a new activity ID (UUID v4)
function generateActivityId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// ============== SSE Helpers ==============

function parseSSEEvents(text) {
    /**
     * Parse SSE text into array of event objects.
     * Handles multiple events in a single chunk.
     */
    const events = [];
    const lines = text.split('\n');
    
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            try {
                const jsonStr = line.substring(6);
                if (jsonStr.trim()) {
                    events.push(JSON.parse(jsonStr));
                }
            } catch (e) {
                console.warn('Failed to parse SSE event:', line, e);
            }
        }
    }
    
    return events;
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
    
    const activityId = generateActivityId();
    
    if (STREAMING_ENABLED) {
        await performSearchStream(query, resultsDiv, activityId);
    } else {
        await performSearchNonStream(query, resultsDiv, activityId);
    }
}

async function performSearchStream(query, resultsDiv, activityId) {
    // Show streaming placeholder
    resultsDiv.innerHTML = `
        <div class="rag-response">
            <h3>🤖 AI Response</h3>
            <div class="ai-content streaming" id="search-stream-content">
                <span class="streaming-cursor">▌</span>
            </div>
        </div>
    `;
    
    const contentDiv = document.getElementById('search-stream-content');
    let fullResponse = '';
    let timings = null;
    
    try {
        const response = await fetch(`${API_URL}/search/rag/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Activity-ID': activityId,
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        contentDiv.innerHTML = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const text = decoder.decode(value, { stream: true });
            const events = parseSSEEvents(text);
            
            for (const event of events) {
                switch (event.type) {
                    case 'start':
                        // Could show sources indicator here
                        break;
                        
                    case 'token':
                        fullResponse += event.content;
                        contentDiv.textContent = fullResponse;
                        break;
                        
                    case 'done':
                        timings = event.timings;
                        break;
                        
                    case 'error':
                        contentDiv.innerHTML = `<span class="error">Error: ${escapeHtml(event.message)}</span>`;
                        return;
                }
            }
        }
        
        // Apply final formatting
        const queryTime = timings ? `${(timings.total_ms / 1000).toFixed(1)}s` : '';
        
        resultsDiv.innerHTML = `
            <div class="rag-response">
                <h3>🤖 AI Response</h3>
                <div class="ai-content">${formatAIResponse(fullResponse)}</div>
                ${queryTime ? `<p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 12px;">Query time: ${queryTime}</p>` : ''}
            </div>
        `;
        
    } catch (error) {
        resultsDiv.innerHTML = `<p class="empty-state">Error: ${escapeHtml(error.message)}</p>`;
    }
}

async function performSearchNonStream(query, resultsDiv, activityId) {
    resultsDiv.innerHTML = '<p>Generating AI response...</p>';
    
    try {
        const response = await fetch(`${API_URL}/search/rag`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Activity-ID': activityId
            },
            body: JSON.stringify({ query })
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
    
    // Create assistant message container
    const messageId = 'msg-' + Date.now();
    messagesDiv.innerHTML += `
        <div class="message assistant" id="${messageId}">
            <div class="message-content streaming">
                <span class="streaming-cursor">▌</span>
            </div>
        </div>
    `;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    const messageDiv = document.getElementById(messageId);
    const contentDiv = messageDiv.querySelector('.message-content');
    
    const activityId = generateActivityId();
    
    if (STREAMING_ENABLED) {
        await sendMessageStream(message, contentDiv, activityId, messagesDiv);
    } else {
        await sendMessageNonStream(message, contentDiv, activityId);
    }
    
    // Add to history
    const finalContent = contentDiv.textContent || contentDiv.innerText;
    chatHistory.push({ role: 'assistant', content: finalContent });
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function sendMessageStream(message, contentDiv, activityId, messagesDiv) {
    let fullResponse = '';
    
    try {
        const response = await fetch(`${API_URL}/search/rag/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Activity-ID': activityId,
                'Accept': 'text/event-stream'
            },
            body: JSON.stringify({ query: message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // Remove cursor, prepare for streaming content
        contentDiv.innerHTML = '';
        contentDiv.classList.add('streaming');
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const text = decoder.decode(value, { stream: true });
            const events = parseSSEEvents(text);
            
            for (const event of events) {
                switch (event.type) {
                    case 'start':
                        console.log('Stream started, sources:', event.sources);
                        break;
                        
                    case 'token':
                        fullResponse += event.content;
                        contentDiv.textContent = fullResponse;
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        break;
                        
                    case 'done':
                        contentDiv.classList.remove('streaming');
                        contentDiv.innerHTML = formatAIResponse(fullResponse);
                        console.log('Stream complete, timings:', event.timings);
                        break;
                        
                    case 'error':
                        contentDiv.classList.remove('streaming');
                        contentDiv.innerHTML = `<span class="error">Error: ${escapeHtml(event.message)}</span>`;
                        console.error('Stream error:', event);
                        return;
                }
            }
        }
        
        // Ensure formatting is applied if we missed done event
        if (contentDiv.classList.contains('streaming')) {
            contentDiv.classList.remove('streaming');
            contentDiv.innerHTML = formatAIResponse(fullResponse);
        }
        
    } catch (error) {
        contentDiv.classList.remove('streaming');
        contentDiv.innerHTML = `<span class="error">Error: ${escapeHtml(error.message)}</span>`;
        console.error('Fetch error:', error);
    }
}

async function sendMessageNonStream(message, contentDiv, activityId) {
    try {
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
        
        contentDiv.classList.remove('streaming');
        contentDiv.innerHTML = formatAIResponse(assistantMessage);
        
    } catch (error) {
        contentDiv.classList.remove('streaming');
        contentDiv.innerHTML = `<span class="error">Error: ${escapeHtml(error.message)}</span>`;
    }
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
