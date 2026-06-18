from django.urls import path
from . import paid_views

urlpatterns = [
    path('', paid_views.home, name='paid_home'),
    path('redeem/', paid_views.redeem, name='paid_redeem'),
    path('portal/<int:package_id>/', paid_views.portal, name='paid_portal'),
    path('download/<int:app_id>/', paid_views.download_file, name='paid_download'),
]
