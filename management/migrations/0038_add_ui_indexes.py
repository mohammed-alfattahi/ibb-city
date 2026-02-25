# management/migrations/0038_add_ui_indexes.py
# Performance optimization: Add database indexes for frequently queried UI models
# This reduces query time for site_ui context processor and HomeView

from django.db import migrations, models


class Migration(migrations.Migration):
    
    dependencies = [
        ("management", "0037_wizardstep_wizardfield"),
    ]

    operations = [
        # Menu: filter(location=..., is_active=True).order_by("order")
        migrations.AddIndex(
            model_name="menu",
            index=models.Index(
                fields=["location", "is_active", "order"], 
                name="menu_loc_act_ord_idx"
            ),
        ),
        
        # SocialLink: filter(is_active=True).order_by("order")
        migrations.AddIndex(
            model_name="sociallink",
            index=models.Index(
                fields=["is_active", "order"], 
                name="social_act_ord_idx"
            ),
        ),
        
        # SidebarWidget: filter(is_visible=True).order_by("order")
        migrations.AddIndex(
            model_name="sidebarwidget",
            index=models.Index(
                fields=["is_visible", "order"], 
                name="widget_vis_ord_idx"
            ),
        ),
        
        # SidebarLink: filter(widget=..., is_active=True).order_by("order")
        migrations.AddIndex(
            model_name="sidebarlink",
            index=models.Index(
                fields=["widget", "is_active", "order"], 
                name="wlink_wid_act_ord_idx"
            ),
        ),
        
        # HomePageSection: filter(is_visible=True).order_by("order")
        migrations.AddIndex(
            model_name="homepagesection",
            index=models.Index(
                fields=["is_visible", "order"], 
                name="homesec_vis_ord_idx"
            ),
        ),
        
        # HeroSlide: filter(is_active=True).order_by("order")
        migrations.AddIndex(
            model_name="heroslide",
            index=models.Index(
                fields=["is_active", "order"], 
                name="hero_act_ord_idx"
            ),
        ),
    ]
