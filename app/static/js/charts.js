/**
 * Spotify Charts Page JavaScript
 * 차트 데이터 로딩 및 표시 관리
 */

let chartsData = null;
let currentFilter = 'all';
let currentSource = 'melon';  // 'melon', 'bugs', 'genie', 'korea-all'
let currentMelonType = 'realtime';  // 'realtime' 또는 'hot100'
let currentBugsType = 'realtime';   // 'realtime', 'daily', 'weekly'
let currentGenieType = 'realtime';  // 'realtime', 'top200'
let currentKoreaServices = ['melon', 'bugs', 'genie'];  // 통합차트 서비스 목록

// DOM 요소들
const elements = {
    refreshBtn: document.getElementById('refreshBtn'),
    toggleSourceBtn: document.getElementById('toggleSourceBtn'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    errorMessage: document.getElementById('errorMessage'),
    chartGrid: document.getElementById('chartGrid'),
    
    // 멜론 차트 요소들
    melonCharts: document.getElementById('melonCharts'),
    melonChart: document.getElementById('melonChart'),
    melonChartTitle: document.getElementById('melonChartTitle'),
    melonFilters: document.getElementById('melonFilters'),
    
    // 벅스 차트 요소들
    bugsCharts: document.getElementById('bugsCharts'),
    bugsChart: document.getElementById('bugsChart'),
    bugsChartTitle: document.getElementById('bugsChartTitle'),
    bugsFilters: document.getElementById('bugsFilters'),
    
    // 지니 차트 요소들
    genieCharts: document.getElementById('genieCharts'),
    genieChart: document.getElementById('genieChart'),
    genieChartTitle: document.getElementById('genieChartTitle'),
    genieFilters: document.getElementById('genieFilters'),
    
    // 통합 차트 요소들
    koreaCharts: document.getElementById('koreaCharts'),
    koreaStats: document.getElementById('koreaStats'),
    crossPlatformSection: document.getElementById('crossPlatformSection'),
    crossPlatformChart: document.getElementById('crossPlatformChart'),
    serviceCharts: document.getElementById('serviceCharts'),
    koreaFilters: document.getElementById('koreaFilters'),
    
    // 통계 및 필터 요소들
    totalTracks: document.getElementById('totalTracks'),
    koreaCount: document.getElementById('koreaCount'),
    globalCount: document.getElementById('globalCount'),
    lastUpdated: document.getElementById('lastUpdated'),
    
    // 버튼들
    sourceButtons: document.querySelectorAll('.source-btn'),
    melonTypeButtons: document.querySelectorAll('.melon-type-btn'),
    bugsTypeButtons: document.querySelectorAll('.bugs-type-btn'),
    genieTypeButtons: document.querySelectorAll('.genie-type-btn'),
    koreaServiceButtons: document.querySelectorAll('.korea-service-btn')
};

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Charts] 차트 페이지 초기화');
    setupEventListeners();
    
    // 초기 로딩 시 멜론 차트를 기본으로 표시
    switchSource('melon');
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 새로고침 버튼
    elements.refreshBtn.addEventListener('click', function() {
        console.log('[Charts] 새로고침 버튼 클릭');
        loadChartData();
    });

    // 차트 전환 버튼
    if (elements.toggleSourceBtn) {
        elements.toggleSourceBtn.addEventListener('click', function() {
            const newSource = currentSource === 'spotify' ? 'melon' : 'spotify';
            switchSource(newSource);
        });
    }

    // 소스 버튼들 (Spotify/멜론)
    elements.sourceButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const source = this.dataset.source;
            switchSource(source);
        });
    });

    // Spotify 필터 버튼들
    elements.filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            setActiveFilter(filter);
            applyFilter(filter);
        });
    });

    // 멜론 타입 버튼들
    elements.melonTypeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const type = this.dataset.type;
            setActiveMelonType(type);
            loadMelonChart(type);
        });
    });

    // 통합 차트 서비스 버튼들
    elements.koreaServiceButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const services = this.dataset.services.split(',');
            setActiveKoreaServices(services);
            loadKoreaCharts(services);
        });
    });
}

// 활성 필터 설정
function setActiveFilter(filter) {
    elements.filterButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
    currentFilter = filter;
}

// 필터 적용
function applyFilter(filter) {
    const koreaSection = document.querySelector('.chart-section:nth-child(1)');
    const globalSection = document.querySelector('.chart-section:nth-child(2)');
    
    switch(filter) {
        case 'korea':
            koreaSection.style.display = 'block';
            globalSection.style.display = 'none';
            break;
        case 'global':
            koreaSection.style.display = 'none';
            globalSection.style.display = 'block';
            break;
        case 'all':
        default:
            koreaSection.style.display = 'block';
            globalSection.style.display = 'block';
            break;
    }
}

// 소스 전환 함수
function switchSource(source) {
    console.log(`[Charts] 소스 전환: ${currentSource} -> ${source}`);
    
    // 소스 버튼 활성화 상태 변경
    elements.sourceButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.source === source) {
            btn.classList.add('active');
        }
    });
    
    // 모든 차트 섹션과 필터 숨기기
    const chartSections = ['melonCharts', 'bugsCharts', 'genieCharts', 'koreaCharts'];
    const filterSections = ['melonFilters', 'bugsFilters', 'genieFilters', 'koreaFilters'];
    
    chartSections.forEach(section => {
        if (elements[section]) elements[section].style.display = 'none';
    });
    
    filterSections.forEach(section => {
        if (elements[section]) elements[section].style.display = 'none';
    });
    
    // 선택된 소스에 따라 표시
    switch(source) {
        case 'melon':
            elements.melonFilters.style.display = 'flex';
            elements.melonCharts.style.display = 'block';
            loadMelonChart(currentMelonType);
            break;
        case 'bugs':
            elements.bugsFilters.style.display = 'flex';
            elements.bugsCharts.style.display = 'block';
            loadBugsChart(currentBugsType);
            break;
        case 'genie':
            elements.genieFilters.style.display = 'flex';
            elements.genieCharts.style.display = 'block';
            loadGenieChart(currentGenieType);
            break;
        case 'korea-all':
            elements.koreaFilters.style.display = 'flex';
            elements.koreaCharts.style.display = 'block';
            loadKoreaCharts(currentKoreaServices);
            break;
    }
    
    currentSource = source;
}

// 멜론 타입 활성화 설정
function setActiveMelonType(type) {
    elements.melonTypeButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === type) {
            btn.classList.add('active');
        }
    });
    currentMelonType = type;
    
    // 차트 제목 업데이트
    const titleMap = {
        'realtime': '🍈 멜론 실시간 TOP 50',
        'hot100': '🍈 멜론 HOT100'
    };
    elements.melonChartTitle.textContent = titleMap[type] || '🍈 멜론 차트';
}

// 차트 데이터 로딩 (소스에 따라 분기)
async function loadChartData() {
    console.log(`[Charts] ${currentSource} 차트 데이터 로딩 시작`);
    
    switch(currentSource) {
        case 'melon':
            await loadMelonChart(currentMelonType);
            break;
        case 'bugs':
            await loadBugsChart(currentBugsType);
            break;
        case 'genie':
            await loadGenieChart(currentGenieType);
            break;
        case 'korea-all':
            await loadKoreaCharts(currentKoreaServices);
            break;
        default:
            await loadMelonChart(currentMelonType);
            break;
    }
}


// 멜론 차트 로딩
async function loadMelonChart(type = 'realtime') {
    console.log(`[Charts] [DEBUG] 멜론 차트 로딩 시작 - type: ${type}`);
    showLoading(true);
    hideError();
    
    try {
        const apiUrl = `/api/melon/charts?type=${type}&limit=50`;
        console.log(`[Charts] [DEBUG] API 호출: ${apiUrl}`);
        
        const response = await fetch(apiUrl);
        console.log(`[Charts] [DEBUG] 응답 상태: ${response.status} ${response.statusText}`);
        
        const data = await response.json();
        console.log(`[Charts] [DEBUG] 응답 데이터:`, data);
        
        if (data.success) {
            chartsData = data;
            console.log(`[Charts] [DEBUG] 차트 데이터 저장 완료, 트랙 수: ${data.total_tracks || 0}`);
            
            displayMelonData(data);
            console.log(`[Charts] [DEBUG] 멜론 차트 화면 표시 완료`);
            
            updateMelonStats(data);
            console.log(`[Charts] [DEBUG] 멜론 통계 업데이트 완료`);
            
            console.log('[Charts] 멜론 차트 데이터 로딩 완료:', data.total_tracks || 0, '개 트랙');
        } else {
            console.error('[Charts] [DEBUG] 멜론 차트 로딩 실패:', data.error);
            throw new Error(data.error || '멜론 차트 데이터 로딩 실패');
        }
    } catch (error) {
        console.error('[Charts] [DEBUG] 멜론 차트 로딩 오류:', error);
        console.error('[Charts] 멜론 차트 데이터 로딩 오류:', error);
        showError('멜론 차트 데이터를 불러올 수 없습니다: ' + error.message);
    }
    
    showLoading(false);
    console.log(`[Charts] [DEBUG] 멜론 차트 로딩 완료`);
}


// 멜론 통계 정보 업데이트
function updateMelonStats(data) {
    console.log(`[Charts] [DEBUG] 멜론 통계 업데이트 시작:`, data);
    
    const tracks = data.chart_data?.tracks || [];
    console.log(`[Charts] [DEBUG] 추출된 트랙 수: ${tracks.length}`);
    
    if (elements.totalTracks) {
        elements.totalTracks.textContent = data.total_tracks || 0;
        console.log(`[Charts] [DEBUG] 총 트랙 수 업데이트: ${data.total_tracks || 0}`);
    }
    
    if (elements.koreaCount) {
        elements.koreaCount.textContent = tracks.length;  // 멜론은 모두 한국 차트
        console.log(`[Charts] [DEBUG] 한국 차트 수 업데이트: ${tracks.length}`);
    }
    
    if (elements.globalCount) {
        elements.globalCount.textContent = 0;  // 멜론은 글로벌 차트 없음
        console.log(`[Charts] [DEBUG] 글로벌 차트 수 업데이트: 0`);
    }
    
    if (elements.lastUpdated) {
        const timestamp = new Date(data.timestamp).toLocaleTimeString('ko-KR');
        elements.lastUpdated.textContent = timestamp;
        console.log(`[Charts] [DEBUG] 마지막 업데이트 시간: ${timestamp}`);
    }
    
    console.log(`[Charts] [DEBUG] 멜론 통계 업데이트 완료`);
}


// 멜론 차트 데이터 표시
function displayMelonData(data) {
    console.log(`[Charts] [DEBUG] 멜론 차트 데이터 표시 시작:`, data);
    
    const tracks = data.chart_data?.tracks || [];
    console.log(`[Charts] [DEBUG] 표시할 트랙 수: ${tracks.length}`);
    console.log(`[Charts] [DEBUG] 트랙 데이터 샘플:`, tracks.slice(0, 3));
    
    if (elements.melonChart) {
        displayMelonTrackList(elements.melonChart, tracks);
        console.log(`[Charts] [DEBUG] 멜론 트랙 리스트 표시 완료`);
    } else {
        console.error(`[Charts] [DEBUG] 멜론 차트 엘리먼트를 찾을 수 없음`);
    }
}


// 멜론 트랙 리스트 표시
function displayMelonTrackList(container, tracks) {
    console.log(`[Charts] [DEBUG] 멜론 트랙 리스트 표시 시작, 컨테이너:`, container);
    console.log(`[Charts] [DEBUG] 표시할 트랙 배열:`, tracks);
    
    if (!tracks || tracks.length === 0) {
        console.log(`[Charts] [DEBUG] 트랙 데이터 없음, "데이터가 없습니다" 메시지 표시`);
        container.innerHTML = '<p class="no-data">데이터가 없습니다.</p>';
        return;
    }
    
    console.log(`[Charts] [DEBUG] ${tracks.length}개 트랙 HTML 생성 시작`);
    
    const tracksHtml = tracks.map((track, index) => {
        const rank = track.rank || (index + 1);
        console.log(`[Charts] [DEBUG] 트랙 ${index + 1}: ${track.title} - ${track.artist} (순위: ${rank})`);
        return createMelonTrackItemHTML(track, rank);
    }).join('');
    
    console.log(`[Charts] [DEBUG] 생성된 HTML 길이: ${tracksHtml.length} 문자`);
    
    container.innerHTML = tracksHtml;
    console.log(`[Charts] [DEBUG] 멜론 트랙 리스트 HTML 설정 완료`);
}


// 멜론 트랙 아이템 HTML 생성
function createMelonTrackItemHTML(track, rank) {
    const thumbnail = track.thumbnail || '';
    const songUrl = track.url || '#';
    
    return `
        <div class="track-item melon-track-item" data-song-id="${track.song_id}">
            <div class="track-rank">#${rank}</div>
            ${thumbnail ? `<img src="${thumbnail}" alt="앨범 커버" class="melon-thumbnail" onerror="this.style.display='none'">` : ''}
            <div class="track-info">
                <div class="track-title">
                    <a href="${songUrl}" target="_blank" style="color: inherit; text-decoration: none;">
                        ${escapeHtml(track.title || 'Unknown Track')}
                    </a>
                </div>
                <div class="track-artist">${escapeHtml(track.artist || 'Unknown Artist')}</div>
                <div style="font-size: 0.8em; color: var(--text-secondary); margin-top: 2px;">
                    ${escapeHtml(track.album || '')}
                </div>
            </div>
            <div class="track-meta">
                <div class="source-badge melon-badge">🍈 MELON</div>
                <small style="color: var(--text-secondary);">${track.chart_type}</small>
            </div>
        </div>
    `;
}

// HTML 이스케이프 함수
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text ? text.replace(/[&<>"']/g, m => map[m]) : '';
}

// 로딩 스피너 표시/숨김
function showLoading(show) {
    elements.loadingSpinner.style.display = show ? 'block' : 'none';
    elements.chartGrid.style.display = show ? 'none' : 'grid';
    elements.refreshBtn.disabled = show;
    elements.refreshBtn.textContent = show ? '⏳ 로딩중...' : '🔄 새로고침';
}

// 에러 메시지 표시
function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorMessage.style.display = 'block';
    elements.chartGrid.style.display = 'none';
}

// 에러 메시지 숨김
function hideError() {
    elements.errorMessage.style.display = 'none';
}

// 유틸리티: 차트 데이터 내보내기 (디버깅용)
function exportChartData() {
    if (chartsData) {
        console.log('[Charts] 현재 차트 데이터:', chartsData);
        return chartsData;
    } else {
        console.warn('[Charts] 차트 데이터가 없습니다.');
        return null;
    }
}

// 통합 차트 서비스 활성화 설정
function setActiveKoreaServices(services) {
    elements.koreaServiceButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.services === services.join(',')) {
            btn.classList.add('active');
        }
    });
    currentKoreaServices = services;
}

// 통합 차트 로딩
async function loadKoreaCharts(services = currentKoreaServices) {
    console.log(`[Charts] 통합 차트 로딩: ${services.join(', ')}`);
    showLoading(true);
    hideError();
    
    try {
        const params = new URLSearchParams();
        services.forEach(service => params.append('services', service));
        params.append('limit', '50');
        
        const response = await fetch(`/api/korea-charts/all?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            displayKoreaCharts(data);
        } else {
            throw new Error(data.error || '통합 차트 데이터 로딩 실패');
        }
    } catch (error) {
        console.error('[Charts] 통합 차트 로딩 오류:', error);
        showError(`통합 차트 로딩 실패: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// 통합 차트 표시
function displayKoreaCharts(data) {
    console.log('[Charts] 통합 차트 표시:', data);
    
    // 통계 정보 업데이트
    if (elements.koreaStats) {
        elements.koreaStats.style.display = 'grid';
        document.getElementById('totalTracks').textContent = data.total_tracks || 0;
        document.getElementById('successfulServices').textContent = data.successful_services || 0;
        document.getElementById('successRate').textContent = `${Math.round(data.success_rate || 0)}%`;
        
        const crossPlatformCount = data.cross_platform_analysis?.cross_platform_hits?.length || 0;
        document.getElementById('crossPlatformHits').textContent = crossPlatformCount;
    }
    
    // 크로스 플랫폼 히트곡 표시
    if (data.cross_platform_analysis?.success && data.cross_platform_analysis.cross_platform_hits) {
        displayCrossPlatformHits(data.cross_platform_analysis.cross_platform_hits);
    }
    
    // 서비스별 차트 표시
    displayServiceCharts(data.services);
}

// 크로스 플랫폼 히트곡 표시
function displayCrossPlatformHits(hits) {
    if (!elements.crossPlatformChart || !hits.length) return;
    
    elements.crossPlatformSection.style.display = 'block';
    
    const html = hits.map((hit, index) => `
        <div class="track-item cross-platform-track">
            <div class="track-rank">${index + 1}</div>
            <div class="track-info">
                <div class="track-title">${escapeHtml(hit.title)}</div>
                <div class="track-artist">${escapeHtml(hit.artist)}</div>
                <div class="track-details">
                    <span class="services-badge">${hit.services_count}개 서비스</span>
                    <span class="rank-badge">평균 ${hit.avg_rank}위</span>
                    <span class="services-list">${hit.services.join(', ')}</span>
                </div>
            </div>
            <div class="cross-platform-score">${Math.round(hit.cross_platform_score)}</div>
        </div>
    `).join('');
    
    elements.crossPlatformChart.innerHTML = html;
}

// 서비스별 차트 표시
function displayServiceCharts(services) {
    if (!elements.serviceCharts || !services) return;
    
    let html = '';
    
    Object.entries(services).forEach(([serviceName, charts]) => {
        const serviceKoreanName = {
            'melon': '멜론',
            'bugs': '벅스',
            'genie': '지니',
            'vibe': '바이브',
            'flo': '플로'
        }[serviceName] || serviceName;
        
        Object.entries(charts).forEach(([chartType, chartData]) => {
            if (chartData.success && chartData.tracks) {
                html += `
                    <div class="chart-section service-chart">
                        <h3>${serviceKoreanName} ${chartType} (${chartData.total_tracks}곡)</h3>
                        <div class="track-list">
                            ${chartData.tracks.slice(0, 20).map(track => `
                                <div class="track-item service-track" data-source="${serviceName}">
                                    <div class="track-rank">${track.rank}</div>
                                    <div class="track-info">
                                        <div class="track-title">${escapeHtml(track.title)}</div>
                                        <div class="track-artist">${escapeHtml(track.artist)}</div>
                                        ${track.album !== '알 수 없음' ? `<div class="track-album">${escapeHtml(track.album)}</div>` : ''}
                                    </div>
                                    <div class="service-badge ${serviceName}">${serviceKoreanName}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
        });
    });
    
    elements.serviceCharts.innerHTML = html;
}

// 각 플랫폼별 차트 로딩 함수들
async function loadBugsChart(chartType = currentBugsType) {
    console.log(`[Charts] [DEBUG] 벅스 차트 로딩 시작 - type: ${chartType}`);
    showLoading(true);
    hideError();
    
    try {
        const apiUrl = `/api/individual-chart/bugs?type=${chartType}&limit=50`;
        console.log(`[Charts] [DEBUG] 벅스 API 호출: ${apiUrl}`);
        
        const response = await fetch(apiUrl);
        console.log(`[Charts] [DEBUG] 벅스 응답 상태: ${response.status} ${response.statusText}`);
        
        const data = await response.json();
        console.log(`[Charts] [DEBUG] 벅스 응답 데이터:`, data);
        
        if (data.success) {
            console.log(`[Charts] [DEBUG] 벅스 차트 트랙 수: ${data.tracks ? data.tracks.length : 0}`);
            displayBugsChart(data, chartType);
            updateBugsTitle(chartType);
            console.log(`[Charts] [DEBUG] 벅스 차트 표시 완료`);
        } else {
            console.error(`[Charts] [DEBUG] 벅스 차트 로딩 실패:`, data.error);
            throw new Error(data.error || '벅스 차트 로딩 실패');
        }
    } catch (error) {
        console.error('[Charts] [DEBUG] 벅스 차트 로딩 오류:', error);
        console.error('[Charts] 벅스 차트 로딩 오류:', error);
        showError(`벅스 차트 로딩 실패: ${error.message}`);
    } finally {
        showLoading(false);
        console.log(`[Charts] [DEBUG] 벅스 차트 로딩 완료`);
    }
}

async function loadGenieChart(chartType = currentGenieType) {
    console.log(`[Charts] 지니 ${chartType} 차트 로딩`);
    showLoading(true);
    hideError();
    
    try {
        const response = await fetch(`/api/individual-chart/genie?type=${chartType}&limit=50`);
        const data = await response.json();
        
        if (data.success) {
            displayGenieChart(data, chartType);
            updateGenieTitle(chartType);
        } else {
            throw new Error(data.error || '지니 차트 로딩 실패');
        }
    } catch (error) {
        console.error('[Charts] 지니 차트 로딩 오류:', error);
        showError(`지니 차트 로딩 실패: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

async function loadVibeChart(chartType = currentVibeType) {
    console.log(`[Charts] 바이브 ${chartType} 차트 로딩`);
    showLoading(true);
    hideError();
    
    try {
        const response = await fetch(`/api/individual-chart/vibe?type=${chartType}&limit=50`);
        const data = await response.json();
        
        if (data.success) {
            displayVibeChart(data, chartType);
            updateVibeTitle(chartType);
        } else {
            throw new Error(data.error || '바이브 차트 로딩 실패');
        }
    } catch (error) {
        console.error('[Charts] 바이브 차트 로딩 오류:', error);
        showError(`바이브 차트 로딩 실패: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// 각 플랫폼별 차트 표시 함수들
function displayBugsChart(data, chartType) {
    console.log(`[Charts] [DEBUG] 벅스 차트 표시 시작:`, data);
    
    if (!elements.bugsChart) {
        console.error(`[Charts] [DEBUG] 벅스 차트 엘리먼트를 찾을 수 없음`);
        return;
    }
    
    if (!data.tracks) {
        console.error(`[Charts] [DEBUG] 벅스 트랙 데이터 없음`);
        return;
    }
    
    console.log(`[Charts] [DEBUG] 벅스 트랙 수: ${data.tracks.length}`);
    console.log(`[Charts] [DEBUG] 벅스 트랙 샘플:`, data.tracks.slice(0, 3));
    
    const html = data.tracks.map((track, index) => {
        console.log(`[Charts] [DEBUG] 벅스 트랙 ${index + 1}: ${track.title} - ${track.artist} (순위: ${track.rank})`);
        return `
            <div class="track-item bugs-track">
                <div class="track-rank">${track.rank}</div>
                <div class="track-info">
                    <div class="track-title">${escapeHtml(track.title)}</div>
                    <div class="track-artist">${escapeHtml(track.artist)}</div>
                    ${track.album !== '알 수 없음' ? `<div class="track-album">${escapeHtml(track.album)}</div>` : ''}
                </div>
                <div class="service-badge bugs">벅스</div>
            </div>
        `;
    }).join('');
    
    console.log(`[Charts] [DEBUG] 벅스 생성된 HTML 길이: ${html.length} 문자`);
    
    elements.bugsChart.innerHTML = html;
    console.log(`[Charts] [DEBUG] 벅스 차트 HTML 설정 완료`);
}

function displayGenieChart(data, chartType) {
    if (!elements.genieChart || !data.tracks) return;
    
    const html = data.tracks.map(track => `
        <div class="track-item genie-track">
            <div class="track-rank">${track.rank}</div>
            <div class="track-info">
                <div class="track-title">${escapeHtml(track.title)}</div>
                <div class="track-artist">${escapeHtml(track.artist)}</div>
                ${track.album !== '알 수 없음' ? `<div class="track-album">${escapeHtml(track.album)}</div>` : ''}
            </div>
            <div class="service-badge genie">지니</div>
        </div>
    `).join('');
    
    elements.genieChart.innerHTML = html;
}

function displayVibeChart(data, chartType) {
    if (!elements.vibeChart || !data.tracks) return;
    
    const html = data.tracks.map(track => `
        <div class="track-item vibe-track">
            <div class="track-rank">${track.rank}</div>
            <div class="track-info">
                <div class="track-title">${escapeHtml(track.title)}</div>
                <div class="track-artist">${escapeHtml(track.artist)}</div>
                ${track.album !== '알 수 없음' ? `<div class="track-album">${escapeHtml(track.album)}</div>` : ''}
            </div>
            <div class="service-badge vibe">바이브</div>
        </div>
    `).join('');
    
    elements.vibeChart.innerHTML = html;
}

// 제목 업데이트 함수들
function updateBugsTitle(chartType) {
    const titles = {
        'realtime': '🐛 벅스 실시간 TOP 50',
        'daily': '🐛 벅스 일간 TOP 50',
        'weekly': '🐛 벅스 주간 TOP 50'
    };
    elements.bugsChartTitle.textContent = titles[chartType] || '🐛 벅스 차트';
}

function updateGenieTitle(chartType) {
    const titles = {
        'realtime': '🧞 지니 실시간 TOP 50',
        'top200': '🧞 지니 TOP 200'
    };
    elements.genieChartTitle.textContent = titles[chartType] || '🧞 지니 차트';
}

function updateVibeTitle(chartType) {
    const titles = {
        'chart': '💚 바이브 메인 차트 TOP 50'
    };
    elements.vibeChartTitle.textContent = titles[chartType] || '💚 바이브 차트';
}

// loadChartData 함수 업데이트
function loadChartData() {
    switch(currentSource) {
        case 'korea-all':
            loadKoreaCharts(currentKoreaServices);
            break;
        case 'bugs':
            loadBugsChart(currentBugsType);
            break;
        case 'genie':
            loadGenieChart(currentGenieType);
            break;
        case 'vibe':
            loadVibeChart(currentVibeType);
            break;
        default:
            // 기존 Spotify/Melon 처리
            break;
    }
}

// 전역 함수로 내보내기 (콘솔에서 사용 가능)
window.exportChartData = exportChartData;
window.refreshCharts = loadChartData;
window.loadKoreaCharts = loadKoreaCharts;

console.log('[Charts] JavaScript 초기화 완료');