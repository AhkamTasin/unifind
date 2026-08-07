"""Seed the database with categories, demo users, sample items and claims.

Usage:
    python manage.py seed_data
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Category, Claim, FoundItem, LostItem, Notification, User
from core.utils import generate_tracking_id

CATEGORIES = [
    ("Electronics", "bi-phone"),
    ("Documents & ID", "bi-card-text"),
    ("Wallets & Purses", "bi-wallet2"),
    ("Books & Notes", "bi-book"),
    ("Keys", "bi-key"),
    ("Clothing & Bags", "bi-bag"),
    ("Accessories", "bi-gem"),
    ("Other", "bi-box"),
]


class Command(BaseCommand):
    help = "Seed the database with demo data for the Campus Lost & Found system."

    def handle(self, *args, **options):
        self.stdout.write("Seeding database ...")

        # --- Users ---------------------------------------------------------
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "desk@campus.edu.bd",
                "first_name": "Lost & Found Desk",
                "role": User.Role.ADMIN,
                "phone": "01700000000",
                "department": "Campus Lost and Found Desk",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("  + admin account created (admin / admin123)"))

        student, created = User.objects.get_or_create(
            username="student",
            defaults={
                "email": "student@campus.edu.bd",
                "first_name": "Ayesha Rahman",
                "role": User.Role.STUDENT,
                "phone": "01711111111",
                "department": "CSE",
            },
        )
        if created:
            student.set_password("student123")
            student.save()

        teacher, created = User.objects.get_or_create(
            username="teacher",
            defaults={
                "email": "teacher@campus.edu.bd",
                "first_name": "Dr. Kamal Hossain",
                "role": User.Role.TEACHER,
                "phone": "01722222222",
                "department": "Data Science",
            },
        )
        if created:
            teacher.set_password("teacher123")
            teacher.save()

        staff, created = User.objects.get_or_create(
            username="staff",
            defaults={
                "email": "staff@campus.edu.bd",
                "first_name": "Mahmudul Hasan",
                "role": User.Role.STAFF,
                "phone": "01733333333",
                "department": "Administration",
            },
        )
        if created:
            staff.set_password("staff123")
            staff.save()

        users = {"student": student, "teacher": teacher, "staff": staff}

        # --- Categories ------------------------------------------------------
        cat = {}
        for name, icon in CATEGORIES:
            obj, _ = Category.objects.get_or_create(name=name, defaults={"icon": icon})
            cat[name] = obj

        # --- Sample lost items ------------------------------------------------
        electronics, wallet, docs, book = (
            cat["Electronics"],
            cat["Wallets & Purses"],
            cat["Documents & ID"],
            cat["Books & Notes"],
        )
        today = timezone.localdate()

        lost_samples = [
            dict(
                reporter=student, category=electronics, item_name="Black Sony Headphones",
                description="Sony WH-CH520 wireless headphones with a scratch on the right cup. Last used near the library stairs.",
                lost_location="Central Library, 2nd floor", lost_date=today - timedelta(days=2), status=LostItem.Status.OPEN,
            ),
            dict(
                reporter=teacher, category=docs, item_name="Blue Identity Card",
                description="Official staff ID card with photo, name 'Dr. Kamal Hossain' and a lanyard.",
                lost_location="Faculty Lounge", lost_date=today - timedelta(days=4), status=LostItem.Status.OPEN,
            ),
            dict(
                reporter=staff, category=book, item_name="Database Systems Textbook",
                description="Elmasri & Navathe, 7th edition with highlighted chapters 5-8.",
                lost_location="Cafeteria", lost_date=today - timedelta(days=6), status=LostItem.Status.RESOLVED,
            ),
        ]
        for data in lost_samples:
            LostItem.objects.get_or_create(
                reporter=data["reporter"], item_name=data["item_name"], defaults=data
            )

        # --- Sample found items -----------------------------------------------
        found_samples = [
            dict(
                finder=student, category=wallet, item_name="Brown Leather Wallet",
                description="Brown leather wallet found on a bench near the main gate. Contains some cash and cards.",
                found_location="Main gate bench", found_date=today - timedelta(days=1),
                tracking_id=generate_tracking_id(), status=FoundItem.Status.AVAILABLE, verified_by=admin,
            ),
            dict(
                finder=teacher, category=electronics, item_name="USB Flash Drive (32GB)",
                description="Black and red USB drive with a keyring, found in Lab 3.",
                found_location="Computer Lab 3", found_date=today - timedelta(days=3),
                tracking_id=generate_tracking_id(), status=FoundItem.Status.AVAILABLE, verified_by=admin,
            ),
            dict(
                finder=staff, category=docs, item_name="Student ID Card",
                description="Student ID card with the name 'Rahim Uddin', found near the parking area.",
                found_location="Parking area", found_date=today - timedelta(days=5),
                tracking_id=generate_tracking_id(), status=FoundItem.Status.RESERVED, verified_by=admin,
            ),
        ]
        found_objs = []
        for data in found_samples:
            obj, created = FoundItem.objects.get_or_create(
                finder=data["finder"], item_name=data["item_name"], defaults=data
            )
            if created:
                found_objs.append(obj)

        # --- Sample claims -------------------------------------------------------
        if found_objs and len(found_objs) >= 3:
            Claim.objects.get_or_create(
                found_item=found_objs[2],
                claimant=student,
                defaults=dict(
                    claim_description=(
                        "I lost my student ID card near the parking area last week. "
                        "The card has my photo and student number on it."
                    ),
                    status=Claim.Status.APPROVED,
                    reviewed_by=admin,
                    reviewed_at=timezone.now(),
                ),
            )

        # A pending claim for the flash drive
        usb = FoundItem.objects.filter(item_name__icontains="Flash Drive").first()
        if usb:
            Claim.objects.get_or_create(
                found_item=usb,
                claimant=student,
                defaults=dict(
                    claim_description=(
                        "I believe this is my flash drive - it has my course notes for "
                        "Web Technologies and a small blue sticker on the back."
                    ),
                    status=Claim.Status.PENDING,
                ),
            )

        # --- Sample notifications ------------------------------------------------
        for u in users.values():
            Notification.objects.get_or_create(
                user=u,
                title="Welcome to UniFind!",
                defaults=dict(
                    message="Welcome to UniFind! Report lost or found items, search the desk records and track your claims.",
                    link="/",
                ),
            )

        self.stdout.write(self.style.SUCCESS(
            "Done! Demo accounts:  admin/admin123  student/student123  "
            "teacher/teacher123  staff/staff123"
        ))
