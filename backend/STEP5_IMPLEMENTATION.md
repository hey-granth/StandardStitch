# STEP 5 - Checkout App

## checkout/models.py

```python
import uuid
from decimal import Decimal
from typing import ClassVar
from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class Cart(models.Model):
    objects: ClassVar[models.Manager]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return f"Cart {self.id}"


class CartItem(models.Model):
    objects: ClassVar[models.Manager]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey('vendors.Listing', on_delete=models.PROTECT, related_name='cart_items')
    qty = models.IntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = [['cart', 'listing']]
        indexes = [
            models.Index(fields=['cart', 'listing'], name='idx_cart_listing'),
        ]


class Payment(models.Model):
    objects: ClassVar[models.Manager]
    
    STATUS_CHOICES: list[tuple[str, str]] = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=50)
    provider_ref = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    raw_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['provider_ref'], name='idx_payment_provider_ref'),
            models.Index(fields=['status', 'created_at'], name='idx_payment_status_created'),
        ]
```

## Migration SQL

```sql
CREATE TABLE "carts" (
    "id" char(32) NOT NULL PRIMARY KEY,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "user_id" char(32) NOT NULL REFERENCES "users" ("id")
);

CREATE TABLE "payments" (
    "id" char(32) NOT NULL PRIMARY KEY,
    "provider" varchar(50) NOT NULL,
    "provider_ref" varchar(255) NOT NULL UNIQUE,
    "amount" decimal NOT NULL,
    "status" varchar(20) NOT NULL,
    "raw_payload" text NOT NULL CHECK ((JSON_VALID("raw_payload") OR "raw_payload" IS NULL)),
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL
);

CREATE TABLE "cart_items" (
    "id" char(32) NOT NULL PRIMARY KEY,
    "qty" integer NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "cart_id" char(32) NOT NULL REFERENCES "carts" ("id"),
    "listing_id" char(32) NOT NULL REFERENCES "listings" ("id")
);

-- Indexes
CREATE INDEX "carts_user_id" ON "carts" ("user_id");
CREATE INDEX "idx_payment_provider_ref" ON "payments" ("provider_ref");
CREATE INDEX "idx_payment_status_created" ON "payments" ("status", "created_at");
CREATE UNIQUE INDEX "cart_items_cart_id_listing_id_uniq" ON "cart_items" ("cart_id", "listing_id");
CREATE INDEX "idx_cart_listing" ON "cart_items" ("cart_id", "listing_id");
```

## Test Results

```
Ran 11 tests - OK ✓
- Add cart item
- Update cart item quantity
- Remove cart item
- Get cart with total
- Create checkout session
- Checkout idempotency
- Empty cart validation
- Webhook updates payment
- Invalid webhook signature
- Webhook idempotency

All Tests: 44/44 passing ✓
```

## API Endpoints

**POST /api/cart/items**
```json
{"listing": "uuid", "qty": 2}
→ Creates/updates cart item
```

**DELETE /api/cart/items/{id}**
```
→ Removes cart item
```

**GET /api/cart**
```json
→ {
  "id": "uuid",
  "items": [...],
  "total_amount": "240.00"
}
```

**POST /api/checkout/session** (requires Idempotency-Key)
```json
{"cart_id": "uuid"}
→ {
  "payment_id": "uuid",
  "payment_token": "mock_pi_...",
  "amount": "240.00",
  "status": "pending"
}
```

**POST /api/payments/webhook**
```json
{
  "provider_ref": "mock_pi_...",
  "status": "paid",
  "signature": "sha256_hash",
  "raw_data": {}
}
→ Updates payment status
```

## Performance Optimizations

- ✅ select_related('vendor', 'school', 'spec') on listing lookups
- ✅ prefetch_related('items__listing__vendor') on cart retrieval
- ✅ Atomic transactions for checkout + webhook
- ✅ Cache checkout sessions (5 min TTL)
- ✅ Cache webhook processing (10 min TTL)
- ✅ Composite index (cart_id, listing_id)
- ✅ Index on Payment(provider_ref)
- ✅ PROTECT on listing FK (prevents orphaned cart items)

