// ========================================
// ROBERTA SENTIMENT ANALYSIS - MAIN SCRIPT
// ========================================

console.log("🔵 Script loaded successfully");

// ========================================
// CONFIGURATION
// ========================================
const API_BASE_URL = 'http://13.48.16.109:8001';
const POLL_INTERVAL = 2000; // 2 seconds

// ========================================
// DOM ELEMENTS
// ========================================
const form = document.getElementById('analysisForm');
const searchMethodSelect = document.getElementById('searchMethod');
const urlInputGroup = document.getElementById('urlInputGroup');
const keywordsInputGroup = document.getElementById('keywordsInputGroup');
const submitBtn = document.getElementById('submitBtn');
const languageSelect = document.getElementById('language');

// Modal elements
const analysisModal = document.getElementById('analysisModal');
const modalClose = document.getElementById('modalClose');
const modalProgressFill = document.getElementById('modalProgressFill');
const modalStatus = document.getElementById('modalStatus');
const modalProgress = document.getElementById('modalProgress');
const resultsSummary = document.getElementById('resultsSummary');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const downloadPdfBtn = document.getElementById('downloadPdfBtn');

// Chatbot elements
const chatbotTrigger = document.getElementById('chatbotTrigger');
const chatbotWindow = document.getElementById('chatbotWindow');
const chatbotClose = document.getElementById('chatbotClose');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const chatbotMessages = document.getElementById('chatbotMessages');

let currentJobId = null;

console.log("🔵 Form elements initialized");

// ========================================
// LANGUAGE SWITCHING
// ========================================
const translations = {
    de: {
        heroSubtitle: "Performance-Driven AI Solution",
        heroTitle: "Wir machen aus<br/>Kundenfeedback Insights",
        formTitle: "Starten Sie Ihre Analyse",
        formSubtitle: "Analysieren Sie Kundenfeedback mit modernster KI-Technologie",
        companyLabel: "Firmenname *",
        companyPlaceholder: "z.B. Awesome Enterprise Software GmbH",
        methodLabel: "Analysemethode *",
        emailLabel: "E-Mail für Berichtszustellung *",
        emailPlaceholder: "ihre.email@firma.de",
        emailHint: "💡 Mehrere E-Mails möglich: email1@firma.de, email2@firma.de",
        promptLabel: "Individuelle Analyseanforderungen (optional)",
        promptPlaceholder: "Spezielle Aspekte, die Sie analysieren möchten...",
        submitBtn: "🚀 Analyse starten",
        processing: "⏳ Analyse läuft...",
        chatPlaceholder: "Ihre Nachricht...",
        chatSend: "Senden"
    },
    en: {
        heroSubtitle: "Performance-Driven AI Solution",
        heroTitle: "We turn customer feedback<br/>into insights",
        formTitle: "Start Your Analysis",
        formSubtitle: "Analyze customer feedback with cutting-edge AI technology",
        companyLabel: "Company Name *",
        companyPlaceholder: "e.g. Awesome Enterprise Software Inc.",
        methodLabel: "Analysis Method *",
        emailLabel: "Email for Report Delivery *",
        emailPlaceholder: "your.email@company.com",
        emailHint: "💡 Multiple emails possible: email1@company.com, email2@company.com",
        promptLabel: "Custom Analysis Requirements (optional)",
        promptPlaceholder: "Special aspects you want to analyze...",
        submitBtn: "🚀 Start Analysis",
        processing: "⏳ Processing...",
        chatPlaceholder: "Your message...",
        chatSend: "Send"
    }
};

function updateLanguage(lang) {
    const t = translations[lang];
    
    // Update UI text
    document.querySelector('.hero .subtitle').textContent = t.heroSubtitle;
    document.querySelector('.hero h1').innerHTML = t.heroTitle;
    document.querySelector('.form-card h2').textContent = t.formTitle;
    document.querySelector('.form-card .subtitle').textContent = t.formSubtitle;
    document.querySelector('label[for="companyName"]').textContent = t.companyLabel;
    document.getElementById('companyName').placeholder = t.companyPlaceholder;
    document.querySelector('label[for="searchMethod"]').textContent = t.methodLabel;
    document.querySelector('label[for="email"]').textContent = t.emailLabel;
    document.getElementById('email').placeholder = t.emailPlaceholder;
    document.querySelector('#email + small').textContent = t.emailHint;
    document.querySelector('label[for="customPrompt"]').textContent = t.promptLabel;
    document.getElementById('customPrompt').placeholder = t.promptPlaceholder;
    document.getElementById('chatInput').placeholder = t.chatPlaceholder;
    document.getElementById('chatSend').textContent = t.chatSend;
    
    if (submitBtn.textContent.includes('🚀')) {
        submitBtn.textContent = t.submitBtn;
    }
}

languageSelect.addEventListener('change', function() {
    updateLanguage(this.value);
});

// Set initial language on page load
updateLanguage(languageSelect.value);

// ========================================
// FORM HANDLERS
// ========================================

// Toggle input fields based on search method
searchMethodSelect.addEventListener('change', function() {
    urlInputGroup.style.display = this.value === 'url' ? 'block' : 'none';
    keywordsInputGroup.style.display = this.value === 'keywords' ? 'block' : 'none';
});

// Email validation helper
function validateEmails(emailString) {
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const emails = emailString.split(',').map(e => e.trim());
    const invalidEmails = emails.filter(email => !emailPattern.test(email));
    
    if (invalidEmails.length > 0) {
        return { valid: false, invalid: invalidEmails };
    }
    return { valid: true, emails: emails };
}

// Form submission
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Validate email addresses
    const emailInput = document.getElementById('email').value;
    const emailValidation = validateEmails(emailInput);
    
    if (!emailValidation.valid) {
        alert('❌ Invalid email address(es):\n' + emailValidation.invalid.join('\n'));
        return;
    }
    
    const formData = {
        email: emailInput,
        customPrompt: document.getElementById('customPrompt').value || null,
        searchMethod: document.getElementById('searchMethod').value,
        language: languageSelect.value,
                job_id: localStorage.getItem('recentJobId')
    };

    if (formData.searchMethod === 'url') {
        formData.url = document.getElementById('targetUrl').value;
    } else if (formData.searchMethod === 'keywords') {
        formData.url = document.getElementById('keywords').value;
    } else if (formData.searchMethod === 'demo') {
        formData.url = 'demo';
    }

    console.log("🟢 Form submitted with data:", formData);

    // Show modal
    analysisModal.classList.add('active');
    modalProgress.style.display = 'block';
    resultsSummary.style.display = 'none';
    modalProgressFill.style.width = '0%';
    modalProgressFill.textContent = '0%';
    modalStatus.textContent = 'Initialisierung...';
    submitBtn.disabled = true;
    submitBtn.textContent = translations[languageSelect.value].processing;

    try {
        console.log("🔵 Sending API request:", formData);
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ API Error:', errorText);
            throw new Error(`API returned ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        console.log("🟢 API Response:", data);
        
        if (!data.job_id) {
            console.error('❌ No job_id in response!', data);
            throw new Error('No job_id received from server');
        }
        
        currentJobId = data.job_id;
        localStorage.setItem('recentJobId', currentJobId);

        // Poll for progress
        const pollInterval = setInterval(async () => {
            const statusResponse = await fetch(`${API_BASE_URL}/api/status/${currentJobId}`);
            const statusData = await statusResponse.json();

            const progress = Math.round(statusData.progress);
            modalProgressFill.style.width = progress + '%';
            modalProgressFill.textContent = progress + '%';
            modalStatus.textContent = statusData.message;

            if (statusData.status === 'completed') {
                clearInterval(pollInterval);
                
                // Fetch sentiment summary
                try {
                    const resultsResponse = await fetch(`${API_BASE_URL}/api/results/${currentJobId}/data`);
                    const resultsData = await resultsResponse.json();
                    
                    console.log('Results data:', resultsData);
                    
                    let totalPositive = 0;
                    let totalNegative = 0;
                    let totalNeutral = 0;
                    let totalReviews = 0;
                    
                    if (resultsData.statistics) {
                        totalPositive = resultsData.statistics.positive || 0;
                        totalNegative = resultsData.statistics.negative || 0;
                        totalNeutral = resultsData.statistics.neutral || 0;
                        totalReviews = resultsData.statistics.total_reviews || 0;
                    } else {
                        const trendsData = resultsData.trends || {};
                        const summary = trendsData.summary || {};
                        totalPositive = summary.total_positive || 0;
                        totalNegative = summary.total_negative || 0;
                        totalNeutral = summary.total_neutral || 0;
                        totalReviews = summary.total_reviews || 0;
                    }
                    
                    console.log('✨ FINAL Counts:', { totalPositive, totalNegative, totalNeutral, totalReviews });
                    
                    // Update UI
                    document.getElementById('positiveCount').textContent = totalPositive;
                    document.getElementById('negativeCount').textContent = totalNegative;
                    document.getElementById('neutralCount').textContent = totalNeutral;
                    
                    if (totalReviews > 0) {
                        document.getElementById('positivePercent').textContent = 
                            Math.round((totalPositive / totalReviews) * 100) + '%';
                        document.getElementById('negativePercent').textContent = 
                            Math.round((totalNegative / totalReviews) * 100) + '%';
                        document.getElementById('neutralPercent').textContent = 
                            Math.round((totalNeutral / totalReviews) * 100) + '%';
                    }
                } catch (err) {
                    console.error('Error fetching results:', err);
                }
                
                modalProgress.style.display = 'none';
                resultsSummary.style.display = 'block';
                
                submitBtn.disabled = false;
                submitBtn.textContent = translations[languageSelect.value].submitBtn;
                
            } else if (statusData.status === 'failed') {
                clearInterval(pollInterval);
                modalStatus.textContent = '❌ Error: ' + statusData.message;
                submitBtn.disabled = false;
                submitBtn.textContent = translations[languageSelect.value].submitBtn;
            }
        }, POLL_INTERVAL);

    } catch (error) {
        console.error('Error:', error);
        modalStatus.textContent = '❌ Connection error. Please try again.';
        submitBtn.disabled = false;
        submitBtn.textContent = translations[languageSelect.value].submitBtn;
    }
});

// ========================================
// MODAL HANDLERS
// ========================================

modalClose.addEventListener('click', () => {
    analysisModal.classList.remove('active');
});

newAnalysisBtn.addEventListener('click', () => {
    analysisModal.classList.remove('active');
    form.reset();
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

downloadPdfBtn.addEventListener('click', () => {
    if (currentJobId) {
        window.open(`${API_BASE_URL}/api/results/${currentJobId}/pdf`, '_blank');
    }
});

// ========================================
// VIDEO SCRIPT GENERATOR
// ========================================

const generateVideoScriptBtn = document.getElementById('generateVideoScriptBtn');
const videoScriptSection = document.getElementById('videoScriptSection');

generateVideoScriptBtn.addEventListener('click', async () => {
    if (!currentJobId) return;
    
    // Toggle script section visibility
    const isVisible = videoScriptSection.style.display === 'block';
    
    if (isVisible) {
        // Close the section
        videoScriptSection.style.display = 'none';
        const imagePromptsSection = document.getElementById('imagePromptsSection');
        if (imagePromptsSection) {
            imagePromptsSection.style.display = 'none';
        }
        generateVideoScriptBtn.textContent = '🎬 Video Script erstellen';
        return;
    }
    
    // Show script section
    videoScriptSection.style.display = 'block';
    
    // Disable button during generation
    generateVideoScriptBtn.disabled = true;
    generateVideoScriptBtn.textContent = '⏳ Generierung läuft...';
    
    // Reset script content
    document.getElementById('scriptHook').textContent = 'Generierung läuft...';
    document.getElementById('scriptMessages').textContent = 'Generierung läuft...';
    document.getElementById('scriptCTA').textContent = 'Generierung läuft...';
    document.getElementById('scriptVisuals').textContent = 'Generierung läuft...';
    
    // Hide image prompts initially
    const imagePromptsSection = document.getElementById('imagePromptsSection');
    if (imagePromptsSection) {
        imagePromptsSection.style.display = 'none';
    }
    
    try {
        const language = languageSelect.value;
        const response = await fetch(`${API_BASE_URL}/api/generate-video-script`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                job_id: currentJobId,
                language: language,
                duration: 30
            })
        });
        
        if (!response.ok) {
            throw new Error('Video script generation failed');
        }
        
        const scriptData = await response.json();
        
        // Update UI with generated script
        document.getElementById('scriptHook').textContent = scriptData.hook || 'N/A';
        document.getElementById('scriptMessages').textContent = scriptData.key_messages.join('\n\n') || 'N/A';
        document.getElementById('scriptCTA').textContent = scriptData.call_to_action || 'N/A';
        document.getElementById('scriptVisuals').textContent = scriptData.visual_suggestions.join('\n') || 'N/A';
        
        // Display image prompts if available
        if (scriptData.image_prompts && imagePromptsSection) {
            imagePromptsSection.style.display = 'block';
            document.getElementById('promptHook').textContent = scriptData.image_prompts.hook || 'N/A';
            document.getElementById('promptKeyMessages').textContent = scriptData.image_prompts.key_messages || 'N/A';
            document.getElementById('promptCTA').textContent = scriptData.image_prompts.cta || 'N/A';
            document.getElementById('promptVisuals').textContent = scriptData.image_prompts.visuals || 'N/A';
            
            // Store prompts for potential image generation
            window.currentImagePrompts = scriptData.image_prompts;
        }
        
        // Re-enable button
        generateVideoScriptBtn.disabled = false;
        generateVideoScriptBtn.textContent = '🎬 Video Script erstellen';
        
    } catch (error) {
        console.error('Error generating video script:', error);
        document.getElementById('scriptHook').textContent = '❌ Fehler bei der Generierung';
        document.getElementById('scriptMessages').textContent = 'Bitte versuchen Sie es erneut.';
        document.getElementById('scriptCTA').textContent = '';
        document.getElementById('scriptVisuals').textContent = '';
        
        generateVideoScriptBtn.disabled = false;
        generateVideoScriptBtn.textContent = '🎬 Video Script erstellen';
    }
});

// ========================================
// CAMPAIGN PREDICTOR
// ========================================

const openCampaignPredictorBtn = document.getElementById('openCampaignPredictorBtn');
const campaignPredictorSection = document.getElementById('campaignPredictorSection');
const predictCampaignBtn = document.getElementById('predictCampaignBtn');
const campaignVariantsInput = document.getElementById('campaignVariantsInput');
const campaignResults = document.getElementById('campaignResults');
const campaignScores = document.getElementById('campaignScores');
const bestPerformer = document.getElementById('bestPerformer');

openCampaignPredictorBtn.addEventListener('click', () => {
    const isVisible = campaignPredictorSection.style.display === 'block';
    campaignPredictorSection.style.display = isVisible ? 'none' : 'block';
    openCampaignPredictorBtn.textContent = isVisible ? '🎯 Campaign Optimizer' : '❌ Campaign Optimizer schließen';
});

predictCampaignBtn.addEventListener('click', async () => {
    const variants = campaignVariantsInput.value.trim();
    
    if (!variants) {
        alert(currentLanguage === 'de' ? 'Bitte geben Sie mindestens eine Werbe-Variante ein!' : 'Please enter at least one ad variant!');
        return;
    }
    
    const variantList = variants.split('\n').filter(v => v.trim().length > 0);
    
    if (variantList.length === 0) {
        alert(currentLanguage === 'de' ? 'Bitte geben Sie gültige Werbe-Texte ein!' : 'Please enter valid ad copy!');
        return;
    }
    
    predictCampaignBtn.disabled = true;
    predictCampaignBtn.textContent = '⏳ Analysiere...';
    campaignResults.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/predict-campaign`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                variants: variantList,
                language: languageSelect.value,
                job_id: localStorage.getItem('recentJobId')
            })
        });
        
        if (!response.ok) {
            throw new Error('Campaign prediction failed');
        }
        
        const data = await response.json();
        displayCampaignResults(data);
        
        predictCampaignBtn.disabled = false;
        predictCampaignBtn.textContent = '🚀 Varianten analysieren';
    } catch (error) {
        console.error('Error predicting campaign:', error);
        alert(languageSelect.value === 'de' ? 'Fehler bei der Analyse. Bitte versuchen Sie es erneut.' : 'Error during analysis. Please try again.');
        predictCampaignBtn.disabled = false;
        predictCampaignBtn.textContent = '🚀 Varianten analysieren';
    }
});

function displayCampaignResults(data) {
    campaignScores.innerHTML = '';
    
    data.predictions.forEach((pred, index) => {
        const scoreDiv = document.createElement('div');
        scoreDiv.className = 'variant-score';
        const scoreClass = pred.score >= 7 ? 'positive' : pred.score >= 5 ? 'neutral' : 'negative';
        scoreDiv.classList.add(scoreClass);
        
        const variantText = document.createElement('div');
        variantText.className = 'variant-text';
        variantText.textContent = `${index + 1}. ${pred.text}`;
        
        const detailsDiv = document.createElement('div');
        detailsDiv.style.marginTop = '10px';
        detailsDiv.style.fontSize = '0.9em';
        
        detailsDiv.innerHTML = `
            <div style="margin-bottom: 5px"><strong>Score:</strong> ${pred.score}/10</div>
            <div style="margin-bottom: 5px; color: #2c5282"><strong>ROI:</strong> ${pred.roi_projection}</div>
            ${pred.sentiment_alignment ? `<div style="margin-bottom: 5px; font-size: 0.85em"><strong>Sentiment:</strong> ${pred.sentiment_alignment}</div>` : ''}
            ${pred.risks && pred.risks.length > 0 ? `<div style="margin-top: 8px; font-size: 0.85em"><strong>Risks:</strong><ul style="margin: 3px 0 0 20px; padding: 0;">${pred.risks.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
            ${pred.recommendation ? `<div style="margin-top: 8px; font-size: 0.85em; color: #2c5282"><strong>Recommendation:</strong> ${pred.recommendation}</div>` : ''}
        `;
        
        scoreDiv.appendChild(variantText);
        scoreDiv.appendChild(detailsDiv);
        campaignScores.appendChild(scoreDiv);
    });
    
    const best = data.best_variant;
    bestPerformer.innerHTML = `
        <h6>🏆 ${languageSelect.value === 'de' ? 'Empfehlung: Beste Variante' : 'Recommendation: Best Variant'}</h6>
        <div class="best-performer-text">"${best.text}"</div>
        <div class="best-performer-stats">
            <span>📊 Score: ${best.score}/10</span>
            <span>�� ROI: ${best.roi_projection}</span>
        </div>
    `;
    
    campaignResults.style.display = 'block';
}


// ========================================
// CHATBOT
// ========================================

chatbotTrigger.addEventListener('click', () => {
    chatbotWindow.classList.toggle('active');
});

chatbotClose.addEventListener('click', () => {
    chatbotWindow.classList.remove('active');
});

function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user' : 'bot'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = isUser ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatbotMessages.appendChild(messageDiv);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    addMessage(message, true);
    chatInput.value = '';
    
    const recentJobId = localStorage.getItem('recentJobId');
    
    // Try job-specific chat first if we have a job ID
    if (recentJobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/results/${recentJobId}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log("🟢 Chat Response:", data);
                addMessage(data.answer, false);
                return; // Success, exit function
            }
            // If not OK, fall through to general chat
            console.log("Job-specific chat failed, falling back to general chat");
        } catch (error) {
            console.error('Job-specific chat error, falling back to general chat:', error);
            // Fall through to general chat
        }
    }
    
    // General chat - for questions before analysis or when job chat fails
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: message })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log("🟢 General Chat Response:", data);
            addMessage(data.answer, false);
        } else {
            addMessage("Sorry, I couldn't process your question. Please try again.", false);
        }
    } catch (error) {
        console.error('General chat error:', error);
        addMessage("I'm having trouble connecting. Please check your connection and try again.", false);
    }
}

function getSimpleBotResponse(userMessage) {
    const msg = userMessage.toLowerCase().trim();
    
    if (msg.includes('hello') || msg.includes('hi') || msg === 'hi' || msg.includes('hey')) {
        return 'Hello! 👋 I\'m your GenAI assistant. Run an analysis first, then I can answer detailed questions about your results. Or ask me about platform features!';
    }
    
    if (msg.includes('feature') || msg.includes('what can')) {
        return 'Our platform offers: 🧠 DistilBERT Sentiment Analysis, 📊 K-means Clustering, 🤖 LLaMA Summaries, 💰 Risk Assessment, 📄 PDF Reports, and ✉️ Email Delivery!';
    }
    
    if (msg.includes('who built') || msg.includes('developer') || msg.includes('created')) {
        return 'Built by Andrey Vlasenko in 2025 for LeadLink. Uses DistilBERT, LLaMA 3.1, and Docker. 👨‍💻';
    }
    
    if (msg.includes('who are you') || msg.includes('what are you')) {
        return 'I\'m an AI assistant! Once you run an analysis, I become much smarter - I can answer specific questions about your sentiment data using RAG. 🤖';
    }
    
    if (msg.includes('how') && (msg.includes('start') || msg.includes('use'))) {
        return 'Fill out the form above, choose Demo mode or enter your own data, then submit! You\'ll get a PDF report via email in 2-5 minutes. ⚡';
    }
    
    return 'Interesting question! 🤔 Run an analysis first, then I can give you detailed insights about your sentiment data. Or ask me about platform features!';
}

chatSend.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// ========================================
// NEW FEATURES - READY FOR IMPLEMENTATION
// ========================================

// TODO: Feature 1 - Video Script Generator
// TODO: Feature 2 - Campaign Performance Predictor  
// ========================================
// REAL-TIME DASHBOARD
// ========================================

const openDashboardBtn = document.getElementById('openDashboardBtn');
const dashboardSection = document.getElementById('dashboardSection');
const refreshDashboardBtn = document.getElementById('refreshDashboardBtn');
const exportCsvBtn = document.getElementById('exportCsvBtn');

let sentimentChart = null;
let gaugeChart = null;
let trendChart = null;
let currentJobIdForDashboard = null;

openDashboardBtn.addEventListener('click', () => {
    const isVisible = dashboardSection.style.display === 'block';
    
    if (!isVisible) {
        dashboardSection.style.display = 'block';
        openDashboardBtn.textContent = '❌ Live Monitor schließen';
        
        // Load dashboard data
        const recentJobId = localStorage.getItem('recentJobId');
        if (recentJobId) {
            currentJobIdForDashboard = recentJobId;
            loadDashboardData(recentJobId);
        }
    } else {
        dashboardSection.style.display = 'none';
        openDashboardBtn.textContent = '📊 Live Monitor';
    }
});

refreshDashboardBtn.addEventListener('click', () => {
    if (currentJobIdForDashboard) {
        loadDashboardData(currentJobIdForDashboard);
    }
});

exportCsvBtn.addEventListener('click', async () => {
    if (!currentJobIdForDashboard) {
        alert('Keine Daten zum Exportieren verfügbar');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/${currentJobIdForDashboard}/export`);
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dashboard_export_${currentJobIdForDashboard}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Export error:', error);
        alert('Export fehlgeschlagen');
    }
});

async function loadDashboardData(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/${jobId}`);
        if (!response.ok) throw new Error('Failed to load dashboard data');
        
        const data = await response.json();
        
        // Update charts
        updateSentimentChart(data.sentiment_distribution);
        updateGauge(data.positive_percentage);
        updateTrendChart(data.sentiment_trends);
        updateAlerts(data.alerts);
        
    } catch (error) {
        console.error('Dashboard error:', error);
    }
}

function updateSentimentChart(distribution) {
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [
                    distribution.POSITIVE || 0,
                    distribution.NEUTRAL || 0,
                    distribution.NEGATIVE || 0
                ],
                backgroundColor: [
                    'rgba(76, 175, 80, 0.95)',
                    'rgba(250, 190, 8, 0.8)',
                    'rgba(244, 67, 54, 0.8)'
                ],
                borderColor: [
                    '#4caf50',
                    '#fabe08',
                    '#f44336'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#fff',
                        font: {
                            family: 'Rajdhani',
                            size: 14
                        }
                    }
                }
            }
        }
    });
}

function updateGauge(percentage) {
    const ctx = document.getElementById('sentimentGauge').getContext('2d');
    
    if (gaugeChart) {
        gaugeChart.destroy();
    }
    
    document.getElementById('gaugeValue').textContent = `${percentage.toFixed(1)}%`;
    
    gaugeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [percentage, 100 - percentage],
                backgroundColor: [
                    percentage >= 70 ? 'rgba(76, 175, 80, 0.95)' :
                    percentage >= 50 ? 'rgba(250, 190, 8, 0.8)' :
                    'rgba(244, 67, 54, 0.8)',
                    'rgba(220, 220, 220, 0.5)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            circumference: 180,
            rotation: 270,
            cutout: '75%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            }
        }
    });
}

function updateTrendChart(trends) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    // Create time series data
    const labels = trends.map((t, i) => `T${i + 1}`);
    const positiveData = trends.map(t => t.positive || 0);
    const neutralData = trends.map(t => t.neutral || 0);
    const negativeData = trends.map(t => t.negative || 0);
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Positive',
                    data: positiveData,
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76, 175, 80, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'Neutral',
                    data: neutralData,
                    borderColor: '#fabe08',
                    backgroundColor: 'rgba(250, 190, 8, 0.2)',
                    tension: 0.4
                },
                {
                    label: 'Negative',
                    data: negativeData,
                    borderColor: '#f44336',
                    backgroundColor: 'rgba(244, 67, 54, 0.2)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#fff',
                        font: {
                            family: 'Rajdhani',
                            size: 14
                        }
                    }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(220, 220, 220, 0.5)' }
                },
                x: {
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(220, 220, 220, 0.5)' }
                }
            }
        }
    });
}

function updateAlerts(alerts) {
    const container = document.getElementById('alertsContainer');
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p class="no-alerts">Keine Alerts - Alles läuft stabil</p>';
        return;
    }
    
    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.severity}">
            <div>${alert.icon} ${alert.message}</div>
            <div class="alert-time">${alert.timestamp}</div>
        </div>
    `).join('');
}

console.log("✅ All systems loaded successfully");



// Video Modal Functionality - Wait for DOM and image prompts section
function initializeVideoModal() {
    const showVideoBtn = document.getElementById('showVideoBtn');
    const videoModal = document.getElementById('videoModal');
    const closeVideoBtn = document.getElementById('closeVideoBtn');
    const adVideo = document.getElementById('adVideo');

    if (!showVideoBtn || !videoModal || !closeVideoBtn || !adVideo) {
        console.log('⏳ Video modal elements not yet in DOM');
        return;
    }

    showVideoBtn.addEventListener('click', () => {
        videoModal.style.display = 'flex';
        adVideo.currentTime = 0;
        adVideo.play().catch(err => console.log('Autoplay prevented:', err));
    });

    closeVideoBtn.addEventListener('click', () => {
        videoModal.style.display = 'none';
        adVideo.pause();
        adVideo.currentTime = 0;
    });

    // Auto-close when video ends
    adVideo.addEventListener('ended', () => {
        videoModal.style.display = 'none';
        adVideo.currentTime = 0;
    });

    // Close on background click
    videoModal.addEventListener('click', (e) => {
        if (e.target === videoModal) {
            videoModal.style.display = 'none';
            adVideo.pause();
            adVideo.currentTime = 0;
        }
    });

    console.log("✅ Video modal functionality loaded");
}

// Initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeVideoModal);
} else {
    initializeVideoModal();
}

// Also try to initialize when image prompts section becomes visible
const observer = new MutationObserver(() => {
    const imagePromptsSection = document.getElementById('imagePromptsSection');
    if (imagePromptsSection && imagePromptsSection.style.display !== 'none') {
        initializeVideoModal();
        observer.disconnect();
    }
});

// Start observing when DOM is ready
setTimeout(() => {
    const imagePromptsSection = document.getElementById('imagePromptsSection');
    if (imagePromptsSection) {
        observer.observe(imagePromptsSection, { attributes: true, attributeFilter: ['style'] });
    }
}, 100);