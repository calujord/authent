from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

# Validator defined at module level so Django can serialize it consistently
# for migrations (avoids regenerating migrations on every makemigrations run)
phone_regex_validator = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=_(
        'Phone number must be entered in the format: "+999999999". '
        "Up to 15 digits allowed."
    ),
)


class PhoneField(models.CharField):
    """
    Custom phone field with built-in validation.

    Validates international phone numbers in the format: +999999999
    Allows up to 15 digits as per ITU-T E.164 recommendation.
    """

    def __init__(self, *args, **kwargs):
        # Set default values
        kwargs.setdefault("max_length", 17)  # +xxx xxxx xxxx xxx
        # Set validators only if not already provided to avoid duplicates
        # during Django migration reconstruction (deconstruct -> reconstruct)
        if "validators" not in kwargs:
            kwargs["validators"] = [phone_regex_validator]
        kwargs.setdefault(
            "help_text", _("International phone number with country code")
        )

        super().__init__(*args, **kwargs)

    def deconstruct(self):
        """
        Custom deconstruct to avoid baking default values into migrations.
        This prevents infinite migration generation from validator duplication.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove defaults so they aren't serialized into migrations
        if kwargs.get("max_length") == 17:
            del kwargs["max_length"]
        if kwargs.get("help_text") == _(
            "International phone number with country code"
        ):
            del kwargs["help_text"]
        # Remove validators if they only contain the default phone_regex_validator
        validators = kwargs.get("validators", [])
        if len(validators) == 1 and isinstance(validators[0], RegexValidator):
            v = validators[0]
            if v.regex.pattern == phone_regex_validator.regex.pattern:
                del kwargs["validators"]
        return name, path, args, kwargs

    def deconstruct(self):
        """
        Custom deconstruct to avoid baking default values into migrations.
        This prevents infinite migration generation from validator duplication.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove defaults so they aren't serialized into migrations
        if kwargs.get("max_length") == 17:
            del kwargs["max_length"]
        if kwargs.get("help_text") == _(
            "International phone number with country code"
        ):
            del kwargs["help_text"]
        # Remove validators if they only contain the default phone_regex_validator
        validators = kwargs.get("validators", [])
        if len(validators) == 1 and isinstance(validators[0], RegexValidator):
            v = validators[0]
            if v.regex.pattern == phone_regex_validator.regex.pattern:
                del kwargs["validators"]
        return name, path, args, kwargs

    def get_prep_value(self, value):
        """Clean and prepare value for database storage."""
        if value:
            # Remove spaces and hyphens for storage
            value = (
                str(value)
                .replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )
        return super().get_prep_value(value)

    def to_python(self, value):
        """Convert value for Python use."""
        value = super().to_python(value)
        if value:
            # Ensure it starts with + if it doesn't have it
            if not value.startswith("+"):
                value = "+" + value
        return value

    def formfield(self, **kwargs):
        """Return a form field for this model field."""
        kwargs.setdefault("widget", models.CharField().formfield().widget)
        return super().formfield(**kwargs)
