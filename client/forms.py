from django import forms
from .models import Grievance


# ---------------------------------------------------------------------------
# Django's FileField does not support multiple files out of the box.
# This small subclass (the pattern recommended in Django's own docs) allows
# the "attachments" field to accept several files under the same input name,
# matching the original HTML's <input type="file" name="attachments" multiple>.
# ---------------------------------------------------------------------------

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        # ClearableFileInput normally returns only ONE file (files.get(name)).
        # Overriding this to use getlist() is required for every selected
        # file to actually be collected, not just the last one.
        upload = files.getlist(name)
        if not upload:
            return None
        return upload


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


# The radio buttons in the template use lowercase values ("low", "medium",
# "high"), while Grievance.PRIORITY_CHOICES stores them capitalized
# ("Low", "Medium", "High"). clean_priority() below bridges the two, exactly
# like the original view's `priority_raw.capitalize()` step did.
PRIORITY_INPUT_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]


class GrievanceForm(forms.Form):
    category = forms.ChoiceField(
        choices=Grievance.CATEGORY_CHOICES,
        required=False,
        initial="other",  # matches the original template's default-selected option
        widget=forms.Select(attrs={"class": "griev-input", "id": "category"}),
    )
    subject = forms.CharField(
        max_length=255,
        required=True,
        error_messages={"required": "Please provide both a subject and a description."},
        widget=forms.TextInput(attrs={
            "class": "griev-input",
            "id": "subject",
            "placeholder": "A short, clear title",
        }),
    )
    description = forms.CharField(
        required=True,
        error_messages={"required": "Please provide both a subject and a description."},
        widget=forms.Textarea(attrs={
            "class": "griev-input resize-y",
            "id": "description",
            "rows": 5,
            "placeholder": "Describe the issue in detail…",
        }),
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_INPUT_CHOICES,
        required=False,
        initial="low",
    )
    coordinates = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "griev-input bg-white font-mono text-xs",
            "id": "coordinates",
            "readonly": "readonly",
        }),
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "griev-input bg-white",
            "id": "location",
            "readonly": "readonly",
        }),
    )
    attachments = MultipleFileField(required=False)

    # ── Field-level cleaning, preserving the original fallback behavior ──

    def clean_category(self):
        category = (self.cleaned_data.get("category") or "").strip()
        valid_categories = dict(Grievance.CATEGORY_CHOICES)
        return category if category in valid_categories else "other"

    def clean_priority(self):
        priority_raw = (self.cleaned_data.get("priority") or "medium").capitalize()
        valid_priorities = dict(Grievance.PRIORITY_CHOICES)
        return priority_raw if priority_raw in valid_priorities else "Medium"

    def clean_subject(self):
        return self.cleaned_data["subject"].strip()

    def clean_description(self):
        return self.cleaned_data["description"].strip()