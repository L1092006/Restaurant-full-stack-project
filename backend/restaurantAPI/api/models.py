from django.db import models

# Create your models here.

class Category(models.Model):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField()

class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(db_index=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)