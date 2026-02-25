import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cms.models import UIZone, UIComponent, ZoneComponent


class Command(BaseCommand):
    help = "Import CMS zones/components from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("--in", dest="in_path", type=str, required=True, help="Input JSON path")
        parser.add_argument("--replace", action="store_true", help="Replace existing zone components for imported zones")

    @transaction.atomic
    def handle(self, *args, **options):
        in_path = Path(options["in_path"]).resolve()
        if not in_path.exists():
            raise CommandError(f"Input file not found: {in_path}")

        data = json.loads(in_path.read_text(encoding="utf-8"))
        replace = options["replace"]

        # components
        comp_map = {}
        for c in data.get("components", []):
            obj, _ = UIComponent.objects.update_or_create(
                slug=c["slug"],
                defaults={
                    "name": c.get("name", c["slug"]),
                    "template_path": c.get("template_path", ""),
                    "default_data": c.get("default_data") or {},
                },
            )
            comp_map[obj.slug] = obj

        # zones
        zone_map = {}
        for z in data.get("zones", []):
            obj, _ = UIZone.objects.update_or_create(
                slug=z["slug"],
                defaults={
                    "name": z.get("name", z["slug"]),
                    "description": z.get("description", ""),
                },
            )
            zone_map[obj.slug] = obj

        imported_zone_slugs = set([z["slug"] for z in data.get("zones", [])])

        if replace and imported_zone_slugs:
            ZoneComponent.objects.filter(zone__slug__in=imported_zone_slugs).delete()

        for item in data.get("zone_components", []):
            zone = zone_map.get(item["zone_slug"]) or UIZone.objects.get(slug=item["zone_slug"])
            comp = comp_map.get(item["component_slug"]) or UIComponent.objects.get(slug=item["component_slug"])

            ZoneComponent.objects.create(
                zone=zone,
                component=comp,
                order=item.get("order", 0),
                is_visible=item.get("is_visible", True),
                stage=item.get("stage", "published"),
                data_override=item.get("data_override") or {},
            )

        self.stdout.write(self.style.SUCCESS(f"Imported CMS from {in_path}"))
