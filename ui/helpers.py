"""Fonctions utilitaires pour l'interface PyQt6."""


def sanitize_filename(name: str) -> str:
    """Nettoie un nom de fichier en supprimant les caractères problématiques."""
    return "".join(c if c.isalnum() or c in " _-." else "_" for c in name).strip()


def format_bytes(n: float) -> str:
    """Formate un nombre d'octets en chaîne lisible (KB, MB, GB, TB)."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
