from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="admin_api_dashboard"),
    path("appointments/", views.appointments, name="admin_api_appointments"),
    path("appointments/<int:pk>/confirm/", views.appointment_confirm, name="admin_api_appointment_confirm"),
    path("appointments/<int:pk>/reject/", views.appointment_reject, name="admin_api_appointment_reject"),
    path("blog-stats/", views.blog_stats, name="admin_api_blog_stats"),
    path("support/tickets/", views.support_tickets, name="admin_api_support_tickets"),
    path("support/tickets/<int:pk>/", views.support_ticket_detail, name="admin_api_support_ticket_detail"),
    path("support/tickets/<int:pk>/reply/", views.support_ticket_reply, name="admin_api_support_ticket_reply"),
    path("support/tickets/<int:pk>/resolve/", views.support_ticket_resolve, name="admin_api_support_ticket_resolve"),
    path("orders/", views.orders, name="admin_api_orders"),
]
