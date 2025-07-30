// Audio Studio - 통합 음악 처리 모듈
console.log("[Audio Studio] 통합 모듈 로드");

// ===========================================
// 전역 상태 관리
// ===========================================
class AudioStudioState {
    constructor() {
        this.files = new Map(); // 업로드된 파일들
        this.currentWork = null; // 현재 선택된 작업 (playlist, extract, video)
        this.isProcessing = false; // 작업 진행 중 여부
        this.results = null; // 작업 결과
        this.selectedImage = null; // 선택된 이미지 파일
        this.selectedLogo = null; // 선택된 로고 파일
        this.logoApplied = false; // 로고 합성 적용 여부
    }

    addFile(fileData) {
        const fileId = this.generateFileId();
        this.files.set(fileId, {
            id: fileId,
            ...fileData,
            timestamp: Date.now()
        });
        return fileId;
    }

    removeFile(fileId) {
        return this.files.delete(fileId);
    }

    getFiles() {
        return Array.from(this.files.values());
    }

    setWork(workType) {
        this.currentWork = workType;
    }

    generateFileId() {
        return 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
    }

    reset() {
        this.files.clear();
        this.currentWork = null;
        this.isProcessing = false;
        this.results = null;
        this.selectedImage = null;
        this.selectedLogo = null;
        this.logoApplied = false;
    }
}

// ===========================================
// 파일 관리자
// ===========================================
class FileManager {
    constructor(state) {
        this.state = state;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // DOM이 완전히 로드될 때까지 대기
        const setup = () => {
            // 파일 입력
            const fileInput = document.getElementById('fileInput');
            console.log("[FileManager] fileInput 요소:", fileInput);
            
            if (fileInput) {
                fileInput.addEventListener('change', (e) => {
                    console.log("[FileManager] 파일 변경 이벤트 발생");
                    this.handleFileSelect(e);
                });
            } else {
                console.error("[FileManager] fileInput 요소를 찾을 수 없습니다");
            }

            // 업로드 영역 드래그앤드롭 (클릭 이벤트 제거)
            const uploadArea = document.getElementById('uploadArea');
            console.log("[FileManager] uploadArea 요소:", uploadArea);
            
            if (uploadArea) {
                uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
                uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
                uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
            } else {
                console.error("[FileManager] uploadArea 요소를 찾을 수 없습니다");
            }

            // 이미지 업로드
            const imageInput = document.getElementById('imageInput');
            const imageUploadArea = document.getElementById('imageUploadArea');
            
            if (imageInput && imageUploadArea) {
                imageInput.addEventListener('change', (e) => {
                    this.handleImageSelect(e);
                });
                
                imageUploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    imageUploadArea.classList.add('drag-over');
                });
                
                imageUploadArea.addEventListener('dragleave', (e) => {
                    imageUploadArea.classList.remove('drag-over');
                });
                
                imageUploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    imageUploadArea.classList.remove('drag-over');
                    
                    const files = Array.from(e.dataTransfer.files);
                    const imageFile = files.find(file => file.type.startsWith('image/'));
                    
                    if (imageFile) {
                        imageInput.files = e.dataTransfer.files;
                        this.handleImageSelect({ target: imageInput });
                    }
                });
            }

            // 로고 업로드
            const logoInput = document.getElementById('logoInput');
            const logoUploadArea = document.getElementById('logoUploadArea');
            
            if (logoInput && logoUploadArea) {
                logoInput.addEventListener('change', (e) => {
                    this.handleLogoSelect(e);
                });
                
                logoUploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    logoUploadArea.classList.add('drag-over');
                });
                
                logoUploadArea.addEventListener('dragleave', (e) => {
                    logoUploadArea.classList.remove('drag-over');
                });
                
                logoUploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    logoUploadArea.classList.remove('drag-over');
                    
                    const files = Array.from(e.dataTransfer.files);
                    const logoFile = files.find(file => file.type.startsWith('image/'));
                    
                    if (logoFile) {
                        logoInput.files = e.dataTransfer.files;
                        this.handleLogoSelect({ target: logoInput });
                    }
                });
            }

            console.log("[FileManager] 이벤트 리스너 설정 완료");
        };

        // DOM 로드 상태 확인
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setup);
        } else {
            setup();
        }
    }

    async handleFileSelect(event) {
        try {
            const files = Array.from(event.target.files);
            console.log(`[FileManager] ${files.length}개 파일 선택됨`, files);
            
            if (files.length === 0) {
                console.log("[FileManager] 선택된 파일이 없습니다");
                return;
            }
            
            for (const file of files) {
                console.log(`[FileManager] 파일 처리 시작: ${file.name}`);
                await this.processFile(file);
            }
            
            this.updateFilesList();
            this.showWorkSelector();
            
        } catch (error) {
            console.error("[FileManager] 파일 선택 처리 오류:", error);
            alert(`파일 업로드 오류: ${error.message}`);
        }
    }

    async processFile(file) {
        try {
            console.log(`[FileManager] 파일 처리: ${file.name}, 크기: ${file.size}, 타입: ${file.type}`);
            
            // 파일 타입 검증
            const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-m4a', 'audio/flac', 'video/mp4', 'video/webm'];
            const allowedExtensions = ['.mp3', '.wav', '.m4a', '.flac', '.mp4', '.webm'];
            
            const isValidType = allowedTypes.some(type => file.type.includes(type)) || 
                               allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
            
            if (!isValidType) {
                throw new Error(`지원하지 않는 파일 형식입니다: ${file.name}`);
            }
            
            // 파일 크기 검증 (100MB 제한)
            const maxSize = 100 * 1024 * 1024; // 100MB
            if (file.size > maxSize) {
                throw new Error(`파일 크기가 너무 큽니다 (최대 100MB): ${file.name}`);
            }
            
            const fileData = {
                name: file.name,
                size: file.size,
                type: file.type,
                file: file,
                source: 'upload'
            };

            const fileId = this.state.addFile(fileData);
            console.log(`[FileManager] 파일 추가 완료: ${fileId}`, fileData);
            
            return fileId;
            
        } catch (error) {
            console.error(`[FileManager] 파일 처리 오류: ${file.name}`, error);
            throw error;
        }
    }

    async extractFromUrl() {
        const urlInput = document.getElementById('urlInput');
        const url = urlInput?.value?.trim();
        
        if (!url) {
            alert('URL을 입력해주세요.');
            return;
        }

        console.log(`[FileManager] URL에서 추출: ${url}`);
        
        try {
            // URL 추출 API 호출
            const response = await fetch('/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            
            if (data.success && data.job_id) {
                console.log(`[FileManager] 추출 작업 시작: ${data.job_id}`);
                
                // 작업 상태 확인 대기
                const result = await this.waitForExtractJob(data.job_id);
                console.log('[FileManager] 추출 결과:', result);
                
                const fileData = {
                    name: result.filename,
                    size: result.file_size || 0,
                    type: 'audio/mpeg',
                    url: result.download_url,
                    source: 'url',
                    original_url: url
                };

                console.log('[FileManager] 파일 데이터:', fileData);
                const fileId = this.state.addFile(fileData);
                console.log(`[FileManager] URL 추출 완료: ${fileId}`);
                console.log('[FileManager] 현재 파일 목록:', this.state.getFiles());
                
                this.updateFilesList();
                this.showWorkSelector();
                
                // URL 입력 초기화
                urlInput.value = '';
            } else {
                throw new Error(data.error || 'URL 추출 실패');
            }
        } catch (error) {
            console.error('[FileManager] URL 추출 오류:', error);
            alert(`URL 추출 실패: ${error.message}`);
        }
    }

    async waitForExtractJob(jobId) {
        console.log(`[FileManager] 추출 작업 상태 확인 시작: ${jobId}`);
        
        const maxAttempts = 60; // 최대 5분 대기
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/extract_status/${jobId}`);
                const status = await response.json();
                
                console.log(`[FileManager] 추출 작업 상태 [${attempts + 1}/${maxAttempts}]:`, status);
                
                if (status.status === 'completed') {
                    const fileInfo = status.result.file_info;
                    return {
                        success: true,
                        filename: fileInfo.filename,
                        download_url: `/download/${fileInfo.filename}`,
                        file_size: fileInfo.file_size || 'N/A'
                    };
                } else if (status.status === 'error' || status.status === 'failed') {
                    throw new Error(status.message || status.error || '추출 작업 실패');
                }
                
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
                
            } catch (error) {
                console.error('[FileManager] 추출 상태 확인 오류:', error);
                if (attempts >= maxAttempts - 1) {
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
            }
        }
        
        throw new Error('추출 작업 시간 초과');
    }

    handleImageSelect(event) {
        const file = event.target.files[0];
        if (!file) {
            console.log('[FileManager] 이미지 파일이 선택되지 않음');
            return;
        }
        
        // 로고 합성 상태 업데이트
        updateImageUploadState(file);

        console.log('[FileManager] 이미지 선택됨:', file.name);
        console.log('[FileManager] 파일 타입:', file.type);
        console.log('[FileManager] 파일 크기:', file.size);

        // 이미지 타입 검증
        if (!file.type.startsWith('image/')) {
            alert('이미지 파일만 선택 가능합니다.');
            return;
        }

        // 파일 크기 검증 (10MB 제한)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            alert('이미지 파일 크기가 너무 큽니다 (최대 10MB).');
            return;
        }

        // state에 이미지 파일 저장
        this.state.selectedImage = file;
        
        // 이미지 미리보기 표시
        this.showImagePreview(file);
    }

    showImagePreview(file) {
        const imageUploadArea = document.getElementById('imageUploadArea');
        if (!imageUploadArea) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            imageUploadArea.innerHTML = `
                <input type="file" id="imageInput" accept=".jpg,.jpeg,.png,.bmp,.gif" hidden>
                <div class="image-preview">
                    <img src="${e.target.result}" alt="미리보기">
                    <p class="image-name">${file.name}</p>
                    <button class="btn btn-outline btn-small" onclick="document.getElementById('imageInput').click()">
                        이미지 변경
                    </button>
                </div>
            `;
            
            // 새로운 imageInput에 이벤트 리스너 재등록
            const newImageInput = document.getElementById('imageInput');
            if (newImageInput) {
                newImageInput.addEventListener('change', (e) => {
                    this.handleImageSelect(e);
                });
            }
        };
        reader.readAsDataURL(file);
    }

    handleLogoSelect(event) {
        // 로고 합성은 music-video 페이지와 동일하게 서버에서 처리
        // 여기서는 파일만 저장하고 이미지 재처리
        const file = event.target.files[0];
        if (!file) {
            console.log('[FileManager] 로고 파일이 선택되지 않음');
            return;
        }

        console.log('[FileManager] 로고 이미지 선택됨:', file.name);
        
        // 이미지 타입 검증
        if (!file.type.startsWith('image/')) {
            alert('이미지 파일만 선택 가능합니다.');
            return;
        }

        // 파일 크기 검증 (5MB 제한)
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            alert('로고 이미지 파일 크기가 너무 큽니다 (최대 5MB).');
            return;
        }

        // state에 로고 파일 저장
        this.state.selectedLogo = file;
        
        // 이미지가 있다면 재처리 (로고 합성 포함)
        if (this.state.selectedImage) {
            this.reprocessImageWithLogo();
        }
    }

    async reprocessImageWithLogo() {
        console.log('[FileManager] 로고 합성으로 이미지 재처리');
        
        if (!this.state.selectedImage || !this.state.selectedLogo) {
            console.log('[FileManager] 이미지 또는 로고가 없어서 재처리 생략');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('image', this.state.selectedImage);
            formData.append('apply_logo', 'true');
            
            // 로고도 함께 업로드
            const logoFormData = new FormData();
            logoFormData.append('image', this.state.selectedLogo);
            
            // 먼저 로고 업로드
            await fetch('/api/music-video/upload-image', {
                method: 'POST',
                body: logoFormData
            });
            
            // 이미지 처리 (로고 합성 포함)
            const response = await fetch('/api/music-video/process-image', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('이미지 처리 실패');
            }

            const result = await response.json();
            console.log('[FileManager] 로고 합성 처리 결과:', result);
            
            // 처리된 이미지로 미리보기 업데이트
            if (result.processed_image_url) {
                this.showProcessedImagePreview(result.processed_image_url, result.filename);
            }
            
        } catch (error) {
            console.error('[FileManager] 로고 합성 처리 오류:', error);
            alert('로고 합성 처리 중 오류가 발생했습니다.');
        }
    }

    showProcessedImagePreview(imageUrl, filename) {
        const imageUploadArea = document.getElementById('imageUploadArea');
        if (!imageUploadArea) return;

        imageUploadArea.innerHTML = `
            <input type="file" id="imageInput" accept=".jpg,.jpeg,.png,.bmp,.gif" hidden>
            <div class="image-preview">
                <img src="${imageUrl}" alt="로고 합성 완료">
                <p class="image-name">로고 합성 완료 ✅</p>
                <p class="file-name">${filename}</p>
                <button class="btn btn-outline btn-small" onclick="document.getElementById('imageInput').click()">
                    이미지 변경
                </button>
            </div>
        `;
        
        // 처리된 파일명을 state에 저장
        this.state.processedImageFilename = filename;
        
        // 이벤트 리스너 재등록
        const newImageInput = document.getElementById('imageInput');
        if (newImageInput) {
            newImageInput.addEventListener('change', (e) => {
                this.handleImageSelect(e);
            });
        }
    }

    updateFilesList() {
        const files = this.state.getFiles();
        const filesContainer = document.getElementById('filesContainer');
        const filesList = document.getElementById('filesList');
        
        if (!filesContainer || !filesList) return;

        if (files.length === 0) {
            filesList.style.display = 'none';
            return;
        }

        filesContainer.innerHTML = '';
        
        files.forEach(fileData => {
            const fileElement = this.createFileElement(fileData);
            filesContainer.appendChild(fileElement);
        });

        filesList.style.display = 'block';
        console.log(`[FileManager] 파일 목록 업데이트: ${files.length}개`);
    }

    createFileElement(fileData) {
        // 템플릿 복제
        const template = document.getElementById('fileItemTemplate');
        if (!template) {
            console.error('[FileManager] fileItemTemplate을 찾을 수 없습니다');
            return this.createSimpleFileElement(fileData);
        }

        const fileElement = template.content.cloneNode(true);
        const fileItem = fileElement.querySelector('.file-item');
        
        // 파일 데이터 설정
        fileItem.dataset.fileId = fileData.id;
        fileItem.dataset.filename = fileData.name;
        
        // 파일 정보 설정
        const fileName = fileElement.querySelector('.file-name');
        const fileIcon = fileElement.querySelector('.file-icon');
        
        fileName.textContent = fileData.name;
        fileIcon.textContent = fileData.source === 'upload' ? '🎵' : '🔗';
        
        // 기본 설정값으로 초기화
        this.initializeFileSettings(fileElement, fileData.id);
        
        // 슬라이더 이벤트 리스너 추가
        this.setupSliderEvents(fileElement, fileData.id);
        
        return fileElement;
    }

    createSimpleFileElement(fileData) {
        // 템플릿이 없을 때 대체 요소 생성
        const div = document.createElement('div');
        div.className = 'file-item';
        div.dataset.fileId = fileData.id;
        
        const sizeText = fileData.size ? this.formatFileSize(fileData.size) : 'Unknown';
        const sourceIcon = fileData.source === 'upload' ? '📁' : '🔗';
        
        div.innerHTML = `
            <div class="file-header">
                <span class="file-icon">${sourceIcon}</span>
                <div class="file-info">
                    <div class="file-name">${fileData.name}</div>
                    <div class="file-details">${sizeText} • ${fileData.source === 'upload' ? '로컬 파일' : 'URL 추출'}</div>
                </div>
                <div class="file-actions">
                    <button class="btn-icon btn-danger" onclick="audioStudio.fileManager.removeFile('${fileData.id}')" title="삭제">❌</button>
                </div>
            </div>
        `;
        
        return div;
    }

    initializeFileSettings(fileElement, fileId) {
        // 기본 설정값
        const defaultSettings = {
            fadeIn: 2,
            fadeOut: 3,
            volume: 0,
            gap: 1
        };

        // AudioStudioState에 설정 저장
        const fileData = this.state.files.get(fileId);
        if (fileData) {
            fileData.settings = defaultSettings;
        }

        console.log(`[FileManager] 파일 설정 초기화: ${fileId}`, defaultSettings);
    }

    setupSliderEvents(fileElement, fileId) {
        const sliders = fileElement.querySelectorAll('.slider');
        
        sliders.forEach(slider => {
            slider.addEventListener('input', (e) => {
                this.updateSliderValue(e.target, fileId);
            });
        });
    }

    updateSliderValue(slider, fileId) {
        const value = parseFloat(slider.value);
        const settingName = slider.name;
        
        // 값 표시 업데이트
        const valueDisplay = slider.parentElement.querySelector('.value-display');
        if (valueDisplay) {
            valueDisplay.textContent = value;
        }
        
        // 상태에 설정 저장
        const fileData = this.state.files.get(fileId);
        if (fileData && fileData.settings) {
            fileData.settings[settingName] = value;
            console.log(`[FileManager] 설정 업데이트: ${fileId} - ${settingName}: ${value}`);
        }
    }

    // 템플릿 버튼 이벤트 핸들러들
    toggleFileSettings(button) {
        const fileItem = button.closest('.file-item');
        const settings = fileItem.querySelector('.file-settings');
        const isVisible = settings.style.display !== 'none';
        
        console.log('[FileManager] 설정 토글:', fileItem.dataset.fileId, !isVisible);
        settings.style.display = isVisible ? 'none' : 'block';
    }

    moveFileUp(button) {
        const fileItem = button.closest('.file-item');
        const fileId = fileItem.dataset.fileId;
        const container = fileItem.parentElement;
        const prevItem = fileItem.previousElementSibling;
        
        if (prevItem) {
            container.insertBefore(fileItem, prevItem);
            console.log(`[FileManager] 파일 위로 이동: ${fileId}`);
        }
    }

    moveFileDown(button) {
        const fileItem = button.closest('.file-item');
        const fileId = fileItem.dataset.fileId;
        const container = fileItem.parentElement;
        const nextItem = fileItem.nextElementSibling;
        
        if (nextItem) {
            container.insertBefore(nextItem, fileItem);
            console.log(`[FileManager] 파일 아래로 이동: ${fileId}`);
        }
    }

    removeFileByButton(button) {
        const fileItem = button.closest('.file-item');
        const fileId = fileItem.dataset.fileId;
        this.removeFile(fileId);
    }

    // 파일 순서 가져오기 (UI 순서 기준)
    getFileOrder() {
        const container = document.getElementById('filesContainer');
        if (!container) return [];
        
        const fileItems = container.querySelectorAll('.file-item');
        const orderedIds = Array.from(fileItems).map(item => item.dataset.fileId);
        
        console.log('[FileManager] 현재 파일 순서:', orderedIds);
        return orderedIds;
    }

    removeFile(fileId) {
        if (this.state.removeFile(fileId)) {
            console.log(`[FileManager] 파일 삭제: ${fileId}`);
            this.updateFilesList();
            
            // 파일이 없으면 작업 선택기 숨김
            if (this.state.getFiles().length === 0) {
                this.hideWorkSelector();
            }
        }
    }

    showWorkSelector() {
        const workSelector = document.getElementById('workSelector');
        if (workSelector) {
            workSelector.style.display = 'block';
        }
    }

    hideWorkSelector() {
        const workSelector = document.getElementById('workSelector');
        if (workSelector) {
            workSelector.style.display = 'none';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.currentTarget.classList.remove('drag-over');
    }

    async handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        console.log(`[FileManager] ${files.length}개 파일 드롭됨`);
        
        for (const file of files) {
            await this.processFile(file);
        }
        
        this.updateFilesList();
        this.showWorkSelector();
    }
}

// ===========================================
// 작업 관리자
// ===========================================
class WorkManager {
    constructor(state, fileManager) {
        this.state = state;
        this.fileManager = fileManager;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // 작업 선택
        const workOptions = document.querySelectorAll('.work-option');
        workOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const workType = option.getAttribute('onclick')?.match(/selectWork\('(\w+)'\)/)?.[1];
                if (workType) {
                    this.selectWork(workType);
                }
            });
        });

        console.log("[WorkManager] 이벤트 리스너 설정 완료");
    }

    selectWork(workType) {
        console.log(`[WorkManager] 작업 선택: ${workType}`);
        
        this.state.setWork(workType);
        this.showWorkSettings(workType);
        this.updateExecuteButton(workType);
    }

    showWorkSettings(workType) {
        const workSettings = document.getElementById('workSettings');
        const allPanels = document.querySelectorAll('.settings-panel');
        
        if (!workSettings) return;

        // 모든 패널 숨김
        allPanels.forEach(panel => panel.style.display = 'none');
        
        // 선택된 작업 패널 표시
        const targetPanel = document.getElementById(`${workType}Settings`);
        if (targetPanel) {
            targetPanel.style.display = 'block';
        }

        workSettings.style.display = 'block';
        console.log(`[WorkManager] ${workType} 설정 표시`);
        
        // DOM 강제 렌더링
        workSettings.offsetHeight;
        
        // 동영상 작업이 선택된 경우 로고 버튼 상태 초기화
        if (workType === 'video') {
            // requestAnimationFrame을 사용하여 렌더링 완료 후 초기화
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    console.log('[WorkManager] 동영상 작업 선택됨 - 로고 버튼 초기화');
                    
                    // 이미 선택된 이미지가 있는지 확인
                    const hasImage = this.state.selectedImage;
                    const hasLogo = this.state.selectedLogo;
                    
                    if (hasLogo) {
                        updateLogoButtons('selected');
                    } else if (hasImage) {
                        updateLogoButtons('none'); // 이미지는 있지만 로고는 없는 상태
                    } else {
                        updateLogoButtons('none'); // 둘 다 없는 상태
                    }
                });
            });
        }
    }

    updateExecuteButton(workType) {
        const executeBtn = document.getElementById('executeBtn');
        const executeText = document.getElementById('executeText');
        
        if (!executeBtn || !executeText) return;

        const workConfig = {
            playlist: { text: '🎵 플레이리스트 생성', color: 'btn-success' },
            extract: { text: '🎧 음원 추출 & 편집', color: 'btn-primary' },
            video: { text: '🎬 동영상 생성', color: 'btn-info' }
        };

        const config = workConfig[workType] || workConfig.playlist;
        
        executeText.textContent = config.text;
        executeBtn.className = `btn btn-large ${config.color}`;
    }

    async executeWork() {
        if (this.state.isProcessing) {
            console.log("[WorkManager] 이미 작업 진행 중");
            return;
        }

        const workType = this.state.currentWork;
        const files = this.state.getFiles();

        if (!workType) {
            alert('작업을 선택해주세요.');
            return;
        }

        if (files.length === 0) {
            alert('파일을 업로드해주세요.');
            return;
        }

        console.log(`[WorkManager] 작업 실행: ${workType}`);
        
        this.state.isProcessing = true;
        this.showProgress(workType);

        try {
            let result;
            switch (workType) {
                case 'playlist':
                    result = await this.executePlaylist(files);
                    break;
                case 'extract':
                    result = await this.executeExtract(files);
                    break;
                case 'video':
                    result = await this.executeVideo(files);
                    break;
                default:
                    throw new Error(`알 수 없는 작업 타입: ${workType}`);
            }

            this.state.results = result;
            this.showResults(result, workType);
            console.log(`[WorkManager] 작업 완료: ${workType}`);

        } catch (error) {
            console.error('[WorkManager] 작업 실행 오류:', error);
            alert(`작업 실행 실패: ${error.message}`);
            this.hideProgress();
        } finally {
            this.state.isProcessing = false;
        }
    }

    async executePlaylist(files) {
        // 1단계: 파일 업로드
        const formData = new FormData();
        
        files.forEach((fileData, index) => {
            if (fileData.file) {
                formData.append('files', fileData.file);
            }
        });

        // 파일 업로드
        const uploadResult = await this.makeApiCall('/upload', formData);
        console.log('[WorkManager] 업로드 결과:', uploadResult);

        // 2단계: 플레이리스트 생성 요청
        const normalizeVolume = document.getElementById('normalizeVolume')?.checked || false;
        const crossfade = document.getElementById('crossfade')?.checked || false;
        
        // 파일 순서 및 설정 가져오기
        const fileOrder = this.fileManager.getFileOrder();
        const orderedFiles = fileOrder.map(fileId => {
            const fileData = this.state.files.get(fileId);
            const uploadedFile = uploadResult.files.find(f => f.original_name === fileData.name);
            
            return {
                filename: uploadedFile ? uploadedFile.filename : fileData.name,
                settings: fileData.settings || {
                    fadeIn: 2,
                    fadeOut: 3,
                    volume: 0,
                    gap: 1
                }
            };
        });

        const processData = {
            files: orderedFiles,
            globalSettings: {
                normalizeVolume: normalizeVolume,
                crossfade: crossfade
            }
        };

        // JSON으로 처리 요청
        const response = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(processData)
        });

        const result = await response.json();
        
        if (!result.success && !result.job_id) {
            throw new Error(result.error || '플레이리스트 생성 실패');
        }

        // 작업 상태 확인 (job_id가 있는 경우 폴링)
        if (result.job_id) {
            return await this.waitForJob(result.job_id);
        }

        return result;
    }

    async waitForJob(jobId) {
        console.log(`[WorkManager] 작업 상태 확인 시작: ${jobId}`);
        
        const maxAttempts = 60; // 최대 5분 대기 (5초 간격)
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/process/status/${jobId}`);
                const status = await response.json();
                
                console.log(`[WorkManager] 작업 상태 [${attempts + 1}/${maxAttempts}]:`, status);
                
                if (status.status === 'completed') {
                    return {
                        success: true,
                        filename: status.result.new_filename || status.result.filename,
                        new_filename: status.result.new_filename,
                        download_url: status.result.download_url,
                        duration: status.result.duration,
                        file_size: status.result.file_size
                    };
                } else if (status.status === 'failed') {
                    throw new Error(status.error || '작업 실패');
                }
                
                // 5초 대기 후 다시 확인
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
                
            } catch (error) {
                console.error('[WorkManager] 상태 확인 오류:', error);
                if (attempts >= maxAttempts - 1) {
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
            }
        }
        
        throw new Error('작업 시간 초과');
    }

    async waitForExtractJob(jobId) {
        console.log(`[WorkManager] 추출 작업 상태 확인 시작: ${jobId}`);
        
        const maxAttempts = 60; // 최대 5분 대기
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/extract_status/${jobId}`);
                const status = await response.json();
                
                console.log(`[WorkManager] 추출 작업 상태 [${attempts + 1}/${maxAttempts}]:`, status);
                
                if (status.status === 'completed') {
                    return {
                        success: true,
                        filename: status.result.filename,
                        download_url: status.result.download_url,
                        format: 'mp3',
                        file_size: status.result.file_size
                    };
                } else if (status.status === 'failed') {
                    throw new Error(status.error || '추출 작업 실패');
                }
                
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
                
            } catch (error) {
                console.error('[WorkManager] 추출 상태 확인 오류:', error);
                if (attempts >= maxAttempts - 1) {
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
            }
        }
        
        throw new Error('추출 작업 시간 초과');
    }

    async executeExtract(files) {
        // 음원 추출 로직 - 첫 번째 파일만 처리
        const fileData = files[0];
        
        // URL에서 추출하는 경우
        if (fileData.source === 'url') {
            const response = await fetch('/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: fileData.original_url })
            });
            
            const result = await response.json();
            if (result.job_id) {
                const extractResult = await this.waitForExtractJob(result.job_id);
                return {
                    success: true,
                    filename: extractResult.filename,
                    download_url: extractResult.download_url,
                    format: 'mp3',
                    file_size: extractResult.file_size
                };
            }
            return result;
        }
        
        // 파일 업로드 추출인 경우
        const formData = new FormData();
        formData.append('file', fileData.file);

        // 1단계: 파일 업로드
        const uploadResult = await this.makeApiCall('/upload_extract_file', formData);
        console.log('[WorkManager] 추출 파일 업로드 결과 전체:', JSON.stringify(uploadResult, null, 2));

        // 2단계: 설정에 따른 처리
        const outputFormat = document.getElementById('outputFormat')?.value || 'mp3';
        const pitchValue = document.getElementById('pitchSlider')?.value || '0';
        const trimToThirtyElement = document.getElementById('trimToThirty');
        const trimToThirty = trimToThirtyElement?.checked || false;
        console.log('[DEBUG] trimToThirty 엘리먼트:', trimToThirtyElement);
        console.log('[DEBUG] trimToThirty 체크됨:', trimToThirtyElement?.checked);
        console.log('[WorkManager] 30초 자르기 옵션:', trimToThirty);
        
        let result = uploadResult;
        
        // 업로드 결과에서 파일명 추출
        let currentFilename = result.file_info?.filename || result.filename;
        console.log('[WorkManager] 현재 파일명:', currentFilename);
        
        // 키 조절이 필요한 경우
        if (pitchValue !== '0') {
            console.log(`[WorkManager] 키 조절 적용: ${pitchValue} 반음`);
            const pitchData = {
                filename: currentFilename,
                semitones: parseInt(pitchValue)
            };
            const pitchResponse = await this.makeApiCall('/adjust-pitch', pitchData);
            console.log('[DEBUG] 키 조절 응답:', pitchResponse);
            
            // 비동기 작업인 경우 대기
            if (pitchResponse.job_id) {
                result = await this.waitForJob(pitchResponse.job_id);
                currentFilename = result.new_filename || result.filename || currentFilename;
            } else {
                result = pitchResponse;
                currentFilename = result.file_info?.filename || result.filename || currentFilename;
            }
            console.log('[WorkManager] 키 조절 후 파일명:', currentFilename);
        }
        
        // 30초 자르기가 필요한 경우
        if (trimToThirty) {
            console.log('[WorkManager] 30초 자르기 적용');
            const trimData = {
                filename: currentFilename
            };
            const trimResponse = await this.makeApiCall('/trim-audio', trimData);
            console.log('[DEBUG] 30초 자르기 응답:', trimResponse);
            
            // 비동기 작업인 경우 대기
            if (trimResponse.job_id) {
                result = await this.waitForJob(trimResponse.job_id);
                currentFilename = result.new_filename || result.filename || currentFilename;
            } else {
                result = trimResponse;
                currentFilename = result.file_info?.new_filename || result.new_filename || result.file_info?.filename || result.filename || currentFilename;
            }
            console.log('[WorkManager] 자르기 후 파일명:', currentFilename);
        }
        
        console.log('[WorkManager] 최종 처리 완료, 파일명:', currentFilename);
        
        return {
            success: true,
            filename: currentFilename,
            download_url: `/download/${currentFilename}`,
            format: outputFormat,
            file_size: result.file_size || result.file_info?.file_size || 'N/A'
        };
    }

    async executeVideo(files) {
        // 동영상 생성 로직
        const audioFile = files[0]; // 첫 번째 오디오 파일
        
        console.log('[WorkManager] state에 저장된 이미지:', this.state.selectedImage);
        console.log('[WorkManager] state에 저장된 로고:', this.state.selectedLogo);
        
        if (!this.state.selectedImage) {
            throw new Error('배경 이미지를 선택해주세요.');
        }

        const formData = new FormData();
        
        // 오디오 파일 처리
        if (audioFile.file) {
            formData.append('audio', audioFile.file);
        } else if (audioFile.url || audioFile.source === 'url') {
            // URL 파일의 경우 파일명을 전달하여 서버에서 처리
            formData.append('audio_filename', audioFile.name);
        } else {
            throw new Error('오디오 파일을 찾을 수 없습니다.');
        }
        
        // 이미지 파일 (state에서 가져옴)
        formData.append('image', this.state.selectedImage);

        // 설정 추가
        const videoQualityElement = document.getElementById('videoQuality');
        const addWatermarkElement = document.getElementById('addWatermark');
        
        const videoQuality = videoQualityElement?.value || 'youtube_hd';
        const addWatermark = addWatermarkElement?.checked || false;
        const logoApplied = this.state.logoApplied || false;
        
        console.log('[WorkManager] 동영상 설정 요소들:', {
            videoQualityElement: !!videoQualityElement,
            addWatermarkElement: !!addWatermarkElement,
            videoQuality: videoQuality,
            addWatermark: addWatermark,
            logoApplied: logoApplied
        });
        console.log('[WorkManager] 사용할 이미지:', this.state.selectedImage);
        
        // 이미지 처리: 로고가 적용된 경우 이미 서버에 있는 파일명 사용
        let imageToUpload;
        if (logoApplied && typeof this.state.selectedImage === 'string') {
            // 로고가 합성된 경우 - 이미 서버에 있는 파일명
            imageToUpload = this.state.selectedImage;
        } else if (this.state.selectedImage instanceof File) {
            // 일반 이미지 파일
            imageToUpload = this.state.selectedImage;
        } else {
            throw new Error('이미지 정보를 찾을 수 없습니다.');
        }

        // 먼저 파일들을 업로드하고 실제 파일명을 받아옴
        const uploadedFiles = await this.uploadFilesForVideo(audioFile, imageToUpload, null);
        
        // 기존 구현된 API 사용: JSON 방식으로 변경
        const requestData = {
            audio_filename: uploadedFiles.audio_filename,
            image_filename: uploadedFiles.image_filename,
            video_quality: videoQuality,
            options: {}
        };
        
        console.log('[WorkManager] 최종 요청 데이터:', requestData);
        
        const result = await this.makeApiCall('/api/music-video/create', requestData);
        
        // 비동기 작업인 경우 job_id를 통해 완료 대기
        if (result.job_id) {
            console.log('[WorkManager] 동영상 생성 작업 ID:', result.job_id);
            return await this.waitForVideoJob(result.job_id);
        }
        
        return result;
    }

    async waitForVideoJob(jobId) {
        console.log(`[WorkManager] 동영상 작업 상태 확인 시작: ${jobId}`);
        
        const maxAttempts = 120; // 최대 10분 대기 (5초 간격)
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/process/status/${jobId}`);
                const status = await response.json();
                
                console.log(`[WorkManager] 동영상 작업 상태 [${attempts + 1}/${maxAttempts}]:`, status);
                
                if (status.status === 'completed') {
                    console.log('[WorkManager] 동영상 작업 완료, 결과 구조:', status.result);
                    
                    const videoInfo = status.result.video_info || status.result || {};
                    const filename = videoInfo.filename || videoInfo.output_file || status.result.filename;
                    
                    return {
                        success: true,
                        filename: filename,
                        download_url: `/download/${filename}`,
                        resolution: videoInfo.resolution || '1920x1080',
                        file_size: videoInfo.size || videoInfo.file_size || 'N/A',
                        duration: videoInfo.duration || 'N/A'
                    };
                } else if (status.status === 'error' || status.status === 'failed') {
                    throw new Error(status.message || status.error || '동영상 생성 실패');
                }
                
                // 진행률 업데이트
                if (status.progress !== undefined) {
                    this.updateProgress(status.progress, status.message || '동영상 생성 중...');
                }
                
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
                
            } catch (error) {
                console.error('[WorkManager] 동영상 상태 확인 오류:', error);
                if (attempts >= maxAttempts - 1) {
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
            }
        }
        
        throw new Error('동영상 생성 시간 초과');
    }

    updateProgress(progress, message) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        if (progressText) {
            progressText.textContent = `${message} ${Math.round(progress)}%`;
        }
    }

    async uploadFilesForVideo(audioFile, imageFile, logoFile) {
        console.log('[WorkManager] 동영상용 파일 업로드 시작');
        
        const uploadedFiles = {};
        
        // 이미지 파일 처리
        if (typeof imageFile === 'string') {
            // 이미 서버에 업로드된 파일명 (로고 합성된 경우)
            console.log('[WorkManager] 로고 합성된 이미지 파일명 사용:', imageFile);
            uploadedFiles.image_filename = imageFile;
        } else {
            // 새로운 이미지 파일 업로드
            const imageFormData = new FormData();
            imageFormData.append('image', imageFile);
            
            console.log('[WorkManager] 이미지 업로드 중...');
            const imageResponse = await fetch('/api/music-video/upload-image', {
                method: 'POST',
                body: imageFormData
            });
            
            if (!imageResponse.ok) {
                throw new Error('이미지 업로드 실패');
            }
            
            const imageResult = await imageResponse.json();
            console.log('[WorkManager] 이미지 업로드 결과:', imageResult);
            uploadedFiles.image_filename = imageResult.filename || imageResult.file_info?.filename || imageFile.name;
        }
        
        // 로고 파일 업로드 (선택된 경우)
        if (logoFile) {
            const logoFormData = new FormData();
            logoFormData.append('image', logoFile); // 'logo'가 아니라 'image'로 전송
            
            console.log('[WorkManager] 로고 업로드 중...');
            const logoResponse = await fetch('/api/music-video/upload-image', {
                method: 'POST',
                body: logoFormData
            });
            
            if (!logoResponse.ok) {
                console.warn('[WorkManager] 로고 업로드 실패, 계속 진행');
            } else {
                const logoResult = await logoResponse.json();
                console.log('[WorkManager] 로고 업로드 결과:', logoResult);
                uploadedFiles.logo_filename = logoResult.filename || logoResult.file_info?.filename || logoFile.name;
            }
        }
        
        // 오디오 파일 업로드 (URL에서 온 파일이 아닌 경우)
        if (audioFile.file) {
            const audioFormData = new FormData();
            audioFormData.append('audio', audioFile.file);
            
            console.log('[WorkManager] 오디오 업로드 중...');
            const audioResponse = await fetch('/api/music-video/upload-audio', {
                method: 'POST',
                body: audioFormData
            });
            
            if (!audioResponse.ok) {
                throw new Error('오디오 업로드 실패');
            }
            
            const audioResult = await audioResponse.json();
            console.log('[WorkManager] 오디오 업로드 결과:', audioResult);
            uploadedFiles.audio_filename = audioResult.filename || audioResult.file_info?.filename || audioFile.file.name;
        } else {
            // URL에서 추출된 파일인 경우 기존 파일명 사용
            uploadedFiles.audio_filename = audioFile.name;
        }
        
        console.log('[WorkManager] 모든 파일 업로드 완료:', uploadedFiles);
        return uploadedFiles;
    }

    async makeApiCall(endpoint, formData) {
        console.log('[makeApiCall] 엔드포인트:', endpoint);
        console.log('[makeApiCall] 데이터 타입:', typeof formData);
        console.log('[makeApiCall] FormData 여부:', formData instanceof FormData);
        
        if (formData instanceof FormData) {
            console.log('[makeApiCall] FormData 내용:');
            for (let [key, value] of formData.entries()) {
                if (value instanceof File) {
                    console.log(` - ${key}: 파일 (${value.name}, ${value.size} bytes)`);
                } else {
                    console.log(` - ${key}: ${value}`);
                }
            }
        }
        
        const options = {
            method: 'POST',
            body: formData
        };
        
        // JSON 데이터인 경우 Content-Type 헤더 설정
        if (typeof formData === 'string' || (formData && formData.constructor === Object)) {
            options.headers = {
                'Content-Type': 'application/json'
            };
            if (typeof formData === 'object') {
                options.body = JSON.stringify(formData);
            }
        }
        
        console.log('[makeApiCall] 요청 시작...');
        
        try {
            const response = await fetch(endpoint, options);
            console.log('[makeApiCall] 응답 받음:', response.status, response.statusText);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('[makeApiCall] JSON 파싱 완료:', data);
            
            if (!data.success) {
                throw new Error(data.error || 'API 호출 실패');
            }

            return data;
        } catch (error) {
            console.error('[makeApiCall] 오류 발생:', error);
            throw error;
        }
    }

    showProgress(workType) {
        const progressSection = document.getElementById('progressSection');
        const progressTitle = document.getElementById('progressTitle');
        const workSettings = document.getElementById('workSettings');
        
        if (progressSection) {
            const titles = {
                playlist: '🎵 플레이리스트 생성 중...',
                extract: '🎧 음원 추출 중...',
                video: '🎬 동영상 생성 중...'
            };
            
            if (progressTitle) {
                progressTitle.textContent = titles[workType] || '처리 중...';
            }
            
            progressSection.style.display = 'block';
        }

        if (workSettings) {
            workSettings.style.display = 'none';
        }

        this.startProgressSimulation();
    }

    hideProgress() {
        const progressSection = document.getElementById('progressSection');
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    }

    startProgressSimulation() {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (!progressFill || !progressText) return;

        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `처리 중... ${Math.round(progress)}%`;
            
            if (!this.state.isProcessing) {
                clearInterval(interval);
                progressFill.style.width = '100%';
                progressText.textContent = '완료!';
            }
        }, 500);
    }

    showResults(result, workType) {
        const resultSection = document.getElementById('resultSection');
        const resultContent = document.getElementById('resultContent');
        const downloadBtn = document.getElementById('downloadBtn');
        
        if (!resultSection || !resultContent) return;

        this.hideProgress();

        // 결과 내용 설정
        resultContent.innerHTML = this.generateResultContent(result, workType);
        
        // 다운로드 버튼 설정
        console.log('[DEBUG] downloadBtn:', downloadBtn);
        console.log('[DEBUG] result:', result);
        console.log('[DEBUG] result.download_url:', result.download_url);
        
        if (downloadBtn && result.download_url) {
            console.log('[WorkManager] 다운로드 URL 설정:', result.download_url);
            downloadBtn.onclick = () => {
                console.log('[DEBUG] 다운로드 버튼 클릭됨!');
                console.log('[DEBUG] 다운로드 URL:', result.download_url);
                console.log('[DEBUG] 파일명:', result.filename);
                
                // 파일 다운로드 방식 변경
                fetch(result.download_url)
                    .then(response => {
                        console.log('[DEBUG] Fetch 응답:', response);
                        console.log('[DEBUG] 응답 상태:', response.status);
                        console.log('[DEBUG] 응답 헤더:', response.headers);
                        
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.blob();
                    })
                    .then(blob => {
                        console.log('[DEBUG] Blob 생성:', blob);
                        console.log('[DEBUG] Blob 크기:', blob.size);
                        console.log('[DEBUG] Blob 타입:', blob.type);
                        
                        const url = window.URL.createObjectURL(blob);
                        console.log('[DEBUG] Object URL 생성:', url);
                        
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = result.filename || 'download';
                        document.body.appendChild(a);
                        
                        console.log('[DEBUG] 다운로드 링크 클릭 시도');
                        a.click();
                        
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);
                        console.log('[WorkManager] 다운로드 완료');
                    })
                    .catch(error => {
                        console.error('[WorkManager] 다운로드 오류:', error);
                        console.error('[DEBUG] 오류 상세:', error.stack);
                        alert(`다운로드 오류: ${error.message}`);
                    });
            };
        } else {
            console.log('[DEBUG] 다운로드 버튼 설정 실패');
            console.log('[DEBUG] downloadBtn 존재:', !!downloadBtn);
            console.log('[DEBUG] download_url 존재:', !!result.download_url);
        }

        resultSection.style.display = 'block';
        console.log('[WorkManager] 결과 표시 완료');
    }

    generateResultContent(result, workType) {
        const templates = {
            playlist: `
                <div class="result-info">
                    <h4>🎵 플레이리스트 생성 완료</h4>
                    <p><strong>파일명:</strong> ${result.filename}</p>
                    <p><strong>길이:</strong> ${result.duration || 'N/A'}</p>
                    <p><strong>크기:</strong> ${result.file_size || 'N/A'}</p>
                </div>
            `,
            extract: `
                <div class="result-info">
                    <h4>🎧 음원 추출 완료</h4>
                    <p><strong>파일명:</strong> ${result.filename}</p>
                    <p><strong>형식:</strong> ${result.format || 'N/A'}</p>
                    <p><strong>크기:</strong> ${result.file_size || 'N/A'}</p>
                </div>
            `,
            video: `
                <div class="result-info">
                    <h4>🎬 동영상 생성 완료</h4>
                    <p><strong>파일명:</strong> ${result.filename}</p>
                    <p><strong>해상도:</strong> ${result.resolution || 'N/A'}</p>
                    <p><strong>크기:</strong> ${result.file_size || 'N/A'}</p>
                </div>
                ${result.preview_url ? `<video controls style="max-width: 100%; margin-top: 10px;"><source src="${result.preview_url}" type="video/mp4"></video>` : ''}
            `
        };

        return templates[workType] || '<p>작업이 완료되었습니다.</p>';
    }
}

// ===========================================
// 메인 Audio Studio 클래스
// ===========================================
class AudioStudio {
    constructor() {
        this.state = new AudioStudioState();
        this.fileManager = new FileManager(this.state);
        this.workManager = new WorkManager(this.state, this.fileManager);
        
        this.init();
    }

    init() {
        console.log("[Audio Studio] 초기화 완료");
        
        // 전역 함수 등록
        window.extractFromUrl = () => this.fileManager.extractFromUrl();
        window.selectWork = (workType) => this.workManager.selectWork(workType);
        window.executeWork = () => this.workManager.executeWork();
        window.resetStudio = () => this.reset();
        
        // 초기 로고 버튼 상태 설정
        setTimeout(() => {
            updateLogoButtons('none');
        }, 100);
    }

    reset() {
        console.log("[Audio Studio] 스튜디오 리셋");
        
        this.state.reset();
        this.fileManager.updateFilesList();
        this.fileManager.hideWorkSelector();
        
        // UI 초기화
        const sections = ['workSettings', 'progressSection', 'resultSection'];
        sections.forEach(sectionId => {
            const section = document.getElementById(sectionId);
            if (section) section.style.display = 'none';
        });

        // 입력 초기화
        const inputs = ['urlInput', 'imageInput'];
        inputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) input.value = '';
        });

        // 이미지 업로드 영역 초기화
        const imageUploadArea = document.getElementById('imageUploadArea');
        if (imageUploadArea) {
            imageUploadArea.innerHTML = `
                <div class="upload-placeholder">
                    <span class="upload-icon">🖼️</span>
                    <p>이미지를 선택하거나 드래그하세요</p>
                    <p class="file-types">JPG, PNG, BMP, GIF</p>
                </div>
                <input type="file" id="imageInput" accept=".jpg,.jpeg,.png,.bmp,.gif" hidden>
                <button class="btn btn-outline" onclick="document.getElementById('imageInput').click()">
                    이미지 선택
                </button>
            `;
            
            // 이벤트 리스너 재등록
            const newImageInput = document.getElementById('imageInput');
            if (newImageInput) {
                newImageInput.addEventListener('change', (e) => {
                    this.fileManager.handleImageSelect(e);
                });
            }
        }

        // 로고 합성 영역 초기화
        const logoCompositeArea = document.getElementById('logoCompositeArea');
        if (logoCompositeArea) {
            logoCompositeArea.innerHTML = `
                <div class="upload-placeholder">
                    <span class="upload-icon">🏷️</span>
                    <p>로고를 선택하여 배경 이미지에 합성</p>
                    <p class="file-types">PNG (투명배경 권장)</p>
                </div>
                <input type="file" id="logoInput" accept=".png,.jpg,.jpeg" hidden>
                <button class="btn btn-secondary" onclick="document.getElementById('logoInput').click()">
                    🎨 로고 합성하기
                </button>
            `;
            logoCompositeArea.classList.remove('has-logo');
            
            // 로고 이벤트 리스너 재등록
            const newLogoInput = document.getElementById('logoInput');
            if (newLogoInput) {
                newLogoInput.addEventListener('change', (e) => {
                    this.fileManager.handleLogoSelect(e);
                });
            }
        }
    }
}

// ===========================================
// 초기화
// ===========================================
let audioStudio;

// ===========================================
// 전역 함수들 (HTML에서 호출됨)
// ===========================================

// 로고 파일 선택 함수
function selectLogoFile() {
    console.log("[Audio Studio] 로고 파일 선택 시작");
    
    // 이미지가 선택되었는지 확인
    if (!audioStudio || !audioStudio.state || !audioStudio.state.selectedImage) {
        alert('먼저 배경 이미지를 선택해주세요.');
        return;
    }
    
    const logoInput = document.getElementById('logoInput');
    if (!logoInput) {
        console.error("[Audio Studio] 로고 입력 요소를 찾을 수 없습니다");
        return;
    }
    
    // 파일 선택 이벤트 리스너 등록 (중복 방지)
    logoInput.removeEventListener('change', handleLogoFileChange);
    logoInput.addEventListener('change', handleLogoFileChange);
    
    // 파일 선택 다이얼로그 열기
    logoInput.click();
}

// 로고 파일 변경 이벤트 핸들러
function handleLogoFileChange(e) {
    const file = e.target.files[0];
    if (file) {
        console.log("[Audio Studio] 로고 파일 선택됨:", file.name);
        showLogoPreview(file);
        updateLogoButtons('selected');
        
        // 상태에 로고 파일 저장
        if (audioStudio && audioStudio.state) {
            audioStudio.state.selectedLogo = file;
            audioStudio.state.logoApplied = false; // 아직 적용되지 않음
        }
    }
}

// 로고 미리보기 표시
function showLogoPreview(file) {
    const logoPreviewArea = document.getElementById('logoPreviewArea');
    if (!logoPreviewArea) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        logoPreviewArea.innerHTML = `
            <div class="logo-preview">
                <img src="${e.target.result}" alt="로고 미리보기">
                <p class="logo-name">${file.name}</p>
                <p class="logo-status">로고가 선택되었습니다. 합성을 적용하려면 "로고 합성 적용" 버튼을 클릭하세요.</p>
            </div>
        `;
        logoPreviewArea.style.display = 'block';
        logoPreviewArea.classList.remove('has-logo');
    };
    reader.readAsDataURL(file);
}

// 로고 합성 적용 함수
async function applyLogoComposite() {
    console.log("[Audio Studio] 로고 합성 적용 시작");
    
    if (!audioStudio || !audioStudio.state || !audioStudio.state.selectedLogo || !audioStudio.state.selectedImage) {
        alert('로고 파일과 이미지가 모두 선택되어야 합니다.');
        return;
    }
    
    try {
        // 로딩 상태 표시
        const logoPreviewArea = document.getElementById('logoPreviewArea');
        if (logoPreviewArea) {
            logoPreviewArea.innerHTML = `
                <div class="logo-preview">
                    <div class="spinner" style="margin: 0 auto 10px;"></div>
                    <p>로고 합성 처리 중...</p>
                </div>
            `;
        }
        
        // 서버에 로고 합성 요청
        const formData = new FormData();
        formData.append('image', audioStudio.state.selectedImage);
        formData.append('logo', audioStudio.state.selectedLogo);
        formData.append('apply_logo', 'true');
        
        const response = await fetch('/api/music-video/process-image', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log("[Audio Studio] 로고 합성 결과:", result);
        
        if (result.success) {
            // 합성된 이미지 정보 업데이트
            audioStudio.state.selectedImage = result.file_info.filename;
            audioStudio.state.logoApplied = true;
            
            // 미리보기 업데이트
            showLogoCompositeResult(result.file_info);
            updateLogoButtons('applied');
            
            alert('로고 합성이 완료되었습니다!');
        } else {
            throw new Error(result.error || '로고 합성 실패');
        }
    } catch (error) {
        console.error("[Audio Studio] 로고 합성 오류:", error);
        alert('로고 합성 중 오류가 발생했습니다: ' + error.message);
        
        // 오류 시 이전 상태로 복원
        if (audioStudio.state.selectedLogo) {
            showLogoPreview(audioStudio.state.selectedLogo);
            updateLogoButtons('selected');
        }
    }
}

// 로고 합성 결과 표시
function showLogoCompositeResult(fileInfo) {
    const logoPreviewArea = document.getElementById('logoPreviewArea');
    if (!logoPreviewArea) return;
    
    logoPreviewArea.innerHTML = `
        <div class="logo-preview">
            <img src="${fileInfo.preview_url}" alt="로고 합성 결과">
            <p class="logo-name">${fileInfo.original_name}</p>
            <p class="logo-status" style="color: #28a745;">✅ 로고 합성이 적용되었습니다.</p>
        </div>
    `;
    logoPreviewArea.classList.add('has-logo');
}

// 로고 합성 제거 함수
function removeLogoComposite() {
    console.log("[Audio Studio] 로고 합성 제거");
    
    if (audioStudio && audioStudio.state) {
        audioStudio.state.selectedLogo = null;
        audioStudio.state.logoApplied = false;
    }
    
    // UI 초기화
    const logoPreviewArea = document.getElementById('logoPreviewArea');
    if (logoPreviewArea) {
        logoPreviewArea.style.display = 'none';
        logoPreviewArea.classList.remove('has-logo');
    }
    
    const logoInput = document.getElementById('logoInput');
    if (logoInput) {
        logoInput.value = '';
    }
    
    updateLogoButtons('none');
}

// 로고 버튼 상태 업데이트
function updateLogoButtons(state) {
    console.log('[Logo] updateLogoButtons 호출됨, state:', state);
    
    const logoSelectBtn = document.getElementById('logoSelectBtn');
    const logoApplyBtn = document.getElementById('logoApplyBtn');
    const logoRemoveBtn = document.getElementById('logoRemoveBtn');
    const logoHelpText = document.getElementById('logoHelpText');
    
    console.log('[Logo] 요소 찾기 결과:', {
        logoSelectBtn: !!logoSelectBtn,
        logoApplyBtn: !!logoApplyBtn,
        logoRemoveBtn: !!logoRemoveBtn,
        logoHelpText: !!logoHelpText
    });
    
    if (!logoSelectBtn || !logoApplyBtn || !logoRemoveBtn) {
        console.error('[Logo] 로고 버튼 요소들을 찾을 수 없습니다');
        console.error('[Logo] 현재 DOM 상태 확인:', {
            videoSettings: !!document.getElementById('videoSettings'),
            logoSection: !!document.getElementById('logoSection')
        });
        return;
    }
    
    // 이미지가 선택되었는지 확인
    const hasImage = audioStudio && audioStudio.state && audioStudio.state.selectedImage;
    
    switch (state) {
        case 'none':
            logoSelectBtn.style.display = 'inline-block';
            logoApplyBtn.style.display = 'none';
            logoRemoveBtn.style.display = 'none';
            logoSelectBtn.textContent = '🏷️ 로고 선택';
            logoSelectBtn.disabled = !hasImage;
            if (logoHelpText) {
                logoHelpText.style.display = hasImage ? 'none' : 'block';
            }
            break;
        case 'selected':
            logoSelectBtn.style.display = 'inline-block';
            logoApplyBtn.style.display = 'inline-block';
            logoRemoveBtn.style.display = 'inline-block';
            logoSelectBtn.textContent = '🔄 로고 변경';
            logoSelectBtn.disabled = false;
            logoApplyBtn.disabled = !hasImage;
            if (logoHelpText) {
                logoHelpText.style.display = 'none';
            }
            break;
        case 'applied':
            logoSelectBtn.style.display = 'inline-block';
            logoApplyBtn.style.display = 'none';
            logoRemoveBtn.style.display = 'inline-block';
            logoSelectBtn.textContent = '🔄 로고 변경';
            logoSelectBtn.disabled = false;
            if (logoHelpText) {
                logoHelpText.style.display = 'none';
            }
            break;
    }
}

// 이미지 업로드 처리 업데이트 (로고 합성과 연동)
function updateImageUploadState(imageFile) {
    console.log('[Image] updateImageUploadState 호출됨:', imageFile.name);
    
    if (audioStudio && audioStudio.state) {
        audioStudio.state.selectedImage = imageFile;
        console.log('[Image] 이미지 상태 저장 완료');
        
        // 동영상 설정 패널이 표시된 상태에서만 로고 버튼 업데이트
        const videoSettings = document.getElementById('videoSettings');
        const logoSection = document.getElementById('logoSection');
        
        if (videoSettings && videoSettings.style.display !== 'none' && logoSection) {
            console.log('[Image] 동영상 패널이 표시된 상태 - 로고 버튼 업데이트');
            // 로고 버튼 상태 업데이트
            if (audioStudio.state.selectedLogo) {
                console.log('[Image] 로고가 이미 선택됨 - selected 상태로 업데이트');
                updateLogoButtons('selected');
            } else {
                console.log('[Image] 로고 없음 - none 상태로 업데이트');
                updateLogoButtons('none');
            }
        } else {
            console.log('[Image] 동영상 패널이 아직 표시되지 않음 - 로고 버튼 업데이트 건너뜀');
        }
    } else {
        console.error('[Image] audioStudio 또는 state가 없습니다');
    }
}

// URL 추출 함수
async function extractFromUrl() {
    const urlInput = document.getElementById('urlInput');
    if (!urlInput || !urlInput.value.trim()) {
        alert('YouTube URL을 입력해주세요.');
        return;
    }
    
    console.log("[Audio Studio] URL 추출 시작:", urlInput.value);
    
    try {
        const response = await fetch('/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: urlInput.value.trim()
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log("[Audio Studio] URL 추출 응답:", data);
        
        if (data.success) {
            // 작업 대기
            await waitForExtractJob(data.job_id);
        } else {
            alert('URL 추출 실패: ' + data.error);
        }
    } catch (error) {
        console.error("[Audio Studio] URL 추출 오류:", error);
        alert('URL 추출 중 오류가 발생했습니다.');
    }
}

// URL 추출 작업 대기 함수
async function waitForExtractJob(jobId, maxWaitTime = 60000) {
    console.log("[Audio Studio] URL 추출 작업 대기:", jobId);
    
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitTime) {
        try {
            const response = await fetch(`/status/${jobId}`);
            const data = await response.json();
            
            console.log("[Audio Studio] 작업 상태:", data);
            
            if (data.status === 'completed') {
                console.log("[Audio Studio] URL 추출 완료:", data.result);
                
                // 파일 정보를 상태에 추가
                if (audioStudio && audioStudio.state && data.result && data.result.file_info) {
                    const fileInfo = data.result.file_info;
                    const fileId = audioStudio.state.addFile({
                        name: fileInfo.filename || fileInfo.original_name,
                        size: fileInfo.size || 0,
                        type: 'audio/mp3', // URL 추출은 MP3
                        source: 'url'
                    });
                    
                    // 파일 목록 업데이트
                    if (audioStudio.fileManager) {
                        audioStudio.fileManager.updateFilesList();
                        audioStudio.fileManager.showWorkSelector();
                    }
                }
                
                // URL 입력 초기화
                const urlInput = document.getElementById('urlInput');
                if (urlInput) {
                    urlInput.value = '';
                }
                
                return data.result;
            } else if (data.status === 'error') {
                throw new Error(data.message || 'URL 추출 실패');
            }
            
            // 2초 대기 후 재시도
            await new Promise(resolve => setTimeout(resolve, 2000));
        } catch (error) {
            console.error("[Audio Studio] 작업 상태 확인 오류:", error);
            throw error;
        }
    }
    
    throw new Error('URL 추출 시간 초과');
}

// 작업 선택 함수
function selectWork(workType) {
    console.log("[Audio Studio] 작업 선택:", workType);
    
    if (!audioStudio || !audioStudio.workManager) {
        console.error("[Audio Studio] 상태 관리자가 초기화되지 않았습니다");
        return;
    }
    
    console.log("[Audio Studio] workManager.selectWork 호출");
    audioStudio.workManager.selectWork(workType);
}

// 작업 실행 함수
function executeWork() {
    console.log("[Audio Studio] 작업 실행");
    
    if (!audioStudio || !audioStudio.workManager) {
        console.error("[Audio Studio] 상태 관리자가 초기화되지 않았습니다");
        return;
    }
    
    audioStudio.workManager.executeWork();
}

// 스튜디오 초기화 함수
function resetStudio() {
    console.log("[Audio Studio] 스튜디오 초기화");
    
    if (audioStudio && audioStudio.state) {
        audioStudio.state.reset();
    }
    
    if (audioStudio && audioStudio.fileManager) {
        audioStudio.fileManager.updateFilesList();
        audioStudio.fileManager.hideWorkSelector();
    }
    
    // 결과 섹션 숨기기
    const resultSection = document.getElementById('resultSection');
    if (resultSection) {
        resultSection.style.display = 'none';
    }
    
    // 진행 섹션 숨기기
    const progressSection = document.getElementById('progressSection');
    if (progressSection) {
        progressSection.style.display = 'none';
    }
    
    // 작업 설정 섹션 숨기기
    const workSettings = document.getElementById('workSettings');
    if (workSettings) {
        workSettings.style.display = 'none';
    }
}

// 초기화 함수
function initializeAudioStudio() {
    try {
        console.log("[Audio Studio] 초기화 시작");
        console.log("[Audio Studio] DOM 상태:", document.readyState);
        
        // DOM 요소 확인
        const requiredElements = ['fileInput', 'uploadArea', 'urlInput'];
        const missingElements = [];
        
        requiredElements.forEach(id => {
            const element = document.getElementById(id);
            if (!element) {
                missingElements.push(id);
            } else {
                console.log(`[Audio Studio] ${id} 요소 찾음:`, element);
            }
        });
        
        if (missingElements.length > 0) {
            console.error("[Audio Studio] 필수 요소들을 찾을 수 없습니다:", missingElements);
            return;
        }
        
        audioStudio = new AudioStudio();
        console.log("[Audio Studio] 초기화 완료");
        
    } catch (error) {
        console.error("[Audio Studio] 초기화 오류:", error);
    }
}

// DOM 로드 완료 시 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAudioStudio);
} else {
    // 이미 로드된 경우 즉시 초기화
    initializeAudioStudio();
}

// 페이지 로드 완료 후 재시도 (혹시 모를 타이밍 이슈 대비)
window.addEventListener('load', () => {
    if (!audioStudio) {
        console.log("[Audio Studio] window.load에서 재초기화 시도");
        initializeAudioStudio();
    }
});