import logging
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Banner

logger = logging.getLogger(__name__)

@receiver(post_delete, sender=Banner)
def auto_delete_file_on_delete_banner(sender, instance, **kwargs):
    """
    Deletes image file from storage when Banner record is deleted.
    """
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting banner image {instance.image.name} from storage: {e}")

@receiver(pre_save, sender=Banner)
def auto_delete_file_on_change_banner(sender, instance, **kwargs):
    """
    Deletes old image file from storage when Banner record is updated with a new image.
    """
    if not instance.pk:
        return False

    try:
        old_file = Banner.objects.get(pk=instance.pk).image
    except Banner.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file:
        return False
    if not new_file or old_file.name != new_file.name:
        try:
            old_file.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting old banner image {old_file.name} from storage: {e}")
