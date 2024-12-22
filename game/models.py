from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import random
from datetime import date

# Extend the User model with a Profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    money = models.IntegerField(default=100)  # Initialize with 100 by default
    display_name = models.CharField(max_length=255, blank=True, null=True)
    color = models.CharField(max_length=7, blank=True, default='')

    def save(self, *args, **kwargs):
        if not self.color:
            self.color = self.generate_random_color()  # Generate color if not set
        super(Profile, self).save(*args, **kwargs)

    def generate_random_color(self):
        return f'#{random.randint(0, 0xFFFFFF):06x}'

class UniversalGoods(models.Model):
    """A model to store all available goods."""
    class Meta:
        verbose_name = "Universal Good"
        verbose_name_plural = "Universal Goods"

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Tile model
class Tile(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tiles")
    population = models.IntegerField(default=0)  # Tile-specific population
    buildings = models.TextField(blank=True, null=True)
    resources = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='tile_images/', blank=True, null=True)
    terrain = models.CharField(
        max_length=10, choices=[
            ('fields', 'Fields'),
            ('mountains', 'Mountains'),
            ('forest', 'Forest'),
            ('plains', 'Plains'),
            ('water', 'Water'),
            ('city', 'City')
        ],
        default='plains'
    )
    goods = models.JSONField(default=dict)  # e.g., {"iron": 30, "wood": 0}
    moving_goods = models.JSONField(default=dict, blank=True, null=True)  # Handle moving goods

    def add_good(self, good_name):
        # Ensure that the good exists in UniversalGoods
        good, created = UniversalGoods.objects.get_or_create(name=good_name)

        # If the good wasn't already in the tile's goods list, add it with 0 quantity
        if good_name not in self.goods:
            self.goods[good_name] = 0
            self.save()

    def remove_good(self, good_name):
        goods = self.goods  # assuming goods is a dictionary
        if good_name in goods:
            del goods[good_name]
            self.goods = goods  # Update the tile's goods field
            self.save()  # Save the tile after modification

    def get_terrain_color(self):
        if self.terrain == 'fields':
            return 'lightyellow'
        elif self.terrain == 'mountains':
            return 'gray'
        elif self.terrain == 'forest':
            return 'forestgreen'
        elif self.terrain == 'plains':
            return 'lightgreen'
        elif self.terrain == 'water':
            return 'blue'
        elif self.terrain == 'city':
            return 'orange'
        return 'lightgray'

    @property
    def terrain_color(self):
        return self.get_terrain_color()

    def __str__(self):
        return f"Tile ({self.x}, {self.y})"

class QueuedAction(models.Model):
    class Meta:
        verbose_name = "Queued Action"
        verbose_name_plural = "Queued Actions"

    ACTION_TYPE_CHOICES = [
        ('move_good', 'Move Good'),
        # Add other action types here
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)  # e.g., "move_goods"
    details = models.JSONField()  # Store details of the action
    timestamp = models.DateTimeField(auto_now_add=True)

# Progressing report on actions
class ProgressAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)
    details = models.JSONField()  # Includes 'turn' initialized at 0
    turn = models.IntegerField(default=0)  # Tracks progress

# Status report on actions
class StatusAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)
    details = models.JSONField()  # Includes 'status' and 'completion_date'
    completion_date = models.DateField()  # Log the date of completion


class GameDate(models.Model):
    current_date = models.DateField(default=date(1100, 1, 1))  # Default start: January 1, 1100

    def __str__(self):
        return self.current_date.strftime('%B %d, %Y')

# Receiver to handle adding goods to all tiles
@receiver(post_save, sender=UniversalGoods)
def add_good_to_tiles(sender, instance, created, **kwargs):
    if created:  # Only run when a new good is added
        good_name = instance.name
        for tile in Tile.objects.all():
            tile.add_good(good_name)


# Receiver to handle removing goods from all tiles
@receiver(post_delete, sender=UniversalGoods)
def remove_good_from_tiles(sender, instance, **kwargs):
    good_name = instance.name
    for tile in Tile.objects.all():
        tile.remove_good(good_name)
