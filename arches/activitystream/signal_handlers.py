from actstream import action, registry
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save


def AS_cu_handler(sender, instance, created, **kwargs):
    request = kwargs.pop('request', None)
    user = kwargs.pop('user', None)
    if request is None:
        if user is None:
            user = User.objects.first()
    else:
        user = request.user

    target = None
    if hasattr(instance, "resourceinstance"):         # Tile
        target = instance.resourceinstance
    elif hasattr(instance, "resourceinstanceid"):  # ResourceModel
        target = instance

    if created:
        action.send(user, verb='create', action_object=instance, 
                    description=instance._meta.object_name, target = target)
    else:
        action.send(user, verb='update', action_object=instance, 
                    description=instance._meta.object_name, target = target)


def AS_delete_handler(sender, instance, **kwargs):
    request = kwargs.pop('request', None)
    user = kwargs.pop('user', None)
    if request is None:
        if user is None:
            user = User.objects.first()
    else:
        user = request.user

    target = None
    if hasattr(instance, "resourceinstance"):         # Tile
        target = instance.resourceinstance
    elif hasattr(instance, "resourceinstanceid"):  # ResourceModel
        target = instance

    action.send(user, verb='delete', action_object=instance, 
                description=instance._meta.object_name, target = target)


def AS_hook_model(modelObject):
        registry.register(modelObject)
        post_save.connect(AS_cu_handler, sender=modelObject)
        post_delete.connect(AS_delete_handler, sender=modelObject)
