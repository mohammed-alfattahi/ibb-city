document.addEventListener('DOMContentLoaded', function () {
    const fieldsets = document.querySelectorAll('form fieldset.module');
    if (fieldsets.length <= 1) return;

    // Create Tabs Container
    const tabsContainer = document.createElement('div');
    tabsContainer.className = 'tabs-container';

    const tabsList = document.createElement('ul');
    tabsList.className = 'admin-tabs';
    tabsContainer.appendChild(tabsList);

    // Insert tabs before the first fieldset
    const firstFieldset = fieldsets[0];
    firstFieldset.parentNode.insertBefore(tabsContainer, firstFieldset);

    // Add class to form
    const form = document.querySelector('#content-main form');
    if (form) form.classList.add('tabbed-form');

    // Icon Mapping (Arabic & English Keywords)
    const iconMap = {
        // Arabic
        'المعلومات الأساسية': 'fa-info-circle',
        'الموقع الجغرافي': 'fa-map-marked-alt',
        'التصنيفات والخصائص': 'fa-tags',
        'الحالة والتشغيل': 'fa-power-off',
        'ساعات العمل والتواصل': 'fa-clock',
        'الإحصائيات': 'fa-chart-pie',
        'المرفقات': 'fa-paperclip',
        'الوسائط': 'fa-images',
        'Place medias': 'fa-images',
        'بيانات الدخول': 'fa-user-lock',
        'المعلومات الشخصية': 'fa-id-card',
        'الصلاحيات': 'fa-user-shield',
        'الدور والوظائف': 'fa-user-tag',
        'تواريخ مهمة': 'fa-calendar-alt',
        'عام': 'fa-layer-group',
        // English Fallbacks
        'General': 'fa-layer-group',
        'Location': 'fa-map-marker-alt',
        'Permissions': 'fa-lock',
        'Important dates': 'fa-calendar',
        'Personal info': 'fa-user'
    };

    function getIconForTitle(title) {
        // Direct match
        if (iconMap[title]) return iconMap[title];

        // Partial match
        for (const [key, icon] of Object.entries(iconMap)) {
            if (title.includes(key)) return icon;
        }

        return 'fa-circle'; // Default
    }

    // Generate Tabs
    fieldsets.forEach((fieldset, index) => {
        const legend = fieldset.querySelector('h2');
        let title = 'عام';

        if (legend) {
            title = legend.innerText;
            // Don't remove legend entirely, just hide it so screen readers might still access structure if needed
            // But visually we want clean form
            legend.style.display = 'none';
        }

        const tab = document.createElement('li');
        tab.className = 'admin-tab';
        if (index === 0) tab.classList.add('active');

        // Create Icon
        const iconClass = getIconForTitle(title);
        tab.innerHTML = `<i class="fas ${iconClass}"></i> ${title}`;

        tab.dataset.targetIndex = index;

        tab.addEventListener('click', function () {
            // Deactivate all
            document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
            fieldsets.forEach(f => f.classList.remove('active'));

            // Activate clicked
            this.classList.add('active');
            fieldsets[index].classList.add('active');

            // Scroll alignment
            const rect = tabsContainer.getBoundingClientRect();
            if (rect.top < 0) {
                window.scrollTo({ top: window.scrollY + rect.top - 60, behavior: 'smooth' });
            }
        });

        tabsList.appendChild(tab);

        // Initialize first as active
        if (index === 0) fieldset.classList.add('active');
    });

    // Move inline help text
    document.querySelectorAll('.help').forEach(help => {
        const row = help.closest('.form-row');
        if (row && !row.querySelector('.help-moved')) {
            row.appendChild(help);
            help.classList.add('help-moved');
        }
    });
});
