/**
 * Global Notifications Manager
 * Handles polling for new notifications and updating the header badge.
 */

const Notifications = {
    pollingInterval: 30000, // 30 seconds
    intervalId: null,

    init() {
        // Check if user is authenticated (APP.user or similar, but we can check if badge exists)
        const badge = document.querySelector('.fa-bell');
        if (!badge) return; // Likely guest

        this.startPolling();
        this.initOneSignal();
    },

    initOneSignal() {
        if (!window.APP || !window.APP.onesignalAppId) return;

        window.OneSignalDeferred = window.OneSignalDeferred || [];
        window.OneSignalDeferred.push(async function(OneSignal) {
            await OneSignal.init({
                appId: window.APP.onesignalAppId,
                safari_web_id: "web.onesignal.auto.simulated", // Placeholder
                notifyButton: {
                    enable: true,
                },
                allowLocalhostAsSecureOrigin: true,
            });
            
            // Log user ID for debugging
            // console.log("OneSignal Init");
        });
    },

    startPolling() {
        this.intervalId = setInterval(() => this.check(), this.pollingInterval);
    },

    stopPolling() {
        if (this.intervalId) clearInterval(this.intervalId);
    },

    async check() {
        try {
            const res = await fetch('/notifications/api/unread-count/');
            if (res.ok) {
                const data = await res.json();
                this.updateBadge(data.count);
            }
        } catch (e) {
            console.error('Notification check failed', e);
        }
    },

    updateBadge(count) {
        const wrapper = document.querySelector('a[href*="notification"]');
        if (!wrapper) return;

        let badge = wrapper.querySelector('.badge');

        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger border border-light p-1';
                badge.style.fontSize = '0.6rem';
                wrapper.appendChild(badge);
            }
            badge.textContent = count;
            badge.style.display = 'block';
        } else {
            if (badge) badge.style.display = 'none';
        }
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Only init if not disabled
    if (window.Features && window.Features.isEnabled('enable_notifications')) {
        Notifications.init();
    }
    window.Notifications = Notifications;
});
