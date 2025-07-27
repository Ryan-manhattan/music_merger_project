// Music Video Creator - JavaScript (Unified Version)
console.log("[Music Video] 통합 버전 JavaScript 로드 완료");

// 전역 변수
let uploadedAudio = null;
let selectedImage = null;
let currentJobs = {};
let activeImageTab = 'upload';

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log("[Music Video] DOM 로드 완료, 이벤트 리스너 설정");
    setupEventListeners();
    updateGenerateButton();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 음원 파일 업로드
    const audioFileInput = document.getElementById('audioFileInput');
    const audioUploadArea = document.getElementById('audioUploadArea');
    
    if (audioFileInput) {
        audioFileInput.addEventListener('change', handleAudioFileSelect);
    }
    
    if (audioUploadArea) {
        audioUploadArea.addEventListener('click', () => audioFileInput.click());
        audioUploadArea.addEventListener('dragover', handleDragOver);
        audioUploadArea.addEventListener('dragleave', handleDragLeave);
        audioUploadArea.addEventListener('drop', handleAudioDrop);
    }
    
    // 이미지 파일 업로드
    const imageFileInput = document.getElementById('imageFileInput');
    const imageUploadArea = document.getElementById('imageUploadArea');
    
    if (imageFileInput) {
        imageFileInput.addEventListener('change', handleImageFileSelect);
    }
    
    if (imageUploadArea) {
        imageUploadArea.addEventListener('click', () => imageFileInput.click());
        imageUploadArea.addEventListener('dragover', handleDragOver);
        imageUploadArea.addEventListener('dragleave', handleDragLeave);
        imageUploadArea.addEventListener('drop', handleImageDrop);
    }
    
    // 로고 합성 옵션 변경
    const applyLogoCheckbox = document.getElementById('applyLogoCheckbox');
    if (applyLogoCheckbox) {
        applyLogoCheckbox.addEventListener('change', handleLogoOptionChange);
    }
    
    console.log("[Music Video] 모든 이벤트 리스너 설정 완료");
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

// ===========================================
// 탭 관리 함수들
// ===========================================

// 이미지 탭 전환
function switchImageTab(tabName) {
    console.log(`[Music Video] 이미지 탭 전환: ${tabName}`);
    
    activeImageTab = tabName;
    
    // 탭 버튼 상태 업데이트
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 활성 탭 표시
    const activeTabBtn = document.querySelector(`.tab-btn[onclick="switchImageTab('${tabName}')"]`);
    const activeTabContent = document.getElementById(tabName === 'upload' ? 'uploadTab' : 'aiTab');
    
    if (activeTabBtn) activeTabBtn.classList.add('active');
    if (activeTabContent) activeTabContent.classList.add('active');
    
    // 이미지 선택 초기화
    if (selectedImage) {
        selectedImage = null;
        hideImagePreview();
        updateSummary();
        updateGenerateButton();
    }
}

// 로고 옵션 변경 처리
function handleLogoOptionChange() {
    console.log("[Music Video] 로고 합성 옵션 변경됨");
    
    // 이미지가 선택된 상태라면 재처리
    if (selectedImage && selectedImage.file) {
        console.log("[Music Video] 이미지 재처리 시작");
        processImageFile(selectedImage.file);
    }
}

// 이미지 처리 중 로딩 표시
function showImageProcessing() {
    const imagePreview = document.getElementById('imagePreview');
    if (imagePreview) {
        imagePreview.innerHTML = '<div class="processing-indicator"><div class="spinner"></div><p>이미지 처리 중...</p></div>';
        imagePreview.style.display = 'block';
    }
}

function hideImageProcessing() {
    // 처리 완료 후 displayImagePreview가 호출되므로 별도 처리 불필요
}

// ===========================================
// 음원 업로드 관련 함수들
// ===========================================

// 음원 파일 선택 처리
function handleAudioFileSelect(e) {
    console.log("[Music Video] 음원 파일 선택됨");
    const file = e.target.files[0];
    if (file) {
        processAudioFile(file);
    }
}

// 음원 드롭 처리
function handleAudioDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    
    console.log("[Music Video] 음원 파일 드롭됨");
    const files = Array.from(e.dataTransfer.files);
    const audioFile = files.find(file => 
        file.type.startsWith('audio/') || 
        /\.(mp3|wav|m4a|flac)$/i.test(file.name)
    );
    
    if (audioFile) {
        processAudioFile(audioFile);
    } else {
        alert('지원하는 음원 파일을 업로드해주세요 (MP3, WAV, M4A, FLAC)');
    }
}

// 음원 파일 처리
function processAudioFile(file) {
    console.log(`[Music Video] 음원 파일 처리: ${file.name}`);
    
    // 파일 정보 생성
    const fileInfo = {
        file: file,
        original_name: file.name,
        size_mb: (file.size / (1024 * 1024)).toFixed(2),
        format: file.name.split('.').pop().toUpperCase()
    };
    
    uploadedAudio = fileInfo;
    displayAudioInfo(fileInfo);
    updateSummary();
    updateGenerateButton();
}

// 음원 정보 표시
function displayAudioInfo(fileInfo) {
    console.log("[Music Video] 음원 정보 표시:", fileInfo);
    
    const audioInfo = document.getElementById('audioInfo');
    const audioFileName = document.getElementById('audioFileName');
    const audioFileDetails = document.getElementById('audioFileDetails');
    
    if (audioFileName) {
        audioFileName.textContent = fileInfo.original_name;
    }
    
    if (audioFileDetails) {
        audioFileDetails.textContent = `${fileInfo.format} · ${fileInfo.size_mb}MB`;
    }
    
    if (audioInfo) {
        audioInfo.style.display = 'block';
    }
}

// 다른 음원 파일 선택
function changeAudioFile() {
    const audioFileInput = document.getElementById('audioFileInput');
    if (audioFileInput) {
        audioFileInput.value = '';
        audioFileInput.click();
    }
}

// ===========================================
// 이미지 업로드 관련 함수들
// ===========================================

// 이미지 파일 선택 처리
function handleImageFileSelect(e) {
    console.log("[Music Video] 이미지 파일 선택됨");
    const file = e.target.files[0];
    if (file) {
        processImageFile(file);
    }
}

// 이미지 드롭 처리
function handleImageDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    
    console.log("[Music Video] 이미지 파일 드롭됨");
    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find(file => 
        file.type.startsWith('image/') || 
        /\.(jpg|jpeg|png|bmp|gif)$/i.test(file.name)
    );
    
    if (imageFile) {
        processImageFile(imageFile);
    } else {
        alert('지원하는 이미지 파일을 업로드해주세요 (JPG, PNG, BMP, GIF)');
    }
}

// 이미지 파일 처리
async function processImageFile(file) {
    console.log(`[Music Video] 이미지 파일 처리: ${file.name}`);
    
    // 로딩 상태 표시
    showImageProcessing();
    
    try {
        // 현재 로고 합성 옵션 확인
        const applyLogo = document.getElementById('applyLogoCheckbox').checked;
        
        // 새로운 이미지 처리 API 호출
        const formData = new FormData();
        formData.append('image', file);
        formData.append('apply_logo', applyLogo ? 'true' : 'false');
        
        const response = await fetch('/api/music-video/process-image', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        console.log("[Music Video] 이미지 처리 응답:", data);
        
        if (data.success) {
            const fileInfo = {
                file: file,
                original_name: data.file_info.original_name,
                size_mb: data.file_info.size_mb,
                filename: data.file_info.filename,
                preview_url: data.file_info.preview_url,
                apply_logo: data.file_info.apply_logo
            };
            
            selectedImage = fileInfo;
            displayImagePreview(fileInfo);
            updateSummary();
            updateGenerateButton();
        } else {
            alert('이미지 처리 실패: ' + data.error);
        }
    } catch (error) {
        console.error("[Music Video] 이미지 처리 오류:", error);
        alert('이미지 처리 중 오류가 발생했습니다.');
    } finally {
        hideImageProcessing();
    }
}

// AI 이미지 생성
async function generateAIImage() {
    const prompt = document.getElementById('imagePrompt').value.trim();
    const style = document.getElementById('imageStyle').value;
    const size = document.getElementById('imageSize').value;
    
    if (!prompt) {
        alert('이미지 설명을 입력해주세요.');
        return;
    }
    
    console.log(`[Music Video] AI 이미지 생성 시작: ${prompt} (스타일: ${style}, 크기: ${size})`);
    
    // 임시로 AI 생성 이미지 처리 (실제 API 연동 필요)
    alert('AI 이미지 생성 기능은 현재 개발 중입니다. 직접 업로드를 사용해주세요.');
}

// 이미지 미리보기 표시
function displayImagePreview(fileInfo) {
    console.log("[Music Video] 이미지 미리보기 표시:", fileInfo);
    
    const imagePreview = document.getElementById('imagePreview');
    const previewImage = document.getElementById('previewImage');
    const imageDetails = document.getElementById('imageDetails');
    
    if (previewImage) {
        previewImage.src = fileInfo.preview_url || `/download/${fileInfo.filename}`;
        previewImage.alt = fileInfo.original_name;
    }
    
    if (imageDetails) {
        let details = `${fileInfo.original_name} · ${fileInfo.size_mb}MB`;
        if (fileInfo.apply_logo) {
            details += ' · 로고 합성 적용';
        }
        imageDetails.textContent = details;
    }
    
    if (imagePreview) {
        // 처리 중 표시를 실제 미리보기로 교체
        imagePreview.innerHTML = `
            <img id="previewImage" src="${fileInfo.preview_url}" alt="${fileInfo.original_name}">
            <p id="imageDetails">${imageDetails ? imageDetails.textContent : ''}</p>
            <button class="btn btn-outline btn-small" onclick="changeImage()">변경</button>
        `;
        imagePreview.style.display = 'block';
    }
}

// 이미지 미리보기 숨기기
function hideImagePreview() {
    const imagePreview = document.getElementById('imagePreview');
    if (imagePreview) {
        imagePreview.style.display = 'none';
    }
}

// 다른 이미지 선택
function changeImage() {
    selectedImage = null;
    hideImagePreview();
    
    // 이미지 입력 필드 초기화
    const imageFileInput = document.getElementById('imageFileInput');
    if (imageFileInput) {
        imageFileInput.value = '';
    }
    
    const imagePrompt = document.getElementById('imagePrompt');
    if (imagePrompt) {
        imagePrompt.value = '';
    }
    
    updateSummary();
    updateGenerateButton();
}

// ===========================================
// 영상 생성 관련 함수들
// ===========================================

// 요약 정보 업데이트
function updateSummary() {
    const summaryAudio = document.getElementById('summaryAudio');
    const summaryImage = document.getElementById('summaryImage');
    
    if (summaryAudio) {
        summaryAudio.textContent = uploadedAudio ? uploadedAudio.original_name : '선택되지 않음';
    }
    
    if (summaryImage) {
        summaryImage.textContent = selectedImage ? selectedImage.original_name : '선택되지 않음';
    }
}

// 생성 버튼 상태 업데이트
function updateGenerateButton() {
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        const canGenerate = uploadedAudio && selectedImage;
        generateBtn.disabled = !canGenerate;
        
        if (canGenerate) {
            generateBtn.textContent = '🎬 영상 생성하기';
        } else {
            generateBtn.textContent = '음원과 이미지를 선택해주세요';
        }
    }
}

// 통합 영상 생성
async function generateVideo() {
    if (!uploadedAudio || !selectedImage) {
        alert('음원과 이미지가 모두 필요합니다.');
        return;
    }
    
    const videoQuality = document.getElementById('videoQuality').value;
    const applyLogo = document.getElementById('applyLogoCheckbox').checked;
    const addWatermark = document.getElementById('addWatermark').checked;
    const fadeInOut = document.getElementById('fadeInOut').checked;
    
    console.log("[Music Video] 통합 영상 생성 시작");
    
    // 진행 상황 표시
    showVideoProgress();
    
    try {
        const formData = new FormData();
        formData.append('audio', uploadedAudio.file);
        
        // 이미 처리된 이미지가 있다면 파일명 사용, 없다면 원본 파일 사용
        if (selectedImage.filename) {
            formData.append('processed_image_filename', selectedImage.filename);
        } else {
            formData.append('image', selectedImage.file);
        }
        
        formData.append('video_quality', videoQuality);
        formData.append('apply_logo', selectedImage.apply_logo ? 'true' : 'false');
        formData.append('add_watermark', addWatermark ? 'true' : 'false');
        formData.append('fade_in_out', fadeInOut ? 'true' : 'false');
        
        // AI 이미지 생성인 경우
        if (activeImageTab === 'ai') {
            const aiPrompt = document.getElementById('imagePrompt').value.trim();
            const aiStyle = document.getElementById('imageStyle').value;
            const aiSize = document.getElementById('imageSize').value;
            
            if (aiPrompt) {
                formData.append('ai_prompt', aiPrompt);
                formData.append('ai_style', aiStyle);
                formData.append('ai_size', aiSize);
            }
        }
        
        const response = await fetch('/api/music-video/create-unified', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        console.log("[Music Video] 통합 영상 생성 응답:", data);
        
        if (data.success) {
            // 작업 진행 상황 모니터링
            monitorJob(data.job_id, 'video_creation');
        } else {
            hideVideoProgress();
            alert('영상 생성 실패: ' + data.error);
        }
    } catch (error) {
        console.error("[Music Video] 통합 영상 생성 오류:", error);
        hideVideoProgress();
        alert('영상 생성 중 오류가 발생했습니다.');
    }
}

// 영상 생성 진행 상황 표시/숨기기
function showVideoProgress() {
    const unifiedForm = document.getElementById('unifiedForm');
    const videoProgress = document.getElementById('videoProgress');
    
    if (unifiedForm) {
        unifiedForm.style.display = 'none';
    }
    
    if (videoProgress) {
        videoProgress.style.display = 'block';
    }
}

function hideVideoProgress() {
    const unifiedForm = document.getElementById('unifiedForm');
    const videoProgress = document.getElementById('videoProgress');
    
    if (unifiedForm) {
        unifiedForm.style.display = 'block';
    }
    
    if (videoProgress) {
        videoProgress.style.display = 'none';
    }
}

// 영상 결과 표시
function displayVideoResult(result) {
    console.log("[Music Video] 영상 결과 표시:", result);
    
    const unifiedForm = document.getElementById('unifiedForm');
    const videoProgress = document.getElementById('videoProgress');
    const videoResult = document.getElementById('videoResult');
    const resultVideo = document.getElementById('resultVideo');
    const videoSource = document.getElementById('videoSource');
    const resultDetails = document.getElementById('resultDetails');
    const downloadVideoBtn = document.getElementById('downloadVideoBtn');
    
    if (unifiedForm) unifiedForm.style.display = 'none';
    if (videoProgress) videoProgress.style.display = 'none';
    
    if (result.video_info && result.video_info.filename) {
        if (videoSource) {
            videoSource.src = `/download/${result.video_info.filename}`;
        }
        
        if (resultVideo) {
            resultVideo.load();
        }
        
        if (resultDetails) {
            resultDetails.textContent = 
                `${result.video_info.filename} · ${result.video_info.size_mb || 'N/A'}MB`;
        }
        
        if (downloadVideoBtn) {
            downloadVideoBtn.onclick = () => {
                window.location.href = `/download/${result.video_info.filename}`;
            };
        }
    }
    
    if (videoResult) {
        videoResult.style.display = 'block';
    }
}

// ===========================================
// 작업 모니터링 관련 함수들
// ===========================================

// 작업 진행 상황 모니터링
function monitorJob(jobId, jobType) {
    console.log(`[Music Video] 작업 모니터링 시작: ${jobId} (${jobType})`);
    
    currentJobs[jobId] = { type: jobType, active: true, lastProgress: 0 };
    
    const checkProgress = async () => {
        if (!currentJobs[jobId] || !currentJobs[jobId].active) {
            return;
        }
        
        try {
            const response = await fetch(`/status/${jobId}`);
            const data = await response.json();
            
            // 진행률이 변경되었거나 5초마다 한 번씩 로그 출력
            const currentTime = Date.now();
            const shouldLog = !currentJobs[jobId].lastLogTime || 
                            (currentTime - currentJobs[jobId].lastLogTime > 5000) ||
                            (data.progress && data.progress !== currentJobs[jobId].lastProgress);
            
            if (shouldLog) {
                console.log(`[Music Video] 작업 상태: ${jobId} - ${data.progress || 0}% - ${data.message || '처리 중'}`);
                currentJobs[jobId].lastLogTime = currentTime;
                currentJobs[jobId].lastProgress = data.progress || 0;
            }
            
            if (data.status === 'completed') {
                currentJobs[jobId].active = false;
                handleJobCompletion(jobId, jobType, data.result);
            } else if (data.status === 'error') {
                currentJobs[jobId].active = false;
                handleJobError(jobId, jobType, data.message);
            } else {
                // 진행률 업데이트
                updateProgress(jobType, data.progress || 0, data.message || '처리 중...');
                
                // 더 빠른 모니터링 간격 (500ms)
                setTimeout(checkProgress, 500);
            }
        } catch (error) {
            console.error(`[Music Video] 작업 상태 확인 오류: ${jobId}`, error);
            currentJobs[jobId].active = false;
            handleJobError(jobId, jobType, '작업 상태 확인 중 오류가 발생했습니다.');
        }
    };
    
    checkProgress();
}

// 진행률 업데이트
function updateProgress(jobType, progress, message) {
    if (jobType === 'video_creation') {
        const progressFill = document.getElementById('videoProgressFill');
        const progressText = document.getElementById('videoProgressText');
        
        if (progressFill) {
            // 부드러운 애니메이션으로 진행률 업데이트
            progressFill.style.transition = 'width 0.3s ease';
            progressFill.style.width = `${Math.min(progress, 100)}%`;
            
            // 진행률에 따른 색상 변경
            if (progress < 30) {
                progressFill.style.background = '#ff7043';  // 주황색 (시작)
            } else if (progress < 70) {
                progressFill.style.background = '#ffa726';  // 노란색 (중간)
            } else if (progress < 95) {
                progressFill.style.background = '#66bb6a';  // 연두색 (거의 완료)
            } else {
                progressFill.style.background = '#4CAF50';  // 녹색 (완료)
            }
        }
        
        if (progressText) {
            // 진행률 퍼센트와 메시지 함께 표시
            const displayText = progress > 0 ? `${progress}% - ${message}` : message;
            progressText.textContent = displayText;
            
            // 메시지에 따른 아이콘 추가
            let icon = '';
            if (message.includes('준비')) icon = '⚙️';
            else if (message.includes('로딩') || message.includes('처리')) icon = '🔄';
            else if (message.includes('생성')) icon = '🎬';
            else if (message.includes('완료')) icon = '✅';
            else if (message.includes('결합')) icon = '🔗';
            
            if (icon) {
                progressText.textContent = `${icon} ${displayText}`;
            }
        }
    }
}

// 작업 완료 처리
function handleJobCompletion(jobId, jobType, result) {
    console.log(`[Music Video] 작업 완료: ${jobId} (${jobType})`, result);
    
    if (jobType === 'video_creation') {
        hideVideoProgress();
        displayVideoResult(result);
    }
}

// 작업 오류 처리
function handleJobError(jobId, jobType, errorMessage) {
    console.error(`[Music Video] 작업 오류: ${jobId} (${jobType})`, errorMessage);
    
    if (jobType === 'video_creation') {
        hideVideoProgress();
    }
    
    alert(`작업 실패: ${errorMessage}`);
}

// ===========================================
// 유틸리티 함수들
// ===========================================

// 전체 초기화
function resetVideoCreation() {
    console.log("[Music Video] 전체 초기화");
    
    uploadedAudio = null;
    selectedImage = null;
    currentJobs = {};
    activeImageTab = 'upload';
    
    // 모든 입력 필드 초기화
    const audioFileInput = document.getElementById('audioFileInput');
    const imageFileInput = document.getElementById('imageFileInput');
    const imagePrompt = document.getElementById('imagePrompt');
    
    if (audioFileInput) audioFileInput.value = '';
    if (imageFileInput) imageFileInput.value = '';
    if (imagePrompt) imagePrompt.value = '';
    
    // 모든 표시 영역 숨기기
    const audioInfo = document.getElementById('audioInfo');
    const imagePreview = document.getElementById('imagePreview');
    const videoProgress = document.getElementById('videoProgress');
    const videoResult = document.getElementById('videoResult');
    const unifiedForm = document.getElementById('unifiedForm');
    
    if (audioInfo) audioInfo.style.display = 'none';
    if (imagePreview) imagePreview.style.display = 'none';
    if (videoProgress) videoProgress.style.display = 'none';
    if (videoResult) videoResult.style.display = 'none';
    if (unifiedForm) unifiedForm.style.display = 'block';
    
    // 탭 초기화
    switchImageTab('upload');
    
    // 요약 및 버튼 상태 업데이트
    updateSummary();
    updateGenerateButton();
}

// 페이지 언로드 시 진행 중인 작업 정리
window.addEventListener('beforeunload', () => {
    Object.keys(currentJobs).forEach(jobId => {
        if (currentJobs[jobId]) {
            currentJobs[jobId].active = false;
        }
    });
});

console.log("[Music Video] 통합 버전 JavaScript 초기화 완료");