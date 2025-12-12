// ColorWar API 클라이언트

const API_BASE = window.location.origin;

// ==================== UI 유틸리티 ====================
function toggleStep(stepId) {
    const step = document.getElementById(stepId);
    const icon = step.querySelector('.toggle-icon');
    
    step.classList.toggle('collapsed');
    icon.textContent = step.classList.contains('collapsed') ? '▶' : '▼';
}

function addLog(logId, message, type = 'info') {
    const logEl = document.getElementById(logId);
    if (!logEl) return;
    
    const logLine = document.createElement('div');
    logLine.className = `log-line log-${type}`;
    logLine.textContent = message;
    logEl.appendChild(logLine);
    
    // 자동 스크롤
    logEl.scrollTop = logEl.scrollHeight;
}

function clearLog(logId) {
    const logEl = document.getElementById(logId);
    if (logEl) {
        logEl.innerHTML = '<div class="log-line log-info">🚀 분석 시작...</div>';
    }
}

// ==================== YouTube 파이프라인 ====================
function normalizeYouTubeUrl(inputUrl) {
    try {
        const u = new URL(inputUrl);
        // youtu.be short link → watch?v=
        if (u.hostname === 'youtu.be') {
            const id = u.pathname.slice(1);
            if (id) return `https://www.youtube.com/watch?v=${id}`;
        }
        // shorts → watch?v=
        if (u.hostname.includes('youtube.com') && u.pathname.startsWith('/shorts/')) {
            const id = u.pathname.split('/')[2];
            if (id) return `https://www.youtube.com/watch?v=${id}`;
        }
        return inputUrl;
    } catch (e) {
        return inputUrl;
    }
}

async function runYoutubePipeline() {
    const rawUrl = document.getElementById('youtube-url').value;
    
    if (!rawUrl) {
        alert('YouTube URL을 입력해주세요');
        return;
    }
    const url = normalizeYouTubeUrl(rawUrl);
    
    const loading = document.getElementById('youtube-loading');
    const logBox = document.getElementById('youtube-log');
    const result = document.getElementById('youtube-result');
    const resultContent = document.getElementById('youtube-result-content');
    
    try {
        // UI 초기화
        loading.classList.add('show');
        logBox.classList.add('show');
        result.classList.remove('show');
        clearLog('youtube-log');
        
        // 로그 시작
        addLog('youtube-log', '📹 비디오 ID 추출 중...', 'info');
        addLog('youtube-log', '🎵 오디오 다운로드 중...', 'info');
        
        setTimeout(() => addLog('youtube-log', '🎤 음성 전사 중... (1~2분 소요)', 'info'), 500);
        setTimeout(() => addLog('youtube-log', '📝 요약 생성 중...', 'info'), 1000);
        setTimeout(() => addLog('youtube-log', '💬 댓글 수집 중...', 'info'), 1500);
        setTimeout(() => addLog('youtube-log', '🔍 대립 의견 분류 중...', 'info'), 2000);
        
        const response = await fetch(`${API_BASE}/api/structure/youtube-pipeline`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                youtube_url: url,
                topic: "영상 주제",
                rounds: 5
            })
        });
        
        const data = await response.json();
        
        // 비디오 ID 저장 (주장 추출용)
        if (data.video_id) {
            currentVideoId = data.video_id;
            console.log('📹 비디오 ID 저장:', currentVideoId);
        }
        
        if (!response.ok) {
            addLog('youtube-log', `❌ 오류: ${data.detail || '처리 실패'}`, 'error');
            throw new Error(data.detail || '처리 실패');
        }
        
        addLog('youtube-log', '✅ 분석 완료!', 'success');
        
        // 결과 표시
        resultContent.textContent = formatYoutubeResult(data);
        result.classList.add('show');
        
    } catch (error) {
        alert(`오류 발생: ${error.message}`);
        addLog('youtube-log', `❌ ${error.message}`, 'error');
    } finally {
        loading.classList.remove('show');
    }
}

function formatYoutubeResult(data) {
    let text = '';
    
    text += `✅ 처리 완료!\n\n`;
    text += `📹 비디오 ID: ${data.video_id}\n\n`;
    
    if (data.summary) {
        text += `📝 요약:\n`;
        if (data.summary.sentences && data.summary.sentences.length > 0) {
            data.summary.sentences.forEach((s, i) => {
                text += `  ${i+1}. ${s}\n`;
            });
        }
        if (data.summary.keywords && data.summary.keywords.length > 0) {
            text += `\n🔑 키워드: ${data.summary.keywords.join(', ')}\n`;
        }
        text += `\n`;
    }
    
    if (data.analysis && data.analysis.statistics) {
        const stats = data.analysis.statistics;
        
        // 백엔드 응답 구조: {'좌파': {count: N, percentage: X}, '우파': {count: M, percentage: Y}}
        const leftCount = stats['좌파']?.count || 0;
        const rightCount = stats['우파']?.count || 0;
        const undeterminedCount = stats['판단불가']?.count || 0;
        const total = leftCount + rightCount + undeterminedCount;
        
        if (total === 0) {
            text += `⚠️  댓글 수집 실패\n`;
            text += `   - 댓글이 비활성화되었거나\n`;
            text += `   - API 할당량이 초과되었거나\n`;
            text += `   - 비공개/제한된 영상일 수 있습니다.\n\n`;
            text += `💡 다른 공개 영상으로 시도해보세요!\n`;
        } else {
            text += `📊 댓글 분석:\n`;
            text += `  A 의견: ${leftCount}개 (${stats['좌파']?.percentage || 0}%)\n`;
            text += `  B 의견: ${rightCount}개 (${stats['우파']?.percentage || 0}%)\n`;
            text += `  판단불가: ${undeterminedCount}개\n`;
            text += `  전체: ${total}개\n\n`;
            
            // YouTube 결과를 Persona로 자동 전달
            if (data.analysis.left_comments && data.analysis.right_comments &&
                data.analysis.left_comments.length > 0 && data.analysis.right_comments.length > 0) {
                text += `\n🔄 AI 페르소나로 데이터 전송 중...\n`;
                
                // Step 1 접기, Step 2 펼치기
                setTimeout(() => {
                    const step1 = document.getElementById('step1');
                    const step2 = document.getElementById('step2');
                    
                    if (!step1.classList.contains('collapsed')) {
                        toggleStep('step1');
                    }
                    if (step2.classList.contains('collapsed')) {
                        toggleStep('step2');
                    }
                    
                    // Step 2로 스크롤
                    step2.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 500);
                
                autoSendToPersona(data.analysis.left_comments, data.analysis.right_comments);
            }
        }
    }
    
    if (data.debate && data.debate.length > 0) {
        text += `🎭 토론 결과: ${data.debate.length}개 메시지\n`;
    }
    
    if (data.message) {
        text += `\n📌 ${data.message}\n`;
    }
    
    return text;
}

// YouTube 결과를 자동으로 Persona에 전달
async function autoSendToPersona(leftComments, rightComments) {
    try {
        // 좌파 댓글 textarea에 채우기
        const leftTextarea = document.getElementById('left-comments');
        const rightTextarea = document.getElementById('right-comments');
        
        if (leftTextarea && leftComments && leftComments.length > 0) {
            leftTextarea.value = leftComments.slice(0, 20).join('\n');
        }
        
        if (rightTextarea && rightComments && rightComments.length > 0) {
            rightTextarea.value = rightComments.slice(0, 20).join('\n');
        }
        
        // 페르소나 결과 영역에 알림 표시
        const personaResult = document.getElementById('persona-result');
        const personaResultContent = document.getElementById('persona-result-content');
        
        if (personaResult && personaResultContent) {
            personaResultContent.textContent = `✅ YouTube 댓글 데이터가 자동으로 입력되었습니다!\n\n좌파 댓글: ${leftComments.length}개\n우파 댓글: ${rightComments.length}개\n\n👇 아래 '페르소나 생성' 버튼을 눌러주세요.`;
            personaResult.classList.add('show');
            
            // 페르소나 카드로 스크롤
            document.querySelector('.module-card:nth-child(2)').scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }
    } catch (error) {
        console.error('Persona 데이터 전송 실패:', error);
    }
}

// ==================== AI 페르소나 ====================
async function generatePersona() {
    const leftText = document.getElementById('left-comments').value;
    const rightText = document.getElementById('right-comments').value;
    
    // <br> 태그를 실제 줄바꿈으로 변환
    const leftComments = leftText.replace(/<br\s*\/?>/gi, '\n').split('\n').filter(c => c.trim());
    const rightComments = rightText.replace(/<br\s*\/?>/gi, '\n').split('\n').filter(c => c.trim());
    
    console.log('📊 전송할 댓글 수:', { left: leftComments.length, right: rightComments.length });
    console.log('📝 좌파 댓글 샘플:', leftComments.slice(0, 3));
    console.log('📝 우파 댓글 샘플:', rightComments.slice(0, 3));
    
    if (leftComments.length < 5 || rightComments.length < 5) {
        alert(`좌파와 우파 댓글을 각각 5개 이상 입력해주세요\n현재: 좌파 ${leftComments.length}개, 우파 ${rightComments.length}개`);
        return;
    }
    
    const loading = document.getElementById('persona-loading');
    const result = document.getElementById('persona-result');
    const resultContent = document.getElementById('persona-result-content');
    
    try {
        loading.classList.add('show');
        result.classList.remove('show');
        
        // 1. 좌파/우파 댓글 배치 등록 (백엔드 스키마: { comments: string[] })
        console.log('🚀 좌파 댓글 전송 중...');
        const leftRes = await fetch(`${API_BASE}/api/persona/api/comments/left`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comments: leftComments })
        });

        if (!leftRes.ok) {
            const err = await leftRes.json().catch(() => ({}));
            console.error('❌ 좌파 댓글 등록 실패:', err);
            throw new Error(err.detail || '좌파 댓글 등록 실패');
        }
        const leftData = await leftRes.json();
        console.log('✅ 좌파 댓글 등록 성공:', leftData);
        
        console.log('🚀 우파 댓글 전송 중...');
        const rightRes = await fetch(`${API_BASE}/api/persona/api/comments/right`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comments: rightComments })
        });
        
        if (!rightRes.ok) {
            const err = await rightRes.json().catch(() => ({}));
            console.error('❌ 우파 댓글 등록 실패:', err);
            throw new Error(err.detail || '우파 댓글 등록 실패');
        }
        const rightData = await rightRes.json();
        console.log('✅ 우파 댓글 등록 성공:', rightData);
         
        // 2. 페르소나 생성
        console.log('🚀 페르소나 생성 요청 중...');
        const response = await fetch(`${API_BASE}/api/persona/api/comments/generate-persona`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            console.error('❌ 페르소나 생성 실패:', data);
            throw new Error(data.detail || '페르소나 생성 실패');
        }
        
        console.log('✅ 페르소나 생성 성공!');
        
        // 페르소나 정보를 먼저 표시
        let personaInfo = formatPersonaResult(data);
        resultContent.textContent = personaInfo + '\n\n🚀 토론을 시작합니다...\n';
        result.classList.add('show');
        
        // 3. 자동으로 토론 시작
        console.log('🚀 토론 시작 요청 중...');
        const debateStartRes = await fetch(`${API_BASE}/api/persona/api/debate/start`, {
            method: 'POST'
        });
        
        if (!debateStartRes.ok) {
            const err = await debateStartRes.json().catch(() => ({}));
            console.error('⚠️ 토론 시작 실패:', err);
            resultContent.textContent = personaInfo + '\n\n⚠️ 페르소나는 생성되었으나 토론 시작에 실패했습니다.\n' + (err.detail || '');
            return;
        }
        
        const debateData = await debateStartRes.json();
        console.log('✅ 토론 시작 성공!');
        
        // 4. 토론 메시지들을 생성 (최대 10개)
        const debateContainer = document.getElementById('debate-container');
        debateContainer.innerHTML = '<h4 style="color: #2c3e50; margin-bottom: 16px; font-size: 1.1rem;">💬 실시간 토론</h4>';
        
        for (let i = 0; i < 10; i++) {
            try {
                const nextRes = await fetch(`${API_BASE}/api/persona/api/debate/next`, {
                    method: 'POST'
                });
                
                if (!nextRes.ok) {
                    console.log('토론 종료 또는 오류');
                    break;
                }
                
                const nextData = await nextRes.json();
                const message = nextData.message;
                
                // 토론 메시지를 카드 형태로 표시
                const messageDiv = document.createElement('div');
                messageDiv.className = `debate-message ${message.side === 'left' ? 'side-a' : 'side-b'}`;
                
                const speakerDiv = document.createElement('div');
                speakerDiv.className = 'debate-speaker';
                speakerDiv.textContent = message.side === 'left' ? '👈 의견 A' : '👉 의견 B';
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'debate-content';
                contentDiv.textContent = message.content;
                
                messageDiv.appendChild(speakerDiv);
                messageDiv.appendChild(contentDiv);
                debateContainer.appendChild(messageDiv);
                
                // 스크롤을 토론 영역으로 이동
                messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                
                // 약간의 딜레이 (너무 빠르면 읽기 힘듦)
                await new Promise(resolve => setTimeout(resolve, 800));
                
            } catch (err) {
                console.error('토론 메시지 생성 오류:', err);
                break;
            }
        }
        
        // 완료 메시지
        const completeDiv = document.createElement('div');
        completeDiv.style.cssText = 'text-align: center; padding: 20px; color: #27ae60; font-weight: 600;';
        completeDiv.textContent = '✅ 토론이 완료되었습니다!';
        debateContainer.appendChild(completeDiv);
        
        console.log('✅ 토론 완료!');
        
        // 토론 완료 후 자동으로 주요 댓글 + 팩트체크 포인트 표시
        console.log('📋 자동으로 주요 댓글 및 팩트체크 포인트 추출 중...');
        await extractClaimsAfterDebate();
        
    } catch (error) {
        console.error('❌ 오류:', error);
        alert(`오류 발생: ${error.message}`);
    } finally {
        loading.classList.remove('show');
    }
}

/**
 * 토론 완료 후 자동으로 주요 댓글 + 팩트체크 포인트 추출
 */
async function extractClaimsAfterDebate() {
    if (!currentVideoId) {
        console.warn('⚠️ 비디오 ID가 없어서 주장 추출 건너뜀');
        return;
    }
    
    try {
        // Step 3 팩트체크 섹션 펼치기
        const step3 = document.getElementById('step3');
        if (step3 && step3.classList.contains('collapsed')) {
            toggleStep('step3');
        }
        
        // 1. 주요 댓글 5개 추출
        const commentsResponse = await fetch(`${API_BASE}/api/claim-extraction/extract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: currentVideoId, top_k: 5 })
        });
        
        const commentsData = await commentsResponse.json();
        
        // 2. 팩트체크 포인트 0~3개 추출
        const factcheckResponse = await fetch(`${API_BASE}/api/claim-extraction/extract-factcheck-points`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: currentVideoId, top_k: 3 })
        });
        
        const factcheckData = await factcheckResponse.json();
        
        console.log('💬 주요 댓글:', commentsData);
        console.log('🔍 팩트체크 포인트:', factcheckData);
        
        // 세 섹션 표시
        displayMainComments(commentsData.claims || []);
        displayFactcheckPoints(factcheckData.claims || []);
        
        // 수동 입력 섹션도 표시
        const manualFactcheck = document.getElementById('manual-factcheck');
        if (manualFactcheck) {
            manualFactcheck.style.display = 'block';
        }
        
        // 팩트체크 섹션으로 스크롤
        setTimeout(() => {
            document.getElementById('step3')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 500);
        
    } catch (error) {
        console.error('주장 추출 오류:', error);
    }
}

function formatPersonaResult(data) {
    // 페르소나 세부 정보는 숨김 (사용자에게 보여줄 필요 없음)
    return `✅ 페르소나 생성 완료! 곧 토론이 시작됩니다...\n`;
}

// ==================== 주장 추출 ====================
let currentVideoId = null;  // 전역 변수로 비디오 ID 저장

async function extractClaims() {
    // 최근 분석한 비디오 ID 가져오기
    if (!currentVideoId) {
        alert('먼저 "주제 검출"을 실행해주세요.');
        return;
    }
    
    try {
        console.log('📋 주요 댓글 + 팩트체크 포인트 추출 요청:', currentVideoId);
        
        // 1. 주요 댓글 5개 추출
        const commentsResponse = await fetch(`${API_BASE}/api/claim-extraction/extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_id: currentVideoId,
                top_k: 5  // 주요 댓글 5개
            })
        });
        
        const commentsData = await commentsResponse.json();
        
        // 2. 팩트체크 포인트 0~3개 추출
        const factcheckResponse = await fetch(`${API_BASE}/api/claim-extraction/extract-factcheck-points`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_id: currentVideoId,
                top_k: 3  // 팩트체크 포인트 3개
            })
        });
        
        const factcheckData = await factcheckResponse.json();
        
        console.log('💬 주요 댓글:', commentsData);
        console.log('🔍 팩트체크 포인트:', factcheckData);
        
        // 두 섹션 표시
        displayMainComments(commentsData.claims || []);
        displayFactcheckPoints(factcheckData.claims || []);
        
    } catch (error) {
        console.error('추출 오류:', error);
        alert(`추출 실패: ${error.message}`);
    }
}

/**
 * 주요 댓글 5개 표시 (읽기 전용)
 */
function displayMainComments(comments) {
    const container = document.getElementById('main-comments');
    const list = document.getElementById('main-comments-list');
    
    if (!comments || comments.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    // 리스트 초기화
    list.innerHTML = '';
    
    // 각 댓글을 읽기 전용으로 표시
    comments.forEach((comment, index) => {
        const item = document.createElement('div');
        item.className = 'comment-item';
        item.innerHTML = `
            <span class="claim-text">${comment.claim}</span>
            <span class="claim-score-box">유형매칭도<br>${(comment.score * 100).toFixed(0)}/100</span>
        `;
        
        list.appendChild(item);
    });
    
    // 컨테이너 표시
    container.style.display = 'block';
}

/**
 * 팩트체크 포인트 0~3개 표시 (클릭 시 바로 팩트체크)
 */
function displayFactcheckPoints(points) {
    const container = document.getElementById('factcheck-points');
    const list = document.getElementById('factcheck-points-list');
    
    if (!points || points.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    // 리스트 초기화
    list.innerHTML = '';
    
    // 각 포인트를 클릭 가능한 항목으로 표시
    points.forEach((point, index) => {
        const item = document.createElement('div');
        item.className = 'claim-item';
        item.innerHTML = `
            <span class="claim-text">${point.claim}</span>
            <span class="claim-score-box">관련도<br>${(point.score * 100).toFixed(0)}/100</span>
        `;
        
        // 클릭 시 바로 팩트체크 실행
        item.onclick = async () => {
            // 선택된 항목 하이라이트
            document.querySelectorAll('.claim-item').forEach(el => el.classList.remove('selected'));
            item.classList.add('selected');
            
            // 입력창에도 표시
            document.getElementById('factcheck-claim').value = point.claim;
            
            // 팩트체크 결과 창으로 스크롤
            document.getElementById('factcheck-result').scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // 바로 팩트체크 실행 (키워드 추출 없이 그대로)
            await runFactcheck();
        };
        
        list.appendChild(item);
    });
    
    // 컨테이너 표시
    container.style.display = 'block';
}

// ==================== 팩트체크 ====================

/**
 * 원본 댓글 → 백엔드 키워드 추출 → 팩트체크
 */
async function runFactcheckWithKeywordExtraction(originalClaim) {
    const loading = document.getElementById('loading');
    const resultDiv = document.getElementById('factcheck-result');
    
    loading.classList.add('show');
    resultDiv.textContent = '📝 키워드 추출 중...';
    
    try {
        console.log('🔑 키워드 추출 요청:', originalClaim);
        
        // 1단계: 백엔드에서 키워드 추출
        const keywordResponse = await fetch(`${API_BASE}/api/claim-extraction/extract-keywords`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ claim: originalClaim })
        });
        
        if (!keywordResponse.ok) {
            throw new Error('키워드 추출 실패');
        }
        
        const keywordData = await keywordResponse.json();
        const keywords = keywordData.keywords;
        
        console.log('✅ 추출된 키워드:', keywords);
        console.log('📋 원본 댓글:', originalClaim);
        
        resultDiv.textContent = `🔍 검색 키워드: "${keywords}"\n\n팩트체크 진행 중...`;
        
        // 2단계: 키워드로 팩트체크
        const factcheckResponse = await fetch(`${API_BASE}/api/factcheck/factcheck`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ claim: keywords })
        });
        
        if (!factcheckResponse.ok) {
            throw new Error('팩트체크 실패');
        }
        
        const factcheckData = await factcheckResponse.json();
        
        console.log('✅ 팩트체크 결과:', factcheckData);
        
        // 결과 표시 (원본 댓글 + 검색 키워드 + 팩트체크 결과)
        resultDiv.innerHTML = formatFactcheckResultWithKeywords(originalClaim, keywords, factcheckData);
        
    } catch (error) {
        console.error('❌ 오류:', error);
        resultDiv.textContent = `❌ 오류 발생: ${error.message}`;
    } finally {
        loading.classList.remove('show');
    }
}

/**
 * 기존 팩트체크 (수동 입력용)
 */
async function runFactcheck() {
    const claim = document.getElementById('factcheck-claim').value.trim();
    
    console.log('🔍 팩트체크 요청:', claim);
    
    if (!claim) {
        alert('검증할 주장을 입력해주세요');
        return;
    }
    
    const loading = document.getElementById('factcheck-loading');
    const result = document.getElementById('factcheck-result');
    const resultContent = document.getElementById('factcheck-result-content');
    
    try {
        loading.classList.add('show');
        result.classList.remove('show');
        
        console.log('📤 전송 데이터:', { claim: claim });
        
        const response = await fetch(`${API_BASE}/api/factcheck/factcheck`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                claim: claim
            })
        });
        
        const data = await response.json();
        
        console.log('📥 응답 데이터:', data);
        
        if (!response.ok) {
            throw new Error(data.detail || '팩트체크 실패');
        }
        
        // 결과 표시
        resultContent.textContent = formatFactcheckResult(data);
        result.classList.add('show');
        
    } catch (error) {
        alert(`오류 발생: ${error.message}`);
    } finally {
        loading.classList.remove('show');
    }
}

/**
 * 원본 댓글 + 키워드 + 팩트체크 결과 포맷
 */
function formatFactcheckResultWithKeywords(originalClaim, keywords, data) {
    let text = '';
    
    // 원본 댓글
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `💬 원본 댓글\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${originalClaim}\n\n`;
    
    // 검색 키워드
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `🔍 검색 키워드\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${keywords}\n\n`;
    
    // 판정 결과 (볼드, 한글)
    const verdictEmoji = {
        'True': '✅',
        'False': '❌',
        'Uncertain': '❓'
    };
    
    const verdictKorean = {
        'True': '사실',
        'False': '거짓',
        'Uncertain': '판단 불가'
    };
    
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${verdictEmoji[data.verdict] || '?'} 판정 결과\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${verdictKorean[data.verdict] || data.verdict}\n\n`;
    
    // 신뢰도 (볼드)
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `⭐ 신뢰도 점수\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${data.confidence_score}/10 (${data.confidence_level})\n\n`;
    
    // 판정 근거
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `💡 판정 근거\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${data.reasoning}\n\n`;
    
    // 참고 증거
    if (data.evidences && data.evidences.length > 0) {
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        text += `📚 참고 증거 (${data.evidences.length}개)\n`;
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
        
        data.evidences.forEach((ev, idx) => {
            text += `[증거 ${idx + 1}]\n`;
            text += `📰 출처: ${ev.source}\n`;
            text += `📅 날짜: ${ev.date}\n`;
            text += `🎯 관련도: ${ev.relevance}\n`;
            text += `📝 내용: ${ev.text}\n\n`;
        });
    }
    
    // 제외된 증거 정보
    if (data.search_metadata && data.search_metadata.excluded_count > 0) {
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        text += `🗑️  관련성 낮은 증거 (제외됨)\n`;
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        text += `총 ${data.search_metadata.total_found}개 문서 중 ${data.search_metadata.excluded_count}개 제외\n`;
        text += `(관련도 임계값 미달)\n\n`;
    }
    
    // 신뢰도 세부 (선택적)
    if (data.score_breakdown && Object.keys(data.score_breakdown).length > 0) {
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        text += `📊 신뢰도 세부 분석\n`;
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        
        // 한글 레이블 매핑
        const labelMap = {
            'multiple_sources': '✅ 복수 출처',
            'recency': '📅 최신성',
            'matching_strength': '🎯 매칭 강도',
            'contradiction_penalty': '⚠️ 모순 페널티',
            'evidence_diversity': '🌐 증거 다양성',
            '문서_수': '📄 문서 수',
            '스니펫_생성': '✂️ 스니펫 생성',
            '관련_증거': '🔗 관련 증거'
        };
        
        for (const [key, value] of Object.entries(data.score_breakdown)) {
            const label = labelMap[key] || key;
            text += `  ${label}: ${value}\n`;
        }
        text += '\n';
    }
    
    return text;
}

/**
 * 기존 팩트체크 결과 포맷 (수동 입력용)
 */
function formatFactcheckResult(data) {
    let text = '';
    
    // 주장 (볼드)
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `📋 검증 주장\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${data.claim}\n\n`;
    
    // 판정 결과 (볼드, 한글)
    const verdictEmoji = {
        'True': '✅',
        'False': '❌',
        'Uncertain': '❓'
    };
    
    const verdictKorean = {
        'True': '사실',
        'False': '거짓',
        'Uncertain': '판단 불가'
    };
    
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${verdictEmoji[data.verdict] || '?'} 판정 결과\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${verdictKorean[data.verdict] || data.verdict}\n\n`;
    
    // 신뢰도 (볼드)
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `⭐ 신뢰도 점수\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${data.confidence_score}/10 (${data.confidence_level})\n\n`;
    
    // 판정 근거
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `💡 판정 근거\n`;
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    text += `${data.reasoning}\n\n`;
    
    // 참고 증거
    if (data.evidences && data.evidences.length > 0) {
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        text += `📚 참고 증거 (${data.evidences.length}개)\n`;
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
        
        data.evidences.forEach((ev, idx) => {
            text += `[증거 ${idx + 1}]\n`;
            text += `📰 출처: ${ev.source}\n`;
            text += `📅 날짜: ${ev.date}\n`;
            text += `🎯 관련도: ${ev.relevance}\n`;
            text += `📝 내용: ${ev.text}\n\n`;
        });
    }
    
    // 제외된 증거 정보
    if (data.search_metadata && data.search_metadata.excluded_count > 0) {
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        text += `🗑️  관련성 낮은 증거 (제외됨)\n`;
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        text += `총 ${data.search_metadata.total_found}개 문서 중 ${data.search_metadata.excluded_count}개 제외\n`;
        text += `(관련도 임계값 미달)\n\n`;
    }
    
    // 신뢰도 세부 (선택적)
    if (data.score_breakdown && Object.keys(data.score_breakdown).length > 0) {
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        text += `📊 신뢰도 세부 분석\n`;
        text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        
        // 한글 레이블 매핑
        const labelMap = {
            'multiple_sources': '복수 출처',
            'recency': '최신성 (12개월)',
            'matching_strength': '매칭 강도',
            'contradiction_penalty': '모순 페널티',
            'evidence_diversity': '증거 다양성',
            '문서_수': '문서 수',
            '스니펫_생성': '스니펫 생성',
            '관련_증거': '관련 증거'
        };
        
        for (const [key, value] of Object.entries(data.score_breakdown)) {
            const label = labelMap[key] || key;
            
            // 점수에 따른 이모지
            let emoji = '';
            if (typeof value === 'number') {
                if (value > 0) emoji = '✅';
                else if (value < 0) emoji = '⚠️ ';
                else emoji = '⬜';
                text += `  ${emoji} ${label}: ${value > 0 ? '+' : ''}${value}\n`;
            } else {
                text += `  • ${label}: ${value}\n`;
            }
        }
        text += `\n`;
    }
    
    text += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    
    return text;
}

