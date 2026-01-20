/**
 * File upload component with drag-and-drop support
 */

import { api } from '../api.js';
import { escapeHtml } from '../utils/escape.js';

export class UploadComponent {
    constructor(selector) {
        this.container = document.querySelector(selector);
        this.files = [];
        this.selectedImages = [];
        this.selectedImage = null;
        this.render();
    }

    render() {
        const html = `
            <h2 class="text-xl font-semibold mb-4 text-gray-900">Upload Images</h2>

            <div id="drop-zone"
                class="drop-zone border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition">
                <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <p class="mt-2 text-sm text-gray-600">Drag & drop images here</p>
                <p class="text-xs text-gray-400 mt-1">or click to browse</p>
                <input type="file" multiple accept="image/*" class="hidden" id="file-input">
            </div>

            <div id="file-list" class="mt-4">
            </div>
        `;

        this.container.innerHTML = html;
        this.attachListeners();
    }

    attachListeners() {
        const dropZone = this.container.querySelector('#drop-zone');
        const fileInput = this.container.querySelector('#file-input');

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');

            const files = Array.from(e.dataTransfer.files);
            await this.uploadFiles(files);
        });

        dropZone.addEventListener('click', (e) => {
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });

        fileInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files);
            await this.uploadFiles(files);
            fileInput.value = '';
        });
    }

    async uploadFiles(files) {
        if (files.length === 0) return;

        const dropZone = this.container.querySelector('#drop-zone');
        dropZone.innerHTML = `
            <div class="spinner mx-auto"></div>
            <p class="mt-2 text-sm text-gray-600">Uploading ${files.length} file(s)...</p>
        `;

        try {
            const result = await api.uploadImages(files);

            this.files = result.files;

            this.render();
            this.renderFileList();

            if (this.files.length > 0) {
                this.selectedImages = [this.files[0].filename];
                this.selectedImage = this.files[0].filename;
                this.renderFileList();
                this.dispatchSelection();
            }

            this.showMessage(`Successfully uploaded ${this.files.length} file(s)`, 'success');

        } catch (error) {
            this.render();
            this.showMessage(`Upload failed: ${error.message}`, 'error');
        }
    }

    renderFileList() {
        const fileListContainer = this.container.querySelector('#file-list');

        if (this.files.length === 0) {
            fileListContainer.innerHTML = `
                <p class="text-sm text-gray-500 text-center">No images uploaded yet</p>
            `;
            return;
        }

        const filesHtml = this.files.map(file => {
            const isSelected = this.selectedImages.includes(file.filename);
            const isPrimary = file.filename === this.selectedImage;
            return `
                <div class="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer ${isSelected ? 'bg-blue-50 border-l-4 border-blue-500' : ''}"
                    data-filename="${escapeHtml(file.filename)}">
                    <div class="flex items-center gap-2 flex-1 min-w-0">
                        <input type="checkbox" class="h-4 w-4 text-blue-600"
                            data-filename="${escapeHtml(file.filename)}" ${isSelected ? 'checked' : ''}>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-900 truncate">${escapeHtml(file.filename)}</p>
                            <p class="text-xs text-gray-500">${this.formatFileSize(file.size)} • ${file.dimensions[0]}×${file.dimensions[1]}</p>
                        </div>
                    </div>
                    ${isPrimary ? `
                        <svg class="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                    ` : ''}
                </div>
            `;
        }).join('');

        fileListContainer.innerHTML = `
            <div class="space-y-1 max-h-64 overflow-y-auto custom-scrollbar">
                ${filesHtml}
            </div>
        `;

        fileListContainer.querySelectorAll('[data-filename]').forEach(item => {
            item.addEventListener('click', (event) => {
                if (event.target.matches('input[type="checkbox"]')) {
                    return;
                }
                this.setPrimaryImage(item.dataset.filename);
            });
        });

        fileListContainer.querySelectorAll('input[type="checkbox"]').forEach(input => {
            input.addEventListener('change', (event) => {
                event.stopPropagation();
                this.toggleImageSelection(input.dataset.filename);
            });
        });
    }

    setPrimaryImage(filename) {
        if (!this.selectedImages.includes(filename)) {
            this.selectedImages.push(filename);
        }
        this.selectedImage = filename;
        this.renderFileList();
        this.dispatchSelection();
    }

    toggleImageSelection(filename) {
        const index = this.selectedImages.indexOf(filename);
        if (index === -1) {
            this.selectedImages.push(filename);
            this.selectedImage = filename;
        } else {
            this.selectedImages.splice(index, 1);
            if (this.selectedImage === filename) {
                this.selectedImage = this.selectedImages[0] || null;
            }
        }
        this.renderFileList();
        this.dispatchSelection();
    }

    dispatchSelection() {
        document.dispatchEvent(new CustomEvent('image-selected', {
            detail: {
                primary: this.selectedImage,
                selected: [...this.selectedImages]
            }
        }));
    }

    formatFileSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    showMessage(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg fade-in z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}
