/**
 * Spotify Charts Page JavaScript
 * 차트 데이터 로딩 및 표시 관리
 */

let chartsData = null;
let currentFilter = 'all';

// DOM 요소들
const elements = {
    refreshBtn: document.getElementById('refreshBtn'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    errorMessage: document.getElementById('errorMessage'),
    chartGrid: document.getElementById('chartGrid'),
    koreaChart: document.getElementById('koreaChart'),
    globalChart: document.getElementById('globalChart'),
    totalTracks: document.getElementById('totalTracks'),
    koreaCount: document.getElementById('koreaCount'),
    globalCount: document.getElementById('globalCount'),
    lastUpdated: document.getElementById('lastUpdated'),
    filterButtons: document.querySelectorAll('.filter-btn')
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

    // 필터 버튼들
    elements.filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            setActiveFilter(filter);
            applyFilter(filter);
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

// 차트 데이터 로딩
async function loadChartData() {
    console.log('[Charts] 차트 데이터 로딩 시작');
    
    showLoading(true);
    hideError();
    
    try {
        const response = await fetch('/api/spotify/charts');
        const data = await response.json();
        
        if (data.success) {
            chartsData = data;
            displayChartData(data);
            updateStats(data);
            console.log('[Charts] 차트 데이터 로딩 완료:', data.total_tracks, '개 트랙');
        } else {
            throw new Error(data.error || '차트 데이터 로딩 실패');
        }
    } catch (error) {
        console.error('[Charts] 차트 데이터 로딩 오류:', error);
        showError('차트 데이터를 불러올 수 없습니다: ' + error.message);
    }
    
    showLoading(false);
}

// 통계 정보 업데이트
function updateStats(data) {
    const chartTracks = data.chart_data?.chart_tracks || [];
    const koreaTrackCount = chartTracks.filter(track => track.chart_region === 'korea').length;
    const globalTrackCount = chartTracks.filter(track => track.chart_region === 'global').length;
    
    elements.totalTracks.textContent = data.total_tracks || 0;
    elements.koreaCount.textContent = koreaTrackCount;
    elements.globalCount.textContent = globalTrackCount;
    elements.lastUpdated.textContent = new Date(data.timestamp).toLocaleTimeString('ko-KR');
}

// 차트 데이터 표시
function displayChartData(data) {
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

// 트랙 아이템 HTML 생성
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