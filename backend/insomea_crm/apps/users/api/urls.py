from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminCreateUserView, MeView, UserManagementViewSet

router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user')

urlpatterns = [
    path('admin/create-user/', AdminCreateUserView.as_view(), name='admin-create-user'),
    path('me/', MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
