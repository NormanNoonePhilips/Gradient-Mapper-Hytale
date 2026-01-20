/**
 * Progress tracker component for batch processing jobs
 */

import { escapeHtml } from '../utils/escape.js';

export class ProgressTracker {
    constructor(selector) {
        this.container = document.querySelector(selector);
        this.currentJob = null;
        this.hide();
    }

    show() {
        this.container.style.display = 'block';
    }

    hide() {
        this.container.style.display = 'none';
    }

    startJob(jobId, taskCount) {
        this.currentJob = {
            job_id: jobId,
            total: taskCount,
            current: 0,
            status: 'processing',
            message: 'Starting...'
        };

        this.show();
        this.render();
    }

    update(data) {
        if (!this.currentJob || data.job_id !== this.currentJob.job_id) {
            return;
        }

        Object.assign(this.currentJob, {
            current: data.current || this.currentJob.current,
            total: data.total || this.currentJob.total,
            status: data.status || this.currentJob.status,
            message: data.message || this.currentJob.message
        });

        this.render();
    }

    complete(data) {
        if (!this.currentJob || data.job_id !== this.currentJob.job_id) {
            return;
        }

        this.currentJob.status = 'completed';
        this.currentJob.current = this.currentJob.total;
        this.currentJob.download_url = data.download_url;

        this.render();

        if (data.download_url) {
            setTimeout(() => {
                this.downloadResults(data.download_url);
            }, 500);
        }
    }

    error(data) {
        if (!this.currentJob || data.job_id !== this.currentJob.job_id) {
            return;
        }

        this.currentJob.status = 'failed';
        this.currentJob.message = data.message || 'Processing failed';

        this.render();
    }

    render() {
        if (!this.currentJob) {
            this.hide();
            return;
        }

        const percentage = this.currentJob.total > 0
            ? Math.round((this.currentJob.current / this.currentJob.total) * 100)
            : 0;

        const isCompleted = this.currentJob.status === 'completed';
        const isFailed = this.currentJob.status === 'failed';
        const isCancelled = this.currentJob.status === 'cancelled';

        const html = `
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold text-gray-900">
                    ${isCompleted ? 'Processing Complete' : isFailed ? 'Processing Failed' : isCancelled ? 'Processing Cancelled' : 'Processing...'}
                </h2>
                <button id="close-progress-btn" class="text-gray-500 hover:text-gray-700">
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div class="mb-4">
                <div class="flex justify-between text-sm text-gray-600 mb-2">
                    <span>${this.currentJob.current} / ${this.currentJob.total} tasks</span>
                    <span>${percentage}%</span>
                </div>
                <div class="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div class="progress-bar h-full ${isFailed ? 'bg-red-500' : isCompleted ? 'bg-green-500' : isCancelled ? 'bg-yellow-500' : 'bg-blue-500'}"
                        style="width: ${percentage}%">
                    </div>
                </div>
            </div>

            <div class="mb-4">
                <p class="text-sm text-gray-700">
                    ${isCompleted ? '✓' : isFailed ? '✗' : isCancelled ? '•' : '⋯'} ${escapeHtml(this.currentJob.message)}
                </p>
            </div>

            ${isCompleted && this.currentJob.download_url ? `
                <button id="download-btn"
                    class="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition">
                    <svg class="inline h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download Results (ZIP)
                </button>
            ` : ''}

            ${isFailed ? `
                <div class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p class="text-sm text-red-700">
                        Some tasks failed. Check console for details.
                    </p>
                </div>
            ` : ''}
        `;

        this.container.innerHTML = html;
        this.attachListeners();
    }

    cancelled(data) {
        if (!this.currentJob || data.job_id !== this.currentJob.job_id) {
            return;
        }

        this.currentJob.status = 'cancelled';
        this.currentJob.message = data.message || 'Cancelled';
        this.render();
    }

    attachListeners() {
        const closeBtn = this.container.querySelector('#close-progress-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hide();
            });
        }

        const downloadBtn = this.container.querySelector('#download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                if (this.currentJob && this.currentJob.download_url) {
                    this.downloadResults(this.currentJob.download_url);
                }
            });
        }
    }

    downloadResults(downloadUrl) {
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `gradient_mapper_${this.currentJob.job_id.slice(0, 8)}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showMessage('Download started', 'success');
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
