from django.apps import AppConfig, apps

class Config(AppConfig):
    name = 'arches.activitystream'
    verbose_name = "Activity Streams configuration"

    def ready(self):
        # django-activity-stream
        from actstream import registry
        registry.register(apps.get_model('auth.user'))