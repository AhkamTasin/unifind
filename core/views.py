"""Views for UniFind — current stage: public pages + user module + reporting.

Implemented so far:
  • Public pages: Home, How It Works, About
  • User module: registration, login, profile management, password change,
    in-app notifications (FR-01, FR-02, FR-03, FR-12)
  • Reporting: users can report lost and found items (FR-04, FR-05)
  • Desk (admin): can VIEW all reports — accept/reject/verify comes later

Next modules (verification & tracking IDs, claims, search/browsing) are being
developed next and will be added in upcoming commits.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import (
    FoundItemForm,
    LostItemForm,
    ProfileUpdateForm,
    UserLoginForm,
    UserRegistrationForm,
)
from .models import FoundItem, LostItem
from .utils import notify, notify_admin


# --------------------------------------------------------------------------
# Public pages
# --------------------------------------------------------------------------

def home(request):
    return render(request, "home.html")


def how_it_works(request):
    return render(request, "how_it_works.html")


def about(request):
    return render(request, "about.html")


# --------------------------------------------------------------------------
# Authentication & profile
# --------------------------------------------------------------------------

def register(request):
    """User registration (FR-01)."""
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            notify(
                user,
                "Welcome to UniFind!",
                "Your account has been created successfully. "
                "You can now report lost and found items from the Report menu.",
                "/",
            )
            messages.success(
                request,
                f"Account created successfully. Welcome, {user.full_name}!",
            )
            return redirect("home")
        messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


class UserLoginView(LoginView):
    """User login (FR-02)."""
    template_name = "accounts/login.html"
    authentication_form = UserLoginForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("home")  # falls back to home; respects ?next=

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().full_name}!")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    next_page = "home"


@login_required
def profile(request):
    return render(request, "accounts/profile.html")


@login_required
def profile_edit(request):
    """Profile management (FR-03)."""
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})


class UserPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        messages.success(self.request, "Your password was changed successfully.")
        return super().form_valid(form)


@login_required
def notifications(request):
    """In-app notifications (FR-12)."""
    notifs = request.user.notifications.all()
    unread_count = notifs.filter(is_read=False).count()
    return render(
        request,
        "accounts/notifications.html",
        {"notifs": notifs, "unread_count": unread_count},
    )


@login_required
@require_POST
def notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.info(request, "All notifications marked as read.")
    return redirect("notifications")


# --------------------------------------------------------------------------
# Reporting (users can report lost / found items)
# --------------------------------------------------------------------------

@login_required
def report_lost(request):
    """Report a lost item (FR-04)."""
    if request.method == "POST":
        form = LostItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.reporter = request.user
            item.save()
            notify_admin(
                request.user,
                "New lost item report",
                f"{request.user.full_name} reported a lost {item.item_name}.",
                "/desk/reports/",
            )
            messages.success(request, "Lost item reported successfully.")
            return redirect("my_reports")
        messages.error(request, "Please correct the errors below.")
    else:
        form = LostItemForm()
    return render(request, "items/lost_form.html", {"form": form, "title": "Report a Lost Item"})


@login_required
def report_found(request):
    """Report a found item (FR-05)."""
    if request.method == "POST":
        form = FoundItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.finder = request.user
            item.save()
            notify_admin(
                request.user,
                "New found item report",
                f"{request.user.full_name} reported a found {item.item_name}.",
                "/desk/reports/",
            )
            messages.success(
                request,
                "Found item reported successfully. The desk can now view your report.",
            )
            return redirect("my_reports")
        messages.error(request, "Please correct the errors below.")
    else:
        form = FoundItemForm()
    return render(request, "items/found_form.html", {"form": form, "title": "Report a Found Item"})


@login_required
def my_reports(request):
    """The logged-in user's own reports."""
    lost_items = LostItem.objects.filter(reporter=request.user)
    found_items = FoundItem.objects.filter(finder=request.user)
    return render(
        request,
        "items/my_reports.html",
        {"lost_items": lost_items, "found_items": found_items},
    )


# --------------------------------------------------------------------------
# Desk (admin) — view reports only. Accept/reject comes in the next module.
# --------------------------------------------------------------------------

@admin_required
def admin_reports(request):
    """Read-only view of all lost and found reports for the desk."""
    lost_items = LostItem.objects.select_related("category", "reporter").order_by("-created_at")
    found_items = FoundItem.objects.select_related("category", "finder").order_by("-created_at")
    return render(
        request,
        "desk/reports.html",
        {"lost_items": lost_items, "found_items": found_items},
    )
