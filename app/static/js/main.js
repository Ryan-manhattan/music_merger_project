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
    
    // 로고 합성 옵션 변경 이벤트
    const applyLogoOption = document.getElementById('applyLogoOption');
    if (applyLogoOption) {
        applyLogoOption.addEventListener('change', handleLogoOptionChange);
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

// 로고 옵션 변경 처리
function handleLogoOptionChange() {
    console.log("[LogoOption] 로고 합성 옵션 변경됨");
    
    // 이미지가 이미 업로드된 상태라면 다시 업로드
    const imageUpload = document.getElementById('imageUpload');
    if (imageUpload && imageUpload.files && imageUpload.files[0]) {
        const file = imageUpload.files[0];
        console.log("[LogoOption] 이미지 재처리:", file.name);
        uploadImage(file);
    }
}

// 이미지 업로드
async function uploadImage(file) {
    console.log("[ImageUpload] 이미지 업로드 시작:", file.name);
    
    const formData = new FormData();
    formData.append('image', file);
    
    // 로고 합성 옵션 확인
    const applyLogoOption = document.getElementById('applyLogoOption');
    if (applyLogoOption && applyLogoOption.checked) {
        formData.append('apply_logo', 'on');
        console.log("[ImageUpload] 로고 합성 옵션 적용");
    }
    
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
        preset: document.getElementById('videoPreset').value,
        options: {
            apply_logo: document.getElementById('applyLogoOption').checked
        }
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
    let lastProgress = 0;
    let lastLogTime = 0;
    
    const checkStatus = async () => {
        try {
            const response = await fetch(`/process/status/${jobId}`);
            const status = await response.json();
            
            // 진행률이 변경되었거나 5초마다 한 번씩 로그 출력
            const currentTime = Date.now();
            const shouldLog = (currentTime - lastLogTime > 5000) ||
                            (status.progress && status.progress !== lastProgress);
            
            if (shouldLog) {
                console.log(`[VideoMonitor] 진행 상황: ${status.progress || 0}% - ${status.message || '처리 중'}`);
                lastLogTime = currentTime;
                lastProgress = status.progress || 0;
            }
            
            // 부드러운 진행률 업데이트
            if (progressFill) {
                progressFill.style.transition = 'width 0.3s ease';
                progressFill.style.width = `${Math.min(status.progress || 0, 100)}%`;
                
                // 진행률에 따른 색상 변경
                const progress = status.progress || 0;
                if (progress < 30) {
                    progressFill.style.background = '#ff7043';  // 주황색
                } else if (progress < 70) {
                    progressFill.style.background = '#ffa726';  // 노란색
                } else if (progress < 95) {
                    progressFill.style.background = '#66bb6a';  // 연두색
                } else {
                    progressFill.style.background = '#4CAF50';  // 녹색
                }
            }
            
            // 상세한 메시지 표시
            if (progressText) {
                const displayText = status.progress > 0 ? 
                    `${status.progress}% - ${status.message || '처리 중'}` : 
                    (status.message || '처리 중');
                
                // 메시지에 따른 아이콘 추가
                let icon = '';
                const message = status.message || '';
                if (message.includes('준비')) icon = '⚙️';
                else if (message.includes('로딩') || message.includes('처리')) icon = '🔄';
                else if (message.includes('생성')) icon = '🎬';
                else if (message.includes('완료')) icon = '✅';
                else if (message.includes('결합')) icon = '🔗';
                
                progressText.textContent = icon ? `${icon} ${displayText}` : displayText;
            }
            
            if (status.status === 'completed') {
                // 동영상 생성 완료
                console.log("[VideoMonitor] 동영상 생성 완료:", status.result);
                showVideoResult(status.result.video_info);
            } else if (status.status === 'error') {
                // 오류 발생
                throw new Error(status.message || '동영상 생성 중 오류 발생');
            } else {
                // 계속 모니터링 - 더 빠른 간격
                setTimeout(checkStatus, 500); // 500ms로 단축
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
