# Generated migration for checkout cart index optimization

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("checkout", "0002_order_orderitem_order_idx_order_user_status_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="cart",
            index=models.Index(fields=["user", "-updated_at"], name="idx_cart_user_updated"),
        ),
    ]

