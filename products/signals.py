import logging
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Category, ProductImage

logger = logging.getLogger(__name__)

@receiver(post_delete, sender=Category)
def auto_delete_file_on_delete_category(sender, instance, **kwargs):
    """
    Deletes image file from storage when Category record is deleted.
    """
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting category image {instance.image.name} from storage: {e}")

@receiver(pre_save, sender=Category)
def auto_delete_file_on_change_category(sender, instance, **kwargs):
    """
    Deletes old image file from storage when Category record is updated with a new image.
    """
    if not instance.pk:
        return False

    try:
        old_file = Category.objects.get(pk=instance.pk).image
    except Category.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file:
        return False
    if not new_file or old_file.name != new_file.name:
        try:
            old_file.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting old category image {old_file.name} from storage: {e}")

@receiver(post_delete, sender=ProductImage)
def auto_delete_file_on_delete_productimage(sender, instance, **kwargs):
    """
    Deletes image file from storage when ProductImage record is deleted.
    """
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting product image {instance.image.name} from storage: {e}")

@receiver(pre_save, sender=ProductImage)
def auto_delete_file_on_change_productimage(sender, instance, **kwargs):
    """
    Deletes old image file from storage when ProductImage record is updated with a new image.
    """
    if not instance.pk:
        return False

    try:
        old_file = ProductImage.objects.get(pk=instance.pk).image
    except ProductImage.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file:
        return False
    if not new_file or old_file.name != new_file.name:
        try:
            old_file.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting old product image {old_file.name} from storage: {e}")
