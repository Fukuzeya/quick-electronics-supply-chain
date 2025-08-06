

// Global JavaScript for Supply Chain Management

// Configuration
const CONFIG = {
    REFRESH_INTERVAL: 30000, // 30 seconds
    API_BASE_URL: '/api/',
    WEBSOCKET_URL: 'ws://localhost:8000/ws/',
    ENABLE_REAL_TIME: true
};

// Utility Functions
const Utils = {
    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    // Format date
    formatDate: function(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : 'info'}-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    },

    // CSRF token helper
    getCsrfToken: function() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
};

// Real-time Updates Manager
const RealTimeManager = {
    websocket: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,

    init: function() {
        if (!CONFIG.ENABLE_REAL_TIME) return;
        
        this.connect();
        this.setupHeartbeat();
    },

    connect: function() {
        if (!window.WebSocket) {
            console.warn('WebSocket not supported');
            return;
        }

        try {
            this.websocket = new WebSocket(CONFIG.WEBSOCKET_URL);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                Utils.showNotification('Real-time updates enabled', 'success');
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.websocket.onclose = () => {
                console.log('WebSocket closed');
                this.attemptReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('WebSocket connection failed:', error);
        }
    },

    handleMessage: function(data) {
        switch (data.type) {
            case 'order_update':
                this.handleOrderUpdate(data);
                break;
            case 'inventory_update':
                this.handleInventoryUpdate(data);
                break;
            case 'tracking_update':
                this.handleTrackingUpdate(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    },

    handleOrderUpdate: function(data) {
        Utils.showNotification(`Order ${data.order_number} status updated to ${data.status}`, 'info');
        
        // Update order status on page if visible
        const statusElement = document.querySelector(`[data-order-id="${data.order_id}"] .order-status`);
        if (statusElement) {
            statusElement.className = `badge status-${data.status}`;
            statusElement.textContent = data.status_display;
        }
    },

    handleInventoryUpdate: function(data) {
        if (data.needs_reorder) {
            Utils.showNotification(`Low stock alert: ${data.product_name}`, 'warning');
        }
        
        // Update inventory displays
        const stockElement = document.querySelector(`[data-product-id="${data.product_id}"] .stock-level`);
        if (stockElement) {
            stockElement.textContent = data.available_stock;
        }
    },

    handleTrackingUpdate: function(data) {
        Utils.showNotification(`Tracking update: ${data.title}`, 'info');
        
        // Add to tracking timeline if on order detail page
        const timeline = document.querySelector('.timeline');
        if (timeline) {
            this.addTrackingEvent(timeline, data);
        }
    },

    addTrackingEvent: function(timeline, data) {
        const eventHTML = `
            <div class="timeline-item">
                <div class="timeline-marker bg-primary"></div>
                <div class="timeline-content">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-1">${data.title}</h6>
                        <small class="text-muted">${Utils.formatDate(data.timestamp)}</small>
                    </div>
                    <p class="text-muted mb-1">${data.description}</p>
                    ${data.location ? `<small class="text-info"><i class="fas fa-map-pin me-1"></i>${data.location}</small>` : ''}
                </div>
            </div>
        `;
        timeline.insertAdjacentHTML('afterbegin', eventHTML);
    },

    attemptReconnect: function() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000;
            
            console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        } else {
            console.error('Max reconnection attempts reached');
            Utils.showNotification('Real-time updates unavailable', 'warning');
        }
    },

    setupHeartbeat: function() {
        setInterval(() => {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    }
};

// Dashboard Manager
const DashboardManager = {
    init: function() {
        this.setupAutoRefresh();
        this.setupCounters();
        this.setupCharts();
    },

    setupAutoRefresh: function() {
        if (window.location.pathname.includes('dashboard')) {
            setInterval(() => {
                this.refreshStats();
            }, CONFIG.REFRESH_INTERVAL);
        }
    },

    setupCounters: function() {
        const counters = document.querySelectorAll('.stats-number, .stats-card h2, .stats-card h3');
        counters.forEach(counter => {
            this.animateCounter(counter);
        });
    },

    animateCounter: function(element) {
        const target = parseInt(element.textContent) || 0;
        let current = 0;
        const increment = target / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 20);
    },

    refreshStats: function() {
        fetch('/api/dashboard/stats/', {
            headers: {
                'X-CSRFToken': Utils.getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            // Update dashboard statistics
            Object.keys(data).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.textContent = data[key];
                }
            });
        })
        .catch(error => console.error('Failed to refresh stats:', error));
    },

    setupCharts: function() {
        // Initialize charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            this.initOrdersChart();
            this.initInventoryChart();
        }
    },

    initOrdersChart: function() {
        const ctx = document.getElementById('ordersChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Orders',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: 'rgb(37, 99, 235)',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    },

    initInventoryChart: function() {
        const ctx = document.getElementById('inventoryChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['In Stock', 'Low Stock', 'Out of Stock'],
                datasets: [{
                    data: [70, 20, 10],
                    backgroundColor: [
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
};

// Search and Filter Manager
const SearchManager = {
    init: function() {
        this.setupInstantSearch();
        this.setupFilters();
    },

    setupInstantSearch: function() {
        const searchInputs = document.querySelectorAll('.instant-search');
        searchInputs.forEach(input => {
            let timeout;
            input.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.performSearch(input);
                }, 300);
            });
        });
    },

    performSearch: function(input) {
        const query = input.value;
        const target = input.dataset.target;
        
        if (!target) return;

        fetch(`/api/search/${target}/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                this.updateSearchResults(target, data.results);
            })
            .catch(error => console.error('Search failed:', error));
    },

    updateSearchResults: function(target, results) {
        const container = document.getElementById(target);
        if (!container) return;

        container.innerHTML = results.map(item => 
            this.renderSearchResult(item)
        ).join('');
    },

    renderSearchResult: function(item) {
        return `
            <div class="search-result-item p-3 border-bottom">
                <h6>${item.title}</h6>
                <p class="text-muted mb-1">${item.description}</p>
                <small class="text-secondary">${item.category}</small>
            </div>
        `;
    },

    setupFilters: function() {
        const filterInputs = document.querySelectorAll('.filter-input');
        filterInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.applyFilters();
            });
        });
    },

    applyFilters: function() {
        const filters = {};
        document.querySelectorAll('.filter-input').forEach(input => {
            if (input.value) {
                filters[input.name] = input.value;
            }
        });

        const params = new URLSearchParams(filters);
        window.location.search = params.toString();
    }
};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    RealTimeManager.init();
    DashboardManager.init();
    SearchManager.init();
    
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    console.log('Supply Chain Management System initialized');
});

// Export for use in other scripts
window.SupplyChain = {
    Utils,
    RealTimeManager,
    DashboardManager,
    SearchManager
};