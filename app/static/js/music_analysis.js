/**
 * Music Analysis - AI 음악 생성 페이지 JavaScript
 */

class MusicAnalysis {
    constructor() {
        this.currentJobId = null;
        this.pollInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateRangeValues();
        this.checkServiceStatus();
    }

    bindEvents() {
        // 버튼 이벤트
        document.getElementById('analyzeBtn').addEventListener('click', () => this.startAnalysis());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearResults());

        // 범위 슬라이더 이벤트
        document.getElementById('duration').addEventListener('input', (e) => {
            document.getElementById('durationValue').textContent = e.target.value;
        });

        document.getElementById('variations').addEventListener('input', (e) => {
            document.getElementById('variationsValue').textContent = e.target.value;
        });

        // 생성 모드 변경 이벤트
        document.getElementById('generationMode').addEventListener('change', (e) => {
            this.toggleGenerationOptions(e.target.value);
        });

        // 프롬프트 타입 변경 이벤트
        document.getElementById('promptType').addEventListener('change', (e) => {
            this.toggleCustomPromptOptions(e.target.value);
        });

        // URL 입력 검증
        document.getElementById('youtubeUrl').addEventListener('input', (e) => {
            this.validateYouTubeUrl(e.target.value);
        });
    }

    updateRangeValues() {
        const duration = document.getElementById('duration').value;
        const variations = document.getElementById('variations').value;
        
        document.getElementById('durationValue').textContent = duration;
        document.getElementById('variationsValue').textContent = variations;
    }

    async checkServiceStatus() {
        try {
            const response = await fetch('/api/music-analysis/status');
            const data = await response.json();
            
            this.updateServiceStatus(data);
        } catch (error) {
            console.error('서비스 상태 확인 실패:', error);
            this.showServiceStatus('서비스 상태 확인 실패', 'error');
        }
    }

    updateServiceStatus(status) {
        const statusSection = document.getElementById('serviceStatus');
        const statusText = document.getElementById('serviceStatusText');
        
        statusSection.style.display = 'block';
        
        if (status.overall_status === 'ready') {
            statusText.textContent = '✅ 모든 서비스가 준비되었습니다';
            statusText.className = 'status-text success';
            statusSection.className = 'status-section';
        } else if (status.overall_status === 'analysis_only') {
            statusText.textContent = '📊 분석 전용 모드 (AI 생성 기능 비활성화)';
            statusText.className = 'status-text warning';
            statusSection.className = 'status-section status-warning';
        } else if (status.overall_status === 'partial') {
            statusText.textContent = '⚠️ 일부 서비스만 사용 가능합니다';
            statusText.className = 'status-text warning';
            statusSection.className = 'status-section status-warning';
        } else {
            statusText.textContent = '❌ 서비스 설정이 필요합니다';
            statusText.className = 'status-text error';
            statusSection.className = 'status-section status-error';
        }
    }

    showServiceStatus(message, type = 'info') {
        const statusSection = document.getElementById('serviceStatus');
        const statusText = document.getElementById('serviceStatusText');
        
        statusSection.style.display = 'block';
        statusText.textContent = message;
        statusText.className = `status-text ${type}`;
        statusSection.className = `status-section ${type === 'error' ? 'status-error' : type === 'warning' ? 'status-warning' : ''}`;
    }

    validateYouTubeUrl(url) {
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
        const inputField = document.getElementById('youtubeUrl');
        
        if (url && !youtubeRegex.test(url)) {
            inputField.style.borderColor = '#e74c3c';
            return false;
        } else {
            inputField.style.borderColor = '#ddd';
            return true;
        }
    }

    toggleGenerationOptions(mode) {
        const generationOptions = document.querySelectorAll('.option-group');
        const isAnalyzeOnly = mode === 'analyze_only';
        
        // 생성 관련 옵션 토글
        generationOptions.forEach(group => {
            const title = group.querySelector('.option-title').textContent;
            if (['음악 스타일', '음악 길이', '생성 변형', '프롬프트 타입'].includes(title)) {
                group.style.display = isAnalyzeOnly ? 'none' : 'block';
            }
        });
    }

    toggleCustomPromptOptions(type) {
        // 커스텀 프롬프트 옵션이 필요한 경우 추가 구현
        console.log('프롬프트 타입 변경:', type);
    }

    async startAnalysis() {
        const url = document.getElementById('youtubeUrl').value.trim();
        
        if (!url) {
            this.showServiceStatus('YouTube URL을 입력해주세요', 'error');
            return;
        }

        if (!this.validateYouTubeUrl(url)) {
            this.showServiceStatus('올바른 YouTube URL을 입력해주세요', 'error');
            return;
        }

        this.showProgress();
        this.hideResults();
        this.setButtonsDisabled(true);

        try {
            const options = this.getAnalysisOptions();
            const mode = document.getElementById('generationMode').value;
            
            let endpoint, payload;
            
            if (mode === 'analyze_only') {
                endpoint = '/api/music-analysis/analyze';
                payload = { url: url };
            } else {
                endpoint = '/api/music-analysis/generate';
                payload = { url: url, options: options };
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                this.currentJobId = data.job_id;
                this.startPolling();
            } else {
                this.showServiceStatus(data.error || '처리 시작 실패', 'error');
                this.hideProgress();
                this.setButtonsDisabled(false);
            }
        } catch (error) {
            console.error('분석 시작 오류:', error);
            this.showServiceStatus('분석 시작 중 오류가 발생했습니다', 'error');
            this.hideProgress();
            this.setButtonsDisabled(false);
        }
    }

    getAnalysisOptions() {
        const style = document.getElementById('musicStyle').value;
        const duration = parseInt(document.getElementById('duration').value);
        const variations = parseInt(document.getElementById('variations').value);
        const promptType = document.getElementById('promptType').value;
        const showAnalysis = document.getElementById('showAnalysis').checked;
        const showPrompt = document.getElementById('showPrompt').checked;

        return {
            style: style === 'auto' ? null : style,
            duration: duration,
            variations: variations,
            prompt_type: promptType,
            show_analysis: showAnalysis,
            show_prompt: showPrompt
        };
    }

    startPolling() {
        this.pollInterval = setInterval(() => {
            this.checkJobStatus();
        }, 1000);
    }

    async checkJobStatus() {
        if (!this.currentJobId) return;

        try {
            const response = await fetch(`/api/music-analysis/status/${this.currentJobId}`);
            const data = await response.json();

            if (data.status === 'completed') {
                this.stopPolling();
                this.handleCompletion(data.result);
            } else if (data.status === 'error') {
                this.stopPolling();
                this.showServiceStatus(data.message || '처리 중 오류가 발생했습니다', 'error');
                this.hideProgress();
                this.setButtonsDisabled(false);
            } else {
                // 진행 중
                this.updateProgress(data.progress || 0, data.message || '처리 중...');
            }
        } catch (error) {
            console.error('상태 확인 오류:', error);
            this.stopPolling();
            this.showServiceStatus('상태 확인 중 오류가 발생했습니다', 'error');
            this.hideProgress();
            this.setButtonsDisabled(false);
        }
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        this.currentJobId = null;
    }

    handleCompletion(result) {
        this.hideProgress();
        this.setButtonsDisabled(false);
        
        // 분석 전용 모드에서는 result가 직접 분석 결과를 포함
        if (result.video_info && result.music_analysis) {
            this.displayAnalysisResults(result);
        } else if (result.analysis) {
            // 기존 구조 지원
            this.displayAnalysisResults(result.analysis);
        }
        
        if (result.prompt_options) {
            this.displayPromptResults(result.prompt_options, result.selected_prompt);
        }
        
        if (result.generation_results) {
            this.displayGenerationResults(result.generation_results);
        }
        
        this.showResults();
        this.showServiceStatus('처리가 완료되었습니다', 'success');
    }

    displayAnalysisResults(analysis) {
        const musicInfo = document.getElementById('musicInfo');
        const musicFeatures = document.getElementById('musicFeatures');
        
        const videoInfo = analysis.video_info;
        const musicAnalysis = analysis.music_analysis;
        
        // 음악 정보
        musicInfo.innerHTML = `
            <div class="result-item">
                <span class="result-label">제목:</span>
                <span class="result-value">${videoInfo.title}</span>
            </div>
            <div class="result-item">
                <span class="result-label">아티스트:</span>
                <span class="result-value">${musicAnalysis.artist}</span>
            </div>
            <div class="result-item">
                <span class="result-label">곡명:</span>
                <span class="result-value">${musicAnalysis.song}</span>
            </div>
            <div class="result-item">
                <span class="result-label">길이:</span>
                <span class="result-value">${videoInfo.duration_str}</span>
            </div>
            <div class="result-item">
                <span class="result-label">조회수:</span>
                <span class="result-value">${videoInfo.view_count.toLocaleString()}</span>
            </div>
        `;
        
        // 음악 특성
        musicFeatures.innerHTML = `
            <div class="result-item">
                <span class="result-label">주 장르:</span>
                <span class="result-value">${musicAnalysis.genre.primary_genre}</span>
            </div>
            <div class="result-item">
                <span class="result-label">예상 장르:</span>
                <span class="result-value">${musicAnalysis.genre.predicted_genres.join(', ')}</span>
            </div>
            <div class="result-item">
                <span class="result-label">주 분위기:</span>
                <span class="result-value">${musicAnalysis.mood.primary_mood}</span>
            </div>
            <div class="result-item">
                <span class="result-label">예상 분위기:</span>
                <span class="result-value">${musicAnalysis.mood.predicted_moods.join(', ')}</span>
            </div>
            <div class="result-item">
                <span class="result-label">예상 BPM:</span>
                <span class="result-value">${musicAnalysis.estimated_bpm}</span>
            </div>
            <div class="result-item">
                <span class="result-label">예상 키:</span>
                <span class="result-value">${musicAnalysis.estimated_key}</span>
            </div>
            <div class="result-item">
                <span class="result-label">에너지 레벨:</span>
                <span class="result-value">${musicAnalysis.energy_level}</span>
            </div>
        `;
    }

    displayPromptResults(promptOptions, selectedPrompt) {
        const promptSection = document.getElementById('promptSection');
        const promptText = document.getElementById('promptText');
        
        if (document.getElementById('showPrompt').checked) {
            promptSection.style.display = 'block';
            promptText.textContent = selectedPrompt || promptOptions.basic;
        } else {
            promptSection.style.display = 'none';
        }
    }

    displayGenerationResults(results) {
        const generatedMusic = document.getElementById('generatedMusic');
        const musicList = document.getElementById('musicList');
        
        if (results && results.length > 0) {
            generatedMusic.style.display = 'block';
            
            let html = '';
            results.forEach((result, index) => {
                html += `
                    <div class="music-item">
                        <div class="music-info">
                            <div class="music-title">생성된 음악 ${index + 1}</div>
                            <div class="music-details">
                                길이: ${result.duration}초 | 스타일: ${result.style || 'Mixed'} | 크기: ${result.size ? (result.size / 1024 / 1024).toFixed(1) + 'MB' : 'N/A'}
                            </div>
                        </div>
                        <div class="music-actions">
                            <button class="btn btn-success" onclick="downloadMusic('${result.filename}')">
                                💾 다운로드
                            </button>
                            <button class="btn btn-primary" onclick="playMusic('${result.filename}')">
                                ▶️ 재생
                            </button>
                        </div>
                    </div>
                `;
            });
            
            musicList.innerHTML = html;
        } else {
            generatedMusic.style.display = 'none';
        }
    }

    showProgress() {
        document.getElementById('progressSection').style.display = 'block';
        this.updateProgress(0, '처리 시작...');
    }

    hideProgress() {
        document.getElementById('progressSection').style.display = 'none';
    }

    updateProgress(percentage, message) {
        document.getElementById('progressBar').style.width = percentage + '%';
        document.getElementById('progressText').textContent = message;
    }

    showResults() {
        document.getElementById('resultsSection').style.display = 'block';
        
        // 분석 결과 표시 여부 확인
        const showAnalysis = document.getElementById('showAnalysis').checked;
        document.getElementById('analysisResults').style.display = showAnalysis ? 'grid' : 'none';
    }

    hideResults() {
        document.getElementById('resultsSection').style.display = 'none';
    }

    clearResults() {
        // 입력 필드 초기화
        document.getElementById('youtubeUrl').value = '';
        document.getElementById('generationMode').value = 'analyze_only';
        document.getElementById('musicStyle').value = 'auto';
        document.getElementById('duration').value = '30';
        document.getElementById('variations').value = '1';
        document.getElementById('promptType').value = 'basic';
        document.getElementById('showAnalysis').checked = true;
        document.getElementById('showPrompt').checked = true;
        
        // 값 업데이트
        this.updateRangeValues();
        
        // 결과 및 진행률 숨기기
        this.hideResults();
        this.hideProgress();
        
        // 폴링 중지
        this.stopPolling();
        
        // 버튼 활성화
        this.setButtonsDisabled(false);
        
        // 서비스 상태 재확인
        this.checkServiceStatus();
    }

    setButtonsDisabled(disabled) {
        document.getElementById('analyzeBtn').disabled = disabled;
        document.getElementById('clearBtn').disabled = disabled;
    }
}

// 전역 함수들
function downloadMusic(filename) {
    const link = document.createElement('a');
    link.href = `/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function playMusic(filename) {
    // 간단한 오디오 플레이어 구현
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.src = `/download/${filename}`;
    audio.play();
    
    // 기존 플레이어 제거
    const existingPlayer = document.querySelector('.audio-player');
    if (existingPlayer) {
        existingPlayer.remove();
    }
    
    // 새 플레이어 추가
    audio.className = 'audio-player';
    audio.style.cssText = 'margin: 10px 0; width: 100%;';
    
    const musicItem = event.target.closest('.music-item');
    musicItem.appendChild(audio);
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    window.musicAnalysis = new MusicAnalysis();
    updateNavigation();
});

// 네비게이션 업데이트 함수
function updateNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        // 현재 페이지와 링크 경로 비교
        const linkPath = new URL(link.href).pathname;
        
        if (currentPath === linkPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// 차트 분석 기능
function showChart(chartType) {
    // 모든 탭 비활성화
    document.querySelectorAll('.chart-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 선택된 탭 활성화
    event.target.classList.add('active');
    
    // 차트 컨테이너 가져오기
    const container = document.getElementById('chartsContainer');
    
    // 로딩 표시
    container.innerHTML = '<div class="loading">차트 데이터 로딩 중...</div>';
    
    // API 호출
    let apiUrl;
    switch(chartType) {
        case 'melon':
            apiUrl = '/api/melon/charts?type=realtime&limit=50';
            break;
        case 'bugs':
            apiUrl = '/api/korea-charts/all?services=bugs&limit=50';
            break;
        case 'genie':
            apiUrl = '/api/korea-charts/all?services=genie&limit=50';
            break;
        case 'korea':
            apiUrl = '/api/korea-charts/all?limit=50';
            break;
        default:
            apiUrl = '/api/melon/charts?type=realtime&limit=50';
    }
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            displayChartData(data, chartType);
        })
        .catch(error => {
            console.error('차트 데이터 로드 실패:', error);
            container.innerHTML = '<div class="error">차트 데이터를 불러올 수 없습니다.</div>';
        });
}

function displayChartData(data, chartType) {
    const container = document.getElementById('chartsContainer');
    
    console.log('=== 차트 데이터 디버깅 ===');
    console.log('전체 데이터:', data);
    console.log('데이터 타입:', typeof data);
    console.log('데이터 키들:', Object.keys(data || {}));
    
    // 데이터 구조를 더 자세히 분석
    let tracks = [];
    let debugInfo = '';
    
    if (data && typeof data === 'object') {
        // 경우 1: { chart_data: { success: true, tracks: [...] } } 형태 (멜론 API)
        if (data.chart_data && typeof data.chart_data === 'object') {
            const chartData = data.chart_data;
            if (chartData.success && chartData.tracks && Array.isArray(chartData.tracks)) {
                tracks = chartData.tracks;
                debugInfo = '형태1: chart_data';
            }
        }
        // 경우 2: { success: true, tracks: [...] } 형태
        else if (data.success && data.tracks && Array.isArray(data.tracks)) {
            tracks = data.tracks;
            debugInfo = '형태2: success + tracks';
        }
        // 경우 3: { services: { service: { chartType: { success: true, tracks: [...] } } } } 형태 (벅스/지니 API)
        else if (data.services && typeof data.services === 'object') {
            const serviceKeys = Object.keys(data.services);
            console.log('서비스들:', serviceKeys);
            
            for (const service of serviceKeys) {
                const serviceData = data.services[service];
                console.log(`${service} 서비스 데이터:`, serviceData);
                
                if (serviceData && typeof serviceData === 'object') {
                    // realtime, daily 등 차트 타입 확인
                    const chartTypeKeys = Object.keys(serviceData);
                    for (const chartType of chartTypeKeys) {
                        const chartData = serviceData[chartType];
                        console.log(`${service}.${chartType} 데이터:`, chartData);
                        
                        if (chartData && chartData.success && chartData.tracks && Array.isArray(chartData.tracks)) {
                            tracks = chartData.tracks;
                            debugInfo = `형태3: services.${service}.${chartType}`;
                            break;
                        }
                    }
                    if (tracks.length > 0) break;
                }
            }
        }
        // 경우 4: { charts: { service: { success: true, tracks: [...] } } } 형태
        else if (data.charts && typeof data.charts === 'object') {
            const chartKeys = Object.keys(data.charts);
            console.log('차트 서비스들:', chartKeys);
            
            for (const service of chartKeys) {
                const serviceData = data.charts[service];
                console.log(`${service} 데이터:`, serviceData);
                
                if (serviceData && serviceData.success && serviceData.tracks && Array.isArray(serviceData.tracks)) {
                    tracks = serviceData.tracks;
                    debugInfo = `형태4: charts.${service}`;
                    break;
                }
            }
        }
        // 경우 5: 직접 tracks 배열
        else if (data.tracks && Array.isArray(data.tracks)) {
            tracks = data.tracks;
            debugInfo = '형태5: 직접 tracks';
        }
        // 경우 6: 데이터 자체가 배열
        else if (Array.isArray(data)) {
            tracks = data;
            debugInfo = '형태6: 직접 배열';
        }
        // 경우 7: 다른 가능한 구조들 확인
        else {
            console.log('알 수 없는 데이터 구조 - 모든 속성 탐색:');
            for (const [key, value] of Object.entries(data)) {
                console.log(`  ${key}:`, value);
                if (Array.isArray(value) && value.length > 0) {
                    console.log(`    ${key}는 배열이고 ${value.length}개 항목 포함`);
                    if (value[0] && (value[0].title || value[0].name || value[0].artist)) {
                        tracks = value;
                        debugInfo = `형태7: ${key} 배열`;
                        break;
                    }
                } else if (value && typeof value === 'object' && value.tracks && Array.isArray(value.tracks)) {
                    console.log(`    ${key}.tracks 발견: ${value.tracks.length}개 항목`);
                    tracks = value.tracks;
                    debugInfo = `형태7: ${key}.tracks`;
                    break;
                }
            }
        }
    }
    
    console.log('추출된 트랙 개수:', tracks.length);
    console.log('디버그 정보:', debugInfo);
    
    if (tracks.length > 0) {
        console.log('첫 번째 트랙 샘플:', tracks[0]);
    }
    
    if (!tracks || tracks.length === 0) {
        container.innerHTML = `
            <div class="no-data">
                <p>차트 데이터가 없습니다.</p>
                <p><small>디버그: ${debugInfo || '데이터 구조 인식 실패'}</small></p>
                <details>
                    <summary>원본 데이터 보기</summary>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                </details>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="chart-header">
            <div class="chart-title-wrapper">
                <h3 class="chart-title">${getChartTitle(chartType)}</h3>
                <div class="chart-info">
                    <span class="track-count">${tracks.length}곡</span>
                    <span class="update-time">${new Date().toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'})} 업데이트</span>
                </div>
            </div>
            <div class="chart-decoration">
                <div class="music-note">♪</div>
                <div class="music-note delay-1">♫</div>
                <div class="music-note delay-2">♪</div>
            </div>
        </div>
    `;
    html += '<div class="chart-list">';
    
    tracks.forEach((track, index) => {
        const rank = track.rank || track.ranking || (index + 1);
        const title = track.name || track.title || track.song || track.songName || '제목 없음';
        
        let artist = '아티스트 없음';
        if (track.artists) {
            if (Array.isArray(track.artists)) {
                artist = track.artists.map(a => a.name || a).join(', ');
            } else {
                artist = track.artists;
            }
        } else if (track.artist) {
            artist = track.artist;
        } else if (track.singer) {
            artist = track.singer;
        }
        
        const popularity = track.popularity || track.score || track.point || '';
        
        html += `
            <div class="chart-item">
                <div class="rank">${rank}</div>
                <div class="track-info">
                    <div class="track-title">${title}</div>
                    <div class="track-artist">${artist}</div>
                </div>
                <div class="track-popularity">${popularity}${popularity ? (popularity > 1 ? '' : '%') : ''}</div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function getChartTitle(chartType) {
    switch(chartType) {
        case 'melon': return '멜론 차트';
        case 'bugs': return '벅스 차트';
        case 'genie': return '지니 차트';
        case 'korea': return '통합 한국 차트';
        default: return '멜론 차트';
    }
}

// 하위 탭 전환 기능
function showSubTab(tabName) {
    // 모든 하위 탭 버튼 비활성화
    document.querySelectorAll('.sub-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 모든 하위 탭 컨텐츠 숨김
    document.querySelectorAll('.sub-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 클릭된 버튼 활성화
    event.target.classList.add('active');
    
    // 해당 탭 컨텐츠 표시
    let tabId;
    switch(tabName) {
        case 'music-analysis':
            tabId = 'musicAnalysisTab';
            break;
        case 'charts-analysis':
            tabId = 'chartsAnalysisTab';
            // 차트 탭이 활성화되면 기본 차트 로드
            setTimeout(() => {
                if (document.getElementById('chartsContainer')) {
                    showChart('melon');
                }
            }, 100);
            break;
    }
    
    if (tabId) {
        const tabContent = document.getElementById(tabId);
        if (tabContent) {
            tabContent.classList.add('active');
        }
    }
}

// 페이지 로드 시 초기화
window.addEventListener('DOMContentLoaded', function() {
    // 기본적으로 실시간 차트 분석 탭 활성화
    const chartsAnalysisTab = document.getElementById('chartsAnalysisTab');
    if (chartsAnalysisTab) {
        chartsAnalysisTab.classList.add('active');
        // 기본 차트 로드 (멜론)
        setTimeout(() => {
            if (document.getElementById('chartsContainer')) {
                showChart('melon');
            }
        }, 100);
    }
});

// 페이지 언로드 시 폴링 정리
window.addEventListener('beforeunload', function() {
    if (window.musicAnalysis) {
        window.musicAnalysis.stopPolling();
    }
});