from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class ImagePreviewListDisplayMixin:
    """Mixin to display image previews in list display."""

    def image_preview(self, image: str, title: str, subtitle: str):
        """Display image preview."""
        return format_html(
            '<div style="display: flex; align-items: center; gap: 12px;">'
            '<img src="{}" width="40" height="40" style="border-radius: 50%; '
            'object-fit: cover;" />'
            '<div style="display: flex; flex-direction: column;">'
            '<strong style="font-size: 14px;">{}</strong>'
            '<span style="font-size: 12px; color: #6b7280;">{}</span>'
            "</div>"
            "</div>",
            image,
            title,
            subtitle,
        )

    image_preview.short_description = _("Avatar Preview")
