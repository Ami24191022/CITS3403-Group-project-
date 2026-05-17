from app.models import db, User
from werkzeug.security import generate_password_hash


# Helper function — create a test user in the database
def create_user(email="test@example.com", password="Password123"):
    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        password_hash=generate_password_hash(password, method="pbkdf2:sha256")
    )
    db.session.add(user)
    db.session.commit()
    return user


# Helper function — manually log in a test user
def login(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id


# Test 1 — invalid login shows error message
def test_invalid_login_shows_error_message(client, app):
    response = client.post("/login", data={
        "email": "wrong@test.com",
        "password": "wrongpassword"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


# Test 2 — signup with mismatched passwords shows error message
def test_signup_password_mismatch_shows_error_message(client, app):
    response = client.post("/signup", data={
        "firstName": "Test",
        "lastName": "User",
        "email": "newuser@test.com",
        "password": "Password123",
        "confirmPassword": "Different123",
        "agree": "on"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Passwords do not match" in response.data

    user = User.query.filter_by(email="newuser@test.com").first()
    assert user is None


# Test 3 — dashboard requires login
def test_dashboard_requires_login(client, app):
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# Test 4 — logout works
def test_logout_works(client, app):
    user = create_user()
    login(client, user)

    response = client.get("/logout", follow_redirects=True)

    assert response.status_code == 200

    with client.session_transaction() as sess:
        assert "user_id" not in sess

    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]