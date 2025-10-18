from django.urls import path
from .views import chatbot_api, teach_api, teach_page

urlpatterns = [
    path("api/", chatbot_api, name="chatbot_api"),
    path("teach/", teach_api, name="teach_api"),
    path("admin/teach/", teach_page, name="teach_page"),
]
