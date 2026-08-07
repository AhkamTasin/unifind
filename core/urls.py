"""URL routing for the core app."""
from django.urls import path

from . import views

urlpatterns = [
    # Public
    path("", views.home, name="home"),
    path("lost/", views.browse_lost, name="browse_lost"),
    path("found/", views.browse_found, name="browse_found"),
    path("lost/<int:pk>/", views.lost_detail, name="lost_detail"),
    path("found/<int:pk>/", views.found_detail, name="found_detail"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("about/", views.about, name="about"),
    # Auth & profile
    path("register/", views.register, name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/password/", views.UserPasswordChangeView.as_view(), name="password_change"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/read/", views.notifications_read, name="notifications_read"),
    # Reporting
    path("report/lost/", views.report_lost, name="report_lost"),
    path("report/found/", views.report_found, name="report_found"),
    path("my-reports/", views.my_reports, name="my_reports"),
    path("my-reports/<str:kind>/<int:pk>/delete/", views.delete_my_report, name="delete_my_report"),
    path("found/<int:pk>/submit/", views.mark_submitted, name="mark_submitted"),
    # Claims
    path("claims/<int:found_id>/new/", views.submit_claim, name="submit_claim"),
    path("my-claims/", views.my_claims, name="my_claims"),
    path("my-claims/<int:pk>/", views.claim_detail, name="claim_detail"),
    # Admin panel
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/items/", views.admin_items, name="admin_items"),
    path("admin-panel/items/<str:kind>/<int:pk>/", views.admin_item_detail, name="admin_item_detail"),
    path("admin-panel/items/lost/<int:pk>/action/", views.admin_lost_action, name="admin_lost_action"),
    path("admin-panel/items/found/<int:pk>/action/", views.admin_found_action, name="admin_found_action"),
    path("admin-panel/claims/", views.admin_claims, name="admin_claims"),
    path("admin-panel/claims/<int:pk>/", views.admin_claim_detail, name="admin_claim_detail"),
    path("admin-panel/claims/<int:pk>/action/", views.admin_claim_action, name="admin_claim_action"),
    path("admin-panel/users/", views.admin_users, name="admin_users"),
    path("admin-panel/users/<int:pk>/action/", views.admin_user_action, name="admin_user_action"),
    path("admin-panel/categories/", views.admin_categories, name="admin_categories"),
    path("admin-panel/categories/add/", views.admin_category_add, name="admin_category_add"),
    path(
        "admin-panel/categories/<int:pk>/delete/",
        views.admin_category_delete,
        name="admin_category_delete",
    ),
]
