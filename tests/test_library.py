import os
import sys

import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Initialize the password context with bcrypt hashing
pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

# Add the directory containing `main.py` to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, get_db
import models
from database import Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override the get_db dependency to use the test database."""
    db = None
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Database setup and teardown for the test session
@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Create the test database schema before running tests."""
    Base.metadata.create_all(bind=engine)
    yield  # Tests run here
    Base.metadata.drop_all(bind=engine)


# Fixture for getting a test database session
@pytest.fixture
def db():
    """Provide a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def create_user(db):
    """Fixture to create a user in the database."""
    hashed_password = pwd_context.hash("securepassword")
    user = models.User(email="test@example.com", username="testuser", hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def login_user(create_user, db):
    """Fixture to log in the user and return the access token."""
    # Check if the user already exists in the database by email
    user = db.query(models.User).filter(models.User.email == create_user.email).first()

    # If the user does not exist, create a new one
    if not user:
        user = models.User(email=create_user.email, username=create_user.username, hashed_password=create_user.hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
    # Log in the user to get the access token
    response = client.post(
        "/login",
        json={"email": user.email, "password": "securepassword"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return token

@pytest.fixture
def create_book(db):
    """Fixture to create a book in the database."""
    book = models.Book(title="Test Book", author="Test Author", isbn="1234567890322", is_available=True)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@pytest.fixture(autouse=True)
def cleanup(db):
    """Cleanup the database before each test."""
    db.query(models.User).delete()
    db.query(models.Book).delete()
    db.commit()


# Test cases
def test_list_borrowed_books(create_user, create_book, login_user):
    headers = {"Authorization": f"Bearer {login_user}"}

    response = client.post(
        f"/books/{create_book.id}/borrow",
        json={"user_id": create_user.id},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["book_id"] == create_book.id
    assert data["user_id"] == create_user.id

    response = client.get("/books/borrowed", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # we borrowed one book

def test_create_user():
    """Test user creation."""
    response = client.post(
        "/users/",
        json={
            "email": "test3@example.com",
            "username": "testuser3",
            "password": "securepassword"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test3@example.com"
    assert data["username"] == "testuser3"


def test_delete_user(create_user, login_user):
    """Test deleting a user."""
    user_id = create_user.id
    headers = {"Authorization": f"Bearer {login_user}"}

    response = client.delete(f"/users/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.status_code != 404
    # Verify the user is deleted
    # response = client.get(f"/users/{user_id}", headers=headers)
    # assert response.status_code == 404


def test_create_book(login_user):
    """Test book creation."""
    headers = {"Authorization": f"Bearer {login_user}"}
    response = client.post(
        "/books/",
        json={
            "title": "Test Book",
            "author": "Test Author",
            "isbn": "1234567890143"
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"
    assert data["isbn"] == "1234567890143"
    assert data["is_available"] is True


def test_borrow_book(create_user, create_book, login_user):
    """Test borrowing a book."""
    headers = {"Authorization": f"Bearer {login_user}"}

    response = client.post(
        f"/books/{create_book.id}/borrow",
        json={"user_id": create_user.id},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["book_id"] == create_book.id
    assert data["user_id"] == create_user.id


def test_return_book(create_user, create_book, login_user):
    """Test returning a borrowed book."""
    headers = {"Authorization": f"Bearer {login_user}"}
    # Simulate borrowing the book first
    response1 = client.post(
        f"/books/{create_book.id}/borrow",
        json={"user_id": create_user.id},
        headers=headers
    )
    assert response1.status_code == 200

    response = client.post(
        f"/books/{create_book.id}/return",
        json={"user_id": create_user.id},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == create_book.id
    assert data["is_available"] is True
