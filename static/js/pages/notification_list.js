/**
 * Notification List Interactions
 * Handles marking notifications as read and navigating.
 */

// General Click Handler for Navigation (delegated from template)
window.handleNotificationClick = async function (event, id, url) {
    // Prevent if clicking on buttons
    if (event.target.closest('.notif-actions') || event.target.closest('button') || event.target.closest('a')) {
        return;
    }

        // Mark as read first if unread
        const item = document.querySelector(`.notif-item[data-id="${id}"]`);
        if (item && item.classList.contains('unread')) {
            await markAsRead(event, id, false); // Don't reload, just mark
        }

        // Navigate
        if (url && url !== 'None' && url !== '') {
            window.location.href = url;
        }
    };

    // Explicit Mark as Read (Button)
    window.markAsRead = async function (event, id, showToast = true) {
        if (event) event.stopPropagation();

        const item = document.querySelector(`.notif-item[data-id="${id}"]`);

        try {
            const res = await Http.post(`/notifications/mark-read/${id}/`);
            if (res.ok) {
                if (item) {
                    item.classList.remove('unread');
                    const indicator = item.querySelector('.notif-indicator');
                    if (indicator) indicator.remove();

                    // Remove "Mark Read" button if it exists
                    const btn = item.querySelector('button[onclick*="markAsRead"]');
                    if (btn) btn.remove();
                }
                if (showToast) UI.toast('تم تحديد الإشعار كمقروء', 'success');
                
                // Update Badge Immediately
                if (window.Notifications) window.Notifications.check();
            }
        } catch (error) {
            console.error('Failed to mark notification as read', error);
        }
    };

    // Explicit Delete (Button)
    window.deleteNotification = async function (event, id) {
        if (event) event.stopPropagation();

        if (!confirm('هل أنت متأكد من حذف هذا الإشعار؟')) return;

        const item = document.querySelector(`.notif-item[data-id="${id}"]`);
        if (item) {
            item.style.transition = 'all 0.3s ease';
            item.style.opacity = '0.5';
        }

        try {
            const res = await Http.post(`/notifications/delete/${id}/`);
            if (res.ok) {
                if (item) {
                    item.classList.add('animate__animated', 'animate__fadeOutRight');
                    setTimeout(() => item.remove(), 300);
                }
                UI.toast('تم حذف الإشعار', 'success');
                
                // Update Badge Immediately
                if (window.Notifications) window.Notifications.check();
            } else {
                UI.toast('فشل حذف الإشعار', 'error');
                if (item) item.style.opacity = '1';
            }
        } catch (error) {
            console.error('Failed to delete notification', error);
            UI.toast('حدث خطأ في الاتصال', 'error');
            if (item) item.style.opacity = '1';
        }
    };

    window.markAllAsRead = async function () {
        if (!confirm('هل تريد تحديد جميع الإشعارات كمقروءة؟')) return;

        try {
            const res = await Http.post('/notifications/mark-all-read/');

            if (res.ok) {
                document.querySelectorAll('.notif-item').forEach(item => {
                    item.classList.remove('unread');
                    const ind = item.querySelector('.notif-indicator');
                    if (ind) ind.remove();

                    // Remove individual mark read buttons
                    const btn = item.querySelector('button[onclick*="markAsRead"]');
                    if (btn) btn.remove();
                });
                UI.toast('تم تحديد الكل كمقروء', 'success');
                
                // Update Badge Immediately
                if (window.Notifications) window.Notifications.check();
            } else {
                UI.toast('حدث خطأ أثناء التحديث', 'error');
            }
        } catch (error) {
            console.error(error);
            UI.toast('حدث خطأ في الاتصال', 'error');
        }
    };
