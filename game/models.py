from django.contrib.auth.models import User
from django.db import models
import random

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)  # e.g., "move_goods"
    details = models.JSONField()  # Store details of the action
    timestamp = models.DateTimeField(auto_now_add=True)
