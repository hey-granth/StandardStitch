from django.urls import path
from .views import vendor_apply, create_listing, VendorListingViewSet

urlpatterns = [
    path("vendors/apply", vendor_apply, name="vendor-apply"),
    path("listings", create_listing, name="listing-create"),
    path(
        "vendors/<uuid:vendor_id>/listings",
        VendorListingViewSet.as_view({"get": "list"}),
        name="vendor-listings",
    ),
]
