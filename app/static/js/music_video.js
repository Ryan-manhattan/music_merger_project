// Music Video Creator - JavaScript
console.log("[Music Video] JavaScript 로드 완료");

// 전역 변수
let currentStep = 1;
let uploadedAudio = null;
let selectedImage = null;
let currentJobs = {};

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log("[Music Video] DOM 로드 완료, 이벤트 리스너 설정");
    setupEventListeners();
    showStep(1);
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
    
    console.log("[Music Video] 모든 이벤트 리스너 설정 완료");
}

// 단계 표시 함수
function showStep(stepNumber) {
    console.log(`[Music Video] 단계 ${stepNumber} 표시`);
    
    currentStep = stepNumber;
    
    // 모든 단계 숨기기
    document.querySelectorAll('.video-step').forEach(step => {
        step.style.display = 'none';
    });
    
    // 진행 단계 업데이트
    document.querySelectorAll('.step').forEach((step, index) => {
        const stepNum = index + 1;
        step.classList.remove('active', 'completed');
        
        if (stepNum < stepNumber) {
            step.classList.add('completed');
        } else if (stepNum === stepNumber) {
            step.classList.add('active');
        }
    });
    
    // 현재 단계 표시
    const stepElements = {
        1: 'audioStep',
        2: 'imageStep',
        3: 'videoStep'
    };
    
    const currentStepElement = document.getElementById(stepElements[stepNumber]);
    if (currentStepElement) {
        currentStepElement.style.display = 'block';
    }
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
// 음원 업로드 관련 함수들
// ===========================================

// 음원 파일 선택 처리
function handleAudioFileSelect(e) {
    console.log("[Music Video] 음원 파일 선택됨");
    const file = e.target.files[0];
    if (file) {
        uploadAudioFile(file);
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
        uploadAudioFile(audioFile);
    } else {
        alert('지원하는 음원 파일을 업로드해주세요 (MP3, WAV, M4A, FLAC)');
    }
}

// 음원 파일 업로드
async function uploadAudioFile(file) {
    console.log(`[Music Video] 음원 파일 업로드 시작: ${file.name}`);
    
    const formData = new FormData();
    formData.append('audio', file);
    
    try {
        const response = await fetch('/api/music-video/upload-audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        console.log("[Music Video] 음원 업로드 응답:", data);
        
        if (data.success) {
            uploadedAudio = data.file_info;
            displayAudioInfo(data.file_info);
        } else {
            alert('음원 업로드 실패: ' + data.error);
        }
    } catch (error) {
        console.error("[Music Video] 음원 업로드 오류:", error);
        alert('음원 업로드 중 오류가 발생했습니다.');
    }
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
        audioFileDetails.textContent = 
            `${fileInfo.format.toUpperCase()} · ${fileInfo.size_mb}MB · ${fileInfo.duration_str}`;
    }
    
    if (audioInfo) {
        audioInfo.style.display = 'block';
    }
}

// 다른 음원 파일 선택
function changeAudioFile() {
    const audioFileInput = document.getElementById('audioFileInput');
    if (audioFileInput) {
        audioFileInput.click();
    }
}

// 이미지 단계로 진행
function proceedToImageStep() {
    if (!uploadedAudio) {
        alert('음원 파일을 먼저 업로드해주세요.');
        return;
    }
    
    showStep(2);
}

// ===========================================
// 이미지 업로드 관련 함수들
// ===========================================

// 이미지 파일 선택 처리
function handleImageFileSelect(e) {
    console.log("[Music Video] 이미지 파일 선택됨");
    const file = e.target.files[0];
    if (file) {
        uploadImageFile(file);
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
        uploadImageFile(imageFile);
    } else {
        alert('지원하는 이미지 파일을 업로드해주세요 (JPG, PNG, BMP, GIF)');
    }
}

// 이미지 파일 업로드
async function uploadImageFile(file) {
    console.log(`[Music Video] 이미지 파일 업로드 시작: ${file.name}`);
    
    const formData = new FormData();
    formData.append('image', file);

    const applyLogoCheckbox = document.getElementById('applyLogoCheckbox');
    if (applyLogoCheckbox && applyLogoCheckbox.checked) {
        formData.append('apply_logo', 'on');
    }
    
    try {
        const response = await fetch('/api/music-video/upload-image', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        console.log("[Music Video] 이미지 업로드 응답:", data);
        
        if (data.success) {
            selectedImage = data.file_info;
            displayImagePreview(data.file_info);
        } else {
            alert('이미지 업로드 실패: ' + data.error);
        }
    } catch (error) {
        console.error("[Music Video] 이미지 업로드 오류:", error);
        alert('이미지 업로드 중 오류가 발생했습니다.');
    }
}

// AI 이미지 생성
async function generateAIImage() {
    const prompt = document.getElementById('imagePrompt').value.trim();
    const style = document.querySelector('input[name="imageStyle"]:checked').value;
    const quality = document.getElementById('imageQuality').value;
    const size = document.getElementById('imageSize').value;
    
    if (!prompt) {
        alert('이미지 설명을 입력해주세요.');
        return;
    }
    
    console.log(`[Music Video] AI 이미지 생성 시작: ${prompt} (스타일: ${style}, 품질: ${quality}, 크기: ${size})`);
    
    // AI 생성 진행 상황 표시
    showAIProgress();
    
    try {
        const response = await fetch('/api/music-video/generate-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                style: style,
                quality: quality,
                size: size
            })
        });
        
        const data = await response.json();
        console.log("[Music Video] AI 이미지 생성 응답:", data);
        
        if (data.success) {
            // 작업 진행 상황 모니터링
            monitorJob(data.job_id, 'ai_image');
        } else {
            hideAIProgress();
            alert('AI 이미지 생성 실패: ' + data.error);
        }
    } catch (error) {
        console.error("[Music Video] AI 이미지 생성 오류:", error);
        hideAIProgress();
        alert('AI 이미지 생성 중 오류가 발생했습니다.');
    }
}

// AI 생성 진행 상황 표시/숨기기
function showAIProgress() {
    const aiProgress = document.getElementById('aiProgress');
    if (aiProgress) {
        aiProgress.style.display = 'block';
    }
}

function hideAIProgress() {
    const aiProgress = document.getElementById('aiProgress');
    if (aiProgress) {
        aiProgress.style.display = 'none';
    }
}

// 이미지 미리보기 표시
function displayImagePreview(fileInfo) {
    console.log("[Music Video] 이미지 미리보기 표시:", fileInfo);
    
    const imagePreview = document.getElementById('imagePreview');
    const previewImage = document.getElementById('previewImage');
    const imageDetails = document.getElementById('imageDetails');
    
    if (previewImage) {
        previewImage.src = `/download/${fileInfo.filename}`;
        previewImage.alt = fileInfo.original_name;
    }
    
    if (imageDetails) {
        let details = `${fileInfo.size_mb}MB`;
        if (fileInfo.prompt) {
            details += ` · AI 생성 (${fileInfo.style})`;
        }
        imageDetails.textContent = details;
    }
    
    if (imagePreview) {
        imagePreview.style.display = 'block';
    }
    
    hideAIProgress();
}

// 다른 이미지 선택
function changeImage() {
    selectedImage = null;
    
    const imagePreview = document.getElementById('imagePreview');
    if (imagePreview) {
        imagePreview.style.display = 'none';
    }
    
    // 이미지 입력 필드 초기화
    const imageFileInput = document.getElementById('imageFileInput');
    if (imageFileInput) {
        imageFileInput.value = '';
    }
    
    const imagePrompt = document.getElementById('imagePrompt');
    if (imagePrompt) {
        imagePrompt.value = '';
    }
}

// 영상 생성 단계로 진행
function proceedToVideoStep() {
    if (!selectedImage) {
        alert('이미지를 먼저 선택해주세요.');
        return;
    }
    
    updateVideoSummary();
    showStep(3);
}

// ===========================================
// 영상 생성 관련 함수들
// ===========================================

// 영상 요약 정보 업데이트
function updateVideoSummary() {
    const summaryAudio = document.getElementById('summaryAudio');
    const summaryImage = document.getElementById('summaryImage');
    const summaryDuration = document.getElementById('summaryDuration');
    
    if (summaryAudio && uploadedAudio) {
        summaryAudio.textContent = uploadedAudio.original_name;
    }
    
    if (summaryImage && selectedImage) {
        summaryImage.textContent = selectedImage.original_name;
    }
    
    if (summaryDuration && uploadedAudio) {
        summaryDuration.textContent = uploadedAudio.duration_str;
    }
}

// 영상 생성 시작
async function startVideoGeneration() {
    if (!uploadedAudio || !selectedImage) {
        alert('음원과 이미지가 모두 필요합니다.');
        return;
    }
    
    const videoQuality = document.getElementById('videoQuality').value;
    const addWatermark = document.getElementById('addWatermark').checked;
    const fadeInOut = document.getElementById('fadeInOut').checked;
    
    console.log("[Music Video] 영상 생성 시작");
    
    // 영상 생성 진행 상황 표시
    showVideoProgress();
    
    try {
        const response = await fetch('/api/music-video/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                audio_filename: uploadedAudio.filename,
                image_filename: selectedImage.filename,
                video_quality: videoQuality,
                options: {
                    watermark: addWatermark,
                    fade_in_out: fadeInOut
                }
            })
        });
        
        const data = await response.json();
        console.log("[Music Video] 영상 생성 응답:", data);
        
        if (data.success) {
            // 작업 진행 상황 모니터링
            monitorJob(data.job_id, 'video_creation');
        } else {
            hideVideoProgress();
            alert('영상 생성 실패: ' + data.error);
        }
    } catch (error) {
        console.error("[Music Video] 영상 생성 오류:", error);
        hideVideoProgress();
        alert('영상 생성 중 오류가 발생했습니다.');
    }
}

// 영상 생성 진행 상황 표시/숨기기
function showVideoProgress() {
    // 모든 단계 숨기기
    document.querySelectorAll('.video-step').forEach(step => {
        step.style.display = 'none';
    });
    
    const videoProgress = document.getElementById('videoProgress');
    if (videoProgress) {
        videoProgress.style.display = 'block';
    }
}

function hideVideoProgress() {
    const videoProgress = document.getElementById('videoProgress');
    if (videoProgress) {
        videoProgress.style.display = 'none';
    }
}

// 영상 결과 표시
function displayVideoResult(result) {
    console.log("[Music Video] 영상 결과 표시:", result);
    
    // 모든 단계 숨기기
    document.querySelectorAll('.video-step, #videoProgress').forEach(step => {
        step.style.display = 'none';
    });
    
    const videoResult = document.getElementById('videoResult');
    const resultVideo = document.getElementById('resultVideo');
    const videoSource = document.getElementById('videoSource');
    const resultDetails = document.getElementById('resultDetails');
    const downloadVideoBtn = document.getElementById('downloadVideoBtn');
    
    if (result.video_info && result.video_info.filename) {
        if (videoSource) {
            videoSource.src = `/download/${result.video_info.filename}`;
        }
        
        if (resultVideo) {
            resultVideo.load(); // 비디오 리로드
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
    
    currentJobs[jobId] = { type: jobType, active: true };
    
    const checkProgress = async () => {
        if (!currentJobs[jobId] || !currentJobs[jobId].active) {
            return;
        }
        
        try {
            const response = await fetch(`/status/${jobId}`);
            const data = await response.json();
            
            console.log(`[Music Video] 작업 상태: ${jobId}`, data);
            
            if (data.status === 'completed') {
                currentJobs[jobId].active = false;
                handleJobCompletion(jobId, jobType, data.result);
            } else if (data.status === 'error') {
                currentJobs[jobId].active = false;
                handleJobError(jobId, jobType, data.message);
            } else {
                // 진행률 업데이트
                updateProgress(jobType, data.progress || 0, data.message || '처리 중...');
                
                // 계속 모니터링
                setTimeout(checkProgress, 1000);
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
            progressFill.style.width = `${progress}%`;
        }
        
        if (progressText) {
            progressText.textContent = message;
        }
    }
    // AI 이미지 생성은 스피너로 표시하므로 별도 진행률 없음
}

// 작업 완료 처리
function handleJobCompletion(jobId, jobType, result) {
    console.log(`[Music Video] 작업 완료: ${jobId} (${jobType})`, result);
    
    if (jobType === 'ai_image' && result.file_info) {
        selectedImage = result.file_info;
        displayImagePreview(result.file_info);
    } else if (jobType === 'video_creation') {
        hideVideoProgress();
        displayVideoResult(result);
    }
}

// 작업 오류 처리
function handleJobError(jobId, jobType, errorMessage) {
    console.error(`[Music Video] 작업 오류: ${jobId} (${jobType})`, errorMessage);
    
    if (jobType === 'ai_image') {
        hideAIProgress();
    } else if (jobType === 'video_creation') {
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
    
    currentStep = 1;
    uploadedAudio = null;
    selectedImage = null;
    currentJobs = {};
    
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
    const aiProgress = document.getElementById('aiProgress');
    const videoProgress = document.getElementById('videoProgress');
    const videoResult = document.getElementById('videoResult');
    
    if (audioInfo) audioInfo.style.display = 'none';
    if (imagePreview) imagePreview.style.display = 'none';
    if (aiProgress) aiProgress.style.display = 'none';
    if (videoProgress) videoProgress.style.display = 'none';
    if (videoResult) videoResult.style.display = 'none';
    
    // 첫 번째 단계로 이동
    showStep(1);
}

// 페이지 언로드 시 진행 중인 작업 정리
window.addEventListener('beforeunload', () => {
    Object.keys(currentJobs).forEach(jobId => {
        if (currentJobs[jobId]) {
            currentJobs[jobId].active = false;
        }
    });
});

console.log("[Music Video] JavaScript 초기화 완료");