class VSISApp {
    constructor() {
        this.socket = io();
        this.selectedTasks = new Set();
        this.currentService = null;
        this.initializeEventListeners();
        this.initializeSocketListeners();
        this.initializeAutoCalculations();
    }

    initializeEventListeners() {
        // Task selection
        document.querySelectorAll('.task-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.handleTaskSelection(e.target);
            });
        });

        // Form submission
        const predictBtn = document.getElementById('predict-btn');
        if (predictBtn) {
            predictBtn.addEventListener('click', () => this.handlePrediction());
        }

        // Auto-calculate days since last service
        const lastServiceDate = document.getElementById('last_service_date');
        if (lastServiceDate) {
            lastServiceDate.addEventListener('change', () => this.calculateDaysSinceService());
        }

        // Task category collapse
        document.querySelectorAll('.task-header').forEach(header => {
            header.addEventListener('click', (e) => {
                const category = e.target.closest('.task-category');
                const items = category.querySelector('.task-items');
                const icon = category.querySelector('.task-header span');
                
                items.style.display = items.style.display === 'none' ? 'grid' : 'none';
                icon.textContent = items.style.display === 'none' ? '▶' : '▼';
            });
        });

        // Number plate formatting
        const numberPlateInput = document.getElementById('number_plate');
        if (numberPlateInput) {
            numberPlateInput.addEventListener('input', (e) => {
                this.formatNumberPlate(e.target);
            });
        }
    }

    initializeSocketListeners() {
        this.socket.on('workload_update', (data) => {
            this.updateWorkloadDisplay(data);
        });

        this.socket.on('inventory_update', (data) => {
            this.updateInventoryDisplay(data);
        });

        this.socket.on('low_stock_alert', (data) => {
            this.showLowStockAlert(data);
        });

        this.socket.on('service_assigned', (data) => {
            console.log('New service assigned:', data);
        });

        this.socket.on('active_services_update', (data) => {
            this.updateActiveServices(data);
        });
    }

    initializeAutoCalculations() {
        // Auto-calculate KM since last service based on total KM
        const totalKmInput = document.getElementById('total_km');
        const kmSinceInput = document.getElementById('km_since_last_service');
        
        if (totalKmInput && kmSinceInput) {
            totalKmInput.addEventListener('input', () => {
                this.estimateKmSinceLastService();
            });
        }
    }

    formatNumberPlate(input) {
        let value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        
        // Format as MH12AB1234
        if (value.length > 2) {
            value = value.substring(0, 2) + ' ' + value.substring(2);
        }
        if (value.length > 5) {
            value = value.substring(0, 5) + ' ' + value.substring(5);
        }
        if (value.length > 8) {
            value = value.substring(0, 8) + ' ' + value.substring(8);
        }
        
        input.value = value.substring(0, 13); // Limit length
    }

    estimateKmSinceLastService() {
        const totalKm = parseInt(document.getElementById('total_km').value) || 0;
        const lastServiceDate = document.getElementById('last_service_date').value;
        
        if (totalKm > 0 && lastServiceDate) {
            const lastDate = new Date(lastServiceDate);
            const today = new Date();
            const daysDiff = Math.ceil((today - lastDate) / (1000 * 60 * 60 * 24));
            
            // Estimate 40km per day average usage
            const estimatedKm = Math.min(totalKm, Math.max(1000, daysDiff * 40));
            document.getElementById('km_since_last_service').value = estimatedKm;
        }
    }

    calculateDaysSinceService() {
        const lastServiceDate = document.getElementById('last_service_date').value;
        const daysSinceElement = document.getElementById('days_since_last_service');
        
        if (lastServiceDate && daysSinceElement) {
            const lastDate = new Date(lastServiceDate);
            const today = new Date();
            const diffTime = Math.abs(today - lastDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            daysSinceElement.value = diffDays;
            
            // Update KM estimate
            this.estimateKmSinceLastService();
        }
    }

    handleTaskSelection(checkbox) {
        const taskId = checkbox.value;
        const taskTime = parseFloat(checkbox.dataset.time);

        if (checkbox.checked) {
            this.selectedTasks.add(taskId);
        } else {
            this.selectedTasks.delete(taskId);
        }

        this.updateTaskSummary();
    }

    updateTaskSummary() {
        const selectedCount = document.getElementById('selected-count');
        const taskNames = document.getElementById('task-names');
        const estimatedTime = document.getElementById('estimated-time');

        if (selectedCount && taskNames && estimatedTime) {
            selectedCount.textContent = this.selectedTasks.size;
            
            const taskElements = Array.from(document.querySelectorAll('.task-checkbox:checked'))
                .map(cb => cb.closest('.task-item').querySelector('.task-name').textContent);
            
            taskNames.textContent = taskElements.join(', ') || 'No tasks selected';
            
            const totalTime = Array.from(document.querySelectorAll('.task-checkbox:checked'))
                .reduce((sum, cb) => sum + parseFloat(cb.dataset.time), 0);
            
            estimatedTime.textContent = totalTime.toFixed(1) + 'h';
            
            // Update button state
            const predictBtn = document.getElementById('predict-btn');
            if (predictBtn) {
                predictBtn.disabled = this.selectedTasks.size === 0;
            }
        }
    }

    validateForm(formData) {
        const required = ['car_model', 'manufacture_year', 'fuel_type', 'service_type', 'number_plate', 'total_km'];
        
        for (const field of required) {
            if (!formData[field] || formData[field].toString().trim() === '') {
                this.showToast(`Please fill in the ${field.replace('_', ' ')} field`, 'error');
                return false;
            }
        }

        if (this.selectedTasks.size === 0) {
            this.showToast('Please select at least one service task', 'error');
            return false;
        }

        if (formData.number_plate.replace(/[^A-Z0-9]/g, '').length < 5) {
            this.showToast('Please enter a valid number plate', 'error');
            return false;
        }

        return true;
    }

    async handlePrediction() {
        const formData = {
            car_model: document.getElementById('car_model').value,
            manufacture_year: document.getElementById('manufacture_year').value,
            fuel_type: document.getElementById('fuel_type').value,
            service_type: document.getElementById('service_type').value,
            number_plate: document.getElementById('number_plate').value.replace(/\s/g, ''),
            last_service_date: document.getElementById('last_service_date').value,
            total_km: document.getElementById('total_km').value,
            km_since_last_service: document.getElementById('km_since_last_service').value,
            days_since_last_service: document.getElementById('days_since_last_service').value,
            selected_tasks: Array.from(this.selectedTasks)
        };

        if (!this.validateForm(formData)) {
            return;
        }

        try {
            const predictBtn = document.getElementById('predict-btn');
            const originalText = predictBtn.innerHTML;
            
            predictBtn.innerHTML = '<div class="loading"></div> Predicting...';
            predictBtn.disabled = true;

            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.currentService = result;
                this.displayPredictionResult(result);
                this.showToast('✅ Prediction Complete! Service assigned successfully.', 'success');
            } else {
                throw new Error(result.error || 'Prediction failed');
            }

        } catch (error) {
            console.error('Prediction error:', error);
            this.showToast('Prediction failed: ' + error.message, 'error');
        } finally {
            const predictBtn = document.getElementById('predict-btn');
            predictBtn.innerHTML = '🔮 Predict Service Time';
            predictBtn.disabled = false;
        }
    }

    displayPredictionResult(result) {
        // Hide input form and show results
        document.getElementById('input-form').style.display = 'none';
        const resultCard = document.getElementById('prediction-result');
        resultCard.style.display = 'block';

        // Smooth scroll to results
        resultCard.scrollIntoView({ behavior: 'smooth' });

        // Update result elements
        document.getElementById('predicted-time').textContent = result.predicted_time;
        document.getElementById('service-id').textContent = result.service_id;
        document.getElementById('worker-name').textContent = result.worker_assigned.worker_name;
        document.getElementById('worker-specialization').textContent = result.worker_assigned.specialization;
        document.getElementById('worker-rating').textContent = result.worker_assigned.rating;
        
        const completionTime = new Date(result.worker_assigned.completion_time);
        document.getElementById('completion-time').textContent = completionTime.toLocaleString();

        // Update gauge
        this.updateTimeGauge(result.predicted_time);
        
        // Update workload bar
        this.updateWorkloadBar(result.worker_assigned.workload_percentage);
        
        // Update parts availability
        const partsElement = document.getElementById('parts-availability');
        if (result.inventory_status.available) {
            partsElement.className = 'text-success';
            partsElement.innerHTML = '✅ All Parts Available';
        } else {
            partsElement.className = 'text-danger pulse';
            partsElement.innerHTML = '❌ Some Parts Unavailable';
        }

        // Update queue info
        document.getElementById('queue-position').textContent = result.queue_info.total_active_jobs + 1;
        document.getElementById('cars-ahead').textContent = result.queue_info.total_active_jobs;

        // Add download report button
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn btn-success';
        downloadBtn.innerHTML = '📄 Download Service Report';
        downloadBtn.onclick = () => this.downloadReport(result.service_id);
        
        const buttonContainer = document.querySelector('#prediction-result .btn-success').parentNode;
        buttonContainer.appendChild(downloadBtn);
    }

    updateTimeGauge(time) {
        const gaugeCircle = document.querySelector('.gauge-circle');
        const percentage = Math.min((time / 8) * 100, 100); // Max 8 hours
        
        // Create gradient based on time
        let gradient;
        if (time <= 3) {
            gradient = `conic-gradient(var(--success) 0% ${percentage}%, var(--blue-gray) ${percentage}% 100%)`;
        } else if (time <= 5) {
            gradient = `conic-gradient(var(--warning) 0% ${percentage}%, var(--blue-gray) ${percentage}% 100%)`;
        } else {
            gradient = `conic-gradient(var(--danger) 0% ${percentage}%, var(--blue-gray) ${percentage}% 100%)`;
        }
        
        gaugeCircle.style.background = gradient;
    }

    updateWorkloadBar(percentage) {
        const workloadFill = document.querySelector('.workload-fill');
        workloadFill.style.width = percentage + '%';
        
        // Update color based on percentage
        if (percentage < 40) {
            workloadFill.style.background = 'linear-gradient(90deg, var(--success), #05C18E)';
        } else if (percentage < 70) {
            workloadFill.style.background = 'linear-gradient(90deg, var(--warning), #E68A00)';
        } else {
            workloadFill.style.background = 'linear-gradient(90deg, var(--danger), #D43A5C)';
        }
    }

    updateWorkloadDisplay(workloadData) {
        // Update stats if on admin page
        this.updateWorkloadStats(workloadData);
    }

    updateWorkloadStats(workloadData) {
        const totalJobs = workloadData.reduce((sum, worker) => sum + worker.current_jobs, 0);
        const availableWorkers = workloadData.filter(worker => worker.workload_percentage < 70).length;
        
        const totalJobsElem = document.getElementById('total-jobs');
        const availableWorkersElem = document.getElementById('available-workers');
        
        if (totalJobsElem) totalJobsElem.textContent = totalJobs;
        if (availableWorkersElem) availableWorkersElem.textContent = availableWorkers;
    }

    updateInventoryDisplay(inventoryData) {
        // This would be used in admin dashboard
        console.log('Inventory updated:', inventoryData);
    }

    updateActiveServices(services) {
        // This would be used in admin dashboard
        console.log('Active services updated:', services);
    }

    async downloadReport(serviceId) {
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
                this.showToast('📄 Report downloaded successfully!', 'success');
            } else {
                throw new Error('Failed to download report');
            }
        } catch (error) {
            this.showToast('Download failed: ' + error.message, 'error');
        }
    }

    showLowStockAlert(alertData) {
        this.showToast(`⚠️ Low stock alert: ${alertData.part_name} (${alertData.quantity} left)`, 'warning');
    }

    showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.toast').forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Utility methods for form handling
    populateSampleData() {
        // For demo purposes - populate form with sample data
        document.getElementById('number_plate').value = 'MH12AB1234';
        document.getElementById('car_model').value = 'XC60';
        document.getElementById('manufacture_year').value = '2022';
        document.getElementById('total_km').value = '35000';
        document.getElementById('last_service_date').value = '2024-01-15';
        document.getElementById('km_since_last_service').value = '5000';
        
        this.calculateDaysSinceService();
        
        // Select some sample tasks
        const sampleTasks = ['engine_oil', 'air_filter', 'brake_fluid'];
        sampleTasks.forEach(taskId => {
            const checkbox = document.querySelector(`input[value="${taskId}"]`);
            if (checkbox) {
                checkbox.checked = true;
                this.selectedTasks.add(taskId);
            }
        });
        
        this.updateTaskSummary();
        this.showToast('Sample data populated for demo', 'info');
    }
}

// Global functions
function restartPrediction() {
    document.getElementById('input-form').style.display = 'block';
    document.getElementById('prediction-result').style.display = 'none';
    
    // Reset form
    document.querySelectorAll('.task-checkbox').forEach(cb => cb.checked = false);
    window.app.selectedTasks.clear();
    window.app.updateTaskSummary();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function useSampleData() {
    if (window.app) {
        window.app.populateSampleData();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VSISApp();
    
    // Add sample data button for demo
    if (document.getElementById('input-form')) {
        const sampleBtn = document.createElement('button');
        sampleBtn.type = 'button';
        sampleBtn.className = 'btn btn-warning';
        sampleBtn.innerHTML = '🎮 Use Sample Data';
        sampleBtn.onclick = useSampleData;
        sampleBtn.style.marginTop = '10px';
        
        const predictBtn = document.getElementById('predict-btn');
        if (predictBtn) {
            predictBtn.parentNode.appendChild(sampleBtn);
        }
    }
});