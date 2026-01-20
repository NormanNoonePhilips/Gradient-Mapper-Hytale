/**
 * Preview component with multiple viewing modes
 */

import { api } from '../api.js';

export class PreviewComponent {
    constructor(selector) {
        this.container = document.querySelector(selector);
        this.mode = 'side-by-side';
        this.previewData = null;
        this.currentImage = null;
        this.currentGradient = null;
        this.originalImageUrl = null;
        this.isGenerating = false;
        this.gridPreviews = [];
        this.gridLoading = false;
        this.gridError = null;
        this.gradientCatalog = null;
        this.gridLimit = 9;
        this.sliderHandlers = null;
        this.render();
    }

    render() {
        const html = `
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold text-gray-900">Preview</h2>

                <div class="btn-group">
                    <button data-mode="side-by-side" class="${this.mode === 'side-by-side' ? 'active' : ''}">
                        Side by Side
                    </button>
                    <button data-mode="slider" class="${this.mode === 'slider' ? 'active' : ''}">
                        Slider
                    </button>
                    <button data-mode="grid" class="${this.mode === 'grid' ? 'active' : ''}">
                        Grid
                    </button>
                </div>
            </div>

            <div id="preview-display" class="min-h-96">
                ${this.renderContent()}
            </div>

            ${this.currentImage && this.currentGradient ? `
                <button id="add-to-queue-btn"
                    class="mt-4 w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition">
                    Add to Queue
                </button>
            ` : ''}
        `;

        this.container.innerHTML = html;
        this.attachListeners();
    }

    renderContent() {
        if (this.mode === 'grid') {
            return this.renderGrid();
        }

        if (this.isGenerating) {
            return `
                <div class="flex flex-col items-center justify-center h-64">
                    <div class="spinner"></div>
                    <p class="mt-4 text-gray-600">Generating preview...</p>
                </div>
            `;
        }

        if (!this.previewData) {
            return `
                <div class="flex flex-col items-center justify-center h-64 text-gray-500">
                    <svg class="h-16 w-16 mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p>Select an image and gradient to preview</p>
                </div>
            `;
        }

        switch (this.mode) {
            case 'side-by-side':
                return this.renderSideBySide();
            case 'slider':
                return this.renderSlider();
            default:
                return '';
        }
    }

    renderSideBySide() {
        return `
            <div class="grid grid-cols-2 gap-4">
                <div class="border border-gray-200 rounded-lg overflow-hidden">
                    <div class="bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700">
                        Original
                    </div>
                    <div class="p-2 bg-white">
                        <img src="${this.originalImageUrl}"
                            alt="Original"
                            class="w-full h-auto">
                    </div>
                </div>
                <div class="border border-gray-200 rounded-lg overflow-hidden">
                    <div class="bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700">
                        With Gradient
                    </div>
                    <div class="p-2 bg-white">
                        <img src="${this.previewData.preview_image}"
                            alt="Preview"
                            class="w-full h-auto">
                    </div>
                </div>
            </div>
            <p class="text-xs text-gray-500 mt-2 text-center">
                Preview: ${this.previewData.dimensions[0]}×${this.previewData.dimensions[1]} •
                Original: ${this.previewData.original_dimensions[0]}×${this.previewData.original_dimensions[1]}
            </p>
        `;
    }

    renderSlider() {
        return `
            <div class="border border-gray-200 rounded-lg overflow-hidden">
                <div class="bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700">
                    Drag to compare
                </div>
                <div class="p-2 bg-white">
                    <div id="slider-container" class="preview-slider-container relative">
                        <img src="${this.previewData.preview_image}"
                            alt="Preview"
                            class="w-full h-auto">
                        <img src="${this.originalImageUrl}"
                            alt="Original"
                            id="slider-original"
                            class="w-full h-auto absolute top-0 left-0"
                            style="clip-path: inset(0 50% 0 0);">
                        <div id="slider-divider" class="preview-slider" style="left: 50%;"></div>
                    </div>
                </div>
            </div>
            <p class="text-xs text-gray-500 mt-2 text-center">
                Preview: ${this.previewData.dimensions[0]}×${this.previewData.dimensions[1]} •
                Original: ${this.previewData.original_dimensions[0]}×${this.previewData.original_dimensions[1]}
            </p>
        `;
    }

    renderGrid() {
        if (!this.currentImage || !this.currentGradient) {
            return `
                <div class="flex flex-col items-center justify-center h-64 text-gray-500">
                    <svg class="h-16 w-16 mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p>Select an image and gradient to preview</p>
                </div>
            `;
        }

        if (this.gridLoading) {
            return `
                <div class="flex flex-col items-center justify-center h-64">
                    <div class="spinner"></div>
                    <p class="mt-4 text-gray-600">Building grid...</p>
                </div>
            `;
        }

        if (this.gridError) {
            return `
                <div class="flex flex-col items-center justify-center h-64 text-red-500">
                    <svg class="h-16 w-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p>${this.gridError}</p>
                </div>
            `;
        }

        if (!this.gridPreviews.length) {
            return `
                <div class="flex flex-col items-center justify-center h-64 text-gray-500">
                    <p>No previews available</p>
                </div>
            `;
        }

        return `
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                ${this.gridPreviews.map(item => {
                    const isSelected = this.currentGradient
                        && item.gradient.relative_path === this.currentGradient.path;
                    return `
                        <button
                            class="group text-left border rounded-lg overflow-hidden ${isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200 hover:border-gray-300'}"
                            data-grid-gradient="true"
                            data-gradient-path="${item.gradient.relative_path}"
                            data-gradient-name="${item.gradient.name}">
                            <div class="bg-gray-100 px-3 py-2 text-xs font-medium text-gray-700 truncate">
                                ${item.gradient.name}
                            </div>
                            <div class="p-2 bg-white">
                                <img src="${item.preview.preview_image}"
                                    alt="${item.gradient.name}"
                                    class="w-full h-auto">
                            </div>
                        </button>
                    `;
                }).join('')}
            </div>
        `;
    }

    attachListeners() {
        this.container.querySelectorAll('[data-mode]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.mode = btn.dataset.mode;
                this.render();

                if (this.currentImage && this.currentGradient) {
                    this.updatePreview(this.currentImage, this.currentGradient);
                } else if (this.mode === 'slider' && this.previewData) {
                    this.enableSlider();
                }
            });
        });

        const addToQueueBtn = this.container.querySelector('#add-to-queue-btn');
        if (addToQueueBtn) {
            addToQueueBtn.addEventListener('click', () => {
                this.addToQueue();
            });
        }

        if (this.mode === 'slider' && this.previewData) {
            this.enableSlider();
        }

        this.container.querySelectorAll('[data-grid-gradient="true"]').forEach(item => {
            item.addEventListener('click', () => {
                this.selectGridGradient(
                    item.dataset.gradientPath,
                    item.dataset.gradientName
                );
            });
        });
    }

    enableSlider() {
        const sliderContainer = this.container.querySelector('#slider-container');
        const sliderDivider = this.container.querySelector('#slider-divider');
        const originalImg = this.container.querySelector('#slider-original');

        if (!sliderContainer || !sliderDivider || !originalImg) return;

        if (this.sliderHandlers) {
            const {
                divider,
                onMouseDown,
                onMouseMove,
                onMouseUp,
                onTouchStart,
                onTouchMove,
                onTouchEnd
            } = this.sliderHandlers;

            divider.removeEventListener('mousedown', onMouseDown);
            divider.removeEventListener('touchstart', onTouchStart);
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            document.removeEventListener('touchmove', onTouchMove);
            document.removeEventListener('touchend', onTouchEnd);
            this.sliderHandlers = null;
        }

        let isDragging = false;

        const updateSliderPosition = (clientX) => {
            const rect = sliderContainer.getBoundingClientRect();
            const x = clientX - rect.left;
            const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));

            sliderDivider.style.left = `${percentage}%`;
            originalImg.style.clipPath = `inset(0 ${100 - percentage}% 0 0)`;
        };

        const onMouseDown = (e) => {
            isDragging = true;
            e.preventDefault();
        };

        const onMouseMove = (e) => {
            if (isDragging) {
                updateSliderPosition(e.clientX);
            }
        };

        const onMouseUp = () => {
            isDragging = false;
        };

        const onTouchStart = (e) => {
            isDragging = true;
            e.preventDefault();
        };

        const onTouchMove = (e) => {
            if (isDragging) {
                const touch = e.touches[0];
                if (touch) {
                    updateSliderPosition(touch.clientX);
                }
            }
        };

        const onTouchEnd = () => {
            isDragging = false;
        };

        sliderDivider.addEventListener('mousedown', onMouseDown);
        sliderDivider.addEventListener('touchstart', onTouchStart);
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        document.addEventListener('touchmove', onTouchMove);
        document.addEventListener('touchend', onTouchEnd);

        this.sliderHandlers = {
            divider: sliderDivider,
            onMouseDown,
            onMouseMove,
            onMouseUp,
            onTouchStart,
            onTouchMove,
            onTouchEnd
        };
    }

    async updatePreview(imageName, gradientData) {
        this.currentImage = imageName;
        this.currentGradient = gradientData;
        if (this.mode === 'grid') {
            this.previewData = null;
            this.isGenerating = false;
            await this.updateGridPreviews();
            return;
        }

        this.isGenerating = true;
        this.previewData = null;
        this.render();

        try {
            this.originalImageUrl = `/api/images/${imageName}`;

            const preview = await api.generatePreview(imageName, gradientData.path);

            this.previewData = preview;
            this.isGenerating = false;
            this.render();

            if (this.mode === 'slider') {
                this.enableSlider();
            }

        } catch (error) {
            this.isGenerating = false;
            this.previewData = null;
            this.render();
            this.showError(`Failed to generate preview: ${error.message}`);
        }
    }

    async updateGridPreviews() {
        if (!this.currentImage) {
            this.gridPreviews = [];
            this.gridError = null;
            this.gridLoading = false;
            this.render();
            return;
        }

        this.gridLoading = true;
        this.gridError = null;
        this.render();

        try {
            const catalog = await this.ensureGradientCatalog();
            const gradients = this.getGradientsForGrid(catalog);

            if (!gradients.length) {
                this.gridPreviews = [];
                this.gridError = 'No gradients available';
                this.gridLoading = false;
                this.render();
                return;
            }

            const results = await Promise.allSettled(
                gradients.map(gradient =>
                    api.generatePreview(this.currentImage, gradient.relative_path, 300)
                )
            );

            this.gridPreviews = results
                .map((result, index) => {
                    if (result.status !== 'fulfilled') return null;
                    return {
                        gradient: gradients[index],
                        preview: result.value
                    };
                })
                .filter(Boolean);

            if (!this.gridPreviews.length) {
                this.gridError = 'No previews available';
            }
        } catch (error) {
            this.gridPreviews = [];
            this.gridError = error.message || 'Failed to load previews';
        } finally {
            this.gridLoading = false;
            this.render();
        }
    }

    async ensureGradientCatalog() {
        if (this.gradientCatalog) {
            return this.gradientCatalog;
        }

        this.gradientCatalog = await api.listGradients();
        return this.gradientCatalog;
    }

    getGradientsForGrid(catalog) {
        const selectedPath = this.currentGradient?.path;
        const category = this.getCategoryFromPath(selectedPath);
        let gradients = [];

        if (category && catalog.categories[category]) {
            gradients = catalog.categories[category];
        } else {
            Object.values(catalog.categories).forEach(categoryGradients => {
                gradients.push(...categoryGradients);
            });
        }

        if (selectedPath) {
            const selected = gradients.find(
                gradient => gradient.relative_path === selectedPath
            );
            if (selected) {
                gradients = [
                    selected,
                    ...gradients.filter(
                        gradient => gradient.relative_path !== selectedPath
                    )
                ];
            }
        }

        return gradients.slice(0, this.gridLimit);
    }

    getCategoryFromPath(path) {
        if (!path) return null;
        const parts = path.split('/');
        if (parts.length > 1) {
            return parts[0];
        }
        return 'Uncategorized';
    }

    selectGridGradient(gradientPath, gradientName) {
        const selection = { path: gradientPath, name: gradientName };
        this.currentGradient = selection;
        document.dispatchEvent(new CustomEvent('gradient-selected', {
            detail: selection
        }));
    }

    addToQueue() {
        if (!this.currentImage || !this.currentGradient) return;

        document.dispatchEvent(new CustomEvent('add-to-queue', {
            detail: {
                image_name: this.currentImage,
                gradient_path: this.currentGradient.path
            }
        }));
    }

    showError(message) {
        const displayContainer = this.container.querySelector('#preview-display');
        if (displayContainer) {
            displayContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center h-64 text-red-500">
                    <svg class="h-16 w-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p>${message}</p>
                </div>
            `;
        }
    }
}
