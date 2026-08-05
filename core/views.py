"""Views for the Campus Lost & Found Management System."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
)
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import (
    ClaimForm,
    FoundItemForm,
    LostItemForm,
    ProfileUpdateForm,
    UserLoginForm,
    UserRegistrationForm,
)
from .models import Category, Claim, FoundItem, LostItem, Notification, User
from .utils import generate_tracking_id, notify, notify_admin

PAGE_SIZE = 9


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

def _apply_item_filters(queryset, request, date_field, location_field):
    """Filter an item queryset using GET params (FR-09 search & filter)."""
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    status = request.GET.get("status", "").strip()

    if q:
        queryset = queryset.filter(
            Q(item_name__icontains=q)
            | Q(description__icontains=q)
            | Q(**{f"{location_field}__icontains": q})
        )
    if category:
        queryset = queryset.filter(category_id=category)
    if date_from:
        queryset = queryset.filter(**{f"{date_field}__gte": date_from})
    if date_to:
        queryset = queryset.filter(**{f"{date_field}__lte": date_to})
    if status and status != "ALL":
        queryset = queryset.filter(status=status)
    return queryset


def _paginate(request, queryset):
    paginator = Paginator(queryset, PAGE_SIZE)
    page = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page)
    except Exception:
        page_obj = paginator.page(1)
    return page_obj


def _site_stats():
    return {
        "lost_count": LostItem.objects.filter(status=LostItem.Status.OPEN).count(),
        "found_count": FoundItem.objects.filter(
            status__in=[FoundItem.Status.AVAILABLE, FoundItem.Status.RESERVED]
        ).count(),
        "claims_count": Claim.objects.filter(status=Claim.Status.PENDING).count(),
        "resolved_count": FoundItem.objects.filter(
            status=FoundItem.Status.RESOLVED
        ).count(),
    }


# --------------------------------------------------------------------------
# Public pages
# --------------------------------------------------------------------------

def home(request):
    recent_lost = LostItem.objects.filter(status=LostItem.Status.OPEN).select_related(
        "category", "reporter"
    )[:6]
    recent_found = (
        FoundItem.objects.filter(status__in=[FoundItem.Status.AVAILABLE])
        .select_related("category", "finder")[:6]
    )
    context = {
        "stats": _site_stats(),
        "recent_lost": recent_lost,
        "recent_found": recent_found,
        "categories": Category.objects.all(),
    }
    return render(request, "home.html", context)


def browse_lost(request):
    items = _apply_item_filters(
        LostItem.objects.select_related("category", "reporter"), request, "lost_date", "lost_location"
    )
    context = {
        "items": _paginate(request, items),
        "page_title": "Lost Items",
        "kind": "lost",
        "categories": Category.objects.all(),
        "status_choices": LostItem.Status.choices,
        "params": request.GET,
    }
    return render(request, "items/browse.html", context)


def browse_found(request):
    qs = FoundItem.objects.select_related("category", "finder")
    if request.user.is_authenticated and request.GET.get("status", "AVAILABLE") == "ALL":
        qs = qs.all()
    else:
        qs = qs.filter(status=FoundItem.Status.AVAILABLE)
    items = _apply_item_filters(qs, request, "found_date", "found_location")
    context = {
        "items": _paginate(request, items),
        "page_title": "Found Items",
        "kind": "found",
        "categories": Category.objects.all(),
        "status_choices": FoundItem.Status.choices,
        "params": request.GET,
        "default_status": "AVAILABLE",
    }
    return render(request, "items/browse.html", context)


def lost_detail(request, pk):
    item = get_object_or_404(
        LostItem.objects.select_related("category", "reporter"), pk=pk
    )
    return render(request, "items/lost_detail.html", {"item": item})


def found_detail(request, pk):
    item = get_object_or_404(
        FoundItem.objects.select_related("category", "finder", "verified_by"),
        pk=pk,
    )
    already_claimed = False
    if request.user.is_authenticated:
        already_claimed = Claim.objects.filter(
            found_item=item, claimant=request.user
        ).exists()
    context = {
        "item": item,
        "already_claimed": already_claimed,
        "claims": item.claims.select_related("claimant").all()
        if request.user.is_admin_user
        else None,
    }
    return render(request, "items/found_detail.html", context)


def how_it_works(request):
    return render(request, "how_it_works.html")


def about(request):
    return render(request, "about.html")


# --------------------------------------------------------------------------
# Authentication & profile
# --------------------------------------------------------------------------

def register(request):
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
                "Report lost or found items and check back for updates.",
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
    my_lost = LostItem.objects.filter(reporter=request.user)[:5]
    my_found = FoundItem.objects.filter(finder=request.user)[:5]
    my_claims = Claim.objects.filter(claimant=request.user).select_related("found_item")[:5]
    context = {
        "my_lost": my_lost,
        "my_found": my_found,
        "my_claims": my_claims,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request):
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
# Reporting lost / found items
# --------------------------------------------------------------------------

@login_required
def report_lost(request):
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
                f"/admin-panel/items/?kind=lost&status=OPEN",
            )
            messages.success(
                request,
                "Lost item reported. We will notify you when something similar is found.",
            )
            return redirect("my_reports")
        messages.error(request, "Please correct the errors below.")
    else:
        form = LostItemForm()
    return render(request, "items/lost_form.html", {"form": form, "title": "Report a Lost Item"})


@login_required
def report_found(request):
    if request.method == "POST":
        form = FoundItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.finder = request.user
            item.save()
            notify_admin(
                request.user,
                "New found item report",
                f"{request.user.full_name} reported a found {item.item_name}. "
                "Awaiting physical submission at the desk.",
                f"/admin-panel/items/?kind=found&status=PENDING",
            )
            messages.success(
                request,
                "Found item reported! Remember: please physically submit the item to the "
                "Campus Lost and Found Desk so it can be verified and published.",
            )
            return redirect("my_reports")
        messages.error(request, "Please correct the errors below.")
    else:
        form = FoundItemForm()
    return render(request, "items/found_form.html", {"form": form, "title": "Report a Found Item"})


@login_required
def my_reports(request):
    lost_items = LostItem.objects.filter(reporter=request.user)
    found_items = FoundItem.objects.filter(finder=request.user)
    return render(
        request,
        "items/my_reports.html",
        {"lost_items": lost_items, "found_items": found_items},
    )


@login_required
@require_POST
def delete_my_report(request, kind, pk):
    """Users may remove their own pending/inactive reports."""
    if kind == "lost":
        item = get_object_or_404(LostItem, pk=pk, reporter=request.user)
        if item.status != LostItem.Status.RESOLVED:
            item.delete()
            messages.success(request, "Lost item report removed.")
    elif kind == "found":
        item = get_object_or_404(FoundItem, pk=pk, finder=request.user)
        if item.status in (FoundItem.Status.PENDING, FoundItem.Status.REJECTED):
            item.delete()
            messages.success(request, "Found item report removed.")
    return redirect("my_reports")


@login_required
@require_POST
def mark_submitted(request, pk):
    """Finder confirms the item has been physically handed to the desk (FR-06)."""
    item = get_object_or_404(FoundItem, pk=pk, finder=request.user)
    if item.status == FoundItem.Status.PENDING:
        item.status = FoundItem.Status.SUBMITTED
        item.save()
        notify_admin(
            request.user,
            "Found item submitted to desk",
            f"{request.user.full_name} submitted '{item.item_name}' at the Lost and Found Desk. "
            "Please verify and assign a tracking ID.",
            f"/admin-panel/items/?kind=found&status=SUBMITTED",
        )
        messages.success(request, "Item marked as submitted. The desk will verify it now.")
    else:
        messages.error(request, "This item is not pending submission.")
    return redirect("found_detail", pk=item.pk)


# --------------------------------------------------------------------------
# Ownership claims (FR-10, FR-11)
# --------------------------------------------------------------------------

@login_required
def submit_claim(request, found_id):
    item = get_object_or_404(FoundItem, pk=found_id)
    if not item.open_for_claims:
        messages.error(request, "Claims are not open for this item right now.")
        return redirect("found_detail", pk=item.pk)
    if item.finder == request.user:
        messages.error(request, "You cannot claim an item you found yourself.")
        return redirect("found_detail", pk=item.pk)
    if Claim.objects.filter(found_item=item, claimant=request.user).exists():
        messages.warning(request, "You have already submitted a claim for this item.")
        return redirect("my_claims")

    if request.method == "POST":
        form = ClaimForm(request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.found_item = item
            claim.claimant = request.user
            claim.save()
            notify_admin(
                request.user,
                "New ownership claim",
                f"{request.user.full_name} submitted a claim for '{item.item_name}' "
                f"(Tracking ID: {item.tracking_id or 'pending'}).",
                f"/admin-panel/claims/{claim.pk}/",
            )
            messages.success(
                request,
                "Claim submitted. The Lost and Found Desk will review it shortly.",
            )
            return redirect("my_claims")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ClaimForm()
    return render(request, "claims/claim_form.html", {"form": form, "item": item})


@login_required
def my_claims(request):
    claims = Claim.objects.filter(claimant=request.user).select_related("found_item", "found_item__category")
    return render(request, "claims/my_claims.html", {"claims": claims})


@login_required
def claim_detail(request, pk):
    claim = get_object_or_404(
        Claim.objects.select_related("found_item", "claimant"),
        pk=pk,
        claimant=request.user,
    )
    return render(request, "claims/claim_detail.html", {"claim": claim})


# --------------------------------------------------------------------------
# Admin panel
# --------------------------------------------------------------------------

@admin_required
def admin_dashboard(request):
    total_users = User.objects.filter(is_active=True).count()
    total_lost = LostItem.objects.count()
    total_found = FoundItem.objects.count()
    pending_found = FoundItem.objects.filter(
        status__in=[FoundItem.Status.PENDING, FoundItem.Status.SUBMITTED]
    ).count()
    pending_claims = Claim.objects.filter(status=Claim.Status.PENDING).count()
    resolved = FoundItem.objects.filter(status=FoundItem.Status.RESOLVED).count()
    total_claims = Claim.objects.count()

    # Chart data: lost + found per category
    categories = list(Category.objects.values_list("name", flat=True))
    lost_by_cat = dict(
        LostItem.objects.values_list("category__name").annotate(c=Count("id"))
    )
    found_by_cat = dict(
        FoundItem.objects.values_list("category__name").annotate(c=Count("id"))
    )
    lost_series = [lost_by_cat.get(name, 0) for name in categories]
    found_series = [found_by_cat.get(name, 0) for name in categories]

    recent_items = list(
        LostItem.objects.select_related("category", "reporter")[:5]
    ) + list(FoundItem.objects.select_related("category", "finder")[:5])
    recent_items.sort(key=lambda x: x.created_at, reverse=True)

    recent_claims = Claim.objects.select_related("claimant", "found_item").filter(
        status=Claim.Status.PENDING
    )[:6]

    context = {
        "stats": {
            "total_users": total_users,
            "total_lost": total_lost,
            "total_found": total_found,
            "pending_found": pending_found,
            "pending_claims": pending_claims,
            "total_claims": total_claims,
            "resolved": resolved,
        },
        "chart_labels": categories,
        "chart_lost": lost_series,
        "chart_found": found_series,
        "recent_items": recent_items,
        "recent_claims": recent_claims,
    }
    return render(request, "admin_panel/dashboard.html", context)


@admin_required
def admin_items(request):
    kind = request.GET.get("kind", "found")
    if kind == "lost":
        qs = LostItem.objects.select_related("category", "reporter")
        items = _apply_item_filters(qs, request, "lost_date", "lost_location")
        status_choices = LostItem.Status.choices
    else:
        qs = FoundItem.objects.select_related("category", "finder")
        items = _apply_item_filters(qs, request, "found_date", "found_location")
        status_choices = FoundItem.Status.choices
    context = {
        "kind": kind,
        "items": _paginate(request, items),
        "categories": Category.objects.all(),
        "status_choices": status_choices,
        "params": request.GET,
    }
    return render(request, "admin_panel/items.html", context)


@admin_required
def admin_item_detail(request, kind, pk):
    if kind == "lost":
        item = get_object_or_404(
            LostItem.objects.select_related("category", "reporter"), pk=pk
        )
        claims = None
    else:
        item = get_object_or_404(
            FoundItem.objects.select_related("category", "finder", "verified_by"), pk=pk
        )
        claims = item.claims.select_related("claimant").all()
    context = {"item": item, "kind": kind, "claims": claims}
    return render(request, "admin_panel/item_detail.html", context)


@admin_required
@require_POST
def admin_lost_action(request, pk):
    """Approve/reject/resolve a lost item report (FR-16, FR-14)."""
    item = get_object_or_404(LostItem, pk=pk)
    action = request.POST.get("action")
    if action == "resolve":
        item.status = LostItem.Status.RESOLVED
        item.save()
        notify(
            item.reporter,
            "Your lost item case was resolved",
            f"The desk marked your lost {item.item_name} as resolved. "
            "We hope you recovered it!",
            "/profile/",
        )
        messages.success(request, "Lost item case marked as resolved.")
    elif action == "reject":
        item.status = LostItem.Status.REJECTED
        item.save()
        notify(
            item.reporter,
            "Your lost item report was rejected",
            "Your report did not meet our guidelines and was removed by the desk.",
            "/profile/",
        )
        messages.success(request, "Lost item report rejected.")
    return redirect("admin_item_detail", kind="lost", pk=item.pk)


@admin_required
@require_POST
def admin_found_action(request, pk):
    """Verify & publish (assign tracking ID), reject, or resolve a found item (FR-07/08/14)."""
    item = get_object_or_404(FoundItem, pk=pk)
    action = request.POST.get("action")

    if action == "verify":
        if not item.tracking_id:
            item.tracking_id = generate_tracking_id()
        item.status = FoundItem.Status.AVAILABLE
        item.verified_by = request.user
        item.save()
        notify(
            item.finder,
            "Your found report is verified & published!",
            f"'{item.item_name}' was verified at the desk. Tracking ID: {item.tracking_id}. "
            "Owners can now claim it.",
            f"/found/{item.pk}/",
        )
        # Notify users with matching open lost reports (same category)
        matches = LostItem.objects.filter(
            category=item.category, status=LostItem.Status.OPEN
        ).exclude(reporter=item.finder)
        for lost in matches:
            notify(
                lost.reporter,
                "Possible match for your lost item",
                f"A found {item.item_name} in '{item.category}' was verified at the desk. "
                f"Tracking ID: {item.tracking_id}. Submit a claim if it may be yours!",
                f"/found/{item.pk}/",
            )
        messages.success(request, f"Item verified and published. Tracking ID: {item.tracking_id}")
    elif action == "reject":
        item.status = FoundItem.Status.REJECTED
        item.save()
        notify(
            item.finder,
            "Your found report was rejected",
            "Your found item report was rejected by the desk and is no longer visible.",
            "/profile/",
        )
        messages.success(request, "Found item report rejected.")
    elif action == "resolve":
        if item.status in (FoundItem.Status.AVAILABLE, FoundItem.Status.RESERVED):
            item.status = FoundItem.Status.RESOLVED
            item.save()
            for claim in item.claims.filter(status=Claim.Status.APPROVED):
                notify(
                    claim.claimant,
                    "Item collected — case resolved",
                    f"Your case for '{item.item_name}' (Tracking ID: {item.tracking_id}) "
                    "was closed. Thanks for using UniFind!",
                    "/profile/",
                )
            notify(
                item.finder,
                "Found item case resolved",
                f"The case for '{item.item_name}' was closed by the desk.",
                "/profile/",
            )
            messages.success(request, "Found item case marked as resolved.")
    return redirect("admin_item_detail", kind="found", pk=item.pk)


@admin_required
def admin_claims(request):
    status = request.GET.get("status", "")
    qs = Claim.objects.select_related("claimant", "found_item")
    if status and status != "ALL":
        qs = qs.filter(status=status)
    context = {
        "claims": _paginate(request, qs),
        "status_choices": Claim.Status.choices,
        "params": request.GET,
    }
    return render(request, "admin_panel/claims.html", context)


@admin_required
def admin_claim_detail(request, pk):
    claim = get_object_or_404(
        Claim.objects.select_related("claimant", "found_item", "found_item__category"),
        pk=pk,
    )
    return render(request, "admin_panel/claim_detail.html", {"claim": claim})


@admin_required
@require_POST
def admin_claim_action(request, pk):
    """Approve or reject an ownership claim (FR-11)."""
    claim = get_object_or_404(Claim.objects.select_related("found_item", "claimant"), pk=pk)
    action = request.POST.get("action")
    if action == "approve" and claim.status == Claim.Status.PENDING:
        claim.status = Claim.Status.APPROVED
        claim.reviewed_by = request.user
        claim.reviewed_at = timezone.now()
        claim.save()
        item = claim.found_item
        if item.status in (FoundItem.Status.AVAILABLE, FoundItem.Status.RESERVED):
            item.status = FoundItem.Status.RESERVED
            item.save()
        notify(
            claim.claimant,
            "Your ownership claim was approved!",
            f"Your claim for '{item.item_name}' (Tracking ID: {item.tracking_id}) was "
            "approved. Please collect your item from the Campus Lost and Found Desk "
            "with your student ID / valid proof.",
            f"/found/{item.pk}/",
        )
        notify(
            item.finder,
            "A claim was approved for your found item",
            f"A claim for '{item.item_name}' was approved. The item is ready for collection.",
            f"/found/{item.pk}/",
        )
        messages.success(request, "Claim approved. The item is now reserved for the claimant.")
    elif action == "reject" and claim.status == Claim.Status.PENDING:
        claim.status = Claim.Status.REJECTED
        claim.reviewed_by = request.user
        claim.reviewed_at = timezone.now()
        claim.save()
        notify(
            claim.claimant,
            "Your ownership claim was rejected",
            f"Unfortunately your claim for '{claim.found_item.item_name}' was not "
            "approved by the desk.",
            f"/found/{claim.found_item.pk}/",
        )
        messages.success(request, "Claim rejected.")
    return redirect("admin_claim_detail", pk=claim.pk)


@admin_required
def admin_users(request):
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    qs = User.objects.order_by("-created_at")
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(email__icontains=q)
            | Q(department__icontains=q)
        )
    if role and role != "ALL":
        qs = qs.filter(role=role)
    context = {
        "users": _paginate(request, qs),
        "role_choices": User.Role.choices,
        "params": request.GET,
    }
    return render(request, "admin_panel/users.html", context)


@admin_required
@require_POST
def admin_user_action(request, pk):
    """Deactivate/activate a user or change their role (FR-15)."""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot modify your own account here.")
        return redirect("admin_users")
    action = request.POST.get("action")
    new_role = request.POST.get("new_role")
    if action == "deactivate":
        user.is_active = False
        user.save()
        messages.success(request, f"{user.full_name} has been deactivated.")
    elif action == "activate":
        user.is_active = True
        user.save()
        messages.success(request, f"{user.full_name} has been activated.")
    elif new_role and new_role in User.Role.values:
        user.role = new_role
        user.save()
        messages.success(request, f"{user.full_name}'s role updated to {user.get_role_display()}.")
    return redirect("admin_users")


@admin_required
def admin_categories(request):
    cats = Category.objects.all()
    return render(request, "admin_panel/categories.html", {"categories": cats})


@admin_required
@require_POST
def admin_category_add(request):
    name = request.POST.get("name", "").strip()
    icon = request.POST.get("icon", "bi-box").strip()
    if name:
        Category.objects.get_or_create(name=name, defaults={"icon": icon or "bi-box"})
        messages.success(request, f"Category '{name}' added.")
    else:
        messages.error(request, "Category name is required.")
    return redirect("admin_categories")


@admin_required
@require_POST
def admin_category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if cat.lost_items.exists() or cat.found_items.exists():
        messages.error(request, "Cannot delete a category that has items.")
    else:
        cat.delete()
        messages.success(request, "Category deleted.")
    return redirect("admin_categories")


@admin_required
def admin_reports(request):
    """Read-only view of all lost and found reports for the desk.

    (Kept during development — replaced by the full admin panel later.)
    """
    lost_items = LostItem.objects.select_related("category", "reporter").order_by("-created_at")
    found_items = FoundItem.objects.select_related("category", "finder").order_by("-created_at")
    return render(
        request,
        "desk/reports.html",
        {"lost_items": lost_items, "found_items": found_items},
    )
