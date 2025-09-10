document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 KisanMitra script loaded");
    
    // --- DOM Element References ---
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.getElementById('menu-btn');
    const closeBtn = document.getElementById('sidebar-close-btn');
    const overlay = document.getElementById('overlay');
    const queryInput = document.getElementById('queryInput');
    const chatWindow = document.getElementById('chat-window');
    const navButtons = document.querySelectorAll('.quick-query-btn');
    const views = document.querySelectorAll('.view');
    const headerIcon = document.getElementById('header-icon');
    const headerTitle = document.getElementById('header-title');
    const headerSubtitle = document.getElementById('header-subtitle');
    const sidebarSearchInput = document.getElementById('sidebar-search-input');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const submitBtn = document.getElementById('submitBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Header Popover Elements
    const headerLangBtn = document.getElementById('header-lang-btn');
    const langPopover = document.getElementById('lang-popover');
    const popoverCloseBtn = document.getElementById('popover-close-btn');
    const popoverSearchInput = document.getElementById('popover-search-input');
    const popoverLangList = document.getElementById('popover-lang-list');
    const settingsLangList = document.getElementById('settings-lang-list');

    // ⭐ IMPORTANT: Current language variable (FIXED)
    let currentLanguage = 'en';
    console.log("✅ Current language initialized:", currentLanguage);

    // --- Check essential elements ---
    if (!submitBtn) {
        console.error("❌ Submit button not found!");
        return;
    }
    if (!queryInput) {
        console.error("❌ Query input not found!");
        return;
    }
    if (!chatWindow) {
        console.error("❌ Chat window not found!");
        return;
    }
    console.log("✅ All essential elements found");

    // --- INITIALIZATION ---
    if (popoverLangList && settingsLangList) {
        popoverLangList.innerHTML = settingsLangList.innerHTML;
    }

    // --- Mobile Sidebar Logic ---
    const toggleSidebar = () => {
        if (sidebar && overlay) {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        }
    };
    
    if (menuBtn && closeBtn && overlay) {
        menuBtn.addEventListener('click', toggleSidebar);
        closeBtn.addEventListener('click', toggleSidebar);
        overlay.addEventListener('click', toggleSidebar);
    }

    // --- Auto-Resizing Textarea ---
    if (queryInput) {
        queryInput.addEventListener('input', () => {
            queryInput.style.height = 'auto';
            queryInput.style.height = `${queryInput.scrollHeight}px`;
        });
    }

    // --- Module/View Switching Logic ---
    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetViewId = button.dataset.view;
            if (!targetViewId) return;

            navButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            views.forEach(view => view.classList.remove('active'));
            const targetView = document.getElementById(targetViewId);
            if (targetView) targetView.classList.add('active');
            
            if (headerIcon && headerTitle && headerSubtitle) {
                const iconClass = button.querySelector('i')?.className;
                const title = button.querySelector('span')?.firstChild?.textContent;
                const subtitle = button.querySelector('small')?.textContent;
                
                if (iconClass) headerIcon.className = `${iconClass} header-icon`;
                if (title) headerTitle.firstChild.textContent = title;
                if (subtitle) headerSubtitle.textContent = subtitle;
            }

            if (window.innerWidth <= 900) toggleSidebar();
        });
    });
    
    // --- Sidebar Search Functionality ---
    if (sidebarSearchInput) {
        sidebarSearchInput.addEventListener('keyup', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            document.querySelectorAll('.quick-btn-grid .quick-query-btn').forEach(button => {
                button.style.display = button.textContent.toLowerCase().includes(searchTerm) ? 'flex' : 'none';
            });
        });
    }

    // --- Header Language Popover Logic ---
    if (headerLangBtn && langPopover && popoverCloseBtn) {
        headerLangBtn.addEventListener('click', () => langPopover.classList.toggle('open'));
        popoverCloseBtn.addEventListener('click', () => langPopover.classList.remove('open'));
        
        document.addEventListener('click', (e) => {
            if (!langPopover.contains(e.target) && !headerLangBtn.contains(e.target)) {
                langPopover.classList.remove('open');
            }
        });

        if (popoverSearchInput) {
            popoverSearchInput.addEventListener('keyup', (e) => {
                const searchTerm = e.target.value.toLowerCase();
                if (popoverLangList) {
                    popoverLangList.querySelectorAll('.language-item').forEach(button => {
                        button.style.display = button.textContent.toLowerCase().includes(searchTerm) ? 'flex' : 'none';
                    });
                }
            });
        }
    }

    // --- Language Selection Logic (FIXED) ---
    const handleLanguageSelection = (clickedButton) => {
        const langName = clickedButton.querySelector('.lang-name')?.textContent;
        if (!langName) return;
        
        console.log("🌐 Language button clicked:", langName);
        
        const languageMap = {
            'English': 'en',
            'Hindi': 'hi',
            'Bengali': 'bn',
            'Tamil': 'ta',
            'Telugu': 'te',
            'Gujarati': 'gu',
            'Marathi': 'mr',
            'Punjabi': 'pa',
            'Assamese': 'as',
            'Kannada': 'kn',
            'Malayalam': 'ml',
            'Odia': 'or',
            'Nepali': 'ne'
        };
        
        // Update current language
        const newLanguage = languageMap[langName] || 'en';
        currentLanguage = newLanguage;
        console.log("✅ Language changed to:", currentLanguage);
        
        // Update visual state
        document.querySelectorAll('.language-list .language-item').forEach(btn => {
            if (btn.querySelector('.lang-name')?.textContent === langName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Show confirmation
        const confirmationMessages = {
            'en': '✅ Language changed to English',
            'ml': '✅ ഭാഷ മലയാളത്തിലേക്ക് മാറ്റി',
            'hi': '✅ भाषा हिंदी में बदली गई',
            'ta': '✅ மொழி தமிழுக்கு மாற்றப்பட்டது',
            'te': '✅ భాష తెలుగులోకి మార్చబడింది'
        };
        
        createSystemMessage(confirmationMessages[currentLanguage] || confirmationMessages['en']);
        
        // Close popover
        if (langPopover && langPopover.classList.contains('open')) {
            langPopover.classList.remove('open');
        }
    };

    // Add event listeners for language selection
    document.querySelectorAll('.language-list').forEach(list => {
        list.addEventListener('click', (e) => {
            const button = e.target.closest('.language-item');
            if (button) {
                handleLanguageSelection(button);
            }
        });
    });

    // --- Chat Clearing Logic ---
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear the chat history? This cannot be undone.')) {
                chatWindow.innerHTML = '';
                createWelcomeMessage();
                scrollToBottom();
            }
        });
    }

    // --- CHAT FUNCTIONALITY (FIXED) ---
    
    // Show/Hide loading
    function showLoading(message = "Processing your query...") {
        if (loadingOverlay) {
            const loadingText = document.getElementById('loadingText');
            if (loadingText) loadingText.textContent = message;
            loadingOverlay.style.display = 'flex';
        }
    }

    function hideLoading() {
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    // Create different types of messages
    function createUserMessage(textContent) {
        const userBubble = document.createElement('div');
        userBubble.className = 'message-bubble user-message';
        userBubble.textContent = textContent;
        chatWindow.appendChild(userBubble);
        console.log("✅ User message added:", textContent);
    }

    function createAiMessage(htmlContent, category = null, isDemo = false) {
        const newAiBubble = document.createElement('div');
        newAiBubble.className = 'message-bubble ai-message';
        
        let categoryBadge = '';
        if (category) {
            const categoryNames = {
                'pest': '🐛 Pest Control',
                'weather': '🌤️ Weather',
                'fertilizer': '🌱 Fertilizer',
                'market': '💰 Market',
                'subsidy': '🏛️ Government',
                'general': '💬 General'
            };
            categoryBadge = `<div class="category-badge">${categoryNames[category] || '💬 General'}</div>`;
        }
        
        let demoBadge = isDemo ? '<div class="demo-badge">🤖 Demo Mode</div>' : '';
        
        newAiBubble.innerHTML = `
            ${categoryBadge}
            ${demoBadge}
            <div>${htmlContent}</div>
        `;
        chatWindow.appendChild(newAiBubble);
        console.log("✅ AI message added");
    }

    function createErrorMessage(errorText) {
        const errorBubble = document.createElement('div');
        errorBubble.className = 'message-bubble ai-message error-message';
        errorBubble.innerHTML = `
            <div class="error-badge">❌ Error</div>
            <div>${errorText}</div>
        `;
        chatWindow.appendChild(errorBubble);
        console.log("❌ Error message added:", errorText);
    }

    function createSystemMessage(text) {
        const systemBubble = document.createElement('div');
        systemBubble.className = 'message-bubble system-message';
        systemBubble.innerHTML = `
            <div class="system-badge">⚙️ System</div>
            <div>${text}</div>
        `;
        chatWindow.appendChild(systemBubble);
        scrollToBottom();
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (systemBubble.parentNode) {
                systemBubble.remove();
            }
        }, 3000);
        console.log("ℹ️ System message added:", text);
    }

    function createWelcomeMessage() {
        createAiMessage("🌾 Namaste! I'm your AI Krishi Officer. I can help you with crop problems, weather advice, market prices, and government schemes. Ask me anything in your preferred language!");
    }

    function scrollToBottom() {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Main API function (FIXED)
    async function sendQueryToBackend(userQuery) {
        try {
            console.log("📤 Sending query:", userQuery, "Language:", currentLanguage);
            showLoading();
            
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: userQuery,
                    language: currentLanguage
                })
            });

            console.log("📡 Response status:", response.status);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("📨 Response data:", data);
            
            hideLoading();

            if (data.success) {
                createAiMessage(
                    data.response, 
                    data.category, 
                    data.is_demo
                );
                scrollToBottom();
                console.log("✅ Response received successfully");
            } else {
                createErrorMessage(data.error || 'Sorry, something went wrong. Please try again.');
                scrollToBottom();
            }

        } catch (error) {
            hideLoading();
            console.error('💥 Error calling backend:', error);
            createErrorMessage('Unable to connect to the server. Please check your connection and try again.');
            scrollToBottom();
        }
    }

    // Handle submit (FIXED)
    const handleSubmit = async () => {
        const userText = queryInput.value.trim();
        console.log("🎯 Submit triggered, text:", userText);
        
        if (userText) {
            // Add user message to chat
            createUserMessage(userText);
            scrollToBottom();
            
            // Clear input
            queryInput.value = '';
            queryInput.style.height = 'auto';
            
            // Send to backend
            await sendQueryToBackend(userText);
        } else {
            console.log("⚠️ Empty query, ignoring");
        }
    };

    // Event listeners for submit (FIXED)
    if (submitBtn) {
        submitBtn.addEventListener('click', (e) => {
            console.log("🖱️ Submit button clicked");
            e.preventDefault();
            handleSubmit();
        });
    }

    if (queryInput) {
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                console.log("⌨️ Enter key pressed");
                e.preventDefault();
                handleSubmit();
            }
        });
    }

    // Voice input functionality
    if (voiceBtn) {
        voiceBtn.addEventListener('click', () => {
            alert('Voice input feature will be implemented soon!');
        });
    }

    // --- Initial Setup ---
    createWelcomeMessage();
    scrollToBottom();
    
    // Make testChat function available globally for debugging
    window.testChat = function() {
        console.log("🧪 Running test chat...");
        queryInput.value = "test message";
        handleSubmit();
    };
    
    window.getCurrentLanguage = function() {
        console.log("Current language:", currentLanguage);
        return currentLanguage;
    };
    
    console.log("✅ KisanMitra initialization complete");
    console.log("💡 Debug commands: testChat(), getCurrentLanguage()");
});