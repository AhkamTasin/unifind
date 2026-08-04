"""URL routing for the core app — public pages, user module, reporting."""
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
]
