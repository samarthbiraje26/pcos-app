document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    populateSidebarUser();
    loadChatHistory();
  
    const sendBtn = document.getElementById('chat-send-btn');
    const inputField = document.getElementById('chat-input');
  
    sendBtn?.addEventListener('click', handleSend);
    inputField?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') handleSend();
    });
  
    document.querySelectorAll('.js-quick-reply').forEach(btn => {
      btn.addEventListener('click', () => {
        inputField.value = btn.textContent;
        handleSend();
      });
    });
  });
  
  const chatBody = document.getElementById('chat-body');
  
  async function loadChatHistory() {
    const res = await API.getChatHistory();
    if (res && res.ok && res.data && res.data.data) {
      chatBody.innerHTML = '';
      if (res.data.data.length === 0) {
        appendMessage('assistant', 'Hello! I am your PCOS health assistant. Ask me anything about diet, exercise, or lifestyle habits to help manage your health.');
      }
      res.data.data.forEach(msg => {
        appendMessage(msg.role, msg.message);
      });
      scrollToBottom();
    }
  }
  
  async function handleSend() {
    const inputField = document.getElementById('chat-input');
    const message = inputField.value.trim();
    if (!message) return;
  
    inputField.value = '';
    appendMessage('user', message);
    scrollToBottom();
  
    const typingRow = appendTypingIndicator();
    scrollToBottom();
  
    const res = await API.sendChatMessage(message);
    
    if (typingRow) typingRow.remove();
  
    if (res && res.ok && res.data && res.data.data) {
      appendMessage(res.data.data.role, res.data.data.message);
    } else {
      appendMessage('assistant', 'Sorry, I am having trouble connecting to the server. Please try again later.');
    }
    scrollToBottom();
  }
  
  function appendMessage(role, text) {
    const isUser = role === 'user';
    const row = document.createElement('div');
    row.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    
    if (isUser) {
      bubble.textContent = text;
    } else {
      bubble.innerHTML = parseMarkdown(text);
    }
    
    row.appendChild(bubble);
    chatBody.appendChild(row);
  }

  function parseMarkdown(text) {
    if (!text) return '';
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Bold tags: **text**
    html = html.replace(/\*\*([\s\S]*?)\*\*/g, '<strong>$1</strong>');

    // Bullet & Number lists
    const lines = html.split('\n');
    let inBulletedList = false;
    let inNumberedList = false;
    const processedLines = [];

    for (let line of lines) {
      let trimmed = line.trim();
      
      // Match bullet points starting with - or *
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        if (inNumberedList) {
          processedLines.push('</ol>');
          inNumberedList = false;
        }
        if (!inBulletedList) {
          processedLines.push('<ul style="margin: 0.4rem 0 0.8rem 0; padding-left: 1.25rem; list-style-type: disc;">');
          inBulletedList = true;
        }
        processedLines.push(`<li style="margin-bottom: 0.25rem;">${trimmed.substring(2)}</li>`);
      }
      // Match numbered lists starting with digit + dot + space
      else if (/^\d+\.\s/.test(trimmed)) {
        if (inBulletedList) {
          processedLines.push('</ul>');
          inBulletedList = false;
        }
        if (!inNumberedList) {
          processedLines.push('<ol style="margin: 0.4rem 0 0.8rem 0; padding-left: 1.25rem; list-style-type: decimal;">');
          inNumberedList = true;
        }
        const itemContent = trimmed.replace(/^\d+\.\s/, '');
        processedLines.push(`<li style="margin-bottom: 0.25rem;">${itemContent}</li>`);
      }
      // Non-list line
      else {
        if (inBulletedList) {
          processedLines.push('</ul>');
          inBulletedList = false;
        }
        if (inNumberedList) {
          processedLines.push('</ol>');
          inNumberedList = false;
        }
        processedLines.push(line);
      }
    }

    if (inBulletedList) processedLines.push('</ul>');
    if (inNumberedList) processedLines.push('</ol>');

    html = processedLines.join('\n');

    // Format paragraphs & line breaks (excluding list tags)
    const finalLines = [];
    const joinedLines = html.split('\n');
    for (let line of joinedLines) {
      let trimmed = line.trim();
      if (trimmed.startsWith('<ul') || trimmed.startsWith('</ul') || trimmed.startsWith('<ol') || trimmed.startsWith('</ol') || trimmed.startsWith('<li') || trimmed.startsWith('</li')) {
        finalLines.push(line);
      } else if (trimmed === '') {
        finalLines.push('<div style="height: 0.4rem;"></div>');
      } else {
        finalLines.push(line + '<br>');
      }
    }

    return finalLines.join(' ');
  }
  
  function appendTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'chat-message bot-message';
    row.innerHTML = `<div class="chat-bubble" style="display:flex;gap:4px;padding:12px 16px;">
      <span class="typing-dot" style="animation: pulse 1s infinite .1s">.</span>
      <span class="typing-dot" style="animation: pulse 1s infinite .2s">.</span>
      <span class="typing-dot" style="animation: pulse 1s infinite .3s">.</span>
    </div>`;
    chatBody.appendChild(row);
    return row;
  }
  
  function scrollToBottom() {
    if (chatBody) chatBody.scrollTop = chatBody.scrollHeight;
  }
