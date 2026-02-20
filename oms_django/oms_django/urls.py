from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def healthz(_request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz),
    path("api/", include("oms_app.urls")),
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),
]
