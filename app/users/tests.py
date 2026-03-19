import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from auth.models import PasswordReset, TermsAndConditions

User = get_user_model()


@pytest.fixture
def api_client():
    """API client fixture."""
    return APIClient()


@pytest.fixture
def user_data():
    """Valid user registration data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "password_confirm": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "terms_accepted": True,
    }


@pytest.fixture
def create_user():
    """Create a test user."""

    def _create_user(**kwargs):
        default_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }
        default_data.update(kwargs)
        return User.objects.create_user(**default_data)

    return _create_user


@pytest.fixture
def terms_and_conditions():
    """Create active terms and conditions."""
    return TermsAndConditions.objects.create(
        title="Terms of Service",
        version="1.0",
        content="These are the terms and conditions...",
        is_active=True,
    )


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration endpoint."""

    def test_successful_registration(self, api_client, user_data, terms_and_conditions):
        """Test successful user registration."""
        url = reverse("auth:register")
        response = api_client.post(url, user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert "message" in response.data
        assert "user_id" in response.data
        assert User.objects.filter(email=user_data["email"]).exists()

    def test_registration_without_terms(self, api_client, user_data):
        """Test registration fails without accepting terms."""
        user_data["terms_accepted"] = False
        url = reverse("auth:register")
        response = api_client.post(url, user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "terms_accepted" in response.data

    def test_registration_password_mismatch(
        self, api_client, user_data, terms_and_conditions
    ):
        """Test registration fails with password mismatch."""
        user_data["password_confirm"] = "DifferentPassword123!"
        url = reverse("auth:register")
        response = api_client.post(url, user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_registration_duplicate_email(
        self, api_client, user_data, terms_and_conditions, create_user
    ):
        """Test registration fails with duplicate email."""
        create_user(email=user_data["email"])

        url = reverse("auth:register")
        response = api_client.post(url, user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data


@pytest.mark.django_db
class TestUserLogin:
    """Test user login endpoint."""

    def test_successful_login(self, api_client, create_user):
        """Test successful user login."""
        user = create_user(email="test@example.com")
        user.set_password("TestPassword123!")
        user.save()

        url = reverse("auth:login")
        data = {"email": "test@example.com", "password": "TestPassword123!"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

    def test_login_invalid_credentials(self, api_client, create_user):
        """Test login fails with invalid credentials."""
        user = create_user(email="test@example.com")
        user.set_password("TestPassword123!")
        user.save()

        url = reverse("auth:login")
        data = {"email": "test@example.com", "password": "WrongPassword"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client, create_user):
        """Test login fails for inactive user."""
        user = create_user(email="test@example.com", is_active=False)
        user.set_password("TestPassword123!")
        user.save()

        url = reverse("auth:login")
        data = {"email": "test@example.com", "password": "TestPassword123!"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordReset:
    """Test password reset flow."""

    def test_password_reset_request(self, api_client, create_user):
        """Test password reset request."""
        user = create_user(email="test@example.com")

        url = reverse("auth:password_reset_request")
        data = {"email": "test@example.com"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "hash_token" in response.data
        assert PasswordReset.objects.filter(user=user).exists()

    def test_password_reset_invalid_email(self, api_client):
        """Test password reset request with invalid email."""
        url = reverse("auth:password_reset_request")
        data = {"email": "nonexistent@example.com"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_verify_pin(self, api_client, create_user):
        """Test PIN verification."""
        user = create_user(email="test@example.com")

        # Create password reset
        reset = PasswordReset.objects.create(user=user)

        url = reverse("auth:password_reset_verify")
        data = {
            "hash_token": reset.hash_token,
            "pin_code": reset.pin_code,
            "email": user.email,
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True

    def test_password_reset_confirm(self, api_client, create_user):
        """Test password reset confirmation."""
        user = create_user(email="test@example.com")
        old_password = user.password

        # Create password reset
        reset = PasswordReset.objects.create(user=user)

        url = reverse("auth:password_reset_confirm")
        data = {
            "hash_token": reset.hash_token,
            "pin_code": reset.pin_code,
            "email": user.email,
            "new_password": "NewPassword123!",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        # Check password was changed
        user.refresh_from_db()
        assert user.password != old_password

        # Check reset was marked as used
        reset.refresh_from_db()
        assert reset.is_used is True


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile endpoint."""

    def test_get_profile_authenticated(self, api_client, create_user):
        """Test getting user profile when authenticated."""
        user = create_user(email="test@example.com")
        api_client.force_authenticate(user=user)

        url = reverse("auth:profile")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_get_profile_unauthenticated(self, api_client):
        """Test getting user profile when unauthenticated."""
        url = reverse("auth:profile")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, api_client, create_user):
        """Test updating user profile."""
        user = create_user(email="test@example.com")
        api_client.force_authenticate(user=user)

        url = reverse("auth:profile")
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone_number": "+1234567890",
        }
        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"
        assert response.data["last_name"] == "Name"
        assert response.data["phone_number"] == "+1234567890"


@pytest.mark.django_db
class TestTermsAndConditions:
    """Test terms and conditions endpoints."""

    def test_get_active_terms(self, api_client, terms_and_conditions):
        """Test getting active terms."""
        url = reverse("auth:terms")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["version"] == "1.0"

    def test_check_terms_acceptance(
        self, api_client, create_user, terms_and_conditions
    ):
        """Test checking terms acceptance."""
        user = create_user(email="test@example.com")
        api_client.force_authenticate(user=user)

        url = reverse("auth:check_terms")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["needs_acceptance"] is True

    def test_accept_terms(self, api_client, create_user, terms_and_conditions):
        """Test accepting terms."""
        user = create_user(email="test@example.com")
        api_client.force_authenticate(user=user)

        url = reverse("auth:accept_terms")
        data = {"version": "1.0"}
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert user.terms_acceptances.filter(terms=terms_and_conditions).exists()
