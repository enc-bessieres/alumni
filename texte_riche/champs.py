"""
Le champ de texte riche commun à tout le site (pages libres, blog, événements, offres).

La liste EXTENSIONS est déclarée une seule fois : elle sert à la fois aux boutons
de l'éditeur et au nettoyage du HTML par nh3 côté serveur.
"""

from django_prose_editor.fields import ProseEditorField, create_sanitizer

EXTENSIONS = {
    "Heading": {"levels": [2, 3]},
    "Bold": True,
    "Italic": True,
    "BulletList": True,
    "OrderedList": True,
    "ListItem": True,
    "Blockquote": True,
    "Link": {"enableTarget": False, "protocols": ["http", "https", "mailto"]},
}

# Pour les migrations de données et l'import : ils ne passent pas par un formulaire,
# donc le nettoyage automatique du champ ne s'applique pas.
nettoyer = create_sanitizer(EXTENSIONS)


class ChampTexteRiche(ProseEditorField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("extensions", EXTENSIONS)
        kwargs.setdefault("sanitize", True)
        super().__init__(*args, **kwargs)
