from django.apps import AppConfig, apps

class Config(AppConfig):
    name = 'arches.activitystream'
    verbose_name = "Activity Streams configuration"

    def ready(self):
        # django-activity-stream
        from actstream import registry
        registry.register(apps.get_model('auth.user'))
        registry.register(apps.get_model('models.GraphModel'))
        registry.register(apps.get_model('models.Concept'))
        registry.register(apps.get_model('models.File'))
        registry.register(apps.get_model('models.Node'))
        registry.register(apps.get_model('models.ResourceInstance'))
        registry.register(apps.get_model('models.TileModel'))
        registry.register(apps.get_model('models.Value'))
