"""Exceptions métier pour l'application."""
class VidsError(Exception):
    """Erreur de base de l'application."""


class FetchError(VidsError):
    """Erreur lors de la récupération des rooms."""


class StreamResolutionError(VidsError):
    """Erreur lors de la résolution d'URL de flux."""


class SettingsError(VidsError):
    """Erreur lors de l'accès aux settings."""
