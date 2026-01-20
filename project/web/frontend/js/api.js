/**
 * API client for Gradient Mapper backend
 */

const baseUrl = '/api';

export const api = {
    /**
     * Upload images to the server
     * @param {FileList|File[]} files - Files to upload
     * @returns {Promise<Object>} Upload response
     */
    async uploadImages(files) {
        const formData = new FormData();

        for (const file of files) {
            formData.append('files', file);
        }

        const response = await fetch(`${baseUrl}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return response.json();
    },

    /**
     * Get list of uploaded images
     * @returns {Promise<Object>} List of images
     */
    async listImages() {
        const response = await fetch(`${baseUrl}/images`);

        if (!response.ok) {
            throw new Error('Failed to list images');
        }

        return response.json();
    },

    /**
     * Get catalog of all gradients
     * @returns {Promise<Object>} Gradient catalog
     */
    async listGradients() {
        const response = await fetch(`${baseUrl}/gradients`);

        if (!response.ok) {
            throw new Error('Failed to list gradients');
        }

        return response.json();
    },

    /**
     * Generate a preview of gradient-mapped image
     * @param {string} imageName - Image filename
     * @param {string} gradientPath - Gradient relative path
     * @param {number} maxDimension - Max preview dimension
     * @returns {Promise<Object>} Preview response
     */
    async generatePreview(imageName, gradientPath, maxDimension = 400) {
        const response = await fetch(`${baseUrl}/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_name: imageName,
                gradient_path: gradientPath,
                max_dimension: maxDimension
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Preview generation failed');
        }

        return response.json();
    },

    /**
     * Create a batch processing job
     * @param {Array} tasks - Array of {image_name, gradient_path} objects
     * @param {Object} options - Processing options
     * @returns {Promise<Object>} Job response
     */
    async createJob(tasks, options = {}) {
        const payload = {
            tasks: tasks,
            output_format: options.output_format || 'png',
            quality: options.quality || 95,
            prefix: options.prefix || null,
            suffix: options.suffix || null
        };

        const response = await fetch(`${baseUrl}/jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Job creation failed');
        }

        return response.json();
    },

    /**
     * Get status of a job
     * @param {string} jobId - Job ID
     * @returns {Promise<Object>} Job status
     */
    async getJobStatus(jobId) {
        const response = await fetch(`${baseUrl}/jobs/${jobId}`);

        if (!response.ok) {
            throw new Error('Failed to get job status');
        }

        return response.json();
    },

    /**
     * Get download URL for job results
     * @param {string} jobId - Job ID
     * @returns {string} Download URL
     */
    getDownloadUrl(jobId) {
        return `${baseUrl}/jobs/${jobId}/download`;
    },

    /**
     * Cancel a job
     * @param {string} jobId - Job ID
     * @returns {Promise<Object>} Cancellation response
     */
    async cancelJob(jobId) {
        const response = await fetch(`${baseUrl}/jobs/${jobId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to cancel job');
        }

        return response.json();
    }
};
