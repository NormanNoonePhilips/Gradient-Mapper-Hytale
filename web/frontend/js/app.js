/**
 * Main application orchestrator for Gradient Mapper
 */

import { UploadComponent } from './components/upload.js';
import { GradientSelector } from './components/gradient-selector.js';
import { PreviewComponent } from './components/preview.js';
import { QueueComponent } from './components/queue.js';
import { ProgressTracker } from './components/progress.js';
import { WebSocketManager } from './utils/websocket.js';

class GradientMapperApp {
    constructor() {
        this.state = {
            selectedImage: null,
            selectedImages: [],
            selectedGradient: null
        };

        this.ws = new WebSocketManager();
        this.initComponents();
        this.attachEventListeners();
        this.updateStatusIndicator();
    }

    initComponents() {
        this.upload = new UploadComponent('#upload-section');
        this.gradients = new GradientSelector('#gradient-section');
        this.preview = new PreviewComponent('#preview-section');
        this.queue = new QueueComponent('#queue-section');
        this.progress = new ProgressTracker('#progress-section');
    }

    attachEventListeners() {
        document.addEventListener('image-selected', (e) => {
            if (typeof e.detail === 'string') {
                this.state.selectedImage = e.detail;
                this.state.selectedImages = [e.detail];
            } else {
                this.state.selectedImage = e.detail.primary || null;
                this.state.selectedImages = e.detail.selected || [];
            }
            this.updatePreview();
        });

        document.addEventListener('gradient-selected', (e) => {
            this.state.selectedGradient = e.detail;
            this.updatePreview();
        });

        document.addEventListener('add-to-queue', (e) => {
            const images = this.state.selectedImages.length
                ? this.state.selectedImages
                : [e.detail.image_name];
            images.forEach(image => {
                this.queue.addToQueue({
                    image_name: image,
                    gradient_path: e.detail.gradient_path
                });
            });
        });

        document.addEventListener('job-created', (e) => {
            this.handleJobCreated(e.detail);
        });

        this.ws.on('connected', () => {
            this.updateStatusIndicator('connected');
        });

        this.ws.on('disconnected', () => {
            this.updateStatusIndicator('disconnected');
        });

        this.ws.on('progress', (data) => {
            this.progress.update(data);
        });

        this.ws.on('complete', (data) => {
            this.progress.complete(data);
        });

        this.ws.on('error', (data) => {
            this.progress.error(data);
        });

        this.ws.on('cancelled', (data) => {
            this.progress.cancelled(data);
        });
    }

    updatePreview() {
        if (this.state.selectedImage && this.state.selectedGradient) {
            this.preview.updatePreview(
                this.state.selectedImage,
                this.state.selectedGradient
            );
        }
    }

    handleJobCreated(jobResponse) {
        this.ws.subscribeToJob(jobResponse.job_id);
        this.progress.startJob(jobResponse.job_id, jobResponse.task_count);
    }

    updateStatusIndicator(status = 'unknown') {
        const indicator = document.getElementById('status-indicator');
        if (!indicator) return;

        let html = '';
        if (status === 'connected') {
            html = `
                <div class="flex items-center">
                    <span class="h-2 w-2 bg-green-500 rounded-full mr-2"></span>
                    <span>Connected</span>
                </div>
            `;
        } else if (status === 'disconnected') {
            html = `
                <div class="flex items-center">
                    <span class="h-2 w-2 bg-red-500 rounded-full mr-2"></span>
                    <span>Disconnected</span>
                </div>
            `;
        } else {
            html = `
                <div class="flex items-center">
                    <span class="h-2 w-2 bg-gray-400 rounded-full mr-2"></span>
                    <span>Connecting...</span>
                </div>
            `;
        }

        indicator.innerHTML = html;
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new GradientMapperApp();
    });
} else {
    window.app = new GradientMapperApp();
}
