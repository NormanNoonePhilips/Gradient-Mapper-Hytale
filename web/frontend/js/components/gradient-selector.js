/**
 * Gradient selector component with categories and search
 */

import { api } from '../api.js';
import { escapeHtml } from '../utils/escape.js';

export class GradientSelector {
    constructor(selector) {
        this.container = document.querySelector(selector);
        this.gradients = null;
        this.selectedCategory = null;
        this.selectedGradient = null;
        this.searchQuery = '';
        this.init();
    }

    async init() {
        this.container.innerHTML = `
            <h2 class="text-xl font-semibold mb-4 text-gray-900">Select Gradient</h2>
            <div class="flex items-center justify-center py-8">
                <div class="spinner"></div>
                <span class="ml-2 text-gray-600">Loading gradients...</span>
            </div>
        `;

        try {
            this.gradients = await api.listGradients();
            this.render();
        } catch (error) {
            this.container.innerHTML = `
                <h2 class="text-xl font-semibold mb-4 text-gray-900">Select Gradient</h2>
                <p class="text-red-500 text-sm">Error loading gradients: ${escapeHtml(error.message)}</p>
            `;
        }
    }

    render() {
        const html = `
            <h2 class="text-xl font-semibold mb-4 text-gray-900">Select Gradient</h2>

            <input type="text"
                id="gradient-search"
                class="w-full p-2 border border-gray-300 rounded-lg mb-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Search gradients..."
                value="${this.searchQuery}">

            <select id="category-select"
                class="w-full p-2 border border-gray-300 rounded-lg mb-4 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                <option value="">All Categories (${this.gradients.total_count})</option>
                ${this.renderCategories()}
            </select>

            <div class="gradient-list max-h-96 overflow-y-auto custom-scrollbar">
                ${this.renderGradientList()}
            </div>
        `;

        this.container.innerHTML = html;
        this.attachListeners();
    }

    renderCategories() {
        return Object.entries(this.gradients.categories)
            .map(([category, gradients]) => `
                <option value="${escapeHtml(category)}" ${this.selectedCategory === category ? 'selected' : ''}>
                    ${escapeHtml(category.replace(/_/g, ' '))} (${gradients.length})
                </option>
            `)
            .join('');
    }

    renderGradientList() {
        const filteredGradients = this.getFilteredGradients();

        if (filteredGradients.length === 0) {
            return `
                <p class="text-sm text-gray-500 text-center py-4">
                    No gradients found
                </p>
            `;
        }

        const gradientsByCategory = {};
        filteredGradients.forEach(gradient => {
            if (!gradientsByCategory[gradient.category]) {
                gradientsByCategory[gradient.category] = [];
            }
            gradientsByCategory[gradient.category].push(gradient);
        });

        return Object.entries(gradientsByCategory)
            .map(([category, gradients]) => `
                <div class="mb-4">
                    ${!this.selectedCategory ? `
                        <h3 class="text-sm font-semibold text-gray-700 mb-2">
                            ${escapeHtml(category.replace(/_/g, ' '))}
                        </h3>
                    ` : ''}
                    <div class="space-y-2">
                        ${gradients.map(gradient => this.renderGradientItem(gradient)).join('')}
                    </div>
                </div>
            `)
            .join('');
    }

    renderGradientItem(gradient) {
        const isSelected = this.selectedGradient === gradient.relative_path;

        return `
            <div class="gradient-item p-2 rounded border ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'} cursor-pointer transition"
                data-gradient-path="${escapeHtml(gradient.relative_path)}"
                data-gradient-name="${escapeHtml(gradient.name)}">
                <div class="flex items-center">
                    <div class="flex-1 mr-2">
                        <img src="${gradient.thumbnail}"
                            alt="${escapeHtml(gradient.name)}"
                            class="gradient-thumbnail w-full ${isSelected ? 'selected' : ''}"
                            style="height: 20px;">
                    </div>
                    ${isSelected ? `
                        <svg class="h-5 w-5 text-blue-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                    ` : ''}
                </div>
                <p class="text-xs text-gray-600 mt-1 truncate">${escapeHtml(gradient.name)}</p>
            </div>
        `;
    }

    getFilteredGradients() {
        let gradients = [];

        if (this.selectedCategory) {
            gradients = this.gradients.categories[this.selectedCategory] || [];
        } else {
            Object.values(this.gradients.categories).forEach(categoryGradients => {
                gradients.push(...categoryGradients);
            });
        }

        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            gradients = gradients.filter(g =>
                g.name.toLowerCase().includes(query) ||
                g.category.toLowerCase().includes(query)
            );
        }

        return gradients;
    }

    attachListeners() {
        const searchInput = this.container.querySelector('#gradient-search');
        searchInput.addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            this.renderGradientListOnly();
        });

        const categorySelect = this.container.querySelector('#category-select');
        categorySelect.addEventListener('change', (e) => {
            this.selectedCategory = e.target.value || null;
            this.renderGradientListOnly();
        });

        this.container.querySelectorAll('.gradient-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectGradient(
                    item.dataset.gradientPath,
                    item.dataset.gradientName
                );
            });
        });
    }

    renderGradientListOnly() {
        const listContainer = this.container.querySelector('.gradient-list');
        listContainer.innerHTML = this.renderGradientList();

        this.container.querySelectorAll('.gradient-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectGradient(
                    item.dataset.gradientPath,
                    item.dataset.gradientName
                );
            });
        });
    }

    selectGradient(gradientPath, gradientName) {
        this.selectedGradient = gradientPath;
        this.renderGradientListOnly();

        document.dispatchEvent(new CustomEvent('gradient-selected', {
            detail: {
                path: gradientPath,
                name: gradientName
            }
        }));
    }
}
