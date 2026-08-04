"""Database models for the Campus Lost & Found Management System.

Schema follows the project proposal (Chapter 3.4):
  User, Category, Lost_Item, Found_Item, Claim  (+ Notification helper table)
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


class User(AbstractUser):
    """Custom user model for students, teachers, staff and admins."""

    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        TEACHER = "TEACHER", "Teacher"
        STAFF = "STAFF", "University Staff"
        ADMIN = "ADMIN", "Admin (Lost & Found Desk Officer)"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.STUDENT, verbose_name="Role"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone")
    department = models.CharField(max_length=100, blank=True, verbose_name="Department")
    profile_photo = models.ImageField(
        upload_to="profile_photos/", blank=True, null=True, verbose_name="Profile photo"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Registration time")
    is_active = models.BooleanField(default=True)  # admins can deactivate accounts

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    @property
    def role_label(self):
        return self.get_role_display()

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class Category(models.Model):
    """Item categories (Electronics, Documents, etc.)."""

    name = models.CharField(max_length=50, unique=True, verbose_name="Category name")
    icon = models.CharField(max_length=50, default="bi-box", verbose_name="Bootstrap icon")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class LostItem(models.Model):
    """A 'lost' report created by a user."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESOLVED = "RESOLVED", "Resolved"
        REJECTED = "REJECTED", "Rejected"

    reporter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="lost_items", verbose_name="Reporter"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="lost_items", verbose_name="Category"
    )
    item_name = models.CharField(max_length=100, verbose_name="Item name")
    description = models.TextField(verbose_name="Description")
    lost_location = models.CharField(max_length=150, verbose_name="Lost location")
    lost_date = models.DateField(verbose_name="Lost date")
    image = models.ImageField(
        upload_to="item_images/", blank=True, null=True, verbose_name="Item image"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN, verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Reported at")

    class Meta:
        verbose_name = "Lost item"
        verbose_name_plural = "Lost items"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.item_name} (lost by {self.reporter.username})"

    def get_absolute_url(self):
        return reverse("lost_detail", args=[self.pk])


class FoundItem(models.Model):
    """A 'found' report. Must be physically submitted to the Campus Lost and
    Found Desk and verified by an admin before it is published with a tracking ID."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Submission"          # reported online only
        SUBMITTED = "SUBMITTED", "Submitted to Desk"       # physically at the desk
        AVAILABLE = "AVAILABLE", "Verified & Available"    # tracking ID assigned, claims open
        RESERVED = "RESERVED", "Claim Approved"            # approved claimant to collect
        RESOLVED = "RESOLVED", "Returned / Resolved"       # case closed
        REJECTED = "REJECTED", "Rejected"                  # fake / inappropriate post

    finder = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="found_items", verbose_name="Finder"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="found_items", verbose_name="Category"
    )
    tracking_id = models.CharField(
        max_length=30, unique=True, blank=True, null=True, verbose_name="Tracking ID"
    )
    item_name = models.CharField(max_length=100, verbose_name="Item name")
    description = models.TextField(verbose_name="Description")
    found_location = models.CharField(max_length=150, verbose_name="Found location")
    found_date = models.DateField(verbose_name="Found date")
    image = models.ImageField(
        upload_to="item_images/", blank=True, null=True, verbose_name="Item image"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Status"
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_items",
        verbose_name="Verified by",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Reported at")

    class Meta:
        verbose_name = "Found item"
        verbose_name_plural = "Found items"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.item_name} (found by {self.finder.username})"

    def get_absolute_url(self):
        return reverse("found_detail", args=[self.pk])

    def status_badge(self):
        return {
            self.Status.PENDING: ("secondary", "Pending Submission"),
            self.Status.SUBMITTED: ("info", "Submitted to Desk"),
            self.Status.AVAILABLE: ("success", "Verified & Available"),
            self.Status.RESERVED: ("primary", "Claim Approved"),
            self.Status.RESOLVED: ("dark", "Returned / Resolved"),
            self.Status.REJECTED: ("danger", "Rejected"),
        }.get(self.status, ("secondary", self.status))

    @property
    def open_for_claims(self):
        return self.status == self.Status.AVAILABLE


class Claim(models.Model):
    """An ownership claim submitted by a user for a verified found item."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    found_item = models.ForeignKey(
        FoundItem, on_delete=models.CASCADE, related_name="claims", verbose_name="Found item"
    )
    claimant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="claims", verbose_name="Claimant"
    )
    claim_description = models.TextField(verbose_name="Claim description / proof details")
    proof_file = models.FileField(
        upload_to="claim_proofs/", blank=True, null=True, verbose_name="Supporting file"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Status"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_claims",
        verbose_name="Reviewed by",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Reviewed at")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Submitted at")

    class Meta:
        verbose_name = "Claim"
        verbose_name_plural = "Claims"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["found_item", "claimant"], name="unique_claim_per_item"
            )
        ]

    def __str__(self):
        return f"Claim #{self.pk} on {self.found_item.item_name} by {self.claimant.username}"

    def status_badge(self):
        return {
            self.Status.PENDING: ("warning", "Pending"),
            self.Status.APPROVED: ("success", "Approved"),
            self.Status.REJECTED: ("danger", "Rejected"),
        }.get(self.status, ("secondary", self.status))


class Notification(models.Model):
    """In-app notifications (post approval, claim status, item collection, ...)."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications", verbose_name="Recipient"
    )
    title = models.CharField(max_length=150)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.title}"
