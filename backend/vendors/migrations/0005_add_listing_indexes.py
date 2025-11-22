# Generated migration for vendor listing index optimizations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vendors", "0004_add_vendor_user_and_gst"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="listing",
            index=models.Index(fields=["vendor", "enabled"], name="idx_listing_vendor_en"),
        ),
        migrations.AddIndex(
            model_name="listing",
            index=models.Index(fields=["enabled", "created_at"], name="idx_listing_en_created"),
        ),
        migrations.AddIndex(
            model_name="listing",
            index=models.Index(fields=["vendor", "school"], name="idx_listing_vendor_school"),
        ),
    ]

