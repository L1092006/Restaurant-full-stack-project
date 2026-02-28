from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from decimal import Decimal
from .models import MenuItem, Category  

# Create your tests here.


# Test menuitem api
class MenuItemViewCorrectedBehaviorTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Drinks")
        self.item = MenuItem.objects.create(
            title="Coffee",
            price=Decimal("2.50"),
            stock=10,
            featured=False,
            description="Hot coffee",
            category=self.category,
            image_paths=None,
        )

        self.list_url = reverse('api:menuitem-list')
        self.detail_url = reverse('api:menuitem-detail', args=[self.item.id])

        self.client = APIClient()
        self.user_no_perms = User.objects.create_user(username="noperms", password="pass")
        self.user_with_perms = User.objects.create_user(username="withperms", password="pass")

        ct = ContentType.objects.get_for_model(MenuItem)
        self.perm_add = Permission.objects.get(content_type=ct, codename="add_menuitem")
        self.perm_change = Permission.objects.get(content_type=ct, codename="change_menuitem")
        self.perm_delete = Permission.objects.get(content_type=ct, codename="delete_menuitem")

    def test_get_list_allowed_anonymous(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_post_requires_add_permission(self):
        payload = {
            "title": "Tea",
            "category_id": self.category.id,
            "price": "1.75",
            "stock": 5,
            "featured": False,
            "description": "Green tea",
            "image_paths": None,
        }

        # unauthenticated -> 401
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # authenticated without add -> 403
        self.client.force_authenticate(self.user_no_perms)
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)

        # authenticated with add -> 201
        self.user_with_perms.user_permissions.add(self.perm_add)
        self.client.force_authenticate(self.user_with_perms)
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(None)

    def test_put_patch_require_change_permission(self):
        update = {
            "title": "Coffee Large",
            "category_id": self.category.id,
            "price": "3.00",
            "stock": 8,
            "featured": True,
            "description": "Large hot coffee",
            "image_paths": None,
        }

        # unauthenticated -> 401
        resp = self.client.put(self.detail_url, update, format="json")
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # authenticated without change -> 403
        self.client.force_authenticate(self.user_no_perms)
        resp = self.client.put(self.detail_url, update, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)

        # authenticated with change -> 200
        self.user_with_perms.user_permissions.add(self.perm_change)
        self.client.force_authenticate(self.user_with_perms)
        resp = self.client.put(self.detail_url, update, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(None)

    def test_delete_requires_delete_permission(self):
        # unauthenticated -> 401
        resp = self.client.delete(self.detail_url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # authenticated without delete -> 403
        self.client.force_authenticate(self.user_no_perms)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)

        # authenticated with delete -> 204
        self.user_with_perms.user_permissions.add(self.perm_delete)
        self.client.force_authenticate(self.user_with_perms)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.client.force_authenticate(None)


# Test category api

class CategoryApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create an initial category for detail/modify/delete tests
        self.category = Category.objects.create(title="Beverages", slug="beverages")

        # Reverse URLs (assumes router registered with basename='category' and app_name='api')
        self.list_url = reverse('api:category-list')
        self.detail_url = reverse('api:category-detail', args=[self.category.id])

        # Users
        self.user_no_perms = User.objects.create_user(username="noperms", password="pass")
        self.user_with_perms = User.objects.create_user(username="withperms", password="pass")

        # Permissions for Category model
        ct = ContentType.objects.get_for_model(Category)
        self.perm_add = Permission.objects.get(content_type=ct, codename='add_category')
        self.perm_change = Permission.objects.get(content_type=ct, codename='change_category')
        self.perm_delete = Permission.objects.get(content_type=ct, codename='delete_category')

    def test_get_list_and_detail_allowed_anonymous(self):
        """Anonymous users can GET list and detail"""
        list_resp = self.client.get(self.list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)

        detail_resp = self.client.get(self.detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

    def test_post_requires_add_permission_and_creates_slug(self):
        """POST without add permission -> 401/403; with permission -> 201 and slug generated"""
        payload = {"title": "Hot Drinks"}

        # Unauthenticated attempt
        resp = self.client.post(self.list_url, payload, format='json')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # Authenticated without permission
        self.client.force_authenticate(self.user_no_perms)
        resp = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)

        # Authenticated with add permission
        self.user_with_perms.user_permissions.add(self.perm_add)
        self.client.force_authenticate(self.user_with_perms)
        resp = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Verify slug was created from title
        created_id = resp.data.get('id')
        self.assertIsNotNone(created_id)
        created = Category.objects.get(id=created_id)
        self.assertEqual(created.slug, "hot-drinks")
        self.client.force_authenticate(None)

    def test_put_requires_change_permission(self):
        """PUT without change permission -> 401/403; with permission -> 200 and title updated"""
        updated = {"title": "Cold Beverages"}

        # Unauthenticated attempt
        resp = self.client.put(self.detail_url, updated, format='json')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # Authenticated without permission
        self.client.force_authenticate(self.user_no_perms)
        resp = self.client.put(self.detail_url, updated, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)

        # Authenticated with change permission
        self.user_with_perms.user_permissions.add(self.perm_change)
        self.client.force_authenticate(self.user_with_perms)
        resp = self.client.put(self.detail_url, updated, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Verify change persisted and slug updated by serializer create/update logic if applicable
        self.category.refresh_from_db()
        self.assertEqual(self.category.title, "Cold Beverages")
        # If your serializer updates slug on update, assert it here; otherwise skip
        self.client.force_authenticate(None)

    def test_patch_requires_change_permission(self):
        """PATCH without change permission -> 401/403; with permission -> 200 and partial update"""
        patch_data = {"title": "Warm Beverages"}

        # Unauthenticated attempt
        resp = self.client.patch(self.detail_url, patch_data, format='json')
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # Authenticated without permission
        self.client.force_authenticate(self.user_no_perms)
        resp = self.client.patch(self.detail_url, patch_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)

        # Authenticated with change permission
        self.user_with_perms.user_permissions.add(self.perm_change)
        self.client.force_authenticate(self.user_with_perms)
        resp = self.client.patch(self.detail_url, patch_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.category.refresh_from_db()
        self.assertEqual(self.category.title, "Warm Beverages")
        self.client.force_authenticate(None)

    def test_delete_requires_delete_permission(self):
        """DELETE without delete permission -> 401/403; with permission -> 204 and object removed"""
        # Unauthenticated attempt
        resp = self.client.delete(self.detail_url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

        # Authenticated without permission
        self.client.force_authenticate(self.user_no_perms)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)

        # Authenticated with delete permission
        self.user_with_perms.user_permissions.add(self.perm_delete)
        self.client.force_authenticate(self.user_with_perms)
        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deletion
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())
        self.client.force_authenticate(None)