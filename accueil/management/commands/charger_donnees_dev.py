from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Charge les fausses données de développement. Jamais de données réelles."

    def handle(self, *args, **options):
        # Le générateur de fausses données arrive avec l'issue #10 (Luc).
        self.stdout.write("Rien à charger pour l'instant : le générateur arrive avec l'issue #10.")
