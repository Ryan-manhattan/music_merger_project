// Music Merger - 메인 JavaScript
console.log("[Music Merger] JavaScript 로드 완료");

// 전역 변수
let uploadedFiles = [];
let fileSettings = {};
let currentExtractJob = null;
let uploadedImage = null;
let currentAudioResult = null;

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log("[Init] DOM 로드 완료, 이벤트 리스너 설정");
    setupEventListeners();
    updateNavigation();
    setupMarketAnalysisListeners();
    setupPitchSlider();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    // 파일 선택 이벤트
    fileInput.addEventListener('change', handleFileSelect);
    
    // 드래그 앤 드롭 이벤트
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // 이미지 업로드 이벤트
    const imageUpload = document.getElementById('imageUpload');
    if (imageUpload) {
        imageUpload.addEventListener('change', handleImageSelect);
    }
    
    // 슬라이더 값 변경 이벤트 (이벤트 위임)
    document.addEventListener('input', (e) => {
        if (e.target.classList.contains('slider')) {
            updateSliderValue(e.target);
        }
    });
    
    console.log("[Init] 모든 이벤트 리스너 설정 완료");
}

// 파일 선택 처리
function handleFileSelect(e) {
    console.log("[FileSelect] 파일 선택됨");
    const files = Array.from(e.target.files);
    uploadFiles(files);
}

// 드래그 오버 처리
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

// 드래그 리브 처리
function handleDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

// 드롭 처리
function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    
    console.log("[Drop] 파일 드롭됨");
    const files = Array.from(e.dataTransfer.files);
    uploadFiles(files);
}

// 파일 업로드
async function uploadFiles(files) {
    console.log(`[Upload] ${files.length}개 파일 업로드 시작`);
    
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        console.log("[Upload] 서버 응답:", data);
        
        if (data.success) {
            data.files.forEach(file => {
                addFileToList(file);
            });
            
            // UI 섹션 표시
            document.getElementById('filesSection').style.display = 'block';
            document.getElementById('globalSettings').style.display = 'block';
            document.getElementById('actionSection').style.display = 'block';
            
            // 총 파일 크기와 시간 계산
            updateTotalInfo();
        } else if (data.error) {
            alert('파일 업로드 오류: ' + data.error);
        }
    } catch (error) {
        console.error("[Upload] 오류:", error);
        alert('파일 업로드 중 오류가 발생했습니다.');
    }
}

// 파일 목록에 추가
function addFileToList(fileInfo) {
    console.log("[FileList] 파일 추가:", fileInfo.filename);
    
    // 파일 정보 저장
    uploadedFiles.push(fileInfo);
    
    // 기본 설정 초기화
    fileSettings[fileInfo.filename] = {
        fadeIn: 2,
        fadeOut: 3,
        volume: 0,
        gap: 1
    };
    
    // 템플릿 복제
    const template = document.getElementById('fileItemTemplate');
    const fileItem = template.content.cloneNode(true);
    
    // 데이터 설정
    const fileDiv = fileItem.querySelector('.file-item');
    fileDiv.dataset.filename = fileInfo.filename;
    
    // 링크 추출 소스인지 확인하여 추가 버튼 표시
    const isExtracted = fileInfo.source === 'link_extract';
    if (isExtracted) {
        const extractedButtons = fileItem.querySelectorAll('.extracted-only');
        extractedButtons.forEach(btn => {
            btn.style.display = 'inline-block';
        });
        
        // 키 조절 섹션도 표시
        const pitchSection = fileItem.querySelector('.pitch-adjust-section');
        if (pitchSection) {
            pitchSection.style.display = 'block';
        }
    }
    
    // 파일 이름과 정보 설정
    const fileName = fileItem.querySelector('.file-name');
    fileName.innerHTML = `
        <div class="file-title">${fileInfo.original_name}</div>
        <div class="file-meta">
            <span>${fileInfo.format}</span>
            <span>•</span>
            <span>${fileInfo.duration_str}</span>
            <span>•</span>
            <span>${fileInfo.size_mb} MB</span>
            ${isExtracted ? '<span>• 🔗 링크 추출</span>' : ''}
        </div>
    `;
    
    // DOM에 추가
    document.getElementById('filesList').appendChild(fileItem);
    console.log("[FileList] 파일 아이템 DOM 추가 완료");
}

// 파일 설정 토글
function toggleFileSettings(btn) {
    const fileItem = btn.closest('.file-item');
    const settings = fileItem.querySelector('.file-settings');
    const isVisible = settings.style.display !== 'none';
    
    console.log("[Settings] 설정 토글:", fileItem.dataset.filename, !isVisible);
    settings.style.display = isVisible ? 'none' : 'block';
}

// 파일 위로 이동
function moveFileUp(btn) {
    const fileItem = btn.closest('.file-item');
    const prev = fileItem.previousElementSibling;
    
    if (prev) {
        console.log("[Move] 파일 위로 이동:", fileItem.dataset.filename);
        fileItem.parentNode.insertBefore(fileItem, prev);
        updateFileOrder();
    }
}

// 파일 아래로 이동
function moveFileDown(btn) {
    const fileItem = btn.closest('.file-item');
    const next = fileItem.nextElementSibling;
    
    if (next) {
        console.log("[Move] 파일 아래로 이동:", fileItem.dataset.filename);
        fileItem.parentNode.insertBefore(next, fileItem);
        updateFileOrder();
    }
}

// 파일 제거
function removeFile(btn) {
    const fileItem = btn.closest('.file-item');
    const filename = fileItem.dataset.filename;
    
    console.log("[Remove] 파일 제거:", filename);
    
    // 배열에서 제거
    uploadedFiles = uploadedFiles.filter(f => f.filename !== filename);
    delete fileSettings[filename];
    
    // DOM에서 제거
    fileItem.remove();
    
    // 파일이 없으면 섹션 숨기기
    if (uploadedFiles.length === 0) {
        document.getElementById('filesSection').style.display = 'none';
        document.getElementById('globalSettings').style.display = 'none';
        document.getElementById('actionSection').style.display = 'none';
    } else {
        // 총 정보 업데이트
        updateTotalInfo();
    }
}

// 파일 순서 업데이트
function updateFileOrder() {
    const fileItems = document.querySelectorAll('.file-item');
    const newOrder = [];
    
    fileItems.forEach(item => {
        const filename = item.dataset.filename;
        const file = uploadedFiles.find(f => f.filename === filename);
        if (file) newOrder.push(file);
    });
    
    uploadedFiles = newOrder;
    console.log("[Order] 파일 순서 업데이트 완료");
}

// 슬라이더 값 업데이트
function updateSliderValue(slider) {
    const fileItem = slider.closest('.file-item');
    const filename = fileItem.dataset.filename;
    const settingName = slider.name;
    const value = parseFloat(slider.value);
    
    // 값 표시 업데이트
    const valueDisplay = slider.parentElement.querySelector('.value-display');
    valueDisplay.textContent = value;
    
    // 설정 저장
    fileSettings[filename][settingName] = value;
    console.log(`[Settings] ${filename} - ${settingName}: ${value}`);
}

// 오디오 처리 시작
async function processAudio() {
    console.log("[Process] 오디오 처리 시작");
    
    // UI 상태 변경
    document.getElementById('actionSection').style.display = 'none';
    document.getElementById('progressSection').style.display = 'block';
    
    // 파일 순서와 설정 수집
    const processingData = {
        files: uploadedFiles.map(file => ({
            filename: file.filename,
            settings: fileSettings[file.filename]
        })),
        globalSettings: {
            normalizeVolume: document.getElementById('normalizeVolume').checked,
            crossfade: document.getElementById('crossfade').checked
        }
    };
    
    console.log("[Process] 처리 데이터:", processingData);
    console.log("[Process] 업로드된 파일 목록:", uploadedFiles.map(f => f.filename));
    console.log("[Process] 현재 파일 설정:", fileSettings);
    
    try {
        // 처리 시작 요청
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(processingData)
        });
        
        const result = await response.json();
        console.log("[Process] 처리 시작 응답:", result);
        
        if (result.success && result.job_id) {
            // 진행 상황 모니터링 시작
            monitorProgress(result.job_id);
        } else {
            throw new Error(result.message || '처리 시작 실패');
        }
    } catch (error) {
        console.error("[Process] 오류:", error);
        alert('처리 중 오류가 발생했습니다: ' + error.message);
        resetProgress();
    }
}

// 진행 상황 모니터링
async function monitorProgress(jobId) {
    console.log("[Monitor] 진행 상황 모니터링 시작:", jobId);
    
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    const checkStatus = async () => {
        try {
            const response = await fetch(`/process/status/${jobId}`);
            const status = await response.json();
            
            console.log("[Monitor] 상태:", status);
            
            // 진행률 업데이트
            progressFill.style.width = status.progress + '%';
            progressText.textContent = status.message || `처리 중... ${status.progress}%`;
            
            if (status.status === 'completed') {
                // 처리 완료
                console.log("[Monitor] 처리 완료:", status.result);
                showResult(status.result);
            } else if (status.status === 'error') {
                // 오류 발생
                throw new Error(status.message || '처리 중 오류 발생');
            } else {
                // 계속 모니터링
                setTimeout(checkStatus, 500); // 0.5초마다 확인
            }
        } catch (error) {
            console.error("[Monitor] 오류:", error);
            alert('처리 중 오류가 발생했습니다: ' + error.message);
            resetProgress();
        }
    };
    
    // 첫 확인
    checkStatus();
}

// 결과 표시
function showResult(result) {
    console.log("[Result] 결과 표시");
    
    // 현재 오디오 결과 저장
    currentAudioResult = result;
    
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'block';
    
    // 결과 정보 표시
    const totalFiles = uploadedFiles.length;
    document.getElementById('resultInfo').textContent = 
        `${totalFiles}개의 파일이 성공적으로 합쳐졌습니다.`;
    
    // 다운로드 버튼 설정
    document.getElementById('downloadBtn').onclick = () => {
        console.log("[Download] 다운로드 시작:", result.filename);
        window.location.href = `/download/${result.filename}`;
    };
}

// 앱 초기화
function resetApp() {
    console.log("[Reset] 앱 초기화");
    
    // 변수 초기화
    uploadedFiles = [];
    fileSettings = {};
    uploadedImage = null;
    currentAudioResult = null;
    
    // UI 초기화
    document.getElementById('filesList').innerHTML = '';
    document.getElementById('filesSection').style.display = 'none';
    document.getElementById('globalSettings').style.display = 'none';
    document.getElementById('actionSection').style.display = 'none';
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('videoSection').style.display = 'none';
    document.getElementById('videoProgressSection').style.display = 'none';
    document.getElementById('videoResultSection').style.display = 'none';
    document.getElementById('fileInput').value = '';
    
    // 이미지 업로드 초기화
    const imageUpload = document.getElementById('imageUpload');
    const imageUploadArea = document.getElementById('imageUploadArea');
    const imagePreview = document.getElementById('imagePreview');
    const generateVideoBtn = document.getElementById('generateVideoBtn');
    
    if (imageUpload) imageUpload.value = '';
    if (imageUploadArea) imageUploadArea.style.display = 'block';
    if (imagePreview) imagePreview.style.display = 'none';
    if (generateVideoBtn) generateVideoBtn.disabled = true;
    
    // 진행률 초기화
    resetProgress();
    resetVideoProgress();
}

// 진행률 초기화
function resetProgress() {
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressText').textContent = '처리 중...';
    document.getElementById('actionSection').style.display = 'block';
    document.getElementById('progressSection').style.display = 'none';
}

// 진행률 업데이트
function updateProgress(progress, message) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressFill) {
        progressFill.style.width = progress + '%';
    }
    if (progressText) {
        progressText.textContent = message || `처리 중... ${progress}%`;
    }
}

// 링크에서 음악 추출
async function extractFromLink() {
    console.log("[Extract] 링크 추출 시작");
    
    const linkInput = document.getElementById('linkInput');
    const extractBtn = document.getElementById('extractBtn');
    
    const url = linkInput.value.trim();
    
    if (!url) {
        alert('링크를 입력해주세요');
        return;
    }
    
    // URL 형식 검증
    try {
        new URL(url);
    } catch {
        alert('올바른 URL 형식이 아닙니다');
        return;
    }
    
    // 버튼 비활성화
    extractBtn.disabled = true;
    extractBtn.textContent = '추출 중...';
    
    try {
        // 추출 요청
        const response = await fetch('/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentExtractJob = result.job_id;
            
            // 진행 상황 모니터링 시작
            document.getElementById('progressSection').style.display = 'block';
            updateProgress(0, '링크 분석 중...');
            monitorExtractProgress(result.job_id);
            
            // 입력 필드 초기화
            linkInput.value = '';
        } else {
            throw new Error(result.error);
        }
        
    } catch (error) {
        console.error("[Extract] 오류:", error);
        alert(`추출 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        // 버튼 복원
        extractBtn.disabled = false;
        extractBtn.textContent = '🎵 추출';
    }
}

// 추출 진행 상황 모니터링
async function monitorExtractProgress(jobId) {
    console.log("[Extract] 진행 상황 모니터링 시작:", jobId);
    
    let checkCount = 0;
    
    const checkProgress = async () => {
        checkCount++;
        console.log(`[Extract] 진행 상황 확인 중... (${checkCount}회차)`);
        
        try {
            const response = await fetch(`/process/status/${jobId}`);
            console.log(`[Extract] 서버 응답 상태: ${response.status}`);
            
            if (response.status === 404) {
                // 작업이 존재하지 않음
                throw new Error('작업을 찾을 수 없습니다. 서버에서 처리가 중단되었을 수 있습니다.');
            }
            
            const status = await response.json();
            console.log(`[Extract] 현재 상태:`, status);
            
            // 진행률 업데이트
            updateProgress(status.progress || 0, status.message || '처리 중...');
            
            if (status.status === 'completed') {
                // 추출 완료
                if (status.result && status.result.type === 'extract') {
                    const fileInfo = status.result.file_info;
                    console.log("[Extract] 추출 완료:", fileInfo);
                    
                    // 추출된 파일을 업로드 목록에 추가
                    uploadedFiles.push(fileInfo);
                    addFileToList(fileInfo);
                    
                    // UI 업데이트
                    document.getElementById('filesSection').style.display = 'block';
                    document.getElementById('globalSettings').style.display = 'block';
                    document.getElementById('actionSection').style.display = 'block';
                    
                    updateProgress(100, '추출 완료!');
                    
                    setTimeout(() => {
                        document.getElementById('progressSection').style.display = 'none';
                        currentExtractJob = null;
                    }, 2000);
                } else {
                    throw new Error('예상치 못한 결과 형식');
                }
                
            } else if (status.status === 'error') {
                // 추출 실패
                throw new Error(status.message || '추출 중 오류 발생');
                
            } else {
                // 계속 진행 중
                console.log(`[Extract] 1초 후 다시 확인... (현재 진행률: ${status.progress || 0}%)`);
                setTimeout(checkProgress, 1000);
            }
            
        } catch (error) {
            console.error("[Extract] 진행 상황 확인 오류:", error);
            updateProgress(0, `오류: ${error.message}`);
            
            setTimeout(() => {
                document.getElementById('progressSection').style.display = 'none';
                currentExtractJob = null;
            }, 3000);
        }
    };
    
    checkProgress();
}

// 총 정보 업데이트
function updateTotalInfo() {
    console.log("[TotalInfo] 총 정보 업데이트");
    
    if (uploadedFiles.length === 0) return;
    
    // 총 크기와 시간 계산
    let totalSize = 0;
    let totalDuration = 0;
    
    uploadedFiles.forEach(file => {
        totalSize += file.size_mb || 0;
        totalDuration += file.duration || 0;
    });
    
    // 간격 추가 (기본 1초씩)
    const gaps = (uploadedFiles.length - 1) * 1;
    totalDuration += gaps;
    
    // 표시를 위한 HTML 업데이트
    const totalInfoHtml = `
        <div class="total-info">
            <strong>총 ${uploadedFiles.length}개 파일</strong>
            <span>•</span>
            <span>예상 시간: ${formatDuration(totalDuration)}</span>
            <span>•</span>
            <span>총 크기: ${totalSize.toFixed(1)} MB</span>
        </div>
    `;
    
    // 기존 total-info가 없으면 추가
    let totalInfoEl = document.querySelector('.total-info');
    if (!totalInfoEl) {
        const filesSection = document.getElementById('filesSection');
        filesSection.insertAdjacentHTML('afterbegin', totalInfoHtml);
    } else {
        totalInfoEl.outerHTML = totalInfoHtml;
    }
}

// 시간 포맷 함수
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

// 전역 함수로 노출 (인라인 onclick용)
// 이미지 선택 처리
function handleImageSelect(e) {
    console.log("[ImageSelect] 이미지 선택됨");
    const file = e.target.files[0];
    if (file) {
        uploadImage(file);
    }
}

// 이미지 업로드
async function uploadImage(file) {
    console.log("[ImageUpload] 이미지 업로드 시작:", file.name);
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/upload_image', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        console.log("[ImageUpload] 서버 응답:", data);
        
        if (data.success) {
            uploadedImage = data.image;
            showImagePreview(file, data.image);
            
            // 동영상 생성 버튼 활성화
            document.getElementById('generateVideoBtn').disabled = false;
        } else {
            alert('이미지 업로드 오류: ' + data.error);
        }
    } catch (error) {
        console.error("[ImageUpload] 오류:", error);
        alert('이미지 업로드 중 오류가 발생했습니다.');
    }
}

// 이미지 미리보기 표시
function showImagePreview(file, imageInfo) {
    console.log("[ImagePreview] 이미지 미리보기 표시");
    
    const uploadArea = document.getElementById('imageUploadArea');
    const preview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const imageInfoEl = document.getElementById('imageInfo');
    
    // 미리보기 이미지 설정
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
    };
    reader.readAsDataURL(file);
    
    // 이미지 정보 표시
    imageInfoEl.textContent = `${imageInfo.original_name} (${imageInfo.size_mb.toFixed(1)} MB)`;
    
    // UI 업데이트
    uploadArea.style.display = 'none';
    preview.style.display = 'block';
}

// 동영상 섹션 표시
function showVideoSection() {
    console.log("[VideoSection] 동영상 섹션 표시");
    
    if (!currentAudioResult) {
        alert('먼저 오디오 파일을 처리해주세요.');
        return;
    }
    
    document.getElementById('videoSection').style.display = 'block';
    
    // 스크롤 이동
    document.getElementById('videoSection').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

// 동영상 생성
async function generateVideo() {
    console.log("[Video] 동영상 생성 시작");
    
    if (!currentAudioResult || !uploadedImage) {
        alert('오디오 파일과 이미지가 모두 필요합니다.');
        return;
    }
    
    // UI 상태 변경
    document.getElementById('videoSection').style.display = 'none';
    document.getElementById('videoProgressSection').style.display = 'block';
    
    const videoData = {
        audio_filename: currentAudioResult.filename,
        image_filename: uploadedImage.filename,
        preset: document.getElementById('videoPreset').value
    };
    
    console.log("[Video] 동영상 생성 데이터:", videoData);
    
    try {
        // 동영상 생성 요청
        const response = await fetch('/create_video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(videoData)
        });
        
        const result = await response.json();
        console.log("[Video] 동영상 생성 시작 응답:", result);
        
        if (result.success && result.job_id) {
            // 진행 상황 모니터링 시작
            monitorVideoProgress(result.job_id);
        } else {
            throw new Error(result.message || '동영상 생성 시작 실패');
        }
    } catch (error) {
        console.error("[Video] 오류:", error);
        alert('동영상 생성 중 오류가 발생했습니다: ' + error.message);
        resetVideoProgress();
    }
}

// 동영상 진행 상황 모니터링
async function monitorVideoProgress(jobId) {
    console.log("[VideoMonitor] 동영상 진행 상황 모니터링 시작:", jobId);
    
    const progressFill = document.getElementById('videoProgressFill');
    const progressText = document.getElementById('videoProgressText');
    
    const checkStatus = async () => {
        try {
            const response = await fetch(`/process/status/${jobId}`);
            const status = await response.json();
            
            console.log("[VideoMonitor] 상태:", status);
            
            // 진행률 업데이트
            progressFill.style.width = status.progress + '%';
            progressText.textContent = status.message || `동영상 생성 중... ${status.progress}%`;
            
            if (status.status === 'completed') {
                // 동영상 생성 완료
                console.log("[VideoMonitor] 동영상 생성 완료:", status.result);
                showVideoResult(status.result.video_info);
            } else if (status.status === 'error') {
                // 오류 발생
                throw new Error(status.message || '동영상 생성 중 오류 발생');
            } else {
                // 계속 모니터링
                setTimeout(checkStatus, 1000); // 1초마다 확인
            }
        } catch (error) {
            console.error("[VideoMonitor] 오류:", error);
            alert('동영상 생성 중 오류가 발생했습니다: ' + error.message);
            resetVideoProgress();
        }
    };
    
    // 첫 확인
    checkStatus();
}

// 동영상 결과 표시
function showVideoResult(videoInfo) {
    console.log("[VideoResult] 동영상 결과 표시");
    
    document.getElementById('videoProgressSection').style.display = 'none';
    document.getElementById('videoResultSection').style.display = 'block';
    
    // 결과 정보 표시
    document.getElementById('videoResultInfo').textContent = 
        `동영상이 성공적으로 생성되었습니다! (${videoInfo.resolution}, ${(videoInfo.size / (1024*1024)).toFixed(1)} MB)`;
    
    // 다운로드 버튼 설정
    document.getElementById('downloadVideoBtn').onclick = () => {
        console.log("[VideoDownload] 동영상 다운로드 시작:", videoInfo.filename);
        window.location.href = `/download/${videoInfo.filename}`;
    };
    
    // 스크롤 이동
    document.getElementById('videoResultSection').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

// 동영상 진행률 초기화
function resetVideoProgress() {
    document.getElementById('videoProgressFill').style.width = '0%';
    document.getElementById('videoProgressText').textContent = '동영상 생성 준비 중...';
    document.getElementById('videoSection').style.display = 'block';
    document.getElementById('videoProgressSection').style.display = 'none';
}

// 전역 함수로 노출 (인라인 onclick용)
window.toggleFileSettings = toggleFileSettings;
window.moveFileUp = moveFileUp;
window.moveFileDown = moveFileDown;
window.removeFile = removeFile;
window.processAudio = processAudio;
window.resetApp = resetApp;
window.showVideoSection = showVideoSection;
window.generateVideo = generateVideo;

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

// ===========================================
// 탭 관리 기능
// ===========================================

function showTab(tabName) {
    console.log(`[Tab] 탭 전환: ${tabName}`);
    
    // 모든 탭 버튼에서 active 클래스 제거
    document.querySelectorAll('.nav-tab').forEach(btn => btn.classList.remove('active'));
    
    // 모든 탭 컨텐츠 숨김
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // 선택된 탭 버튼에 active 클래스 추가
    event.target.classList.add('active');
    
    // 선택된 탭 컨텐츠 표시
    const tabContent = document.getElementById(tabName + 'Tab');
    if (tabContent) {
        tabContent.classList.add('active');
    }
}

// ===========================================
// 시장 분석 기능
// ===========================================

let marketGenres = [];

// 장르 목록 로드
async function loadGenres() {
    try {
        const response = await fetch('/api/market/genres');
        const data = await response.json();
        
        if (data.success) {
            marketGenres = data.genres;
            populateGenreSelects();
            console.log("[Market] 장르 목록 로드 완료:", data.count, "개");
        } else {
            console.error("[Market] 장르 로드 실패:", data.error);
        }
    } catch (error) {
        console.error("[Market] 장르 로드 오류:", error);
    }
}

// 장르 선택 요소들 채우기
function populateGenreSelects() {
    const genreSelect = document.getElementById('genreSelect');
    const genreCheckboxes = document.getElementById('genreCheckboxes');
    
    if (genreSelect && marketGenres.length > 0) {
        genreSelect.innerHTML = '<option value="">장르를 선택하세요...</option>';
        marketGenres.forEach(genre => {
            const option = document.createElement('option');
            option.value = genre.id;
            option.textContent = `${genre.korean} (${genre.english})`;
            genreSelect.appendChild(option);
        });
    }
    
    if (genreCheckboxes && marketGenres.length > 0) {
        genreCheckboxes.innerHTML = '';
        marketGenres.forEach(genre => {
            const label = document.createElement('label');
            label.className = 'checkbox-label';
            label.innerHTML = `
                <input type="checkbox" name="compareGenres" value="${genre.id}">
                <span>${genre.korean} (${genre.english})</span>
            `;
            genreCheckboxes.appendChild(label);
        });
    }
}

// 시장 분석 이벤트 리스너 설정
function setupMarketAnalysisListeners() {
    // V2 모드 변경 시 (나중에 추가되는 요소들을 위해 이벤트 위임 사용)
    document.addEventListener('change', function(e) {
        if (e.target.name === 'v2Mode') {
            handleV2ModeChange();
        }
    });
    
    console.log("[Init] 트렌드 분석 V2 리스너 설정 완료");
}

// 시장 분석 시작 (V2 전용)
async function startMarketAnalysis() {
    console.log(`[Market] 트렌드 분석 V2 시작`);
    
    showMarketProgress();
    
    try {
        const result = await startTrendsV2Analysis();
        
        if (result.success) {
            displayMarketResult(result, 'trends_v2');
        } else {
            alert('분석 실패: ' + result.error);
        }
    } catch (error) {
        console.error("[Market] 분석 오류:", error);
        alert('분석 중 오류가 발생했습니다: ' + error.message);
    }
    
    hideMarketProgress();
}

// 개별 장르 분석
async function analyzeSingleGenre(genre, timeframe, geo) {
    const url = `/api/market/analyze/${genre}?timeframe=${encodeURIComponent(timeframe)}&geo=${geo}`;
    const response = await fetch(url);
    return await response.json();
}

// 장르 비교 분석
async function compareGenres(genres, timeframe, geo) {
    const response = await fetch('/api/market/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ genres, timeframe, geo })
    });
    return await response.json();
}

// 전체 시장 개관
async function getMarketOverview(timeframe, geo) {
    const url = `/api/market/overview?timeframe=${encodeURIComponent(timeframe)}&geo=${geo}`;
    const response = await fetch(url);
    return await response.json();
}

// 진행 상황 표시
function showMarketProgress() {
    document.getElementById('marketProgressSection').style.display = 'block';
    document.getElementById('marketResultSection').style.display = 'none';
    document.getElementById('marketProgressText').textContent = '시장 데이터 수집 중...';
    
    // 진행바 애니메이션
    let progress = 0;
    const progressBar = document.getElementById('marketProgressFill');
    const interval = setInterval(() => {
        progress += 2;
        progressBar.style.width = progress + '%';
        if (progress >= 90) {
            clearInterval(interval);
        }
    }, 100);
}

// 진행 상황 업데이트
function updateMarketProgress(percentage, message) {
    const progressBar = document.getElementById('marketProgressFill');
    const progressText = document.getElementById('marketProgressText');
    
    if (progressBar) {
        progressBar.style.width = percentage + '%';
    }
    
    if (progressText && message) {
        progressText.textContent = message;
    }
    
    console.log(`[Market Progress] ${percentage}% - ${message}`);
}

// 진행 상황 숨김
function hideMarketProgress() {
    document.getElementById('marketProgressSection').style.display = 'none';
    document.getElementById('marketProgressFill').style.width = '100%';
}

// 결과 표시
function displayMarketResult(result, analysisType) {
    const resultSection = document.getElementById('marketResultSection');
    const resultDiv = document.getElementById('marketResult');
    
    let html = '';
    
    if (analysisType === 'single') {
        html = formatSingleGenreResult(result);
    } else if (analysisType === 'compare') {
        html = formatCompareResult(result);
    } else if (analysisType === 'trends_v2') {
        // V2 트렌드 분석 결과 처리
        displayTrendsV2Result(result, analysisType);
        resultSection.style.display = 'block';
        return;
    } else {
        html = formatOverviewResult(result);
    }
    
    resultDiv.innerHTML = html;
    resultSection.style.display = 'block';
}

// 개별 장르 결과 포맷
function formatSingleGenreResult(result) {
    const genreInfo = marketGenres.find(g => g.id === result.genre);
    const genreName = genreInfo ? genreInfo.korean : result.genre;
    
    const trends = result.trends_data || {};
    const metrics = result.market_metrics || {};
    const forecast = result.market_forecast || {};
    
    return `
        <div class="result-card">
            <h4>📊 ${genreName} 시장 분석</h4>
            
            <div class="metrics-grid">
                <div class="metric-item">
                    <span class="metric-label">현재 트렌드 점수</span>
                    <span class="metric-value">${trends.current_score || 0}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">평균 점수</span>
                    <span class="metric-value">${(trends.average_score || 0).toFixed(1)}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">시장 등급</span>
                    <span class="metric-value grade-${(metrics.market_grade || 'C').toLowerCase()}">${metrics.market_grade || 'N/A'}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">트렌드 방향</span>
                    <span class="metric-value direction-${trends.trend_direction || 'stable'}">${getTrendIcon(trends.trend_direction)} ${getTrendText(trends.trend_direction)}</span>
                </div>
            </div>
            
            ${forecast.short_term ? `
                <div class="forecast-section">
                    <h5>📅 단기 예측 (1-3개월)</h5>
                    <p><strong>방향:</strong> ${forecast.short_term.direction} (${forecast.short_term.predicted_change})</p>
                    <p><strong>신뢰도:</strong> ${forecast.short_term.confidence}</p>
                </div>
            ` : ''}
            
            ${forecast.long_term ? `
                <div class="forecast-section">
                    <h5>🔮 장기 전망 (6-12개월)</h5>
                    <p><strong>전망:</strong> ${forecast.long_term.outlook}</p>
                    <p><strong>투자 추천:</strong> ${forecast.long_term.investment_recommendation}</p>
                    <p><strong>리스크:</strong> ${forecast.long_term.risk_level}</p>
                </div>
            ` : ''}
        </div>
    `;
}

// 비교 결과 포맷
function formatCompareResult(result) {
    const ranking = result.market_ranking || {};
    const growth = result.growth_analysis || {};
    
    return `
        <div class="result-card">
            <h4>📊 장르 비교 분석</h4>
            
            ${ranking.trends_ranking ? `
                <div class="ranking-section">
                    <h5>📈 트렌드 순위</h5>
                    <ol class="ranking-list">
                        ${ranking.trends_ranking.map((genre, index) => {
                            const genreInfo = marketGenres.find(g => g.id === genre);
                            const genreName = genreInfo ? genreInfo.korean : genre;
                            return `<li>${genreName}</li>`;
                        }).join('')}
                    </ol>
                </div>
            ` : ''}
            
            ${growth.rising_genres || growth.stable_genres || growth.declining_genres ? `
                <div class="growth-section">
                    <h5>📊 성장 분석</h5>
                    ${growth.rising_genres?.length ? `<p><strong>📈 상승:</strong> ${growth.rising_genres.map(g => getGenreName(g)).join(', ')}</p>` : ''}
                    ${growth.stable_genres?.length ? `<p><strong>➡️ 안정:</strong> ${growth.stable_genres.map(g => getGenreName(g)).join(', ')}</p>` : ''}
                    ${growth.declining_genres?.length ? `<p><strong>📉 하락:</strong> ${growth.declining_genres.map(g => getGenreName(g)).join(', ')}</p>` : ''}
                </div>
            ` : ''}
        </div>
    `;
}

// 전체 시장 개관 결과 포맷
function formatOverviewResult(result) {
    const summary = result.market_summary || {};
    const insights = result.market_insights || [];
    const recommendations = result.recommendations || [];
    
    return `
        <div class="result-card">
            <h4>🌍 전체 음악 시장 개관</h4>
            
            <div class="summary-section">
                <h5>📊 시장 요약</h5>
                <div class="summary-grid">
                    <div class="summary-item">
                        <span class="summary-label">분석 장르 수</span>
                        <span class="summary-value">${summary.total_genres_analyzed || 0}개</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">지배적 장르</span>
                        <span class="summary-value">${getGenreName(summary.dominant_genre) || 'N/A'}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">최고 성장</span>
                        <span class="summary-value">${getGenreName(summary.fastest_growing) || 'N/A'}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-label">최고 참여</span>
                        <span class="summary-value">${getGenreName(summary.most_engaging) || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            ${insights.length ? `
                <div class="insights-section">
                    <h5>💡 시장 인사이트</h5>
                    <ul class="insights-list">
                        ${insights.map(insight => `<li>${insight}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${recommendations.length ? `
                <div class="recommendations-section">
                    <h5>📋 추천사항</h5>
                    <ul class="recommendations-list">
                        ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

// 헬퍼 함수들
function getTrendIcon(direction) {
    switch(direction) {
        case 'rising': return '📈';
        case 'falling': return '📉';
        default: return '➡️';
    }
}

function getTrendText(direction) {
    switch(direction) {
        case 'rising': return '상승';
        case 'falling': return '하락';
        default: return '안정';
    }
}

function getGenreName(genreId) {
    if (!genreId) return null;
    const genre = marketGenres.find(g => g.id === genreId);
    return genre ? genre.korean : genreId;
}

// 분석 초기화
function resetMarketAnalysis() {
    document.getElementById('marketResultSection').style.display = 'none';
    document.getElementById('marketProgressSection').style.display = 'none';
    
    // 폼 초기화
    document.querySelector('input[name="analysisType"][value="single"]').checked = true;
    document.getElementById('genreSelect').value = '';
    document.querySelectorAll('input[name="compareGenres"]').forEach(cb => cb.checked = false);
    document.getElementById('timeframe').value = 'today 3-m';
    document.getElementById('geoRegion').value = 'KR';
    
    // 옵션 표시 상태 리셋
    document.getElementById('singleGenreOption').style.display = 'block';
    document.getElementById('compareGenreOption').style.display = 'none';
}

// 음악 분석 함수
async function analyzeMusic() {
    const url = document.getElementById('analysisLinkInput').value.trim();
    if (!url) {
        alert('YouTube URL을 입력해주세요.');
        return;
    }
    
    console.log("[Analysis] 음악 분석 시작:", url);
    
    // 진행 상황 표시
    document.getElementById('analysisProgressSection').style.display = 'block';
    document.getElementById('analysisResultSection').style.display = 'none';
    
    try {
        const response = await fetch('/api/music-analysis/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 작업 상태 모니터링
            monitorAnalysisJob(data.job_id);
        } else {
            alert('분석 시작 실패: ' + data.error);
            document.getElementById('analysisProgressSection').style.display = 'none';
        }
    } catch (error) {
        console.error("[Analysis] 분석 오류:", error);
        alert('분석 중 오류가 발생했습니다: ' + error.message);
        document.getElementById('analysisProgressSection').style.display = 'none';
    }
}

// 분석 작업 모니터링
function monitorAnalysisJob(jobId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/music-analysis/status/${jobId}`);
            const data = await response.json();
            
            // 진행률 업데이트
            document.getElementById('analysisProgressFill').style.width = (data.progress || 0) + '%';
            document.getElementById('analysisProgressText').textContent = data.message || '분석 중...';
            
            if (data.status === 'completed') {
                clearInterval(interval);
                displayAnalysisResult(data.result);
                document.getElementById('analysisProgressSection').style.display = 'none';
            } else if (data.status === 'error') {
                clearInterval(interval);
                alert('분석 실패: ' + data.message);
                document.getElementById('analysisProgressSection').style.display = 'none';
            }
        } catch (error) {
            console.error("[Analysis] 상태 확인 오류:", error);
            clearInterval(interval);
        }
    }, 2000);
}

// 분석 결과 표시 (상세 버전)
function displayAnalysisResult(result) {
    // 상세 분석 결과 표시
    displayDetailedAnalysisResults(result);
    
    // 기존 간단한 결과도 유지 (호환성)
    const resultDiv = document.getElementById('analysisResult');
    
    let html = `
        <div class="result-card">
            <h4>🎵 ${result.video_info?.title || '분석 결과'}</h4>
            
            <div class="video-info">
                <p><strong>채널:</strong> ${result.video_info?.channel || 'N/A'}</p>
                <p><strong>조회수:</strong> ${(result.video_info?.view_count || 0).toLocaleString()}</p>
                <p><strong>좋아요:</strong> ${(result.video_info?.like_count || 0).toLocaleString()}</p>
            </div>
            
            ${result.music_analysis ? `
                <div class="music-analysis">
                    <h5>🎼 음악 분석</h5>
                    <p><strong>장르:</strong> ${result.music_analysis.primary_genre || 'N/A'}</p>
                    <p><strong>BPM:</strong> ${result.music_analysis.bpm || 'N/A'}</p>
                    <p><strong>감정:</strong> ${result.music_analysis.mood || 'N/A'}</p>
                </div>
            ` : ''}
            
            ${result.comments_analysis ? `
                <div class="comments-analysis">
                    <h5>💬 댓글 분석</h5>
                    <p><strong>댓글 수:</strong> ${result.comments_analysis.total_comments}개</p>
                    <p><strong>평균 감성:</strong> ${(result.comments_analysis.average_sentiment || 0).toFixed(2)}</p>
                </div>
            ` : ''}
        </div>
    `;
    
    resultDiv.innerHTML = html;
    document.getElementById('analysisResultSection').style.display = 'block';
}

// 상세 분석 결과 표시 함수
function displayDetailedAnalysisResults(analysis) {
    const musicInfo = document.getElementById('detailedMusicInfo');
    const musicFeatures = document.getElementById('detailedMusicFeatures');
    const audioAnalysis = document.getElementById('detailedAudioAnalysis');
    const emotionAnalysis = document.getElementById('detailedEmotionAnalysis');
    const promptInfo = document.getElementById('detailedPromptInfo');
    
    const videoInfo = analysis.video_info || {};
    const musicAnalysis = analysis.music_analysis || {};
    
    // 음악 정보
    musicInfo.innerHTML = `
        <div class="analysis-item">
            <span class="analysis-label">제목:</span>
            <span class="analysis-value">${videoInfo.title || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">아티스트:</span>
            <span class="analysis-value">${musicAnalysis.artist || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">곡명:</span>
            <span class="analysis-value">${musicAnalysis.song || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">길이:</span>
            <span class="analysis-value">${videoInfo.duration_str || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">조회수:</span>
            <span class="analysis-value">${(videoInfo.view_count || 0).toLocaleString()}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">좋아요:</span>
            <span class="analysis-value">${(videoInfo.like_count || 0).toLocaleString()}</span>
        </div>
    `;
    
    // 음악 특성
    const genre = musicAnalysis.genre || {};
    const mood = musicAnalysis.mood || {};
    
    musicFeatures.innerHTML = `
        <div class="analysis-item">
            <span class="analysis-label">주 장르:</span>
            <span class="analysis-value">${genre.primary_genre || musicAnalysis.genre || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">예상 장르:</span>
            <span class="analysis-value">${genre.predicted_genres ? genre.predicted_genres.join(', ') : 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">주 분위기:</span>
            <span class="analysis-value">${mood.primary_mood || musicAnalysis.mood || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">예상 분위기:</span>
            <span class="analysis-value">${mood.predicted_moods ? mood.predicted_moods.join(', ') : 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">장르 신뢰도:</span>
            <span class="analysis-value">${genre.confidence ? Math.round(genre.confidence * 100) + '%' : 'N/A'}</span>
        </div>
    `;
    
    // 오디오 분석
    audioAnalysis.innerHTML = `
        <div class="analysis-item">
            <span class="analysis-label">예상 BPM:</span>
            <span class="analysis-value">${musicAnalysis.estimated_bpm || musicAnalysis.bpm || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">예상 키:</span>
            <span class="analysis-value">${musicAnalysis.estimated_key || musicAnalysis.key || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">에너지 레벨:</span>
            <span class="analysis-value">${musicAnalysis.energy_level || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">댄스 가능성:</span>
            <span class="analysis-value">${musicAnalysis.danceability || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">발랜스:</span>
            <span class="analysis-value">${musicAnalysis.valence || 'N/A'}</span>
        </div>
    `;
    
    // 감정 분석
    const sentiment = musicAnalysis.sentiment || {};
    emotionAnalysis.innerHTML = `
        <div class="analysis-item">
            <span class="analysis-label">전체 감정:</span>
            <span class="analysis-value">${sentiment.overall || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">긍정도:</span>
            <span class="analysis-value">${sentiment.positive ? Math.round(sentiment.positive * 100) + '%' : 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">부정도:</span>
            <span class="analysis-value">${sentiment.negative ? Math.round(sentiment.negative * 100) + '%' : 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">중성도:</span>
            <span class="analysis-value">${sentiment.neutral ? Math.round(sentiment.neutral * 100) + '%' : 'N/A'}</span>
        </div>
    `;
    
    // 프롬프트 정보
    const promptOptions = analysis.prompt_options || {};
    const selectedPrompt = analysis.selected_prompt || '';
    
    promptInfo.innerHTML = selectedPrompt || promptOptions.basic || '프롬프트 정보를 생성할 수 없습니다.';
}

// ============================================================================
// Music Trend Analyzer V2 Functions
// ============================================================================

// V2 트렌드 분석 시작
async function startTrendsV2Analysis() {
    const v2Mode = document.querySelector('input[name="v2Mode"]:checked').value;
    
    console.log(`[TrendsV2] V2 트렌드 분석 시작: ${v2Mode}`);
    
    try {
        let result;
        
        if (v2Mode === 'comprehensive') {
            result = await runComprehensiveAnalysis();
        } else {
            result = await runKeywordSearch();
        }
        
        return result;
    } catch (error) {
        console.error("[TrendsV2] 분석 오류:", error);
        throw error;
    }
}

// 종합 트렌드 분석 실행
async function runComprehensiveAnalysis() {
    console.log("[TrendsV2] 종합 트렌드 분석 실행");
    
    // 선택된 카테고리 수집
    const categories = Array.from(document.querySelectorAll('input[name="v2Categories"]:checked'))
        .map(cb => cb.value);
    
    // 선택된 데이터 소스 수집
    const sources = Array.from(document.querySelectorAll('input[name="v2Sources"]:checked'))
        .map(cb => cb.value);
    
    if (categories.length === 0) {
        throw new Error('분석할 카테고리를 하나 이상 선택해주세요.');
    }
    
    const requestData = {
        categories: categories,
        include_reddit: sources.includes('reddit'),
        include_spotify: sources.includes('spotify'),
        include_comments: sources.includes('comments')
    };
    
    console.log("[TrendsV2] 요청 데이터:", requestData);
    updateMarketProgress(20, "Reddit 및 Spotify 데이터 수집 중...");
    
    const response = await fetch('/api/trends/v2/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    });
    
    updateMarketProgress(80, "분석 결과 처리 중...");
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    updateMarketProgress(100, "분석 완료!");
    
    return result;
}

// 키워드 검색 분석 실행
async function runKeywordSearch() {
    console.log("[TrendsV2] 키워드 검색 분석 실행");
    
    const keyword = document.getElementById('v2SearchKeyword').value.trim();
    
    if (!keyword) {
        throw new Error('검색할 키워드를 입력해주세요.');
    }
    
    const requestData = {
        query: keyword,
        deep_analysis: true
    };
    
    console.log("[TrendsV2] 키워드 검색:", requestData);
    updateMarketProgress(30, `"${keyword}" 키워드 검색 중...`);
    
    const response = await fetch('/api/trends/v2/keywords', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    });
    
    updateMarketProgress(80, "검색 결과 처리 중...");
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    updateMarketProgress(100, "검색 완료!");
    
    return result;
}

// V2 키워드 설정 헬퍼 함수
function setV2Keyword(keyword) {
    document.getElementById('v2SearchKeyword').value = keyword;
    console.log(`[TrendsV2] 키워드 설정: ${keyword}`);
}

// V2 분석 모드 전환 처리
function handleV2ModeChange() {
    const mode = document.querySelector('input[name="v2Mode"]:checked').value;
    const comprehensiveOptions = document.getElementById('v2ComprehensiveOptions');
    const keywordOptions = document.getElementById('v2KeywordOptions');
    
    if (mode === 'comprehensive') {
        comprehensiveOptions.style.display = 'block';
        keywordOptions.style.display = 'none';
    } else {
        comprehensiveOptions.style.display = 'none';
        keywordOptions.style.display = 'block';
    }
    
    console.log(`[TrendsV2] 모드 전환: ${mode}`);
}

// 시장 분석 결과 표시 함수 확장 (V2 결과 처리)
function displayTrendsV2Result(result, analysisType) {
    const resultDiv = document.getElementById('marketResult');
    
    if (analysisType === 'trends_v2') {
        const v2Mode = document.querySelector('input[name="v2Mode"]:checked').value;
        
        if (v2Mode === 'comprehensive') {
            displayComprehensiveResult(result, resultDiv);
        } else {
            displayKeywordSearchResult(result, resultDiv);
        }
    }
}

// 종합 분석 결과 표시 (새로운 차트 기반)
function displayComprehensiveResult(result, container) {
    const trendInsights = result.trend_insights || {};
    const recommendations = result.recommendations || [];
    const dataSources = result.data_sources || [];
    const chartTracks = result.chart_tracks || [];
    const representativeOpinions = result.representative_opinions || [];
    const representativeComments = result.representative_comments || [];
    
    const html = `
        <div class="v2-result-container">
            <div class="v2-header">
                <h4>🔥 Spotify 차트 기반 트렌드 분석 결과</h4>
                <p class="analysis-time">분석 시간: ${new Date(result.analysis_timestamp).toLocaleString()}</p>
            </div>
            
            <div class="v2-summary">
                <div class="summary-card">
                    <h5>📊 분석 개요</h5>
                    <p><strong>분석된 데이터 소스:</strong> ${dataSources.join(', ')}</p>
                    <p><strong>분석된 차트 곡 수:</strong> ${chartTracks.length}개</p>
                    <p><strong>전체 트렌드 점수:</strong> ${(trendInsights.overall_trend_score || 0).toFixed(1)}</p>
                    <p><strong>트렌드 방향:</strong> ${getTrendDirectionText(trendInsights.trend_direction)}</p>
                    <p><strong>신뢰도:</strong> ${((trendInsights.confidence_level || 0) * 100).toFixed(1)}%</p>
                </div>
            </div>
            
            ${chartTracks.length > 0 ? `
                <div class="v2-chart-tracks">
                    <h5>🎵 현재 차트 상위 곡들</h5>
                    <div class="chart-tracks-list">
                        ${chartTracks.slice(0, 10).map((track, index) => `
                            <div class="track-card">
                                <div class="track-rank">#${index + 1}</div>
                                <div class="track-info">
                                    <div class="track-title">${track.name}</div>
                                    <div class="track-artist">${track.main_artist}</div>
                                    <div class="track-details">
                                        <span class="popularity">인기도: ${track.popularity}</span>
                                        <span class="chart-region">${track.chart_region === 'korea' ? '🇰🇷 한국' : '🌍 글로벌'}</span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${representativeOpinions.length > 0 ? `
                <div class="v2-reddit-opinions">
                    <h5>💬 Reddit 커뮤니티 대표 의견</h5>
                    ${representativeOpinions.map(trackOpinion => `
                        <div class="opinion-card">
                            <h6>🎵 ${trackOpinion.track_title} - ${trackOpinion.artist}</h6>
                            <div class="opinions-list">
                                ${trackOpinion.opinions.map(opinion => `
                                    <div class="opinion-item">
                                        <div class="opinion-header">
                                            <strong>${opinion.title}</strong>
                                            <span class="opinion-meta">
                                                👍 ${opinion.score} | 💬 ${opinion.comments_count} | 📍 r/${opinion.subreddit}
                                            </span>
                                        </div>
                                        ${opinion.content ? `<div class="opinion-content">${opinion.content}</div>` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            ${representativeComments.length > 0 ? `
                <div class="v2-youtube-comments">
                    <h5>🎬 YouTube 대표 댓글</h5>
                    ${representativeComments.map(trackComment => `
                        <div class="comment-card">
                            <h6>🎵 ${trackComment.track_title} - ${trackComment.artist}</h6>
                            <div class="comments-list">
                                ${trackComment.comments.map(comment => `
                                    <div class="comment-item">
                                        <div class="comment-header">
                                            <strong>@${comment.author}</strong>
                                            <span class="comment-meta">
                                                👍 ${comment.likes} | ${comment.timestamp}
                                            </span>
                                        </div>
                                        <div class="comment-text">${comment.text}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            ${trendInsights.category_scores ? `
                <div class="v2-categories">
                    <h5>🎵 장르별 트렌드 점수</h5>
                    <div class="category-scores">
                        ${Object.entries(trendInsights.category_scores)
                            .sort(([,a], [,b]) => b - a)
                            .map(([category, score]) => `
                                <div class="category-item">
                                    <span class="category-name">${category.toUpperCase()}</span>
                                    <div class="score-bar">
                                        <div class="score-fill" style="width: ${Math.min(score, 100)}%"></div>
                                        <span class="score-text">${score.toFixed(1)}</span>
                                    </div>
                                </div>
                            `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${recommendations.length > 0 ? `
                <div class="v2-recommendations">
                    <h5>💡 추천사항</h5>
                    <ul class="recommendation-list">
                        ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
    
    container.innerHTML = html;
}

// 키워드 검색 결과 표시
function displayKeywordSearchResult(result, container) {
    const spotifyResults = result.spotify_results || {};
    const sourcesAnalyzed = result.sources_analyzed || [];
    
    const html = `
        <div class="v2-result-container">
            <div class="v2-header">
                <h4>🔍 키워드 트렌드 검색 결과</h4>
                <p class="search-query">검색어: <strong>"${result.query}"</strong></p>
                <p class="analysis-time">검색 시간: ${new Date(result.analysis_timestamp).toLocaleString()}</p>
            </div>
            
            <div class="v2-summary">
                <div class="summary-card">
                    <h5>📊 검색 개요</h5>
                    <p><strong>분석된 소스:</strong> ${sourcesAnalyzed.join(', ')}</p>
                    <p><strong>총 결과 수:</strong> ${spotifyResults.total_results || 0}개</p>
                    <p><strong>평균 인기도:</strong> ${(spotifyResults.average_popularity || 0).toFixed(1)}</p>
                    <p><strong>트렌드 점수:</strong> ${(spotifyResults.trend_score || 0).toFixed(1)}</p>
                </div>
            </div>
            
            ${spotifyResults.results && spotifyResults.results.length > 0 ? `
                <div class="v2-spotify-results">
                    <h5>🎧 Spotify 검색 결과 (상위 10개)</h5>
                    <div class="spotify-tracks">
                        ${spotifyResults.results.slice(0, 10).map(track => `
                            <div class="track-card">
                                <div class="track-info">
                                    <div class="track-title">${track.name}</div>
                                    <div class="track-artist">${track.artist}</div>
                                    <div class="track-details">
                                        <span class="popularity">인기도: ${track.popularity}</span>
                                        <span class="release-date">발매: ${track.release_date}</span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${result.trend_analysis ? `
                <div class="v2-trend-analysis">
                    <h5>📈 트렌드 분석</h5>
                    <p><strong>성장 잠재력:</strong> ${getTrendPotentialText(result.trend_analysis.growth_potential)}</p>
                    <p><strong>시장 침투도:</strong> ${getMarketPenetrationText(result.trend_analysis.market_penetration)}</p>
                    <p><strong>종합 점수:</strong> ${(result.trend_analysis.trend_score || 0).toFixed(1)}</p>
                </div>
            ` : ''}
        </div>
    `;
    
    container.innerHTML = html;
}

// 헬퍼 함수들
function getTrendDirectionText(direction) {
    const directions = {
        'rising': '🔥 상승세',
        'stable': '📊 안정적',
        'declining': '📉 하락세'
    };
    return directions[direction] || direction;
}

function getTrendPotentialText(potential) {
    const potentials = {
        'high': '🚀 높음',
        'medium': '📈 보통',
        'low': '📉 낮음'
    };
    return potentials[potential] || potential;
}

function getMarketPenetrationText(penetration) {
    const penetrations = {
        'mainstream': '🌟 메인스트림',
        'emerging': '🌱 새로운 트렌드',
        'niche': '🎯 틈새시장',
        'underground': '🔍 언더그라운드'
    };
    return penetrations[penetration] || penetration;
}

// 직접 V2 분석 시작 함수 (버튼에서 호출)
async function startTrendsV2AnalysisDirect() {
    console.log("[TrendsV2] 직접 V2 분석 시작");
    
    showMarketProgress();
    
    try {
        const result = await startTrendsV2Analysis();
        
        if (result.success) {
            displayTrendsV2Result(result, 'trends_v2');
            document.getElementById('marketResultSection').style.display = 'block';
        } else {
            alert('분석 실패: ' + result.error);
        }
    } catch (error) {
        console.error("[TrendsV2] 분석 오류:", error);
        alert('분석 중 오류가 발생했습니다: ' + error.message);
    }
    
    hideMarketProgress();
}

// 추출된 파일 MP3 다운로드 (팝업 없음)
async function downloadExtractedFileMp3(btn) {
    const fileItem = btn.closest('.file-item');
    const filename = fileItem.dataset.filename;
    
    console.log("[Download] MP3 다운로드:", filename);
    
    try {
        // MP3로 변환하여 다운로드
        const downloadUrl = `/download/${encodeURIComponent(filename)}?mp3=true`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log("[Download] MP3 다운로드 시작:", filename);
        
    } catch (error) {
        console.error("[Download] MP3 다운로드 오류:", error);
        alert('MP3 다운로드 중 오류가 발생했습니다: ' + error.message);
    }
}

// 추출된 파일 원본 다운로드
async function downloadExtractedFileOriginal(btn) {
    const fileItem = btn.closest('.file-item');
    const filename = fileItem.dataset.filename;
    
    console.log("[Download] 원본 다운로드:", filename);
    
    try {
        // 원본 형식으로 다운로드
        const downloadUrl = `/download/${encodeURIComponent(filename)}?mp3=false`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log("[Download] 원본 다운로드 시작:", filename);
        
    } catch (error) {
        console.error("[Download] 원본 다운로드 오류:", error);
        alert('원본 다운로드 중 오류가 발생했습니다: ' + error.message);
    }
}

// 기존 함수는 호환성을 위해 유지 (기본값: MP3 다운로드)
async function downloadExtractedFile(btn) {
    return downloadExtractedFileMp3(btn);
}

// 추출된 파일 30초 자르기 (바로 다운로드)
async function trimExtractedFile(btn) {
    const fileItem = btn.closest('.file-item');
    const filename = fileItem.dataset.filename;
    
    console.log("[Trim] 30초 자르기 및 다운로드:", filename);
    
    if (!confirm('이 파일을 30초로 잘라서 바로 다운로드하시겠습니까?')) {
        return;
    }
    
    btn.disabled = true;
    btn.textContent = '⏳';
    
    try {
        const response = await fetch('/trim-audio-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename: filename })
        });
        
        if (response.ok) {
            // Content-Type 확인
            const contentType = response.headers.get('content-type');
            console.log("[Trim] 응답 Content-Type:", contentType);
            
            // 오디오 파일이나 바이너리 파일인 경우 (MP3 다운로드)
            if (contentType && (
                contentType.includes('audio/') || 
                contentType.includes('application/octet-stream') ||
                contentType.includes('attachment')
            )) {
                // 파일 다운로드
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                
                // 30초 파일명 생성
                const baseName = filename.replace(/\.(mp4|webm|m4a|mp3)$/i, '');
                const downloadFilename = `${baseName}_30s.mp3`;
                
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = downloadFilename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // URL 해제
                window.URL.revokeObjectURL(downloadUrl);
                
                console.log("[Trim] 30초 파일 다운로드 완료:", downloadFilename);
                alert('30초 파일이 성공적으로 다운로드되었습니다!');
                
            } else if (contentType && contentType.includes('application/json')) {
                // JSON 응답인 경우 (오류 처리)
                try {
                    const result = await response.json();
                    
                    if (result.success && result.download_url) {
                        // 다운로드 URL이 제공된 경우
                        const link = document.createElement('a');
                        link.href = result.download_url;
                        link.download = result.filename || `${filename}_30s.mp3`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        
                        console.log("[Trim] 30초 파일 다운로드 완료:", result.filename);
                        alert('30초 파일이 성공적으로 다운로드되었습니다!');
                    } else {
                        throw new Error(result.error || '30초 자르기 처리 실패');
                    }
                } catch (jsonError) {
                    console.error("[Trim] JSON 파싱 오류:", jsonError);
                    throw new Error('서버 응답 처리 중 오류가 발생했습니다');
                }
            } else {
                // Content-Type을 알 수 없는 경우 바이너리로 처리
                console.log("[Trim] 알 수 없는 Content-Type, 바이너리로 처리");
                const blob = await response.blob();
                
                // blob 크기 확인
                if (blob.size === 0) {
                    throw new Error('서버에서 빈 파일이 전송되었습니다');
                }
                
                const downloadUrl = window.URL.createObjectURL(blob);
                
                // 30초 파일명 생성
                const baseName = filename.replace(/\.(mp4|webm|m4a|mp3)$/i, '');
                const downloadFilename = `${baseName}_30s.mp3`;
                
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = downloadFilename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // URL 해제
                window.URL.revokeObjectURL(downloadUrl);
                
                console.log("[Trim] 30초 파일 다운로드 완료:", downloadFilename);
                alert('30초 파일이 성공적으로 다운로드되었습니다!');
            }
        } else {
            // 응답이 실패인 경우
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                try {
                    const errorResult = await response.json();
                    throw new Error(errorResult.error || '서버 오류 발생');
                } catch (jsonError) {
                    throw new Error(`서버 오류 (${response.status}): 응답 처리 실패`);
                }
            } else {
                throw new Error(`서버 오류 (${response.status}): ${response.statusText}`);
            }
        }
        
    } catch (error) {
        console.error("[Trim] 30초 자르기 오류:", error);
        alert('30초 자르기 중 오류가 발생했습니다: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '✂️';
    }
}

// 키 조절 UI 표시
function showPitchAdjust(btn) {
    const fileItem = btn.closest('.file-item');
    const pitchSection = fileItem.querySelector('.pitch-adjust-section');
    
    // 토글
    const isVisible = pitchSection.style.display !== 'none';
    pitchSection.style.display = isVisible ? 'none' : 'block';
    
    // 키 조절 슬라이더 이벤트 등록 (처음에만)
    if (!isVisible) {
        const pitchSlider = pitchSection.querySelector('.pitch-slider');
        const pitchValue = pitchSection.querySelector('.pitch-value');
        
        pitchSlider.addEventListener('input', function() {
            const value = parseInt(this.value);
            let displayValue = value > 0 ? `+${value}` : `${value}`;
            pitchValue.textContent = displayValue;
            
            // 값에 따른 색상 변경
            if (value > 0) {
                pitchValue.style.background = '#e8f5e8';
                pitchValue.style.color = '#2e7d32';
            } else if (value < 0) {
                pitchValue.style.background = '#ffeaa7';
                pitchValue.style.color = '#d35400';
            } else {
                pitchValue.style.background = 'var(--primary-light)';
                pitchValue.style.color = 'var(--primary-color)';
            }
        });
    }
}

// 키 조절 적용
async function applyPitchAdjust(btn) {
    const fileItem = btn.closest('.file-item');
    const filename = fileItem.dataset.filename;
    const pitchSlider = fileItem.querySelector('.pitch-slider');
    const semitones = parseInt(pitchSlider.value);
    
    console.log("[Pitch] 키 조절 적용:", filename, semitones);
    
    if (semitones === 0) {
        alert('키 조절이 필요하지 않습니다.');
        return;
    }
    
    if (!confirm(`이 파일의 키를 ${semitones > 0 ? '+' : ''}${semitones} 반음 조절하시겠습니까? 원본 파일은 유지됩니다.`)) {
        return;
    }
    
    btn.disabled = true;
    btn.textContent = '⏳';
    
    try {
        const response = await fetch('/adjust-pitch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                filename: filename,
                semitones: semitones
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 진행 상황 모니터링
            document.getElementById('progressSection').style.display = 'block';
            updateProgress(0, `키 조절 중... (${semitones > 0 ? '+' : ''}${semitones} 반음)`);
            monitorPitchProgress(result.job_id);
        } else {
            throw new Error(result.error);
        }
        
    } catch (error) {
        console.error("[Pitch] 키 조절 오류:", error);
        alert('키 조절 중 오류가 발생했습니다: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '적용';
    }
}

// 30초 자르기 진행 상황 모니터링
async function monitorTrimProgress(jobId) {
    console.log("[Trim Monitor] 진행 상황 모니터링 시작:", jobId);
    
    const checkProgress = async () => {
        try {
            const response = await fetch(`/status/${jobId}`);
            const status = await response.json();
            
            console.log("[Trim Monitor] 진행 상황:", status);
            
            if (status.status === 'completed') {
                updateProgress(100, '30초 자르기 완료!');
                
                // 새 파일을 리스트에 추가
                if (status.result && status.result.new_filename) {
                    // 새 파일 정보 생성 (기존 파일 기준)
                    const originalFile = uploadedFiles.find(f => f.filename === status.result.original_filename);
                    if (originalFile) {
                        const newFile = {
                            ...originalFile,
                            filename: status.result.new_filename,
                            original_name: originalFile.original_name + ' (30초)',
                            duration: 30,
                            duration_str: '00:30',
                            source: 'link_extract'
                        };
                        
                        addFileToList(newFile);
                        updateTotalInfo();
                    }
                }
                
                setTimeout(() => {
                    document.getElementById('progressSection').style.display = 'none';
                }, 2000);
                
            } else if (status.status === 'error') {
                throw new Error(status.message || '30초 자르기 중 오류 발생');
                
            } else {
                updateProgress(status.progress || 0, status.message || '처리 중...');
                setTimeout(checkProgress, 1000);
            }
            
        } catch (error) {
            console.error("[Trim Monitor] 오류:", error);
            updateProgress(0, `오류: ${error.message}`);
            setTimeout(() => {
                document.getElementById('progressSection').style.display = 'none';
            }, 3000);
        }
    };
    
    checkProgress();
}

// 키 조절 진행 상황 모니터링
async function monitorPitchProgress(jobId) {
    console.log("[Pitch Monitor] 진행 상황 모니터링 시작:", jobId);
    
    const checkProgress = async () => {
        try {
            const response = await fetch(`/status/${jobId}`);
            const status = await response.json();
            
            console.log("[Pitch Monitor] 진행 상황:", status);
            
            if (status.status === 'completed') {
                const semitones = status.result?.semitones || 0;
                updateProgress(100, `키 조절 완료! (${semitones > 0 ? '+' : ''}${semitones} 반음)`);
                
                // 새 파일을 리스트에 추가
                if (status.result && status.result.new_filename) {
                    // 새 파일 정보 생성 (기존 파일 기준)
                    const originalFile = uploadedFiles.find(f => f.filename === status.result.original_filename);
                    if (originalFile) {
                        const pitchStr = semitones > 0 ? `+${semitones}` : `${semitones}`;
                        const newFile = {
                            ...originalFile,
                            filename: status.result.new_filename,
                            original_name: originalFile.original_name + ` (${pitchStr} 반음)`,
                            source: 'link_extract'
                        };
                        
                        addFileToList(newFile);
                        updateTotalInfo();
                    }
                }
                
                setTimeout(() => {
                    document.getElementById('progressSection').style.display = 'none';
                }, 2000);
                
            } else if (status.status === 'error') {
                throw new Error(status.message || '키 조절 중 오류 발생');
                
            } else {
                updateProgress(status.progress || 0, status.message || '처리 중...');
                setTimeout(checkProgress, 1000);
            }
            
        } catch (error) {
            console.error("[Pitch Monitor] 오류:", error);
            updateProgress(0, `오류: ${error.message}`);
            setTimeout(() => {
                document.getElementById('progressSection').style.display = 'none';
            }, 3000);
        }
    };
    
    checkProgress();
}

// 키 조절 슬라이더 설정 (기존 함수 - 사용 안함)
function setupPitchSlider() {
    // 이제 파일별로 개별적으로 처리하므로 빈 함수
}

// 모든 파일 보기
async function showAllFiles() {
    console.log("[Files] 모든 파일 보기 요청");
    
    try {
        const response = await fetch('/files/list');
        const result = await response.json();
        
        if (result.success) {
            const files = result.files;
            console.log(`[Files] ${files.length}개 파일 발견`);
            
            // 모달 창으로 파일 목록 표시
            const modal = document.createElement('div');
            modal.className = 'file-list-modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>📂 저장된 파일 목록 (${files.length}개)</h3>
                        <button class="close-btn" onclick="this.closest('.file-list-modal').remove()">✕</button>
                    </div>
                    <div class="modal-body">
                        <div class="files-grid">
                            ${files.map(file => `
                                <div class="file-card ${file.is_extracted ? 'extracted-file' : ''}">
                                    <div class="file-info">
                                        <div class="file-name" title="${file.filename}">${file.filename}</div>
                                        <div class="file-meta">
                                            <span>${file.size_mb} MB</span>
                                            <span>•</span>
                                            <span>${file.modified}</span>
                                            ${file.is_extracted ? '<span>• 🔗 추출</span>' : ''}
                                        </div>
                                    </div>
                                    <div class="file-actions">
                                        <button class="btn-small" onclick="downloadFileByName('${file.filename}')" title="다운로드">💾</button>
                                        <button class="btn-small btn-danger" onclick="deleteFile('${file.filename}')" title="삭제">🗑️</button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // 모달 외부 클릭 시 닫기
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
            
        } else {
            throw new Error(result.error || '파일 목록을 가져올 수 없습니다');
        }
        
    } catch (error) {
        console.error("[Files] 파일 목록 오류:", error);
        alert('파일 목록을 가져오는 중 오류가 발생했습니다: ' + error.message);
    }
}

// 파일명으로 다운로드
function downloadFileByName(filename) {
    console.log("[Download] 파일 다운로드:", filename);
    
    const downloadUrl = `/download/${encodeURIComponent(filename)}?mp3=false`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 파일 삭제 (미구현)
function deleteFile(filename) {
    alert('파일 삭제 기능은 아직 구현되지 않았습니다.');
}

// 전역 함수로 노출
window.showTab = showTab;
window.startMarketAnalysis = startMarketAnalysis;
window.startTrendsV2Analysis = startTrendsV2AnalysisDirect;
window.resetMarketAnalysis = resetMarketAnalysis;
window.analyzeMusic = analyzeMusic;
window.setV2Keyword = setV2Keyword;
window.handleV2ModeChange = handleV2ModeChange;
window.extractFromLink = extractFromLink;
window.downloadExtractedFile = downloadExtractedFile;
window.downloadExtractedFileMp3 = downloadExtractedFileMp3;
window.downloadExtractedFileOriginal = downloadExtractedFileOriginal;
window.trimExtractedFile = trimExtractedFile;
window.showPitchAdjust = showPitchAdjust;
window.applyPitchAdjust = applyPitchAdjust;
window.showAllFiles = showAllFiles;
window.downloadFileByName = downloadFileByName;
window.deleteFile = deleteFile;

console.log("[Music Merger] 모든 함수 정의 완료 (V2 포함)");
