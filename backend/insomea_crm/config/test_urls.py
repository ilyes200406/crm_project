from django.urls import include, path


urlpatterns = [
    path('api/auth/', include('apps.authentication.api.urls')),
    path('api/ventes/', include('apps.ventes.urls')),
]
