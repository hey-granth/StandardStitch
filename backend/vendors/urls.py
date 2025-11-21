from django.urls import path
from .views import (
    vendor_onboard,
    vendor_approve,
    vendor_reject,
    vendor_list,
    vendor_me,
    vendor_apply,
    create_listing,
    VendorListingViewSet,
)

urlpatterns = [
    # New vendor endpoints
    path("vendors/onboard", vendor_onboard, name="vendor-onboard"),
    path("vendors/<uuid:vendor_id>/approve", vendor_approve, name="vendor-approve"),
    path("vendors/<uuid:vendor_id>/reject", vendor_reject, name="vendor-reject"),
    path("vendors/", vendor_list, name="vendor-list"),
    path("vendors/me", vendor_me, name="vendor-me"),
    # Legacy vendor application
    path("vendors/apply", vendor_apply, name="vendor-apply"),
    # Listing endpoints
    path("listings", create_listing, name="listing-create"),
    path(
        "vendors/<uuid:vendor_id>/listings",
        VendorListingViewSet.as_view({"get": "list"}),
        name="vendor-listings",
    ),
]
