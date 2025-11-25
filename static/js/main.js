console.log('RideShare360 UI loaded');

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 1 second
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            // Create a fade out effect
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 500); // Wait for fade out to complete
        }, 1000); // 1 second delay
    });
});