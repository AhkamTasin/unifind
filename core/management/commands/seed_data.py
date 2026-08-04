"""Seed the demo database with categories and demo accounts.

Current stage of the project: public pages + user module + lost/found reporting.
So this seeds only what is needed to demo those features.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Category, User

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
    help = "Seed the demo database with categories and demo accounts."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding database ...")

        # Categories (needed by the report forms)
        for name, icon in CATEGORIES:
            Category.objects.get_or_create(name=name, defaults={"icon": icon})

        # Demo accounts
        demo = [
            ("admin", "desk@campus.edu.bd", "Lost & Found Desk", User.Role.ADMIN,
             "01700000000", "Campus Lost and Found Desk", True),
            ("student", "student@campus.edu.bd", "Ayesha Rahman", User.Role.STUDENT,
             "01711111111", "CSE", False),
            ("teacher", "teacher@campus.edu.bd", "Dr. Kamal Hossain", User.Role.TEACHER,
             "01722222222", "Data Science", False),
            ("staff", "staff@campus.edu.bd", "Mahmudul Hasan", User.Role.STAFF,
             "01733333333", "Administration", False),
        ]
        for username, email, name, role, phone, dept, is_staff in demo:
            user, created = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    email=email, first_name=name, role=role, phone=phone,
                    department=dept, is_staff=is_staff, is_superuser=is_staff,
                ),
            )
            if created:
                user.set_password(f"{username}123")
                user.save()

        self.stdout.write(self.style.SUCCESS(
            "Done! Demo accounts:  admin/admin123  student/student123  "
            "teacher/teacher123  staff/staff123"
        ))
