from django.urls import path
from . import views
from .feeds import LatestPostsFeed, AtomLatestPostsFeed

urlpatterns = [
    path("", views.blog_list, name="blog_list"),
    path("rss/", LatestPostsFeed(), name="blog_rss"),
    path("atom/", AtomLatestPostsFeed(), name="blog_atom"),
    path("<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("<int:pk>/", views.blog_detail_by_pk, name="blog_detail_pk"),
    path("admin-blog/", views.admin_blog, name="admin_blog"),
    path("create/", views.blog_create, name="create"),
    path("edit/<int:pk>/", views.blog_edit, name="edit"),
    path("delete/<int:pk>/", views.blog_delete, name="delete"),
    path("categories/", views.list_categories, name="list_categories"),
    path("categories/create/", views.create_category, name="create_category"),
    path("categories/<int:pk>/edit/", views.edit_category, name="edit_category"),
    path("categories/<int:pk>/delete/", views.delete_category, name="delete_category"),
]
