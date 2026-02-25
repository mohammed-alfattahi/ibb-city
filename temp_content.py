from django.db import models
from django.utils.translation import gettext_lazy as _

# ============================================
# Phase 1: Culture & Emergency (Retained)
# ============================================

class CulturalLandmark(models.Model):
    title = models.CharField(_("ط§ظ„ط¹ظ†ظˆط§ظ†"), max_length=200)
    description = models.TextField(_("ط§ظ„ظˆطµظپ"))
    icon = models.CharField(_("ط£ظٹظ‚ظˆظ†ط© FontAwesome"), max_length=50, default="fas fa-mosque", help_text="ظ…ط«ط§ظ„: fas fa-mosque")
    color = models.CharField(_("ظ„ظˆظ† ط§ظ„ط£ظٹظ‚ظˆظ†ط©"), max_length=50, default="primary", choices=[
        ('primary', 'Primary (Blue)'),
        ('secondary', 'Secondary (Grey)'),
        ('success', 'Success (Green)'),
        ('danger', 'Danger (Red)'),
        ('warning', 'Warning (Yellow)'),
        ('info', 'Info (Cyan)'),
    ])
    image1 = models.ImageField(_("طµظˆط±ط© 1"), upload_to='culture/', blank=True, null=True)
    image2 = models.ImageField(_("طµظˆط±ط© 2"), upload_to='culture/', blank=True, null=True)
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)
    order = models.PositiveIntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("ظ…ظژط¹ظ„ظ… ط«ظ‚ط§ظپظٹ")
        verbose_name_plural = _("ط§ظ„ظ…ط¹ط§ظ„ظ… ط§ظ„ط«ظ‚ط§ظپظٹط©")
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

class PublicEmergencyContact(models.Model):
    COLOR_CHOICES = [
        ('danger', _('ط£ط­ظ…ط± (ط®ط·ط±)')),
        ('warning', _('ط£طµظپط± (طھط­ط°ظٹط±)')),
        ('success', _('ط£ط®ط¶ط± (ظ†ط¬ط§ط­)')),
        ('primary', _('ط£ط²ط±ظ‚ (ط£ط³ط§ط³ظٹ)')),
        ('info', _('ط³ظ…ط§ظˆظٹ (ظ…ط¹ظ„ظˆظ…ط§طھ)')),
        ('dark', _('ط¯ط§ظƒظ†')),
    ]

    title = models.CharField(_("ط§ظ„ط¬ظ‡ط©"), max_length=100)
    number = models.CharField(_("ط±ظ‚ظ… ط§ظ„ظ‡ط§طھظپ"), max_length=20)
    description = models.CharField(_("ط§ظ„ظˆطµظپ ط§ظ„ظ…ط®طھطµط±"), max_length=200, blank=True)
    icon = models.CharField(_("ط£ظٹظ‚ظˆظ†ط© FontAwesome"), max_length=50, help_text="ظ…ط«ط§ظ„: fas fa-ambulance")
    color = models.CharField(_("ط§ظ„ظ„ظˆظ†"), max_length=20, choices=COLOR_CHOICES, default='danger')
    is_primary_card = models.BooleanField(_("ط¹ط±ط¶ ظƒط¨ط·ط§ظ‚ط© ظƒط¨ظٹط±ط©"), default=False, help_text="طھط¸ظ‡ط± ظپظٹ ط£ط¹ظ„ظ‰ ط§ظ„طµظپط­ط© ظƒط¨ط·ط§ظ‚ط© ظƒط¨ظٹط±ط© (ظ…ط«ظ„: ط§ظ„ط´ط±ط·ط©طŒ ط§ظ„ط¥ط³ط¹ط§ظپ)")
    is_hospital = models.BooleanField(_("ظ…ط³طھط´ظپظ‰طں"), default=False, help_text="طھط¸ظ‡ط± ظپظٹ ظ‚ط§ط¦ظ…ط© ط§ظ„ظ…ط³طھط´ظپظٹط§طھ")
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)
    order = models.PositiveIntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)

    class Meta:
        verbose_name = _("ط±ظ‚ظ… ط·ظˆط§ط±ط¦ ط¹ط§ظ…")
        verbose_name_plural = _("ط£ط±ظ‚ط§ظ… ط§ظ„ط·ظˆط§ط±ط¦ ط§ظ„ط¹ط§ظ…ط©")
        ordering = ['order', 'title']

    def __str__(self):
        if self.is_hospital:
            return f"{self.title} (ظ…ط³طھط´ظپظ‰)"
        return f"{self.title} ({self.number})"

class SafetyGuideline(models.Model):
    COLOR_CHOICES = [
         ('danger', _('ط£ط­ظ…ط± (ط®ط·ط±)')),
        ('warning', _('ط£طµظپط± (طھط­ط°ظٹط±)')),
        ('success', _('ط£ط®ط¶ط± (ظ†ط¬ط§ط­)')),
        ('primary', _('ط£ط²ط±ظ‚ (ط£ط³ط§ط³ظٹ)')),
    ]
    title = models.CharField(_("ط§ظ„ط¹ظ†ظˆط§ظ†"), max_length=200)
    description = models.TextField(_("ط§ظ„طھظپط§طµظٹظ„"))
    icon = models.CharField(_("ط£ظٹظ‚ظˆظ†ط© FontAwesome"), max_length=50)
    color = models.CharField(_("ط§ظ„ظ„ظˆظ†"), max_length=20, choices=COLOR_CHOICES, default='primary')
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)
    order = models.PositiveIntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)

    class Meta:
        verbose_name = _("ط¥ط±ط´ط§ط¯ط§طھ ط§ظ„ط³ظ„ط§ظ…ط©")
        verbose_name_plural = _("ط¥ط±ط´ط§ط¯ط§طھ ط§ظ„ط³ظ„ط§ظ…ط©")
        ordering = ['order']

    def __str__(self):
        return self.title

# ============================================
# Phase 2: Base Architecture (Core)
# ============================================

class SiteSetting(models.Model):
    site_name = models.CharField(_("ط§ط³ظ… ط§ظ„ظ…ظˆظ‚ط¹"), max_length=200, default="ط¯ظ„ظٹظ„ ط¥ط¨ ط§ظ„ط³ظٹط§ط­ظٹ")
    logo = models.ImageField(_("ط§ظ„ط´ط¹ط§ط±"), upload_to="site/", default="site/default_logo.png")
    primary_color = models.CharField(_("ط§ظ„ظ„ظˆظ† ط§ظ„ط£ط³ط§ط³ظٹ"), max_length=20, default="#0d6efd")
    
    # Footer Content
    footer_text = models.TextField(_("ظ†طµ ط§ظ„ظپظˆطھط±"), blank=True)
    copyright_text = models.CharField(_("ظ†طµ ط§ظ„ط­ظ‚ظˆظ‚"), max_length=200, blank=True)
    
    # Contact Info
    contact_email = models.EmailField(_("ط§ظ„ط¨ط±ظٹط¯ ط§ظ„ط¥ظ„ظƒطھط±ظˆظ†ظٹ ظ„ظ„طھظˆط§طµظ„"), blank=True)
    contact_phone = models.CharField(_("ط±ظ‚ظ… ط§ظ„ظ‡ط§طھظپ ظ„ظ„طھظˆط§طµظ„"), max_length=50, blank=True)
    address = models.CharField(_("ط§ظ„ط¹ظ†ظˆط§ظ†"), max_length=255, blank=True)
    
    # Meta / SEO
    meta_description = models.TextField(_("ظˆطµظپ ط§ظ„ظ…ظˆظ‚ط¹ (SEO)"), blank=True)
    keywords = models.CharField(_("ط§ظ„ظƒظ„ظ…ط§طھ ط§ظ„ظ…ظپطھط§ط­ظٹط©"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ظ…ظˆظ‚ط¹")
        verbose_name_plural = _("ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ظ…ظˆظ‚ط¹")

    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        if not self.pk and SiteSetting.objects.exists():
            return
        return super(SiteSetting, self).save(*args, **kwargs)

class SocialLink(models.Model):
    label = models.CharField(_("ط§ظ„ط§ط³ظ…"), max_length=50, help_text="ظ…ط«ط§ظ„: Facebook, Twitter")
    url = models.URLField(_("ط§ظ„ط±ط§ط¨ط·"))
    icon = models.CharField(_("ط£ظٹظ‚ظˆظ†ط© FontAwesome"), max_length=50, blank=True, help_text="ظ…ط«ط§ظ„: fab fa-facebook")
    order = models.IntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)

    class Meta:
        verbose_name = _("ط±ط§ط¨ط· طھظˆط§طµظ„ ط§ط¬طھظ…ط§ط¹ظٹ")
        verbose_name_plural = _("ط±ظˆط§ط¨ط· ط§ظ„طھظˆط§طµظ„ ط§ظ„ط§ط¬طھظ…ط§ط¹ظٹ")
        ordering = ['order']

    def __str__(self):
        return self.label

class Menu(models.Model):
    LOCATION_CHOICES = [
        ("header", _("ط§ظ„ظ‚ط§ط¦ظ…ط© ط§ظ„ط¹ظ„ظˆظٹط© (Header)")),
        ("footer", _("ط§ظ„ظ‚ط§ط¦ظ…ط© ط§ظ„ط³ظپظ„ظٹط© (Footer)")),
        ("sidebar", _("ط§ظ„ظ‚ط§ط¦ظ…ط© ط§ظ„ط¬ط§ظ†ط¨ظٹط© (Sidebar)")),
    ]
    
    title = models.CharField(_("ط§ظ„ط¹ظ†ظˆط§ظ†"), max_length=100)
    url = models.CharField(_("ط§ظ„ط±ط§ط¨ط·"), max_length=200)
    location = models.CharField(_("ط§ظ„ظ…ظƒط§ظ†"), max_length=20, choices=LOCATION_CHOICES)
    order = models.IntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name=_("ط§ظ„ط¹ظ†طµط± ط§ظ„ط£ط¨"))
    
    # Role-based visibility
    visible_for_guests = models.BooleanField(_("ط¸ط§ظ‡ط± ظ„ظ„ط²ظˆط§ط±"), default=True)
    visible_for_users = models.BooleanField(_("ط¸ط§ظ‡ط± ظ„ظ„ظ…ط³طھط®ط¯ظ…ظٹظ† ط§ظ„ظ…ط³ط¬ظ„ظٹظ†"), default=True)
    visible_for_admins = models.BooleanField(_("ط¸ط§ظ‡ط± ظ„ظ„ظ…ط³ط¤ظˆظ„ظٹظ†"), default=True)

    class Meta:
        verbose_name = _("ظ‚ط§ط¦ظ…ط©")
        verbose_name_plural = _("ط§ظ„ظ‚ظˆط§ط¦ظ…")
        ordering = ['location', 'order']

    def __str__(self):
        return f"{self.title} ({self.get_location_display()})"

class SidebarWidget(models.Model):
    WIDGET_TYPES = [
        ("text", _("ظ†طµ (Text)")),
        ("links", _("ط±ظˆط§ط¨ط· (Links)")),
        ("stats", _("ط¥ط­طµط§ط¦ظٹط§طھ (Statistics)")),
        ("cta", _("ط¯ط¹ظˆط© ظ„ط§طھط®ط§ط° ط¥ط¬ط±ط§ط، (CTA)")),
        ("custom_html", _("HTML ظ…ط®طµطµ")),
    ]

    title = models.CharField(_("ط§ظ„ط¹ظ†ظˆط§ظ†"), max_length=200)
    widget_type = models.CharField(_("ظ†ظˆط¹ ط§ظ„ظˆط¬طھ"), max_length=20, choices=WIDGET_TYPES, default="text")
    content = models.TextField(_("ط§ظ„ظ…ط­طھظˆظ‰"), blank=True, help_text=_("ظ„ظ„ظ†طµطŒ HTMLطŒ ط£ظˆ ط±ط§ط¨ط· ط²ط± CTA"))
    
    # Control
    order = models.IntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)
    is_visible = models.BooleanField(_("ط¸ط§ظ‡ط±"), default=True)

    # Customization
    pages = models.JSONField(_("ط§ظ„طµظپط­ط§طھ"), default=list, blank=True, help_text='["home", "places"] list of url names')
    roles = models.JSONField(_("ط§ظ„ط£ط¯ظˆط§ط±"), default=list, blank=True, help_text='["guest", "user", "admin"]')

    class Meta:
        verbose_name = _("ظˆط¬طھ ط¬ط§ظ†ط¨ظٹ")
        verbose_name_plural = _("ظˆط¬طھط§طھ ط§ظ„ط´ط±ظٹط· ط§ظ„ط¬ط§ظ†ط¨ظٹ")
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"

class SidebarLink(models.Model):
    widget = models.ForeignKey(SidebarWidget, related_name="links", on_delete=models.CASCADE, verbose_name=_("ط§ظ„ظˆظٹط¯ط¬طھ"))
    title = models.CharField(_("ط§ظ„ط¹ظ†ظˆط§ظ†"), max_length=150)
    url = models.CharField(_("ط§ظ„ط±ط§ط¨ط·"), max_length=300)
    order = models.IntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)
    
    class Meta:
        verbose_name = _("ط±ط§ط¨ط· ط¬ط§ظ†ط¨ظٹ")
        verbose_name_plural = _("ط±ظˆط§ط¨ط· ط¬ط§ظ†ط¨ظٹط©")
        ordering = ['order']
        
    def __str__(self):
        return self.title


# ============================================
# Phase 3: Dynamic Pages (Home, etc)
# ============================================

class HomePageSection(models.Model):
    SECTION_TYPES = [
        ('hero', _('Hero Section - ط§ظ„ط¹ط±ط¶ ط§ظ„ط±ط¦ظٹط³ظٹ')),
        ('featured_grid', _('Featured Grid - ط´ط¨ظƒط© ط§ظ„ظ…ظ…ظٹط²ط§طھ')),
        ('quick_access', _('Quick Access - ط§ظ„ظˆطµظˆظ„ ط§ظ„ط³ط±ظٹط¹')),
        ('partners', _('Partners Slider - ط´ط±ظٹط· ط§ظ„ط´ط±ظƒط§ط،')),
        ('custom_html', _('Custom HTML - ظ…ط­طھظˆظ‰ ظ…ط®طµطµ')),
    ]

    title = models.CharField(_("ط¹ظ†ظˆط§ظ† ط§ظ„ظ‚ط³ظ…"), max_length=200, help_text=_("ظ„ظ„ط¹ط±ط¶ ظپظٹ ظ„ظˆط­ط© ط§ظ„طھط­ظƒظ…"))
    section_type = models.CharField(_("ظ†ظˆط¹ ط§ظ„ظ‚ط³ظ…"), max_length=50, choices=SECTION_TYPES, default='custom_html')
    content = models.TextField(_("ط§ظ„ظ…ط­طھظˆظ‰ (HTML)"), blank=True, help_text=_("ظٹط³طھط®ط¯ظ… ظپظ‚ط· ظ…ط¹ ظ†ظˆط¹ Custom HTML"))
    
    is_visible = models.BooleanField(_("ط¸ط§ظ‡ط±"), default=True)
    order = models.PositiveIntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)

    class Meta:
        verbose_name = _("ظ‚ط³ظ… ط§ظ„طµظپط­ط© ط§ظ„ط±ط¦ظٹط³ظٹط©")
        verbose_name_plural = _("ط£ظ‚ط³ط§ظ… ط§ظ„طµظپط­ط© ط§ظ„ط±ط¦ظٹط³ظٹط©")
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_section_type_display()})"

class HeroSlide(models.Model):
    title = models.CharField(_("ط§ظ„ط¹ظ†ظˆط§ظ† ط§ظ„ط±ط¦ظٹط³ظٹ"), max_length=200)
    subtitle = models.CharField(_("ط§ظ„ط¹ظ†ظˆط§ظ† ط§ظ„ظپط±ط¹ظٹ"), max_length=200, blank=True)
    image = models.ImageField(_("طµظˆط±ط© ط§ظ„ط®ظ„ظپظٹط©"), upload_to='hero/')
    button_text = models.CharField(_("ظ†طµ ط§ظ„ط²ط±"), max_length=50, blank=True)
    button_link = models.CharField(_("ط±ط§ط¨ط· ط§ظ„ط²ط±"), max_length=200, blank=True)
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)
    order = models.PositiveIntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)

    class Meta:
        verbose_name = _("ط´ط±ظٹط­ط© ط§ظ„ط¹ط±ط¶ (Hero Slide)")
        verbose_name_plural = _("ط´ط±ط§ط¦ط­ ط§ظ„ط¹ط±ط¶ ط§ظ„ط±ط¦ظٹط³ظٹط©")
        ordering = ['order']

    def __str__(self):
        return self.title

class TeamMember(models.Model):
    name = models.CharField(_("ط§ظ„ط§ط³ظ…"), max_length=100)
    role = models.CharField(_("ط§ظ„ظ…ط³ظ…ظ‰ ط§ظ„ظˆط¸ظٹظپظٹ"), max_length=100)
    bio = models.TextField(_("ظ†ط¨ط°ط© ظ…ط®طھطµط±ط©"), blank=True)
    image = models.ImageField(_("ط§ظ„طµظˆط±ط© ط§ظ„ط´ط®طµظٹط©"), upload_to='team/')
    
    # Social Links
    twitter = models.URLField(_("طھظˆظٹطھط±"), blank=True)
    linkedin = models.URLField(_("ظ„ظٹظ†ظƒط¯ ط¥ظ†"), blank=True)
    
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)
    order = models.PositiveIntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)

    class Meta:
        verbose_name = _("ط¹ط¶ظˆ ظپط±ظٹظ‚")
        verbose_name_plural = _("ظپط±ظٹظ‚ ط§ظ„ط¹ظ…ظ„")
        ordering = ['order']

    def __str__(self):
        return self.name

class TransportCompany(models.Model):
    name = models.CharField(_("ط§ط³ظ… ط§ظ„ط´ط±ظƒط©"), max_length=100)
    logo = models.ImageField(_("ط§ظ„ط´ط¹ط§ط±"), upload_to='transport/', blank=True, null=True)
    phone = models.CharField(_("ط±ظ‚ظ… ط§ظ„ط­ط¬ط²"), max_length=20)
    whatsapp = models.CharField(_("ظˆط§طھط³ط§ط¨"), max_length=20, blank=True)
    description = models.TextField(_("ظ†ط¨ط°ط© ط¹ظ† ط§ظ„ط´ط±ظƒط©"), blank=True)
    destinations = models.CharField(_("ط§ظ„ظˆط¬ظ‡ط§طھ ط§ظ„ط±ط¦ظٹط³ظٹط©"), max_length=200, help_text="ظ…ط«ط§ظ„: طµظ†ط¹ط§ط،طŒ ط¹ط¯ظ†طŒ ط§ظ„ط­ط¯ظٹط¯ط©")
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)
    order = models.PositiveIntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)

    class Meta:
        verbose_name = _("ط´ط±ظƒط© ظ†ظ‚ظ„")
        verbose_name_plural = _("ط´ط±ظƒط§طھ ط§ظ„ظ†ظ‚ظ„")
        ordering = ['order']

    def __str__(self):
        return self.name

class ListingConfiguration(models.Model):
    PAGE_CHOICES = [
        ('place_list', _('ط¯ظ„ظٹظ„ ط§ظ„ط£ظ…ط§ظƒظ† (Place List)')),
        ('nature_list', _('ط§ظ„ط·ط¨ظٹط¹ط© (Nature)')),
        ('investment_list', _('ط§ظ„ط§ط³طھط«ظ…ط§ط± (Investment)')),
        ('events_list', _('ط§ظ„ظ…ظ†ط§ط³ط¨ط§طھ (Events)')),
        ('place_detail', _('طھظپط§طµظٹظ„ ط§ظ„ظ…ظƒط§ظ† (Place Detail)')),
    ]

    page_name = models.CharField(_("ط§ظ„طµظپط­ط©"), max_length=50, choices=PAGE_CHOICES, unique=True)
    
    # Hero Section
    hero_title = models.CharField(_("ط¹ظ†ظˆط§ظ† ط§ظ„ط¨ط§ظ†ط±"), max_length=200, default="ط§ط³طھظƒط´ظپ ط§ظ„ط£ظ…ط§ظƒظ†", help_text="ظٹط³طھط®ط¯ظ… ظƒط¹ظ†ظˆط§ظ† ط§ظپطھط±ط§ط¶ظٹ ط¥ط°ط§ ظ„ظ… ظٹظƒظ† ظ„ظ„ظ…ظƒط§ظ† طµظˆط±ط©")
    hero_subtitle = models.CharField(_("ظˆطµظپ ط§ظ„ط¨ط§ظ†ط±"), max_length=300, blank=True)
    hero_image = models.ImageField(_("طµظˆط±ط© ط§ظ„ط¨ط§ظ†ط±"), upload_to='pages/hero/', blank=True, null=True, help_text="طµظˆط±ط© ط§ظپطھط±ط§ط¶ظٹط© ظ„ظ„ظ…ظƒط§ظ†")
    
    # Filter Configuration (Lists)
    show_search = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ط§ظ„ط¨ط­ط«"), default=True)
    show_category_filter = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ظپظ„طھط± ط§ظ„طھطµظ†ظٹظپ"), default=True)
    show_rating_filter = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ظپظ„طھط± ط§ظ„طھظ‚ظٹظٹظ…"), default=True)
    show_price_filter = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ظپظ„طھط± ط§ظ„ط£ط³ط¹ط§ط±"), default=False)
    show_district_filter = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ظپظ„طھط± ط§ظ„ظ…ط¯ظٹط±ظٹط©"), default=False)
    
    # Detail Configuration (Detail Pages)
    show_gallery = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ط§ظ„ظ…ط¹ط±ط¶"), default=True)
    show_reviews = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ط§ظ„طھظ‚ظٹظٹظ…ط§طھ"), default=True)
    show_similar_places = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ط£ظ…ط§ظƒظ† ظ…ط´ط§ط¨ظ‡ط©"), default=True)
    show_sidebar = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ط§ظ„ط´ط±ظٹط· ط§ظ„ط¬ط§ظ†ط¨ظٹ"), default=True)
    show_weather_widget = models.BooleanField(_("ط¥ط¸ظ‡ط§ط± ط­ط§ظ„ط© ط§ظ„ط·ظ‚ط³"), default=True)
    
    # Display Configuration
    items_per_page = models.IntegerField(_("ط¹ط¯ط¯ ط§ظ„ط¹ظ†ط§طµط± ظپظٹ ط§ظ„طµظپط­ط©"), default=9)
    default_view_style = models.CharField(_("ظ†ظ…ط· ط§ظ„ط¹ط±ط¶ ط§ظ„ط§ظپطھط±ط§ط¶ظٹ"), max_length=20, choices=[('grid', 'ط´ط¨ظƒط©'), ('list', 'ظ‚ط§ط¦ظ…ط©')], default='grid')

    def __str__(self):
        return self.get_page_name_display()

    class Meta:
        verbose_name = _("ط¥ط¹ط¯ط§ط¯ط§طھ طµظپط­ط© ط§ظ„ظ‚ظˆط§ط¦ظ…")
        verbose_name_plural = _("ط¥ط¹ط¯ط§ط¯ط§طھ طµظپط­ط§طھ ط§ظ„ظ‚ظˆط§ط¦ظ…")


class PlaceDetailBlock(models.Model):
    BLOCK_TYPES = [
        ("hero", _("Hero Section - ط§ظ„ط¹ط±ط¶ ط§ظ„ط±ط¦ظٹط³ظٹ")),
        ("gallery", _("Image Gallery - ظ…ط¹ط±ط¶ ط§ظ„طµظˆط±")),
        ("overview", _("Overview - ظ†ط¸ط±ط© ط¹ط§ظ…ط©")),
        ("services", _("Services/Units - ط§ظ„ظˆط­ط¯ط§طھ ظˆط§ظ„ط®ط¯ظ…ط§طھ")),
        ("map", _("Map - ط§ظ„ط®ط±ظٹط·ط©")),
        ("contact", _("Contact Info - ظ…ط¹ظ„ظˆظ…ط§طھ ط§ظ„طھظˆط§طµظ„")),
        ("reviews", _("Reviews - ط§ظ„طھظ‚ظٹظٹظ…ط§طھ")),
        ("ad_banner", _("Ad Banner - ط¥ط¹ظ„ط§ظ† ط¹ط±ط¶ظٹ")),
    ]

    block_type = models.CharField(_("ظ†ظˆط¹ ط§ظ„ظ‚ط³ظ…"), max_length=30, choices=BLOCK_TYPES)
    title = models.CharField(_("ط¹ظ†ظˆط§ظ† ط§ظ„ظ‚ط³ظ…"), max_length=200, blank=True)
    order = models.IntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)
    is_visible = models.BooleanField(_("ط¸ط§ظ‡ط±"), default=True)
    
    # Optional customization
    custom_class = models.CharField(_("CSS Class ظ…ط®طµطµ"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("ظ‚ط³ظ… طھظپط§طµظٹظ„ ط§ظ„ظ…ظƒط§ظ†")
        verbose_name_plural = _("ط£ظ‚ط³ط§ظ… طھظپط§طµظٹظ„ ط§ظ„ظ…ظƒط§ظ†")
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_block_type_display()})"


class FeatureToggle(models.Model):
    key = models.CharField(max_length=100, unique=True, help_text="enable_reviews, show_weather, etc.")
    label = models.CharField(_("ط§ط³ظ… ط§ظ„ظ…ظٹط²ط©"), max_length=200, default="")
    is_enabled = models.BooleanField(_("ظ…ظپط¹ظ„"), default=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("ظ…ظٹط²ط© (Feature Toggle)")
        verbose_name_plural = _("ظ…ظٹط²ط§طھ ط§ظ„ظ†ط¸ط§ظ…")

    def __str__(self):
        return self.key


class CommunitySetting(models.Model):
    auto_approve_posts = models.BooleanField(_("ظ…ظˆط§ظپظ‚ط© طھظ„ظ‚ط§ط¦ظٹط© ط¹ظ„ظ‰ ط§ظ„ظ…ظ†ط´ظˆط±ط§طھ"), default=False)
    auto_approve_comments = models.BooleanField(_("ظ…ظˆط§ظپظ‚ط© طھظ„ظ‚ط§ط¦ظٹط© ط¹ظ„ظ‰ ط§ظ„طھط¹ظ„ظٹظ‚ط§طھ"), default=False)
    max_post_length = models.IntegerField(_("ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ظ„ط·ظˆظ„ ط§ظ„ظ…ظ†ط´ظˆط±"), default=500)
    max_comment_length = models.IntegerField(_("ط§ظ„ط­ط¯ ط§ظ„ط£ظ‚طµظ‰ ظ„ط·ظˆظ„ ط§ظ„طھط¹ظ„ظٹظ‚"), default=300)
    
    class Meta:
        verbose_name = _("ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ظ…ط¬طھظ…ط¹")
        verbose_name_plural = _("ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ظ…ط¬طھظ…ط¹")

    def __str__(self):
        return "ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ظ…ط¬طھظ…ط¹"

    def save(self, *args, **kwargs):
        if not self.pk and CommunitySetting.objects.exists():
            return
        return super(CommunitySetting, self).save(*args, **kwargs)


class NotificationSetting(models.Model):
    retention_days = models.IntegerField(_("ظ…ط¯ط© ط§ظ„ط§ط­طھظپط§ط¸ (ط£ظٹط§ظ…)"), default=30)
    allow_mark_all = models.BooleanField(_("ط§ظ„ط³ظ…ط§ط­ ط¨طھط­ط¯ظٹط¯ ط§ظ„ظƒظ„ ظƒظ…ظ‚ط±ظˆط،"), default=True)
    allow_delete = models.BooleanField(_("ط§ظ„ط³ظ…ط§ط­ ط¨ط­ط°ظپ ط§ظ„ط¥ط´ط¹ط§ط±ط§طھ"), default=False)

    class Meta:
        verbose_name = _("ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ط¥ط´ط¹ط§ط±ط§طھ")
        verbose_name_plural = _("ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ط¥ط´ط¹ط§ط±ط§طھ")

    def __str__(self):
        return "ط¥ط¹ط¯ط§ط¯ط§طھ ط§ظ„ط¥ط´ط¹ط§ط±ط§طھ"
    
    def save(self, *args, **kwargs):
        if not self.pk and NotificationSetting.objects.exists():
            return
        return super(NotificationSetting, self).save(*args, **kwargs)


class NotificationType(models.Model):
    key = models.CharField(max_length=50, unique=True, help_text="comment, like, system, etc.")
    label = models.CharField(_("ط§ط³ظ… ط§ظ„ظ†ظˆط¹"), max_length=100)
    is_enabled = models.BooleanField(_("ظ…ظپط¹ظ„"), default=True)
    order = models.IntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)

    class Meta:
        verbose_name = _("ظ†ظˆط¹ ط¥ط´ط¹ط§ط±")
        verbose_name_plural = _("ط£ظ†ظˆط§ط¹ ط§ظ„ط¥ط´ط¹ط§ط±ط§طھ")
        ordering = ['order']

    def __str__(self):
        return self.label


class WizardStep(models.Model):
    key = models.CharField(max_length=50, unique=True)  # basic, location, services, media, review
    title = models.CharField(_("ط¹ظ†ظˆط§ظ† ط§ظ„ط®ط·ظˆط©"), max_length=200)
    order = models.IntegerField(_("ط§ظ„طھط±طھظٹط¨"), default=0)
    is_active = models.BooleanField(_("ظ†ط´ط·"), default=True)

    class Meta:
        verbose_name = _("ط®ط·ظˆط© ط§ظ„ظ…ط¹ط§ظ„ط¬")
        verbose_name_plural = _("ط®ط·ظˆط§طھ ط§ظ„ظ…ط¹ط§ظ„ط¬")
        ordering = ['order']

    def __str__(self):
        return self.title


class WizardField(models.Model):
    step = models.ForeignKey(WizardStep, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100)
    label = models.CharField(_("طھط³ظ…ظٹط© ط§ظ„ط­ظ‚ظ„"), max_length=200)
    is_required_on_submit = models.BooleanField(_("ط¥ظ„ط²ط§ظ…ظٹ ط¹ظ†ط¯ ط§ظ„ط¥ط±ط³ط§ظ„"), default=False)
    is_visible = models.BooleanField(_("ط¸ط§ظ‡ط±"), default=True)

    class Meta:
        verbose_name = _("ط­ظ‚ظ„ ط§ظ„ظ…ط¹ط§ظ„ط¬")
        verbose_name_plural = _("ط­ظ‚ظˆظ„ ط§ظ„ظ…ط¹ط§ظ„ط¬")

    def __str__(self):
        return self.field_name


class WizardStep(models.Model):
    key = models.CharField(max_length=50, unique=True)
    title = models.CharField(_('عنوان الخطوة'), max_length=200)
    order = models.IntegerField(_('الترتيب'), default=0)
    is_active = models.BooleanField(_('نشط'), default=True)
    class Meta:
        verbose_name = _('خطوة المعالج')
        verbose_name_plural = _('خطوات المعالج')
        ordering = ['order']
    def __str__(self):
        return self.title

class WizardField(models.Model):
    step = models.ForeignKey(WizardStep, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100)
    label = models.CharField(_('تسمية الحقل'), max_length=200)
    is_required_on_submit = models.BooleanField(_('إلزامي عند الإرسال'), default=False)
    is_visible = models.BooleanField(_('ظاهر'), default=True)
    class Meta:
        verbose_name = _('حقل المعالج')
        verbose_name_plural = _('حقول المعالج')
    def __str__(self):
        return self.field_name
