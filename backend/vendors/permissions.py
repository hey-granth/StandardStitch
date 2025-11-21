from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View


class IsParentRole(BasePermission):
    """Allow only users with 'parent' role"""

    def has_permission(self, request: Request, view: View) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "parent"
        )


class IsOpsOrStaff(BasePermission):
    """Allow only ops role or staff users"""

    def has_permission(self, request: Request, view: View) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.role == "ops")
        )


class IsApprovedVendor(BasePermission):
    """Allow only users with approved vendor status"""

    def has_permission(self, request: Request, view: View) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False

        if not hasattr(request.user, "vendor_profile"):
            return False

        vendor = request.user.vendor_profile
        return vendor.status == "approved" and request.user.role == "vendor"
