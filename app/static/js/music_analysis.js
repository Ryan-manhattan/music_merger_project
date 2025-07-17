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

// 페이지 언로드 시 폴링 정리
window.addEventListener('beforeunload', function() {
    if (window.musicAnalysis) {
        window.musicAnalysis.stopPolling();
    }
});