import json
from pathlib import Path
from django.core.management.base import BaseCommand

from cms.models import UIZone, UIComponent, ZoneComponent


class Command(BaseCommand):
    help = "Export CMS zones/components to a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("--out", type=str, default="cms_export.json", help="Output JSON path")

    def handle(self, *args, **options):
        out_path = Path(options["out"]).resolve()

        components = list(UIComponent.objects.all().values("name", "slug", "template_path", "default_data"))
        zones = list(UIZone.objects.all().values("name", "slug", "description"))

        zcs = []
        for zc in ZoneComponent.objects.select_related("zone", "component").all().order_by("zone__slug", "stage", "order"):
            zcs.append({
                "zone_slug": zc.zone.slug,
                "component_slug": zc.component.slug,
                "order": zc.order,
                "is_visible": zc.is_visible,
                "stage": zc.stage,
                "data_override": zc.data_override or {},
            })

        payload = {
            "version": 1,
            "components": components,
            "zones": zones,
            "zone_components": zcs,
        }

        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Exported CMS to {out_path}"))
