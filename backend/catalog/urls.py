from django.urls import path
from .views import CatalogViewSet

urlpatterns = [
    path(
        "schools/<uuid:school_id>/catalog",
        CatalogViewSet.as_view({"get": "list"}),
        name="school-catalog",
    ),
]
