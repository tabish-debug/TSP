
from fastapi import status
from .override import client

login_payload = {
    "email": "user@test.com",
    "password": "testpassword"
}

user_payload = {
    "name": "test",
    "email": "user@test.com",
    "photo": "string",
    "password": "testpassword",
    "passwordConfirm": "testpassword"
}


def test_create_user():

    response = client.post("/api/auth/register", json=user_payload)

    assert response.status_code == status.HTTP_201_CREATED

    created_user = response.json()
    assert "id" in created_user
    assert created_user["name"] == user_payload["name"]
    assert created_user["email"] == user_payload["email"]


def test_login_successful():
    response = client.post("/api/auth/login", json=login_payload)

    assert response.status_code == status.HTTP_200_OK

    assert 'access_token' in response.cookies
    assert 'refresh_token' in response.cookies
    assert response.cookies.get('logged_in', None) == 'True'
    assert 'access_token' in response.json()


def test_login_unsuccessful():

    login_payload = {
        "email": "wrong@test.com",
        "password": "wrongpassword"
    }

    response = client.post("/api/auth/login", json=login_payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert 'Incorrect Email or Password' == response.json().get('detail')


def test_get_me():
    response = client.post("/api/auth/login", json=login_payload)
    response = response.json()

    access_token = response.get('access_token', '')

    client.headers.update({"Authorization": f"Bearer {access_token}"})

    response = client.get("/api/user/me")

    assert response.status_code == status.HTTP_200_OK

    user_response = response.json()
    assert user_response["name"] == "test"
    assert user_response["email"] == "user@test.com"


def test_refresh_token():
    response = client.post("/api/auth/login", json=login_payload)
    refresh = response.cookies.get('refresh_token', None)

    client.headers.update({"refresh": refresh})
    client.headers.pop('authorization')

    response = client.get("/api/auth/refresh")
    print(response.content)

    assert response.status_code == status.HTTP_200_OK

    assert 'access_token' in response.cookies
    assert response.cookies.get('logged_in', None) == 'True'
    new_access_token = response.json().get('access_token')
    assert new_access_token is not None


def test_logout():
    response = client.post("/api/auth/login", json=login_payload)
    response = response.json()

    access_token = response.get('access_token', None)

    client.headers.update({"Authorization": f"Bearer {access_token}"})

    response = client.get("/api/auth/logout")

    assert response.status_code == status.HTTP_200_OK

    assert 'logged_in' not in response.cookies
