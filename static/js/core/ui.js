/**
 * IBB GUIDE - UI HELPER
 * Standardized UI interactions (Toast, Loading, Confirm).
 */

const UI = {
    /**
     * Show a toast notification
     * @param {string} message 
     * @param {'success'|'error'|'info'|'warning'} type 
     */
    toast(message, type = 'info') {
        // Check if a toast container exists, else create one (simple implementation)
        // Ideally, integrate with a library like Toastify or Bootstrap Toasts
        // For now, using standard alert as fallback if no toast container
        console.log(`[TOAST-${type.toUpperCase()}]: ${message}`);

        // Use Bootstrap Toast if available
        if (window.bootstrap && document.getElementById('toastContainer')) {
            const toastHtml = `
                <div class="toast align-items-center text-bg-${type === 'error' ? 'danger' : type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            ${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;
            const container = document.getElementById('toastContainer');
            const wrapper = document.createElement('div');
            wrapper.innerHTML = toastHtml;
            const toastEl = wrapper.firstElementChild;
            container.appendChild(toastEl);
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
            toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
        } else {
            // Fallback
            // alert(message); 
        }
    },

    showLoading(element) {
        if (!element) return;
        element.dataset.originalText = element.innerHTML;
        element.disabled = true;
        element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جارِ التحميل...';
    },

    hideLoading(element) {
        if (!element) return;
        element.disabled = false;
        if (element.dataset.originalText) {
            element.innerHTML = element.dataset.originalText;
        }
    },

    confirm(message) {
        return window.confirm(message);
    }
};

window.UI = UI;
