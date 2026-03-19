"""
Callbacks para Unfold Admin
"""

from django.utils.translation import gettext_lazy as _


def environment_callback(request):
    """
    Callback para mostrar el entorno actual en el header del admin.
    """
    return ["Development", "success"]


def dashboard_callback(request, context):
    """
    Callback para personalizar el dashboard del admin.
    """
    return context


def site_dropdown_callback(request):
    """
    Callback para generar dinámicamente el dropdown del sitio.
    """
    dropdown_items = []

    if not request.user.is_authenticated:
        return dropdown_items

    if request.user.is_staff or request.user.is_superuser:
        dropdown_items.append(
            {
                "icon": "admin_panel_settings",
                "title": _("Panel de Administración Atharix Hub"),
                "link": "/admin/",
                "badge": {"text": "Atharix Hub", "color": "primary"},
                "attrs": {"title": _("Ir al panel de administración de Atharix Hub")},
            }
        )

    return dropdown_items
