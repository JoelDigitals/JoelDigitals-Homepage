from django.urls import path
from . import views

urlpatterns = [
    path('', views.status_overview, name='status_overview'),
    path('app/<int:app_id>/', views.app_detail, name='app_detail'),
    path('speedtest/', views.speedtest_form, name='speedtest_form'),
    path('speedtest/result/', views.speedtest_result, name='speedtest_result'),
    path('check-all/', views.check_all_statuses, name='check_all_statuses'),
    path('tools/', views.tools_overview, name='tools_overview'),
    path('tools/ssl-check/', views.tool_ssl_check, name='tool_ssl_check'),
    path('tools/dns-lookup/', views.tool_dns_lookup, name='tool_dns_lookup'),
    path('tools/ping/', views.tool_ping, name='tool_ping'),
    path('tools/http-headers/', views.tool_http_headers, name='tool_http_headers'),
]