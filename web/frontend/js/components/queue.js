/**
 * Batch queue component
 */

import { api } from '../api.js';
import { escapeHtml } from '../utils/escape.js';

export class QueueComponent {
    constructor(selector) {
        this.container = document.querySelector(selector);
        this.queue = [];
        this.render();
    }

    render() {
        const html = `
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold text-gray-900">Batch Queue</h2>
                ${this.queue.length > 0 ? `
                    <button id="clear-queue-btn"
                        class="text-sm text-red-600 hover:text-red-700">
                        Clear All
                    </button>
                ` : ''}
            </div>

            <div id="queue-list" class="min-h-32">
                ${this.renderQueueList()}
            </div>

            <div class="mt-4 space-y-2">
                <button id="process-all-btn"
                    class="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition disabled:bg-gray-300 disabled:cursor-not-allowed"
                    ${this.queue.length === 0 ? 'disabled' : ''}>
                    Process All (${this.queue.length})
                </button>
            </div>

            ${this.queue.length > 0 ? `
                <div class="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <h3 class="text-sm font-medium text-gray-700 mb-2">Options</h3>
                    <div class="space-y-2">
                        <div>
                            <label class="text-xs text-gray-600">Output Format</label>
                            <select id="output-format" class="w-full mt-1 p-1.5 text-sm border border-gray-300 rounded">
                                <option value="png">PNG</option>
                                <option value="jpeg">JPEG</option>
                                <option value="webp">WebP</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs text-gray-600">Quality (for JPEG/WebP)</label>
                            <input type="range" id="quality-slider" min="1" max="100" value="95" class="w-full">
                            <span id="quality-value" class="text-xs text-gray-500">95</span>
                        </div>
                    </div>
                </div>
            ` : ''}
        `;

        this.container.innerHTML = html;
        this.attachListeners();
    }

    renderQueueList() {
        if (this.queue.length === 0) {
            return `
                <div class="flex flex-col items-center justify-center py-8 text-gray-500">
                    <svg class="h-12 w-12 mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p class="text-sm">Queue is empty</p>
                    <p class="text-xs mt-1">Add items from the preview to start</p>
                </div>
            `;
        }

        return `
            <div class="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
                ${this.queue.map((item, index) => `
                    <div class="queue-item flex items-center justify-between p-2 border border-gray-200 rounded hover:bg-gray-50"
                        data-index="${index}">
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-900 truncate">
                                ${escapeHtml(this.getImageName(item.image_name))}
                            </p>
                            <p class="text-xs text-gray-500 truncate">
                                → ${escapeHtml(this.getGradientName(item.gradient_path))}
                            </p>
                        </div>
                        <button class="remove-item-btn ml-2 text-red-500 hover:text-red-700"
                            data-index="${index}">
                            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                            </svg>
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    attachListeners() {
        const processBtn = this.container.querySelector('#process-all-btn');
        if (processBtn) {
            processBtn.addEventListener('click', () => this.processAll());
        }

        const clearBtn = this.container.querySelector('#clear-queue-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.queue = [];
                this.render();
            });
        }

        this.container.querySelectorAll('.remove-item-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                this.removeItem(index);
            });
        });

        const qualitySlider = this.container.querySelector('#quality-slider');
        const qualityValue = this.container.querySelector('#quality-value');
        if (qualitySlider && qualityValue) {
            qualitySlider.addEventListener('input', (e) => {
                qualityValue.textContent = e.target.value;
            });
        }
    }

    addToQueue(task) {
        const exists = this.queue.some(item =>
            item.image_name === task.image_name &&
            item.gradient_path === task.gradient_path
        );

        if (exists) {
            this.showMessage('This combination is already in the queue', 'info');
            return;
        }

        this.queue.push(task);
        this.render();
        this.showMessage('Added to queue', 'success');
    }

    removeItem(index) {
        this.queue.splice(index, 1);
        this.render();
    }

    async processAll() {
        if (this.queue.length === 0) return;

        const formatSelect = this.container.querySelector('#output-format');
        const qualitySlider = this.container.querySelector('#quality-slider');

        const options = {
            output_format: formatSelect ? formatSelect.value : 'png',
            quality: qualitySlider ? parseInt(qualitySlider.value) : 95
        };

        try {
            const response = await api.createJob(this.queue, options);

            this.queue = [];
            this.render();

            document.dispatchEvent(new CustomEvent('job-created', {
                detail: response
            }));

            this.showMessage(`Processing started: ${response.task_count} tasks`, 'success');

        } catch (error) {
            this.showMessage(`Failed to start processing: ${error.message}`, 'error');
        }
    }

    getImageName(filename) {
        return filename.split('/').pop();
    }

    getGradientName(gradientPath) {
        const parts = gradientPath.split('/');
        return parts[parts.length - 1];
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
