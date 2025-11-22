    # Generated migration for catalog index optimizations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_add_performance_indexes"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="uniformspec",
            index=models.Index(fields=["item_type"], name="idx_spec_item_type"),
        ),
        # idx_spec_gender already created in 0002_add_performance_indexes
        migrations.AddIndex(
            model_name="uniformspec",
            index=models.Index(fields=["school", "frozen"], name="idx_school_frozen"),
        ),
    ]

