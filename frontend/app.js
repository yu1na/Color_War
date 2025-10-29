/**
 * 정치 댓글 AI 시뮬레이터 - 프론트엔드 (로컬 LLM 버전)
 */

const API_BASE = window.location.origin;

// 전역 상태
let debateState = null;
let autoMode = false;
let autoInterval = null;

// DOM 요소
const elements = {
    // 서버 상태
    serverStatus: document.getElementById('serverStatus'),
    
    // 댓글 수집
    leftComments: document.getElementById('leftComments'),
    rightComments: document.getElementById('rightComments'),
    submitLeftBtn: document.getElementById('submitLeftBtn'),
    submitRightBtn: document.getElementById('submitRightBtn'),
    leftCount: document.getElementById('leftCount'),
    rightCount: document.getElementById('rightCount'),
    personaStatus: document.getElementById('personaStatus'),
    
    // 페르소나 생성
    analysisSection: document.getElementById('analysisSection'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    analysisLoading: document.getElementById('analysisLoading'),
    analysisResult: document.getElementById('analysisResult'),
    
    // 토론
    debateSection: document.getElementById('debateSection'),
    startDebateBtn: document.getElementById('startDebateBtn'),
    pauseBtn: document.getElementById('pauseBtn'),
    resumeBtn: document.getElementById('resumeBtn'),
    stopBtn: document.getElementById('stopBtn'),
    messageCount: document.getElementById('messageCount'),
    currentTopic: document.getElementById('currentTopic'),
    debateMessages: document.getElementById('debateMessages'),
    debateEndMessage: document.getElementById('debateEndMessage'),
    totalMessages: document.getElementById('totalMessages'),
    restartBtn: document.getElementById('restartBtn')
};

// 이벤트 리스너 설정
function setupEventListeners() {
    elements.submitLeftBtn.addEventListener('click', () => submitComments('left'));
    elements.submitRightBtn.addEventListener('click', () => submitComments('right'));
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.startDebateBtn.addEventListener('click', startDebate);
    elements.pauseBtn.addEventListener('click', handlePause);
    elements.resumeBtn.addEventListener('click', handleResume);
    elements.stopBtn.addEventListener('click', handleStop);
    elements.restartBtn.addEventListener('click', handleRestart);
}

// 서버 상태 확인
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const health = await response.json();
        
        elements.serverStatus.innerHTML = `
            ✓ 서버 연결됨 | 
            ${health.cuda_available ? '🎮 GPU' : '💻 CPU'} 모드 | 
            페르소나: ${health.persona_ready ? '✓ 준비됨' : '⏳ 대기중'}
        `;
        elements.serverStatus.className = 'server-status online';
        
        updateStats();
    } catch (error) {
        elements.serverStatus.innerHTML = '✗ 서버 연결 실패 - backend/main.py를 실행하세요';
        elements.serverStatus.className = 'server-status offline';
    }
}

// 댓글 수집
async function submitComments(side) {
    const textarea = side === 'left' ? elements.leftComments : elements.rightComments;
    const text = textarea.value.trim();
    
    if (!text) {
        alert('댓글을 입력하세요.');
        return;
    }
    
    const comments = text.split('\n').filter(c => c.trim());
    const btn = side === 'left' ? elements.submitLeftBtn : elements.submitRightBtn;
    
    try {
        btn.disabled = true;
        btn.textContent = '⏳ 수집 중...';
        
        const response = await fetch(`${API_BASE}/api/comments/${side}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comments })
        });
        
        if (response.ok) {
            const stats = await response.json();
            updateStatsDisplay(stats);
            // textarea.value = ''; // 입력한 내용 유지
            
            const sideName = side === 'left' ? '좌파' : '우파';
            alert(`✅ ${comments.length}개 ${sideName} 댓글이 수집되었습니다!\n\n💡 입력 내용은 그대로 유지됩니다.\n${stats.persona_ready ? '🎉 양쪽 페르소나가 모두 준비되었습니다!' : '⏳ 다른 진영 댓글도 수집해주세요.'}`);
        } else {
            alert('댓글 수집 실패');
        }
    } catch (error) {
        alert('서버 오류: ' + error.message);
    } finally {
        btn.disabled = false;
        const sideName = side === 'left' ? '좌파' : '우파';
        btn.textContent = `${sideName} 댓글 수집`;
    }
}

// 통계 업데이트
async function updateStats() {
    try {
        const response = await fetch(`${API_BASE}/api/comments/stats`);
        const stats = await response.json();
        updateStatsDisplay(stats);
    } catch (error) {
        console.error('통계 조회 실패:', error);
    }
}

function updateStatsDisplay(stats) {
    elements.leftCount.textContent = stats.left_count;
    elements.rightCount.textContent = stats.right_count;
    
    if (stats.persona_ready) {
        elements.personaStatus.innerHTML = `
            <div class="success-message">
                ✓ 페르소나 학습 완료! 
                (좌파: ${stats.left_count}개, 우파: ${stats.right_count}개)
                <br><strong>👇 아래로 스크롤하여 "2단계: 댓글 분석" 버튼을 눌러주세요!</strong>
            </div>
        `;
        elements.analysisSection.style.display = 'block';
        
        // 잠시 후 스크롤 (애니메이션을 위해)
        setTimeout(() => {
            elements.analysisSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 500);
    } else {
        elements.personaStatus.innerHTML = `
            <div class="info-message">
                각 진영에 최소 5개의 댓글이 필요합니다.
                (좌파: ${stats.left_count}/5, 우파: ${stats.right_count}/5)
            </div>
        `;
    }
}

// 댓글 분석 (페르소나 생성)
async function handleAnalyze() {
    elements.analyzeBtn.disabled = true;
    elements.analysisLoading.style.display = 'block';
    elements.analysisLoading.innerHTML = `
        <div class="spinner"></div>
        <p>🤖 AI가 댓글 패턴을 분석하여 페르소나를 생성하는 중...<br>(1-2분 소요될 수 있습니다)</p>
    `;
    
    try {
        // 페르소나 생성 API 호출
        const response = await fetch(`${API_BASE}/api/comments/generate-persona`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            displayAnalysisResult(result);
            elements.debateSection.style.display = 'block';
            elements.debateSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            const error = await response.json();
            alert('페르소나 생성 실패: ' + error.detail);
        }
    } catch (error) {
        alert('페르소나 생성 중 오류 발생: ' + error.message);
    } finally {
        elements.analyzeBtn.disabled = false;
        elements.analysisLoading.style.display = 'none';
    }
}

function displayAnalysisResult(result) {
    const leftPersona = result.left_persona || {};
    const rightPersona = result.right_persona || {};
    
    elements.analysisResult.innerHTML = `
        <h3>✅ 페르소나 생성 완료!</h3>
        <div class="success-message" style="margin: 20px 0;">
            ${result.message || '좌파/우파 페르소나가 생성되었습니다!'}
        </div>
        
        <div class="persona-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <div class="persona-card" style="background: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 4px solid #4a90e2;">
                <h4>🔵 좌파 페르소나</h4>
                <p><strong>특징:</strong> ${leftPersona.summary || 'N/A'}</p>
                <p><strong>말투:</strong> ${(leftPersona.tone || []).join(', ') || 'N/A'}</p>
                <p><strong>키워드:</strong> ${(leftPersona.keywords || []).slice(0, 5).join(', ') || 'N/A'}</p>
            </div>
            
            <div class="persona-card" style="background: #ffebee; padding: 20px; border-radius: 10px; border-left: 4px solid #e74c3c;">
                <h4>🔴 우파 페르소나</h4>
                <p><strong>특징:</strong> ${rightPersona.summary || 'N/A'}</p>
                <p><strong>말투:</strong> ${(rightPersona.tone || []).join(', ') || 'N/A'}</p>
                <p><strong>키워드:</strong> ${(rightPersona.keywords || []).slice(0, 5).join(', ') || 'N/A'}</p>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <p style="font-size: 18px; font-weight: bold; color: #667eea;">
                👇 이제 3단계로 이동하여 댓글 전쟁을 시작하세요!
            </p>
        </div>
    `;
}

// 토론 시작
async function startDebate() {
    try {
        const response = await fetch(`${API_BASE}/api/debate/start`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            debateState = data.state;
            
            elements.startDebateBtn.style.display = 'none';
            elements.pauseBtn.style.display = 'inline-block';
            elements.stopBtn.style.display = 'inline-block';
            
            // 빈 메시지 제거하고 토론 준비
            elements.debateMessages.innerHTML = '<div class="info-message" style="text-align: center; padding: 20px;">🤖 AI가 댓글 생성 중...</div>';
            elements.debateEndMessage.style.display = 'none';
            
            updateDebateUI();
            startAutoFight();
        } else {
            alert('토론 시작 실패');
        }
    } catch (error) {
        alert('오류: ' + error.message);
    }
}

// 자동 싸움 시작
function startAutoFight() {
    autoMode = true;
    autoInterval = setInterval(async () => {
        if (debateState && debateState.is_active) {
            await generateNextMessage();
        } else {
            stopAutoFight();
        }
    }, 3000); // 3초 간격
}

function stopAutoFight() {
    autoMode = false;
    if (autoInterval) {
        clearInterval(autoInterval);
        autoInterval = null;
    }
}

// 다음 메시지 생성
async function generateNextMessage() {
    try {
        const response = await fetch(`${API_BASE}/api/debate/next`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            debateState = data.state;
            
            addMessageToUI(data.message);
            updateDebateUI();
            
            if (!debateState.is_active) {
                handleDebateEnd();
            }
        }
    } catch (error) {
        console.error('메시지 생성 오류:', error);
    }
}

function addMessageToUI(message) {
    // 첫 메시지인 경우 로딩 메시지 제거
    const loadingMsg = elements.debateMessages.querySelector('.info-message');
    if (loadingMsg) {
        loadingMsg.remove();
    }
    
    const messageCard = document.createElement('div');
    messageCard.className = `message-card ${message.side}`;
    
    const sideEmoji = message.side === 'left' ? '🔵' : '🔴';
    const sideName = message.side === 'left' ? '좌파' : '우파';
    
    messageCard.innerHTML = `
        <div class="message-header">
            <span class="message-author">${sideEmoji} ${sideName}</span>
        </div>
        <div class="message-content">${message.content}</div>
    `;
    
    elements.debateMessages.appendChild(messageCard);
    elements.debateMessages.scrollTop = elements.debateMessages.scrollHeight;
}

function updateDebateUI() {
    elements.messageCount.textContent = debateState.message_count;
    elements.currentTopic.textContent = debateState.current_topic || '-';
}

function handlePause() {
    stopAutoFight();
    elements.pauseBtn.style.display = 'none';
    elements.resumeBtn.style.display = 'inline-block';
}

function handleResume() {
    startAutoFight();
    elements.pauseBtn.style.display = 'inline-block';
    elements.resumeBtn.style.display = 'none';
}

function handleStop() {
    stopAutoFight();
    if (debateState) {
        debateState.is_active = false;
    }
    handleDebateEnd();
}

function handleDebateEnd() {
    stopAutoFight();
    elements.totalMessages.textContent = debateState?.message_count || 0;
    elements.debateEndMessage.style.display = 'block';
    elements.pauseBtn.style.display = 'none';
    elements.stopBtn.style.display = 'none';
}

async function handleRestart() {
    stopAutoFight();
    
    try {
        await fetch(`${API_BASE}/api/debate/reset`, { method: 'POST' });
        await fetch(`${API_BASE}/api/comments/reset`, { method: 'POST' });
        
        location.reload();
    } catch (error) {
        alert('초기화 실패: ' + error.message);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkServerStatus();
    setInterval(checkServerStatus, 10000); // 10초마다 상태 확인
    console.log('정치 댓글 AI 시뮬레이터 (로컬 LLM) 로드 완료');
});

