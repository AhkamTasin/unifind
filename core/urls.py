"""URL routing — public pages, user module, reporting + browsing & item details."""
from django.urls import path

from . import views

urlpatterns = [
    # Public pages
    path("", views.home, name="home"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("about/", views.about, name="about"),
    # Authentication & profile
    path("register/", views.register, name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/password/", views.UserPasswordChangeView.as_view(), name="password_change"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/read/", views.notifications_read, name="notifications_read"),
    # Reporting (user side)
    path("report/lost/", views.report_lost, name="report_lost"),
    path("report/found/", views.report_found, name="report_found"),
    path("my-reports/", views.my_reports, name="my_reports"),
    # Desk (admin) — view only
    path("desk/reports/", views.admin_reports, name="desk_reports"),
    # Browsing, search & item details (FR-09)
    path("lost/", views.browse_lost, name="browse_lost"),
    path("found/", views.browse_found, name="browse_found"),
    path("lost/<int:pk>/", views.lost_detail, name="lost_detail"),
    path("found/<int:pk>/", views.found_detail, name="found_detail"),
    # Desk submission & report management (FR-06)
    path("found/<int:pk>/submit/", views.mark_submitted, name="mark_submitted"),
    path(
        "my-reports/<str:kind>/<int:pk>/delete/",
        views.delete_my_report,
        name="delete_my_report",
    ),
    # Ownership claims (FR-10, FR-11, FR-13)
    path("claims/<int:found_id>/new/", views.submit_claim, name="submit_claim"),
    path("my-claims/", views.my_claims, name="my_claims"),
    path("my-claims/<int:pk>/", views.claim_detail, name="claim_detail"),
]
