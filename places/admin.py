from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.html import format_html
from django import forms
from django.db import models
from .models import Place, Establishment, Landmark, ServicePoint, Category, Amenity, EstablishmentUnit, PlaceMedia
from management.admin_actions import export_as_csv
from management.forms import CsvImportForm
from management.importers import CsvImporter


class PlaceMediaInline(admin.TabularInline):
    model = PlaceMedia
    extra = 1
    classes = ['collapse']

class EstablishmentUnitInline(admin.TabularInline):
    model = EstablishmentUnit
    extra = 1
    classes = ['collapse']


# ============ Custom Filters ============
class OperationalStatusFilter(admin.SimpleListFilter):
    title = 'الحالة التشغيلية'
    parameter_name = 'operational_status'

    def lookups(self, request, model_admin):
        return [
            ('active', '✅ نشط'),
            ('closed', '🚫 مغلق'),
            ('maintenance', '🔧 صيانة'),
            ('dangerous', '⚠️ خطر'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(operational_status=self.value())
        return queryset


# ============ Admin Classes ============
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Enhanced Category Admin with hierarchy visualization."""
    list_display = ('icon_preview', 'name', 'parent', 'places_count')
    list_display_links = ('icon_preview', 'name')
    search_fields = ('name',)
    list_filter = ('parent',)
    save_on_top = True
    list_per_page = 20
    ordering = ('name',)
    actions = ['duplicate_selected']

    fieldsets = (
        ('📂 معلومات التصنيف', {
            'fields': ('name', 'parent', 'icon'),
        }),
    )

    @admin.display(description='الأيقونة')
    def icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" width="32" height="32" style="border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1);"/>',
                obj.icon.url
            )
        return format_html('<span style="color:#6c757d; font-size:20px;">📁</span>')

    @admin.display(description='الأماكن')
    def places_count(self, obj):
        count = obj.places.count() if hasattr(obj, 'places') else 0
        color = '#28a745' if count > 0 else '#6c757d'
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:11px;">{}</span>',
            color, count
        )

    @admin.action(description='📋 تكرار التصنيفات المحددة')
    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.name = f"{obj.name} (نسخة)"
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} تصنيف بنجاح", messages.SUCCESS)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    """Enhanced Amenity Admin with visual management."""
    list_display = ('icon_preview', 'name', 'usage_count')
    list_display_links = ('icon_preview', 'name')
    search_fields = ('name',)
    save_on_top = True
    list_per_page = 20
    actions = ['duplicate_selected']

    fieldsets = (
        ('🏷️ معلومات المرفق', {
            'fields': ('name', 'icon'),
            'description': 'مثال: واي فاي، موقف سيارات، مسبح'
        }),
    )

    @admin.display(description='الأيقونة')
    def icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" width="32" height="32" style="border-radius:6px; background:#f8f9fa; padding:4px;"/>',
                obj.icon.url
            )
        return format_html('<span style="color:#17a2b8; font-size:20px;">🏷️</span>')

    @admin.display(description='الاستخدام')
    def usage_count(self, obj):
        count = obj.establishments.count() if hasattr(obj, 'establishments') else 0
        return format_html(
            '<span style="background:#17a2b8; color:white; padding:3px 10px; border-radius:12px; font-size:11px;">{} منشأة</span>',
            count
        )

    @admin.action(description='📋 تكرار المرافق المحددة')
    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.name = f"{obj.name} (نسخة)"
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} مرفق بنجاح", messages.SUCCESS)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    change_form_template = "admin/tabbed_change_form.html"
    list_display = ('name', 'category', 'status_badge', 'avg_rating', 'is_active', 'directorate', 'created_at')
    list_filter = (OperationalStatusFilter, 'category', 'is_active', 'directorate', 'price_range')
    search_fields = ('name', 'description', 'address_text')
    inlines = [PlaceMediaInline]
    autocomplete_fields = ['category']
    save_on_top = True
    list_per_page = 20
    list_editable = ('is_active',)
    formfield_overrides = {
        models.BooleanField: {'widget': forms.CheckboxInput(attrs={'class': 'toggle-active'})},
    }
    date_hierarchy = 'created_at'
    actions = ['duplicate_selected', 'activate_selected', 'deactivate_selected', export_as_csv]
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'category', 'description', 'cover_image'),
            'description': 'أدخل البيانات الرئيسية للمكان'
        }),
        ('الموقع الجغرافي', {
            'fields': ('directorate', 'address_text', ('latitude', 'longitude')),
        }),
        ('التصنيفات والخصائص', {
            'fields': (('price_range', 'road_condition'), ('classification', 'best_season')),
        }),
        ('الحالة والتشغيل', {
            'fields': ('is_active', 'operational_status', 'status_note', 'reopening_date'),
        }),
        ('ساعات العمل والتواصل', {
            'fields': ('opening_hours_text', 'contact_info'),
        }),
        ('الإحصائيات (للقراءة فقط)', {
            'fields': (('avg_rating', 'rating_count'), 'view_count'),
        }),
    )
    readonly_fields = ('avg_rating', 'rating_count', 'view_count', 'rating_distribution', 'created_at', 'updated_at')

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {
            'active': '#28a745', 'closed': '#dc3545', 'maintenance': '#ffc107',
            'seasonal': '#17a2b8', 'dangerous': '#dc3545',
        }
        labels = {
            'active': 'نشط', 'closed': 'مغلق', 'maintenance': 'صيانة',
            'seasonal': 'موسمي', 'dangerous': 'خطر',
        }
        color = colors.get(obj.operational_status, '#6c757d')
        label = labels.get(obj.operational_status, obj.operational_status)
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:12px; font-size:11px;">{}</span>',
            color, label
        )

    @admin.action(description='تفعيل المحدد')
    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {queryset.count()} مكان")

    @admin.action(description='إلغاء تفعيل المحدد')
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {queryset.count()} مكان")

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "تكرار العناصر المحددة"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data["csv_file"]
                result = CsvImporter.import_places(csv_file, request.user.username)
                
                if result['errors']:
                     messages.warning(request, f"Imported {result['created']} places with errors: " + "; ".join(result['errors']))
                else:
                    messages.success(request, f"Successfully imported {result['created']} places.")
                return redirect("admin:places_place_changelist")
        else:
            form = CsvImportForm()
        
        context = {
            "form": form,
            "title": "Import Places from CSV",
            "opts": self.model._meta,
        }
        return render(request, "admin/csv_form.html", context)


class ApprovalStatusFilter(admin.SimpleListFilter):
    title = 'حالة الاعتماد'
    parameter_name = 'approval_status'

    def lookups(self, request, model_admin):
        return [
            ('pending', '⏳ قيد المراجعة'),
            ('approved', '✅ معتمد'),
            ('rejected', '❌ مرفوض'),
            ('draft', '📝 مسودة'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(approval_status=self.value())
        return queryset


@admin.register(Establishment)
class EstablishmentAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    list_display = ('name', 'owner', 'approval_badge', 'license_badge', 'category', 'is_open_badge', 'created_at')

    list_filter = (ApprovalStatusFilter, 'license_status', 'category', 'is_active', 'is_verified')
    search_fields = ('name', 'owner__username', 'owner__email', 'description')
    inlines = [EstablishmentUnitInline, PlaceMediaInline]
    filter_horizontal = ('amenities',)
    autocomplete_fields = ['owner', 'category', 'approved_by']
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['approve_establishments', 'reject_establishments', 'mark_verified', 'duplicate_selected', export_as_csv]
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'owner', 'category', 'description', 'cover_image'),
        }),
        ('حالة الاعتماد', {
            'fields': (('approval_status', 'is_active'), ('approved_by', 'approved_at'), 'rejected_reason'),
            'classes': ('wide',),
        }),
        ('الترخيص والتحقق', {
            'fields': (('license_status', 'is_verified'), ('license_image', 'commercial_registry_image'), 'license_expiry_date'),
        }),
        ('المرافق والخدمات', {
            'fields': ('amenities',),
            'classes': ('collapse',),
        }),
        ('حالة التشغيل', {
            'fields': (('is_open_now', 'is_suspended'), 'suspension_reason', 'suspension_end_date'),
            'classes': ('collapse',),
        }),
        ('الإحصائيات', {
            'fields': (('cached_avg_rating', 'cached_rating_count', 'cached_review_count'),),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('approved_at', 'cached_avg_rating', 'cached_rating_count', 'cached_review_count', 'created_at', 'updated_at')

    @admin.display(description='الاعتماد')
    def approval_badge(self, obj):
        colors = {'draft': '#6c757d', 'pending': '#ffc107', 'approved': '#28a745', 'rejected': '#dc3545'}
        labels = {'draft': 'مسودة', 'pending': 'قيد المراجعة', 'approved': 'معتمد', 'rejected': 'مرفوض'}
        color = colors.get(obj.approval_status, '#6c757d')
        label = labels.get(obj.approval_status, obj.approval_status)
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color, label
        )

    @admin.display(description='الترخيص')
    def license_badge(self, obj):
        colors = {'approved': '#28a745', 'pending': '#ffc107', 'rejected': '#dc3545', 'Pending': '#ffc107'}
        color = colors.get(obj.license_status, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:12px; font-size:10px;">{}</span>',
            color, obj.license_status
        )

    @admin.display(description='مفتوح')
    def is_open_badge(self, obj):
        if obj.is_suspended:
            return format_html('<span style="color:#dc3545;" title="معلق">⛔</span>')
        if obj.is_open_now:
            return format_html('<span style="color:#28a745;">🟢</span>')
        return format_html('<span style="color:#dc3545;">🔴</span>')

    @admin.action(description='✅ اعتماد المنشآت المحددة')
    def approve_establishments(self, request, queryset):
        count = 0
        for est in queryset.filter(approval_status__in=['pending', 'rejected']):
            est.approve(by_admin=request.user)
            count += 1
        self.message_user(request, f"تم اعتماد {count} منشأة", messages.SUCCESS)

    @admin.action(description='❌ رفض المنشآت المحددة')
    def reject_establishments(self, request, queryset):
        count = 0
        for est in queryset.filter(approval_status__in=['pending', 'approved']):
            est.reject(by_admin=request.user, reason='تم الرفض من قبل المسؤول')
            count += 1
        self.message_user(request, f"تم رفض {count} منشأة", messages.WARNING)

    @admin.action(description='🏅 تحديد كموثق')
    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"تم توثيق {queryset.count()} منشأة", messages.SUCCESS)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.approval_status = 'draft'
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "تكرار العناصر المحددة"



@admin.register(Landmark)
class LandmarkAdmin(admin.ModelAdmin):
    """Enhanced Landmark Admin with organized fieldsets and visual badges."""
    change_form_template = "admin/tabbed_change_form.html"
    
    list_display = (
        'name', 'type_badge', 'verified_badge', 'unesco_badge',
        'category', 'status_badge', 'best_visit_time', 'created_at'
    )
    list_filter = (
        'landmark_type', 'is_verified', 'unesco_listed',
        'operational_status', 'is_active', 'category', 'directorate'
    )
    search_fields = ('name', 'description', 'landmark_type', 'historical_period')
    inlines = [PlaceMediaInline]
    autocomplete_fields = ['category', 'verified_by']
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['verify_landmarks', 'unverify_landmarks', 'mark_unesco', 'duplicate_selected']
    
    fieldsets = (
        ('📍 المعلومات الأساسية', {
            'fields': ('name', 'category', 'description', 'cover_image'),
            'description': 'بيانات المعلم الرئيسية'
        }),
        ('🏛️ نوع المعلم والتصنيف', {
            'fields': (
                ('landmark_type', 'official_classification'),
                ('historical_period', 'estimated_age'),
                'conservation_status'
            ),
        }),
        ('📍 الموقع الجغرافي', {
            'fields': ('directorate', 'address_text', ('latitude', 'longitude')),
        }),
        ('✅ التوثيق والاعتماد', {
            'fields': (
                ('is_verified', 'unesco_listed'),
                ('verified_by', 'verified_at'),
                'verification_notes'
            ),
            'classes': ('wide',),
        }),
        ('🌤️ معلومات الزيارة', {
            'fields': (
                'best_visit_time', 'climate_description',
                'safety_instructions', 'photography_rules'
            ),
            'classes': ('collapse',),
        }),
        ('⚙️ الحالة والتشغيل', {
            'fields': (
                ('is_active', 'operational_status'),
                'status_note', 'reopening_date'
            ),
            'classes': ('collapse',),
        }),
        ('📊 الإحصائيات', {
            'fields': (('avg_rating', 'rating_count'), 'view_count'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = (
        'avg_rating', 'rating_count', 'view_count', 'verified_at',
        'created_at', 'updated_at'
    )

    @admin.display(description='النوع')
    def type_badge(self, obj):
        colors = {
            'historical': '#8b4513', 'natural': '#228b22', 'religious': '#6f42c1',
            'archaeological': '#cd853f', 'cultural': '#17a2b8', 'other': '#6c757d',
        }
        labels = {
            'historical': '🏛️ تاريخي', 'natural': '🌿 طبيعي', 'religious': '🕌 ديني',
            'archaeological': '⚱️ أثري', 'cultural': '🎭 ثقافي', 'other': '📍 أخرى',
        }
        color = colors.get(obj.landmark_type, '#6c757d')
        label = labels.get(obj.landmark_type, obj.landmark_type or '-')
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color, label
        )

    @admin.display(description='التوثيق')
    def verified_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="background:#28a745; color:white; padding:3px 8px; border-radius:12px; font-size:10px;">✅ موثق</span>'
            )
        return format_html(
            '<span style="background:#ffc107; color:#333; padding:3px 8px; border-radius:12px; font-size:10px;">⏳ غير موثق</span>'
        )

    @admin.display(description='يونسكو')
    def unesco_badge(self, obj):
        if obj.unesco_listed:
            return format_html(
                '<span style="background:#0d6efd; color:white; padding:3px 8px; border-radius:12px; font-size:10px;">🌍 UNESCO</span>'
            )
        return '-'

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {
            'active': '#28a745', 'closed': '#dc3545', 'maintenance': '#ffc107',
            'seasonal': '#17a2b8', 'dangerous': '#dc3545',
        }
        labels = {
            'active': '✅ نشط', 'closed': '🚫 مغلق', 'maintenance': '🔧 صيانة',
            'seasonal': '📅 موسمي', 'dangerous': '⚠️ خطر',
        }
        color = colors.get(obj.operational_status, '#6c757d')
        label = labels.get(obj.operational_status, obj.operational_status)
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:12px; font-size:10px;">{}</span>',
            color, label
        )

    @admin.action(description='✅ توثيق المعالم المحددة')
    def verify_landmarks(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(is_verified=False).update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f"تم توثيق {count} معلم", messages.SUCCESS)

    @admin.action(description='❌ إلغاء توثيق المعالم المحددة')
    def unverify_landmarks(self, request, queryset):
        count = queryset.filter(is_verified=True).update(
            is_verified=False,
            verified_by=None,
            verified_at=None,
            verification_notes=''
        )
        self.message_user(request, f"تم إلغاء توثيق {count} معلم", messages.WARNING)

    @admin.action(description='🌍 تحديد كموقع يونسكو')
    def mark_unesco(self, request, queryset):
        count = queryset.update(unesco_listed=True)
        self.message_user(request, f"تم تحديد {count} معلم كموقع يونسكو", messages.SUCCESS)

    @admin.action(description='📋 تكرار العناصر المحددة')
    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.is_verified = False
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} معلم بنجاح")


@admin.register(ServicePoint)
class ServicePointAdmin(admin.ModelAdmin):
    """Enhanced ServicePoint Admin for auxiliary services."""
    change_form_template = "admin/tabbed_change_form.html"
    
    list_display = (
        'service_icon', 'name', 'type_badge', 'is_24_hours_badge',
        'accessibility_badge', 'phone_number', 'status_badge'
    )
    list_display_links = ('service_icon', 'name')
    list_filter = ('service_type', 'is_24_hours', 'has_disabled_access', 'is_active', 'directorate')
    search_fields = ('name', 'phone_number', 'address_text')
    inlines = [PlaceMediaInline]
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['mark_24_hours', 'mark_accessible', 'activate_selected', 'deactivate_selected', 'duplicate_selected']

    fieldsets = (
        ('📍 المعلومات الأساسية', {
            'fields': ('name', 'service_type', 'description', 'cover_image'),
        }),
        ('📞 معلومات الاتصال', {
            'fields': ('phone_number', 'website'),
        }),
        ('📍 الموقع', {
            'fields': ('directorate', 'address_text', ('latitude', 'longitude')),
        }),
        ('⚙️ الخصائص', {
            'fields': (('is_24_hours', 'has_disabled_access'), ('is_active', 'operational_status')),
        }),
        ('⏰ ساعات العمل', {
            'fields': ('opening_hours_text',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='')
    def service_icon(self, obj):
        icons = {
            'bank': ('🏦', '#2c5282'), 'atm': ('💳', '#38a169'),
            'car_rental': ('🚗', '#dd6b20'), 'restroom': ('🚻', '#718096'),
            'mosque': ('🕌', '#805ad5'), 'parking': ('🅿️', '#3182ce'),
            'hospital': ('🏥', '#e53e3e'), 'pharmacy': ('💊', '#38b2ac'),
            'police': ('👮', '#2b6cb0'), 'gas_station': ('⛽', '#d69e2e'),
        }
        icon, color = icons.get(obj.service_type, ('📍', '#6c757d'))
        return format_html(
            '<span style="font-size:24px; background:{}20; padding:6px; border-radius:8px;">{}</span>',
            color, icon
        )

    @admin.display(description='النوع')
    def type_badge(self, obj):
        colors = {
            'bank': '#2c5282', 'atm': '#38a169', 'car_rental': '#dd6b20',
            'restroom': '#718096', 'mosque': '#805ad5', 'parking': '#3182ce',
            'hospital': '#e53e3e', 'pharmacy': '#38b2ac', 'police': '#2b6cb0',
            'gas_station': '#d69e2e',
        }
        color = colors.get(obj.service_type, '#6c757d')
        label = obj.get_service_type_display() if hasattr(obj, 'get_service_type_display') else obj.service_type
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:12px; font-size:11px;">{}</span>',
            color, label
        )

    @admin.display(description='24 ساعة')
    def is_24_hours_badge(self, obj):
        if obj.is_24_hours:
            return format_html(
                '<span style="background:#28a745; color:white; padding:3px 8px; border-radius:12px; font-size:10px;">🕐 24/7</span>'
            )
        return format_html('<span style="color:#adb5bd;">—</span>')

    @admin.display(description='إمكانية الوصول')
    def accessibility_badge(self, obj):
        if obj.has_disabled_access:
            return format_html(
                '<span style="background:#6f42c1; color:white; padding:3px 8px; border-radius:12px; font-size:10px;">♿ مجهز</span>'
            )
        return format_html('<span style="color:#adb5bd;">—</span>')

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#28a745;">✅</span>')
        return format_html('<span style="color:#dc3545;">❌</span>')

    @admin.action(description='🕐 تحديد كخدمة 24 ساعة')
    def mark_24_hours(self, request, queryset):
        count = queryset.update(is_24_hours=True)
        self.message_user(request, f"تم تحديد {count} نقطة خدمة كـ 24 ساعة", messages.SUCCESS)

    @admin.action(description='♿ تحديد كمجهز لذوي الهمم')
    def mark_accessible(self, request, queryset):
        count = queryset.update(has_disabled_access=True)
        self.message_user(request, f"تم تحديد {count} نقطة خدمة كمجهزة لذوي الهمم", messages.SUCCESS)

    @admin.action(description='✅ تفعيل المحدد')
    def activate_selected(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {count} نقطة خدمة", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل المحدد')
    def deactivate_selected(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {count} نقطة خدمة", messages.WARNING)

    @admin.action(description='📋 تكرار العناصر المحددة')
    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} نقطة خدمة بنجاح", messages.SUCCESS)
