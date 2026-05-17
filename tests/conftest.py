"""Fixtures partagées pour les tests."""
from pathlib import Path
import sys

# Ajouter la racine du projet au path pour les imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
