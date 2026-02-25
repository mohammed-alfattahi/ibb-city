/**
 * Admin Enhanced JavaScript
 * تحسينات JavaScript للإدارة
 */

(function () {
    'use strict';

    // ============ Keyboard Shortcuts ============
    document.addEventListener('keydown', function (e) {
        // Ctrl+S = Save
        if (e.ctrlKey && !e.shiftKey && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.querySelector('input[name="_save"]');
            if (saveBtn) saveBtn.click();
        }

        // Ctrl+Shift+S = Save and continue editing
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            const continueBtn = document.querySelector('input[name="_continue"]');
            if (continueBtn) continueBtn.click();
        }

        // Esc = Go back
        if (e.key === 'Escape') {
            if (document.activeElement.tagName === 'INPUT' ||
                document.activeElement.tagName === 'TEXTAREA') {
                document.activeElement.blur();
                return;
            }
            window.history.back();
        }

        // Ctrl+F = Focus on search
        if (e.ctrlKey && e.key === 'f') {
            const searchInput = document.querySelector('#searchbar');
            if (searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
        }
    });

    // ============ Form Enhancements ============
    document.addEventListener('DOMContentLoaded', function () {

        // Add placeholders to common fields
        const placeholders = {
            'name': 'أدخل الاسم هنا...',
            'title': 'أدخل العنوان هنا...',
            'description': 'اكتب وصفاً تفصيلياً...',
            'number': 'رقم الهاتف (مثال: 191)',
            'email': 'example@email.com',
            'address_text': 'أدخل العنوان التفصيلي...',
            'latitude': '15.354',
            'longitude': '44.205',
        };

        Object.keys(placeholders).forEach(name => {
            document.querySelectorAll(`input[name$="${name}"], textarea[name$="${name}"]`).forEach(input => {
                if (!input.placeholder) {
                    input.placeholder = placeholders[name];
                }
            });
        });

        // Auto-focus first input
        const firstInput = document.querySelector('.form-row input:not([type="hidden"]):not([type="checkbox"]), .form-row textarea');
        if (firstInput) {
            firstInput.focus();
        }

        // Add character counter to textareas
        document.querySelectorAll('textarea').forEach(textarea => {
            if (textarea.maxLength && textarea.maxLength > 0) {
                const counter = document.createElement('div');
                counter.className = 'char-counter';
                counter.style.cssText = 'text-align: left; font-size: 11px; color: #6c757d; margin-top: 4px;';
                textarea.parentNode.appendChild(counter);

                const updateCounter = () => {
                    counter.textContent = `${textarea.value.length} / ${textarea.maxLength}`;
                };
                textarea.addEventListener('input', updateCounter);
                updateCounter();
            }
        });

        // Smooth scroll to errors
        const errorList = document.querySelector('.errorlist');
        if (errorList) {
            errorList.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // Add confirmation for delete buttons
        document.querySelectorAll('.deletelink, [name="delete"]').forEach(btn => {
            btn.addEventListener('click', function (e) {
                if (!confirm('هل أنت متأكد من الحذف؟ لا يمكن التراجع عن هذا الإجراء.')) {
                    e.preventDefault();
                }
            });
        });

        // Image preview on file select
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', function (e) {
                const file = e.target.files[0];
                if (file && file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        let preview = input.parentNode.querySelector('.file-preview');
                        if (!preview) {
                            preview = document.createElement('img');
                            preview.className = 'file-preview';
                            preview.style.cssText = 'max-width: 150px; max-height: 150px; margin-top: 10px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);';
                            input.parentNode.appendChild(preview);
                        }
                        preview.src = e.target.result;
                    };
                    reader.readAsDataURL(file);
                }
            });
        });

        // Toast notification on successful actions
        const successMessage = document.querySelector('.messagelist .success');
        if (successMessage) {
            successMessage.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; padding: 16px 24px; background: #28a745; color: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(40, 167, 69, 0.4); animation: slideDown 0.3s ease;';
            setTimeout(() => {
                successMessage.style.opacity = '0';
                successMessage.style.transition = 'opacity 0.3s ease';
            }, 3000);
        }
    });

    // ============ Accordion for Module ============
    window.toggleModule = function (moduleId) {
        const header = document.querySelector(`[data-module="${moduleId}"] .module-header`);
        const content = document.getElementById(`module-${moduleId}`);

        if (header && content) {
            header.classList.toggle('expanded');
            content.classList.toggle('open');

            const expanded = JSON.parse(localStorage.getItem('adminModules') || '{}');
            expanded[moduleId] = content.classList.contains('open');
            localStorage.setItem('adminModules', JSON.stringify(expanded));
        }
    };

    // Restore module states
    document.addEventListener('DOMContentLoaded', function () {
        const expanded = JSON.parse(localStorage.getItem('adminModules') || '{}');
        Object.keys(expanded).forEach(moduleId => {
            const header = document.querySelector(`[data-module="${moduleId}"] .module-header`);
            const content = document.getElementById(`module-${moduleId}`);
            if (header && content) {
                if (expanded[moduleId]) {
                    header.classList.add('expanded');
                    content.classList.add('open');
                } else {
                    header.classList.remove('expanded');
                    content.classList.remove('open');
                }
            }
        });
    });

    // ============ AJAX Toggles ============
    document.addEventListener('click', function (e) {
        const toggleBtn = e.target.closest('.active-toggle');
        if (!toggleBtn) return;

        e.preventDefault();
        const id = toggleBtn.dataset.id;
        const app = toggleBtn.dataset.app;
        const model = toggleBtn.dataset.model;
        const field = toggleBtn.dataset.field;
        const isCurrentlyActive = toggleBtn.classList.contains('btn-success');
        const newValue = !isCurrentlyActive;

        toggleBtn.disabled = true;
        toggleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        const formData = new FormData();
        formData.append('app_label', app);
        formData.append('model_name', model);
        formData.append('object_id', id);
        formData.append('field_name', field);
        formData.append('value', newValue ? 'true' : 'false');
        
        // Robust CSRF retrieval
        let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) {
            csrfToken = getCookie('csrftoken');
        }
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch('/admin/toggle_boolean_field/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI
                if (data.new_value) {
                    toggleBtn.classList.replace('btn-light', 'btn-success');
                    toggleBtn.querySelector('i').className = 'fas fa-toggle-on';
                } else {
                    toggleBtn.classList.replace('btn-success', 'btn-light');
                    toggleBtn.querySelector('i').className = 'fas fa-toggle-off';
                }
                
                // Optional: Update status badge if next to it
                const badge = toggleBtn.parentNode.querySelector('.badge');
                if (badge && app === 'surveys' && model === 'survey') {
                   // Status might change more complexly, relative refresh could be better
                   // but for simple cases:
                   if (!data.new_value) {
                       badge.className = 'badge bg-secondary p-2';
                       badge.innerHTML = '<i class="fas fa-lock me-1"></i> غير نشط';
                   } else {
                       // Logic for 'Active' depends on other factors, so we might leave it or refresh
                       location.reload(); // Simple fallback for complex status logic
                   }
                }
            } else {
                alert('خطأ: ' + data.error);
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            location.reload();
        })
        .finally(() => {
            toggleBtn.disabled = false;
        });
    });

    // Helper for CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Console log for available shortcuts
    console.log('🎹 اختصارات لوحة المفاتيح:');
    console.log('   Ctrl+S = حفظ');
    console.log('   Ctrl+Shift+S = حفظ واستمرار');
    console.log('   Ctrl+F = بحث');
    console.log('   Esc = رجوع');
})();
