(function ($) {
    $(document).ready(function () {
        // Helper to parse body classes for app/model
        function getModelInfo() {
            var bodyClasses = $('body').attr('class').split(' ');
            var appLabel = '';
            var modelName = '';

            bodyClasses.forEach(function (cls) {
                if (cls.startsWith('app-')) appLabel = cls.replace('app-', '');
                if (cls.startsWith('model-')) modelName = cls.replace('model-', '');
            });
            return { app: appLabel, model: modelName };
        }

        var info = getModelInfo();

        // Target inputs with specific class
        $('.toggle-active').each(function () {
            var $checkbox = $(this);
            var $row = $checkbox.closest('tr');

            // derive ID from the hidden input in the same row
            // Django generic inline formset IDs usually look like form-0-id
            // The checkbox name is form-0-field_name
            var nameParts = $checkbox.attr('name').split('-');
            var prefix = nameParts[0] + '-' + nameParts[1]; // e.g., form-0
            var fieldName = nameParts.slice(2).join('-'); // handles field_name

            var $idInput = $row.find('input[name="' + prefix + '-id"]');
            var objectId = $idInput.val();

            if (!objectId || !info.app || !info.model) return; // Skip if can't identify

            // Wrap in toggle UI
            $checkbox.wrap('<div class="toggle-switch"></div>');
            $checkbox.after('<span class="toggle-slider"></span>');

            $checkbox.on('change', function () {
                var isChecked = $checkbox.is(':checked');
                var $container = $checkbox.parent();

                $container.addClass('loading');

                $.ajax({
                    url: '/admin/toggle_boolean_field/',
                    method: 'POST',
                    data: {
                        'app_label': info.app,
                        'model_name': info.model,
                        'object_id': objectId,
                        'field_name': fieldName,
                        'value': isChecked,
                        'csrfmiddlewaretoken': getCookie('csrftoken')
                    },
                    success: function (response) {
                        $container.removeClass('loading');
                        if (response.success) {
                            // Success animation or toast could go here
                        } else {
                            $checkbox.prop('checked', !isChecked);
                            alert('Error: ' + response.error);
                        }
                    },
                    error: function () {
                        $container.removeClass('loading');
                        $checkbox.prop('checked', !isChecked);
                        alert('Connection Error');
                    }
                });
            });
        });

        // Helper for CSRF
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    });
})(django.jQuery);
