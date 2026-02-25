"""
Admin Modules Configuration
تكوين وحدات لوحة الإدارة
"""


def get_admin_modules():
    """
    Returns the list of admin modules with their actions.
    Each module has a name, color, icon, and list of actions.
    Only uses verified admin URLs.
    """
    return [
        {
            'id': 'places',
            'name': 'إدارة الأماكن',
            'color': 'success',
            'icon': 'fa-map-marker-alt',
            'expanded': True,
            'actions': [
                {'icon': 'fa-search', 'label': 'البحث عن مكان', 'url': 'admin:places_place_changelist'},
                {'icon': 'fa-plus-circle', 'label': 'إضافة مكان', 'url': 'admin:places_place_add'},
                {'icon': 'fa-tags', 'label': 'التصنيفات', 'url': 'admin:places_category_changelist'},
                {'icon': 'fa-concierge-bell', 'label': 'المرافق', 'url': 'admin:places_amenity_changelist'},
                {'icon': 'fa-building', 'label': 'المنشآت', 'url': 'admin:places_establishment_changelist'},
            ]
        },
        {
            'id': 'users',
            'name': 'إدارة المستخدمين',
            'color': 'info',
            'icon': 'fa-users',
            'expanded': False,
            'actions': [
                {'icon': 'fa-search', 'label': 'البحث عن مستخدم', 'url': 'admin:users_user_changelist'},
                {'icon': 'fa-user-plus', 'label': 'إضافة مستخدم', 'url': 'admin:users_user_add'},
                {'icon': 'fa-user-tie', 'label': 'الشركاء', 'url': 'admin:users_partnerprofile_changelist'},
                {'icon': 'fa-users-cog', 'label': 'المجموعات', 'url': 'admin:auth_group_changelist'},
            ]
        },
        {
            'id': 'requests',
            'name': 'الطلبات والموافقات',
            'color': 'warning',
            'icon': 'fa-clipboard-list',
            'expanded': False,
            'actions': [
                {'icon': 'fa-list', 'label': 'كل الطلبات', 'url': 'admin:management_request_changelist'},
                {'icon': 'fa-plus', 'label': 'طلب جديد', 'url': 'admin:management_request_add'},
                {'icon': 'fa-history', 'label': 'سجل النظام', 'url': 'admin:management_auditlog_changelist'},
            ]
        },
        {
            'id': 'ads',
            'name': 'الإعلانات والتسويق',
            'color': 'purple',
            'icon': 'fa-bullhorn',
            'expanded': False,
            'actions': [
                {'icon': 'fa-list', 'label': 'كل الإعلانات', 'url': 'admin:management_advertisement_changelist'},
                {'icon': 'fa-plus', 'label': 'إضافة إعلان', 'url': 'admin:management_advertisement_add'},
                {'icon': 'fa-file-invoice-dollar', 'label': 'الفواتير', 'url': 'admin:management_invoice_changelist'},
                {'icon': 'fa-hand-holding-usd', 'label': 'الاستثمار', 'url': 'admin:management_investmentopportunity_changelist'},
            ]
        },
        {
            'id': 'content',
            'name': 'المحتوى والصفحات',
            'color': 'secondary',
            'icon': 'fa-file-alt',
            'expanded': False,
            'actions': [
                {'icon': 'fa-home', 'label': 'أقسام الرئيسية', 'url': 'admin:management_homepagesection_changelist'},
                {'icon': 'fa-images', 'label': 'شرائح العرض', 'url': 'admin:management_heroslide_changelist'},
                {'icon': 'fa-bars', 'label': 'القوائم', 'url': 'admin:management_menu_changelist'},
            ]
        },
        {
            'id': 'system',
            'name': 'إعدادات النظام',
            'color': 'dark',
            'icon': 'fa-cog',
            'expanded': False,
            'actions': [
                {'icon': 'fa-sliders-h', 'label': 'إعدادات الموقع', 'url': 'admin:management_sitesetting_changelist'},
                {'icon': 'fa-book', 'label': 'الإرشادات', 'url': 'admin:management_generalguideline_changelist'},
                {'icon': 'fa-cloud-sun', 'label': 'تنبيهات الطقس', 'url': 'admin:management_weatheralert_changelist'},
            ]
        },
    ]
