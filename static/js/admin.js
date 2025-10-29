class AdminDashboard {
    constructor() {
        this.socket = io();
        this.charts = {};
        this.initializeCharts();
        this.initializeSocketListeners();
        this.loadInitialData();
        this.setupRealTimeUpdates();
    }

    initializeCharts() {
        this.initializeTasksChart();
        this.initializeUtilizationChart();
        this.initializePerformanceChart();
    }

    initializeTasksChart() {
        const ctx = document.getElementById('tasksChart');
        if (!ctx) return;

        this.charts.tasks = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Oil Change', 'Brake Service', 'AC Service', 'Filter Replacement', 'Wheel Alignment', 'Spark Plugs'],
                datasets: [{
                    label: 'Tasks Completed',
                    data: [45, 32, 28, 38, 22, 18],
                    backgroundColor: [
                        'rgba(58, 134, 255, 0.8)',
                        'rgba(255, 158, 0, 0.8)',
                        'rgba(6, 214, 160, 0.8)',
                        'rgba(255, 209, 102, 0.8)',
                        'rgba(239, 71, 111, 0.8)',
                        'rgba(180, 142, 173, 0.8)'
                    ],
                    borderColor: [
                        'rgba(58, 134, 255, 1)',
                        'rgba(255, 158, 0, 1)',
                        'rgba(6, 214, 160, 1)',
                        'rgba(255, 209, 102, 1)',
                        'rgba(239, 71, 111, 1)',
                        'rgba(180, 142, 173, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Top Service Tasks (This Week)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Tasks'
                        }
                    }
                }
            }
        });
    }

    initializeUtilizationChart() {
        const ctx = document.getElementById('utilizationChart');
        if (!ctx) return;

        this.charts.utilization = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Available', 'Moderate', 'Busy'],
                datasets: [{
                    data: [12, 5, 3],
                    backgroundColor: [
                        'rgba(6, 214, 160, 0.8)',
                        'rgba(255, 158, 0, 0.8)',
                        'rgba(239, 71, 111, 0.8)'
                    ],
                    borderColor: [
                        'rgba(6, 214, 160, 1)',
                        'rgba(255, 158, 0, 1)',
                        'rgba(239, 71, 111, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'Worker Utilization Distribution'
                    }
                }
            }
        });
    }

    initializePerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                datasets: [{
                    label: 'Services Completed',
                    data: [18, 22, 25, 20, 28, 15],
                    borderColor: 'rgba(58, 134, 255, 1)',
                    backgroundColor: 'rgba(58, 134, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Average Service Time (hrs)',
                    data: [3.2, 2.8, 2.9, 3.1, 2.7, 3.0],
                    borderColor: 'rgba(255, 158, 0, 1)',
                    backgroundColor: 'rgba(255, 158, 0, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Weekly Performance Trends'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    initializeSocketListeners() {
        this.socket.on('workload_update', (data) => {
            console.log("🔄 Received real-time workload update");
            this.updateWorkloadDisplay(data);
            this.updateStats(data);
            this.updateUtilizationChart(data);
        });

        this.socket.on('inventory_update', (data) => {
            this.updateInventoryDisplay(data);
        });

        this.socket.on('service_assigned', (data) => {
            console.log("➕ New service assigned:", data.service_id);
            this.addActiveService(data);
        });

        this.socket.on('active_services_update', (data) => {
            console.log("📋 Active services updated:", data.length, "services");
            this.updateActiveServices(data);
        });

        this.socket.on('completed_services_update', (data) => {
            this.updateCompletedServices(data);
        });

        this.socket.on('low_stock_alert', (data) => {
            this.addEmailAlert(data);
            this.showAlertNotification(data);
        });
    }

    async loadInitialData() {
        try {
            console.log("📥 Loading initial data...");
            const [workloadRes, inventoryRes, activeRes, completedRes] = await Promise.all([
                fetch('/api/workload'),
                fetch('/api/inventory'),
                fetch('/api/active_services'),
                fetch('/api/completed_services')
            ]);

            const workloadData = await workloadRes.json();
            const inventoryData = await inventoryRes.json();
            const activeServices = await activeRes.json();
            const completedServices = await completedRes.json();

            console.log("✅ Data loaded successfully");
            this.updateWorkloadDisplay(workloadData);
            this.updateInventoryDisplay(inventoryData);
            this.updateActiveServices(activeServices);
            this.updateCompletedServices(completedServices);

        } catch (error) {
            console.error('❌ Error loading initial data:', error);
            this.showToast('Failed to load data: ' + error.message, 'error');
        }
    }

    setupRealTimeUpdates() {
        // Refresh data every 30 seconds
        setInterval(() => {
            this.loadInitialData();
        }, 30000);
    }

    updateWorkloadDisplay(workloadData) {
        console.log("📊 Workload data received:", workloadData);
        
        // Handle the new data structure properly
        let workers = [];
        let summary = {};
        
        if (workloadData.workers && workloadData.summary) {
            // New structure with workers and summary
            workers = workloadData.workers;
            summary = workloadData.summary;
            console.log("✅ Using new data structure");
        } else if (Array.isArray(workloadData)) {
            // Old structure (array of workers) - fallback
            workers = workloadData;
            summary = {
                total_workers: workers.length,
                total_active_jobs: workers.reduce((sum, worker) => sum + (worker.current_jobs || 0), 0),
                available_workers: workers.filter(worker => (worker.workload_percentage || 0) < 70).length,
                queued_services: 0,
                total_capacity_utilization: 0
            };
            console.log("⚠️ Using old data structure (fallback)");
        } else {
            console.error("❌ Invalid workload data structure:", workloadData);
            this.showToast('Invalid data structure received', 'error');
            return;
        }
        
        const workloadGrid = document.getElementById('workload-grid');
        if (!workloadGrid) return;

        // Update summary stats
        this.updateSummaryStats(summary);

        // Update worker cards
        if (workers.length === 0) {
            workloadGrid.innerHTML = '<div class="no-services">No workers data available</div>';
            return;
        }

        workloadGrid.innerHTML = workers.map(worker => {
            const statusClass = worker.status === 'high' ? 'high-workload' : 
                              worker.status === 'medium' ? 'medium-workload' : '';
            
            const jobsInfo = `${worker.current_jobs || 0}/${worker.max_jobs || 3} jobs`;
            const specialization = worker.specialization || 'General Maintenance';
            const workloadPercent = worker.workload_percentage || 0;
            
            return `
                <div class="worker-card ${statusClass}">
                    <div class="worker-info">
                        <div>
                            <strong>${worker.id} - ${worker.name}</strong>
                            <div style="font-size: 0.8em; opacity: 0.8; margin-top: 2px;">
                                ${specialization} • ⭐ ${worker.rating || 4.5}
                            </div>
                        </div>
                        <span class="workload-percent">${workloadPercent}%</span>
                    </div>
                    <div class="worker-progress">
                        <div class="progress-fill progress-${worker.status}" 
                             style="width: ${workloadPercent}%"></div>
                    </div>
                    <div class="worker-stats">
                        <span>${jobsInfo}</span>
                        <span class="status-${worker.status}">${worker.status_text || 'Available'}</span>
                    </div>
                    ${worker.jobs_list && worker.jobs_list.length > 0 ? `
                    <div style="margin-top: 10px; font-size: 0.8em; opacity: 0.7;">
                        <strong>Current Jobs:</strong> ${worker.jobs_list.join(', ')}
                    </div>
                    ` : '<div style="margin-top: 10px; font-size: 0.8em; opacity: 0.5;">No active jobs</div>'}
                </div>
            `;
        }).join('');

        updateLastUpdateTime();
    }

    updateSummaryStats(summary) {
        console.log("📈 Updating summary stats:", summary);
        
        // Update main stats cards
        document.getElementById('total-workers').textContent = summary.total_workers || 20;
        document.getElementById('active-jobs').textContent = summary.total_active_jobs || 0;
        document.getElementById('available-workers').textContent = summary.available_workers || 0;
        document.getElementById('queued-services').textContent = summary.queued_services || 0;
        document.getElementById('capacity-utilization').textContent = 
            Math.round(summary.total_capacity_utilization || 0) + '%';

        // Update detailed summary section
        const totalActiveJobs = document.getElementById('total-active-jobs');
        const availableWorkersCount = document.getElementById('available-workers-count');
        const queuedCount = document.getElementById('queued-count');
        
        if (totalActiveJobs) totalActiveJobs.textContent = summary.total_active_jobs || 0;
        if (availableWorkersCount) availableWorkersCount.textContent = summary.available_workers || 0;
        if (queuedCount) queuedCount.textContent = summary.queued_services || 0;
        
        console.log(`🎯 Stats Updated: ${summary.total_active_jobs || 0} active jobs, ${summary.available_workers || 0} available workers`);
    }

    updateStats(workloadData) {
        // This method ensures stats are always accurate
        let summary = {};
        
        if (workloadData.summary) {
            summary = workloadData.summary;
        } else if (Array.isArray(workloadData)) {
            // Calculate from worker array
            summary = {
                total_workers: workloadData.length,
                total_active_jobs: workloadData.reduce((sum, worker) => sum + (worker.current_jobs || 0), 0),
                available_workers: workloadData.filter(worker => (worker.workload_percentage || 0) < 70).length,
                queued_services: 0
            };
        }
        
        console.log("📊 Final stats calculation:", summary);
    }

    updateInventoryDisplay(inventoryData) {
        const inventoryTable = document.getElementById('inventory-table');
        if (!inventoryTable) return;

        if (Object.keys(inventoryData).length === 0) {
            inventoryTable.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 30px; opacity: 0.6;">No inventory data available</td></tr>';
            return;
        }

        inventoryTable.innerHTML = Object.entries(inventoryData).map(([id, item]) => {
            const isLowStock = item.quantity <= item.min_stock;
            const rowClass = isLowStock ? 'low-stock' : '';
            const stockStatus = isLowStock ? 
                `<span class="text-danger">❌ Low Stock</span>` : 
                `<span class="text-success">✅ In Stock</span>`;
            
            return `
                <tr class="${rowClass}">
                    <td>
                        <strong>${item.name}</strong>
                        <div style="font-size: 0.8em; opacity: 0.7;">${item.unit || 'pieces'}</div>
                    </td>
                    <td>
                        <span style="font-weight: bold; font-size: 1.1em;">${item.quantity}</span>
                        ${stockStatus}
                    </td>
                    <td>${item.min_stock}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="restockPart('${id}')">
                            📦 Restock (+5)
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    updateActiveServices(services) {
        const activeServices = document.getElementById('active-services');
        if (!activeServices) return;

        if (services.length === 0) {
            activeServices.innerHTML = '<div class="no-services">No active services</div>';
            return;
        }

        activeServices.innerHTML = services.map(service => {
            const completionTime = service.completion_time ? new Date(service.completion_time) : null;
            const now = new Date();
            
            let timeLeft = 'N/A';
            let progress = 0;
            
            if (completionTime) {
                const timeDiff = completionTime - now;
                const hoursLeft = Math.max(0, (timeDiff / (1000 * 60 * 60)).toFixed(1));
                timeLeft = `${hoursLeft}h`;
                progress = Math.max(0, Math.min(100, (1 - (hoursLeft / service.predicted_time)) * 100));
            }

            const workerInfo = service.worker_assigned ? 
                `${service.worker_assigned.worker_name} (${service.worker_assigned.specialization})` : 
                'Queued';

            const statusBadge = service.worker_assigned ? 
                `<span class="service-worker">${service.worker_assigned.worker_name}</span>` :
                `<span class="service-worker" style="background: var(--warning);">Queued</span>`;

            return `
                <div class="service-item">
                    <div class="service-header">
                        <span class="service-id">${service.service_id}</span>
                        ${statusBadge}
                    </div>
                    <div class="service-details">
                        <div><strong>Vehicle:</strong> ${service.car_details.car_model}</div>
                        <div><strong>Service:</strong> ${service.car_details.service_type}</div>
                        <div><strong>Predicted Time:</strong> ${service.predicted_time}h</div>
                        <div><strong>Worker:</strong> ${workerInfo}</div>
                        ${completionTime ? `
                        <div><strong>Time Left:</strong> ${timeLeft}</div>
                        <div><strong>Completion:</strong> ${completionTime.toLocaleTimeString()}</div>
                        ` : `
                        <div><strong>Queue Position:</strong> ${service.worker_assigned?.queue_position || 'N/A'}</div>
                        <div><strong>Est. Wait:</strong> ${service.worker_assigned?.estimated_wait_time || 'N/A'}h</div>
                        `}
                    </div>
                    ${completionTime ? `
                    <div class="service-progress">
                        <div class="progress-time">
                            <span>Progress</span>
                            <span>${progress.toFixed(1)}%</span>
                        </div>
                        <div class="worker-progress">
                            <div class="progress-fill progress-medium" style="width: ${progress}%"></div>
                        </div>
                    </div>
                    ` : ''}
                    <div style="margin-top: 10px; text-align: right;">
                        ${service.worker_assigned ? `
                        <button class="btn btn-success btn-sm" onclick="completeService('${service.service_id}')">
                            ✅ Complete Service
                        </button>
                        ` : ''}
                        <button class="btn btn-primary btn-sm" onclick="generateReport('${service.service_id}')">
                            📄 Generate Report
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateCompletedServices(services) {
        const completedServices = document.getElementById('completed-services');
        if (!completedServices) return;

        if (services.length === 0) {
            completedServices.innerHTML = '<div class="no-services">No completed services yet</div>';
            return;
        }

        completedServices.innerHTML = services.map(service => {
            const completedAt = service.completed_at ? new Date(service.completed_at) : new Date();
            
            return `
                <div class="service-item">
                    <div class="service-header">
                        <span class="service-id">${service.service_id}</span>
                        <span class="service-worker">${service.worker_assigned?.worker_name || 'Unknown'}</span>
                    </div>
                    <div class="service-details">
                        <div><strong>Vehicle:</strong> ${service.car_details.car_model}</div>
                        <div><strong>Service:</strong> ${service.car_details.service_type}</div>
                        <div><strong>Actual Time:</strong> ${service.predicted_time}h</div>
                        <div><strong>Completed:</strong> ${completedAt.toLocaleDateString()}</div>
                    </div>
                    <div style="margin-top: 10px; text-align: right;">
                        <button class="btn btn-primary btn-sm" onclick="generateReport('${service.service_id}')">
                            📄 Download Report
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    addEmailAlert(alertData) {
        const emailAlerts = document.getElementById('email-alerts');
        if (!emailAlerts) return;

        const noAlerts = emailAlerts.querySelector('.no-alerts');
        if (noAlerts) {
            noAlerts.remove();
        }

        const alertItem = document.createElement('div');
        alertItem.className = 'alert-item';
        alertItem.innerHTML = `
            <strong>⚠️ Low Stock Alert: ${alertData.part_name}</strong>
            <div>Current quantity: ${alertData.quantity} • Action Required</div>
            <div class="alert-time">${new Date().toLocaleString()}</div>
        `;

        emailAlerts.insertBefore(alertItem, emailAlerts.firstChild);
        
        // Keep only last 10 alerts
        const alerts = emailAlerts.querySelectorAll('.alert-item');
        if (alerts.length > 10) {
            alerts[alerts.length - 1].remove();
        }
    }

    updateUtilizationChart(workloadData) {
        if (!this.charts.utilization) return;

        let workers = [];
        if (workloadData.workers && workloadData.summary) {
            workers = workloadData.workers;
        } else if (Array.isArray(workloadData)) {
            workers = workloadData;
        }

        const available = workers.filter(w => w.status === 'low').length;
        const moderate = workers.filter(w => w.status === 'medium').length;
        const busy = workers.filter(w => w.status === 'high').length;

        this.charts.utilization.data.datasets[0].data = [available, moderate, busy];
        this.charts.utilization.update();
    }

    forceRefresh() {
        console.log("🔄 Force refreshing all data...");
        this.loadInitialData();
        this.showToast('Data refreshed manually', 'info');
    }

    showAlertNotification(alertData) {
        this.showToast(`⚠️ Low stock: ${alertData.part_name} (${alertData.quantity} left)`, 'warning');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
}

// Global admin functions
async function restockPart(partName) {
    try {
        const response = await fetch(`/restock/${partName}`);
        const result = await response.json();
        
        if (result.success) {
            showAdminToast(`✅ ${partName} restocked successfully`, 'success');
            // Reload inventory data
            adminDashboard.loadInitialData();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        showAdminToast('Restock failed: ' + error.message, 'error');
    }
}

async function completeService(serviceId) {
    try {
        const response = await fetch(`/complete_service/${serviceId}`);
        const result = await response.json();
        
        if (result.success) {
            showAdminToast(`✅ Service ${serviceId} completed`, 'success');
            // Reload data
            adminDashboard.loadInitialData();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        showAdminToast('Completion failed: ' + error.message, 'error');
    }
}

async function generateReport(serviceId) {
    try {
        const response = await fetch(`/generate_report/${serviceId}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `${serviceId}_report.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showAdminToast('📄 Report downloaded successfully!', 'success');
        } else {
            throw new Error('Failed to generate report');
        }
    } catch (error) {
        showAdminToast('Report generation failed: ' + error.message, 'error');
    }
}

// Global helper functions
function showAdminToast(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : 'var(--accent-blue)'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    `;
    
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 4000);
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.adminDashboard = new AdminDashboard();
});