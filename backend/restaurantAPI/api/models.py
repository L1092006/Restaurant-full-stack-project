from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model


User = get_user_model()

# Create your models here.

class Category(models.Model):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField()

class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    featured = models.BooleanField(db_index=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    image_paths = models.TextField(null=True, blank=True)

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'menuitem'],
                name='unique_user_menuitem'
            )
        ]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Possible string values for status:
    #   processing: user has just placed order, payment not yet received and confirmed
    #   preparing: payment received, preparing to ship
    #   shipping: order shipped
    #   completed: customer receieved the order.
    #   canceled: canceled by the custormer
    status = models.CharField(max_length=255, db_index=True, default="processing")
    total_price_after_tax = models.DecimalField(max_digits=6, decimal_places=2)
    datetime = models.DateTimeField(db_index=True, auto_now_add=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    class Meta:
        unique_together = ['order', 'menuitem']