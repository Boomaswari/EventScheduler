document.addEventListener('DOMContentLoaded', function() {
    
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = new Date().toISOString().slice(0, 10);
        }
    });
    
    const timeInputs = document.querySelectorAll('input[type="time"]');
    timeInputs.forEach(input => {
        if (!input.value) {
            const now = new Date();
            input.value = now.getHours().toString().padStart(2, '0') + ':' + 
                          now.getMinutes().toString().padStart(2, '0');
        }
    });
});

function checkResourceConflict(eventId, resourceIds, startTime, endTime) {
    return fetch('/api/check_conflict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            event_id: eventId,
            resource_ids: resourceIds,
            start_time: startTime,
            end_time: endTime
        })
    })
    .then(response => response.json())
    .then(data => {
        return data;
    })
    .catch(error => {
        console.error('Error checking conflict:', error);
        return { has_conflicts: false, conflicts: [] };
    });
}

function validateTimeRange(startTimeId, endTimeId) {
    const startTime = document.getElementById(startTimeId).value;
    const endTime = document.getElementById(endTimeId).value;
    
    if (startTime && endTime) {
        const start = new Date(startTime);
        const end = new Date(endTime);
        
        if (end <= start) {
            alert('End time must be after start time');
            return false;
        }

        const duration = (end - start) / (1000 * 60 * 60); 
        if (duration > 24) {
            if (!confirm('Event duration exceeds 24 hours. Continue?')) {
                return false;
            }
        }
    }
    
    return true;
}

function exportToCSV(filename, rows) {
    let csvContent = "data:text/csv;charset=utf-8,";
    
    rows.forEach(row => {
        csvContent += row.join(",") + "\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function calculateDuration(startTime, endTime) {
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end - start;
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        const toast = document.createElement('div');
        toast.className = 'alert alert-success alert-dismissible fade show position-fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <strong>Copied!</strong> ${text.substring(0, 50)}...
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    });
}

function getResourceTypeColor(type) {
    const colors = {
        'room': '#007bff',
        'instructor': '#28a745',
        'equipment': '#ffc107',
        'other': '#17a2b8'
    };
    return colors[type] || '#6c757d';
}

function getWithExpiry(key) {
    const itemStr = localStorage.getItem(key);
    
    if (!itemStr) {
        return null;
    }
    
    const item = JSON.parse(itemStr);
    const now = new Date();
    
    if (now.getTime() > item.expiry) {
        localStorage.removeItem(key);
        return null;
    }
    
    return item.value;
}

function setWithExpiry(key, value, ttl) {
    const now = new Date();
    const item = {
        value: value,
        expiry: now.getTime() + ttl
    };
    localStorage.setItem(key, JSON.stringify(item));
}