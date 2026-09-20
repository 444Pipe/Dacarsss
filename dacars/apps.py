from django.contrib.admin.apps import AdminConfig


class PanelDacarsConfig(AdminConfig):
    """Reemplaza el admin de fábrica por el panel de DACARS."""

    default_site = "dacars.admin.PanelDacars"
