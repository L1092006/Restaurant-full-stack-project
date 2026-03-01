from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from .models import *
import environ
from pathlib import Path
from decimal import Decimal



# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env.read_env(BASE_DIR / '.env')


User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'required': True,
                'validators': [validate_password]
            },
            'username': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all())]
            },
            'email': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all())]
            }
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']
        extra_kwargs = {
            'slug': {'read_only': True}
        }

    def create(self, validated_data):
        title = validated_data.get('title')
        slug = slugify(title)
        validated_data['slug'] = slug
        return super().create(validated_data)
    
class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    price_after_tax = serializers.SerializerMethodField(method_name='getPriceAfterTax')
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'category', 'category_id', 'price', 'price_after_tax', 'stock', 'featured', 'description', 'image_paths']

    def getPriceAfterTax(self, item):
        tax = Decimal(env('TAX'))
        return item.price * tax