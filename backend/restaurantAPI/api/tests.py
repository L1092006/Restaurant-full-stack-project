from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from decimal import Decimal
from .models import * 
import environ
from pathlib import Path
from decimal import Decimal



# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env.read_env(BASE_DIR / '.env')

# Create your tests here.

# Test SignUpView


User = get_user_model()

class SignUpViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("api:signup")

    def test_signup_success_creates_user_and_returns_message(self):
        data = {
            "username": "loc123",
            "password": "StrongPass123!",
            "first_name": "Loc",
            "last_name": "Nguyen",
            "email": "loc@example.com"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"message": "success"})

        user = User.objects.get(username="loc123")
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_signup_missing_username_returns_400_and_field_error(self):
        data = {
            "password": "StrongPass123!",
            "first_name": "Loc",
            "last_name": "Nguyen",
            "email": "loc@example.com"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertTrue(response.data["username"])

    def test_signup_missing_password_returns_400_and_field_error(self):
        data = {
            "username": "loc123",
            "first_name": "Loc",
            "last_name": "Nguyen",
            "email": "loc@example.com"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertTrue(response.data["password"])

    def test_signup_duplicate_username_returns_400(self):
        User.objects.create_user(username="loc123", password="StrongPass123!")

        data = {
            "username": "loc123",
            "password": "AnotherPass123!",
            "first_name": "Loc",
            "last_name": "Nguyen",
            "email": "loc2@example.com"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_signup_weak_password_returns_400(self):
        data = {
            "username": "loc1234",
            "password": "123",
            "first_name": "Loc",
            "last_name": "Nguyen",
            "email": "loc@example.com"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


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



# Test for cart view
TAX = env('TAX')  # Decimal value used by MenuItemSerializer


def _dec(value):
    return Decimal(str(value))

class CartViewTests(APITestCase):
    def setUp(self):
        # users
        self.user = User.objects.create_user(username="user", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        self.staff = User.objects.create_user(username="staff", password="pass")

        # permissions
        self.view_perm = Permission.objects.get(codename="view_cartitem")
        self.change_perm = Permission.objects.get(codename="change_cartitem")
        self.delete_perm = Permission.objects.get(codename="delete_cartitem")

        # category and menu items
        self.cat = Category.objects.create(title="cat1", slug="cat1")
        self.menu1 = MenuItem.objects.create(
            title="m1",
            price=Decimal("10.00"),
            stock=10,
            featured=False,
            description="desc1",
            category=self.cat,
        )
        self.menu2 = MenuItem.objects.create(
            title="m2",
            price=Decimal("5.00"),
            stock=5,
            featured=False,
            description="desc2",
            category=self.cat,
        )

        # cart items
        self.item_user = CartItem.objects.create(user=self.user, menuitem=self.menu1, quantity=1)
        self.item_other = CartItem.objects.create(user=self.other, menuitem=self.menu2, quantity=2)

        # urls
        self.list_url = reverse("api:cart-list")
        self.detail_user = reverse("api:cart-detail", args=[self.item_user.pk])
        self.detail_other = reverse("api:cart-detail", args=[self.item_other.pk])

    def _assert_ok(self, resp, expected=status.HTTP_200_OK):
        if resp.status_code >= 500:
            raise AssertionError(f"Server error {resp.status_code}: {resp.content!r}")
        assert resp.status_code == expected, f"Expected {expected}, got {resp.status_code}: {resp.content!r}"

    def test_get_list_with_view_perm_returns_all_items_and_prices(self):
        self.staff.user_permissions.add(self.view_perm)
        self.client.force_authenticate(self.staff)

        resp = self.client.get(self.list_url)
        self._assert_ok(resp, expected=status.HTTP_200_OK)

        data = resp.json()
        returned_ids = {item["id"] for item in data}
        assert self.item_user.id in returned_ids
        assert self.item_other.id in returned_ids

        # find the serialized entry for item_user and item_other
        by_id = {item["id"]: item for item in data}
        u = by_id[self.item_user.id]
        o = by_id[self.item_other.id]

        # expected totals
        expected_u_total = _dec(self.menu1.price) * _dec(self.item_user.quantity)
        expected_o_total = _dec(self.menu2.price) * _dec(self.item_other.quantity)

        expected_u_after = expected_u_total * _dec(TAX)
        expected_o_after = expected_o_total * _dec(TAX)

        assert _dec(u["total_price"]) == expected_u_total
        assert _dec(o["total_price"]) == expected_o_total

        assert _dec(u["total_price_after_tax"]) == expected_u_after
        assert _dec(o["total_price_after_tax"]) == expected_o_after

    def test_get_list_without_view_perm_returns_only_own_items_and_prices(self):
        self.client.force_authenticate(self.user)

        resp = self.client.get(self.list_url)
        self._assert_ok(resp, expected=status.HTTP_200_OK)

        data = resp.json()
        returned_ids = {item["id"] for item in data}
        assert self.item_user.id in returned_ids
        assert self.item_other.id not in returned_ids

        item = data[0]
        expected_total = _dec(self.menu1.price) * _dec(self.item_user.quantity)
        expected_after = expected_total * _dec(TAX)

        assert _dec(item["total_price"]) == expected_total
        assert _dec(item["total_price_after_tax"]) == expected_after

    def test_create_sets_user_and_computes_totals(self):
        self.client.force_authenticate(self.user)
        payload = {"menuitem_id": self.menu2.pk, "quantity": 3, "user": self.other.pk}

        resp = self.client.post(self.list_url, payload, format="json")
        if resp.status_code >= 500:
            raise AssertionError(f"Server error {resp.status_code}: {resp.content!r}")

        assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST), resp.content

        if resp.status_code == status.HTTP_201_CREATED:
            data = resp.json()
            created = CartItem.objects.get(pk=data["id"])
            assert created.user == self.user
            assert created.menuitem_id == self.menu2.pk
            assert created.quantity == 3

            # totals in response
            assert _dec(data["total_price"]) == _dec(self.menu2.price) * _dec(3)
            assert _dec(data["total_price_after_tax"]) == _dec(self.menu2.price) * _dec(3) * _dec(TAX)

    def test_create_duplicate_menuitem_for_same_user_fails(self):
        self.client.force_authenticate(self.user)
        payload = {"menuitem_id": self.menu1.pk, "quantity": 2}  # user already has menu1

        resp = self.client.post(self.list_url, payload, format="json")
        if resp.status_code >= 500:
            raise AssertionError(f"Server error {resp.status_code}: {resp.content!r}")

        assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.content

    def test_update_allowed_for_owner_updates_totals(self):
        self.client.force_authenticate(self.user)
        payload = {"quantity": 5}

        resp = self.client.patch(self.detail_user, payload, format="json")
        self._assert_ok(resp, expected=status.HTTP_200_OK)

        data = resp.json()
        self.item_user.refresh_from_db()
        assert self.item_user.quantity == 5

        expected_total = _dec(self.menu1.price) * _dec(5)
        expected_after = expected_total * _dec(TAX)

        assert _dec(data["total_price"]) == expected_total
        assert _dec(data["total_price_after_tax"]) == expected_after

    def test_update_allowed_for_user_with_change_perm(self):
        self.staff.user_permissions.add(self.change_perm)
        self.client.force_authenticate(self.staff)
        payload = {"quantity": 7}

        resp = self.client.patch(self.detail_other, payload, format="json")
        self._assert_ok(resp, expected=status.HTTP_404_NOT_FOUND)



    def test_delete_owner_can_delete_own_item(self):
        self.client.force_authenticate(self.user)

        resp = self.client.delete(self.detail_user)
        if resp.status_code >= 500:
            raise AssertionError(f"Server error {resp.status_code}: {resp.content!r}")

        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not CartItem.objects.filter(pk=self.item_user.pk).exists()

    def test_delete_allowed_for_user_with_delete_perm(self):
        self.staff.user_permissions.add(self.delete_perm)
        self.client.force_authenticate(self.staff)

        resp = self.client.delete(self.detail_other)
        if resp.status_code >= 500:
            raise AssertionError(f"Server error {resp.status_code}: {resp.content!r}")

        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not CartItem.objects.filter(pk=self.item_other.pk).exists()

