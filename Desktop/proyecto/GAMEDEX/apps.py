from django.apps import AppConfig

class GamedexConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'GAMEDEX'

    def ready(self):
        import GAMEDEX.signals