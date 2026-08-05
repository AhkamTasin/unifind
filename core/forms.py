"""Forms for the Campus Lost & Found Management System."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.validators import RegexValidator

from .models import Claim, FoundItem, LostItem, User

PHONE_VALIDATOR = RegexValidator(
    regex=r"^\+?[0-9\-\s]{7,20}$",
    message="Enter a valid phone number (digits only, 7-20 characters).",
)


class UserRegistrationForm(forms.ModelForm):
    """Registration form for students, teachers, staff and admins."""

    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Ishtiaq Ahmed Chowdhury"}),
        label="Full name",
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Create a strong password"}
        ),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Re-enter your password"}
        ),
    )

    class Meta:
        model = User
        fields = ["username", "full_name", "email", "role", "department", "phone", "profile_photo"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Choose a username"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "you@university.edu.bd"}
            ),
            "role": forms.Select(attrs={"class": "form-select"}),
            "department": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. CSE"}
            ),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 017XXXXXXXX"}),
            "profile_photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "username": "Username",
            "email": "Email address",
            "role": "I am a",
            "department": "Department",
            "phone": "Phone number",
            "profile_photo": "Profile photo (optional)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].validators.append(PHONE_VALIDATOR)
        self.fields["phone"].required = False

    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("The two password fields didn't match.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["full_name"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}),
        label="Username",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
        label="Password",
    )


class ProfileUpdateForm(forms.ModelForm):
    """Let users edit their own profile information (FR-03)."""

    full_name = forms.CharField(max_length=100, label="Full name")

    class Meta:
        model = User
        fields = ["username", "full_name", "email", "phone", "department", "profile_photo"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.TextInput(attrs={"class": "form-control"}),
            "profile_photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "email": "Email address",
            "phone": "Phone number",
            "department": "Department",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["full_name"].initial = self.instance.get_full_name()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["full_name"]
        if commit:
            user.save()
        return user


class LostItemForm(forms.ModelForm):
    """Report a lost item (FR-04)."""

    class Meta:
        model = LostItem
        fields = ["category", "item_name", "description", "lost_location", "lost_date", "image"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "item_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Blue Calculator"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Colour, brand, distinguishing marks, contents, ...",
                }
            ),
            "lost_location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Library, 2nd floor"}
            ),
            "lost_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "category": "Category",
            "item_name": "Item name",
            "description": "Description",
            "lost_location": "Where was it lost?",
            "lost_date": "When was it lost?",
            "image": "Item image (optional)",
        }

    def clean_lost_date(self):
        from django.utils import timezone

        date = self.cleaned_data["lost_date"]
        if date and date > timezone.localdate():
            raise forms.ValidationError("Lost date cannot be in the future.")
        return date


class FoundItemForm(forms.ModelForm):
    """Report a found item (FR-05). The item must later be physically
    submitted to the Campus Lost and Found Desk (FR-06)."""

    class Meta:
        model = FoundItem
        fields = ["category", "item_name", "description", "found_location", "found_date", "image"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "item_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Black Wallet"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Colour, brand, contents, where exactly you found it, ...",
                }
            ),
            "found_location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Cafeteria table 5"}
            ),
            "found_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "category": "Category",
            "item_name": "Item name",
            "description": "Description",
            "found_location": "Where was it found?",
            "found_date": "When was it found?",
            "image": "Item image (recommended)",
        }

    def clean_found_date(self):
        from django.utils import timezone

        date = self.cleaned_data["found_date"]
        if date and date > timezone.localdate():
            raise forms.ValidationError("Found date cannot be in the future.")
        return date


class ClaimForm(forms.ModelForm):
    """Submit an ownership claim for a verified found item (FR-10)."""

    class Meta:
        model = Claim
        fields = ["claim_description", "proof_file"]
        widgets = {
            "claim_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Describe the item in detail (colour, brand, contents, serial "
                        "number, personal marks ...) so the desk can verify ownership."
                    ),
                }
            ),
            "proof_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "claim_description": "How can you prove this is yours?",
            "proof_file": "Supporting file (photo / receipt / student ID — optional)",
        }

    def clean_claim_description(self):
        desc = self.cleaned_data["claim_description"].strip()
        if len(desc) < 20:
            raise forms.ValidationError(
                "Please give at least a short description (20+ characters) to verify ownership."
            )
        return desc
