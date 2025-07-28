/**
 * Spotify Charts Page JavaScript
 * 차트 데이터 로딩 및 표시 관리
 */

let chartsData = null;
let currentFilter = 'all';
let currentSource = 'spotify';  // 'spotify' 또는 'melon'
let currentMelonType = 'realtime';  // 'realtime' 또는 'hot100'

// DOM 요소들
const elements = {
    refreshBtn: document.getElementById('refreshBtn'),
    toggleSourceBtn: document.getElementById('toggleSourceBtn'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    errorMessage: document.getElementById('errorMessage'),
    chartGrid: document.getElementById('chartGrid'),
    
    // Spotify 차트 요소들
    spotifyCharts: document.getElementById('spotifyCharts'),
    koreaChart: document.getElementById('koreaChart'),
    globalChart: document.getElementById('globalChart'),
    spotifyFilters: document.getElementById('spotifyFilters'),
    
    // 멜론 차트 요소들
    melonCharts: document.getElementById('melonCharts'),
    melonChart: document.getElementById('melonChart'),
    melonChartTitle: document.getElementById('melonChartTitle'),
    melonFilters: document.getElementById('melonFilters'),
    
    // 통계 및 필터 요소들
    totalTracks: document.getElementById('totalTracks'),
    koreaCount: document.getElementById('koreaCount'),
    globalCount: document.getElementById('globalCount'),
    lastUpdated: document.getElementById('lastUpdated'),
    
    // 버튼들
    filterButtons: document.querySelectorAll('.filter-btn'),
    sourceButtons: document.querySelectorAll('.source-btn'),
    melonTypeButtons: document.querySelectorAll('.melon-type-btn')
};

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Charts] 차트 페이지 초기화');
    setupEventListeners();
    loadChartData();
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
    
    // 필터 영역 표시/숨김
    if (source === 'spotify') {
        elements.spotifyFilters.style.display = 'flex';
        elements.melonFilters.style.display = 'none';
        elements.spotifyCharts.style.display = 'block';
        elements.melonCharts.style.display = 'none';
    } else {
        elements.spotifyFilters.style.display = 'none';
        elements.melonFilters.style.display = 'flex';
        elements.spotifyCharts.style.display = 'none';
        elements.melonCharts.style.display = 'block';
    }
    
    currentSource = source;
    loadChartData();
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
    
    if (currentSource === 'spotify') {
        await loadSpotifyChart();
    } else {
        await loadMelonChart(currentMelonType);
    }
}

// Spotify 차트 로딩
async function loadSpotifyChart() {
    showLoading(true);
    hideError();
    
    try {
        const response = await fetch('/api/spotify/charts');
        const data = await response.json();
        
        if (data.success) {
            chartsData = data;
            displaySpotifyData(data);
            updateSpotifyStats(data);
            console.log('[Charts] Spotify 차트 데이터 로딩 완료:', data.total_tracks, '개 트랙');
        } else {
            throw new Error(data.error || 'Spotify 차트 데이터 로딩 실패');
        }
    } catch (error) {
        console.error('[Charts] Spotify 차트 데이터 로딩 오류:', error);
        showError('Spotify 차트 데이터를 불러올 수 없습니다: ' + error.message);
    }
    
    showLoading(false);
}

// 멜론 차트 로딩
async function loadMelonChart(type = 'realtime') {
    showLoading(true);
    hideError();
    
    try {
        const response = await fetch(`/api/melon/charts?type=${type}&limit=50`);
        const data = await response.json();
        
        if (data.success) {
            chartsData = data;
            displayMelonData(data);
            updateMelonStats(data);
            console.log('[Charts] 멜론 차트 데이터 로딩 완료:', data.total_tracks, '개 트랙');
        } else {
            throw new Error(data.error || '멜론 차트 데이터 로딩 실패');
        }
    } catch (error) {
        console.error('[Charts] 멜론 차트 데이터 로딩 오류:', error);
        showError('멜론 차트 데이터를 불러올 수 없습니다: ' + error.message);
    }
    
    showLoading(false);
}

// Spotify 통계 정보 업데이트
function updateSpotifyStats(data) {
    const chartTracks = data.chart_data?.chart_tracks || [];
    const koreaTrackCount = chartTracks.filter(track => track.chart_region === 'korea').length;
    const globalTrackCount = chartTracks.filter(track => track.chart_region === 'global').length;
    
    elements.totalTracks.textContent = data.total_tracks || 0;
    elements.koreaCount.textContent = koreaTrackCount;
    elements.globalCount.textContent = globalTrackCount;
    elements.lastUpdated.textContent = new Date(data.timestamp).toLocaleTimeString('ko-KR');
}

// 멜론 통계 정보 업데이트
function updateMelonStats(data) {
    const tracks = data.chart_data?.tracks || [];
    
    elements.totalTracks.textContent = data.total_tracks || 0;
    elements.koreaCount.textContent = tracks.length;  // 멜론은 모두 한국 차트
    elements.globalCount.textContent = 0;  // 멜론은 글로벌 차트 없음
    elements.lastUpdated.textContent = new Date(data.timestamp).toLocaleTimeString('ko-KR');
}

// Spotify 차트 데이터 표시
function displaySpotifyData(data) {
    const chartTracks = data.chart_data?.chart_tracks || [];
    
    // 지역별로 트랙 분리
    const koreaTraks = chartTracks.filter(track => track.chart_region === 'korea');
    const globalTracks = chartTracks.filter(track => track.chart_region === 'global');
    
    // 차트 표시
    displayTrackList(elements.koreaChart, koreaTraks, 'korea');
    displayTrackList(elements.globalChart, globalTracks, 'global');
    
    // 현재 필터 적용
    applyFilter(currentFilter);
}

// 멜론 차트 데이터 표시
function displayMelonData(data) {
    const tracks = data.chart_data?.tracks || [];
    displayMelonTrackList(elements.melonChart, tracks);
}

// 트랙 리스트 표시
function displayTrackList(container, tracks, region) {
    if (!tracks || tracks.length === 0) {
        container.innerHTML = '<p class="no-data">데이터가 없습니다.</p>';
        return;
    }
    
    const tracksHtml = tracks.map((track, index) => {
        return createTrackItemHTML(track, index + 1, region);
    }).join('');
    
    container.innerHTML = tracksHtml;
}

// 멜론 트랙 리스트 표시
function displayMelonTrackList(container, tracks) {
    if (!tracks || tracks.length === 0) {
        container.innerHTML = '<p class="no-data">데이터가 없습니다.</p>';
        return;
    }
    
    const tracksHtml = tracks.map((track, index) => {
        return createMelonTrackItemHTML(track, track.rank || (index + 1));
    }).join('');
    
    container.innerHTML = tracksHtml;
}

// Spotify 트랙 아이템 HTML 생성
function createTrackItemHTML(track, rank, region) {
    const popularity = track.popularity || 0;
    const regionClass = region === 'korea' ? 'region-korea' : 'region-global';
    const regionText = region === 'korea' ? '🇰🇷 KOR' : '🌍 GLB';
    
    return `
        <div class="track-item" data-track-id="${track.id}">
            <div class="track-rank">#${rank}</div>
            <div class="track-info">
                <div class="track-title">${escapeHtml(track.name || 'Unknown Track')}</div>
                <div class="track-artist">${escapeHtml(track.main_artist || 'Unknown Artist')}</div>
            </div>
            <div class="track-meta">
                <div class="popularity-bar">
                    <div class="popularity-fill" style="width: ${popularity}%"></div>
                </div>
                <div class="region-badge ${regionClass}">${regionText}</div>
                <small style="color: var(--text-secondary);">${popularity}%</small>
            </div>
        </div>
    `;
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

// 전역 함수로 내보내기 (콘솔에서 사용 가능)
window.exportChartData = exportChartData;
window.refreshCharts = loadChartData;

console.log('[Charts] JavaScript 초기화 완료');