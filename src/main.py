import os
from datetime import datetime, timedelta
from typing import List, Any

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import crud
import schemas
from database import engine, Base, get_db
from models import User

load_dotenv(".env")

# Initialize FastAPI app
app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Password hashing and JWT settings
try:
    pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)
except AttributeError:
    pass

# Use HTTPBearer
bearer_scheme = HTTPBearer()

JT_ENCODE_ARG: str = os.getenv("JT_ENCODE_ARG")

ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

"""
Delete existing database and restart the server before running this script!!

"""
# Helper functions
def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JT_ENCODE_ARG, algorithm=ALGORITHM)


# Routes: Login
@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.Login, db: Session = Depends(get_db)):
    """Authenticate user and return an access token."""
    user: User = crud.UserRepository.get_user_by_email(db, email=form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# Authentication dependency function
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)) -> User:
    try:
        # Decode the token
        payload = jwt.decode(credentials.credentials, JT_ENCODE_ARG, algorithms=[ALGORITHM])

        # Extract email from token
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.exceptions.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find the user in the database
    user = crud.UserRepository.get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

# Routes: User Management
# Create User
@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
        user: schemas.UserCreate,
        db: Session = Depends(get_db)):
    """Create a new user."""

    if crud.UserRepository.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user.password = hash_password(user.password)
    return crud.UserRepository.create_user(db=db, user=user)

# List users
@app.get("/users/list", response_model=List[schemas.UserMinimal])
def get_all_users(
        current_user: User = Depends(get_current_user),  # Add authentication
        db: Session = Depends(get_db)
):
    """Retrieve all users - requires authentication."""
    users: List[User] = crud.UserRepository.get_all_users(db)
    return users

# Get user by id
@app.get("/users/{user_id}", response_model=schemas.User)
def get_user(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
       ) -> Any:

    """Get a user by ID."""
    user: User = crud.UserRepository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return user

# Get user by mail
@app.get("/users/email/{email}", response_model=schemas.User)  # not enforcing auth since it is an entry
def get_user_by_email(
        email: str,
        db: Session = Depends(get_db)):
    """Get a user by email."""
    user: User = crud.UserRepository.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# Delete user by id
@app.delete("/users/{user_id}", response_model=schemas.UserDeletionResponse, status_code=status.HTTP_200_OK, )
def delete_user(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """Delete a user."""


    if not crud.UserRepository.get_user(db, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")

    crud.UserRepository.delete_user(db, user_id)
    return schemas.UserDeletionResponse(
        user_id=user_id,
        status="success",
        message="User deleted successfully"
    )

# Update user
@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(
        user_id: int,
        user: schemas.UserUpdate,
        current_user: User = Depends(get_current_user),  # Add authentication
        db: Session = Depends(get_db)):
    """Update user details."""
    db_user: User = crud.UserRepository.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")

    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/books/list", response_model=List[schemas.Book])
def get_books_list(
        current_user: User = Depends(get_current_user),  # Requires authentication
        db: Session = Depends(get_db)
):
    """Retrieve a list of all books."""
    books = crud.BookRepository.get_all_books(db)  # Assuming you have a method for this in the `crud` module
    return books

# Routes: Book Management
# Create Book
@app.post("/books/", response_model=schemas.Book)
def create_book(
        book: schemas.BookCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """Create a new book."""
    return crud.BookRepository.create_book(db=db, book=book)

# Borrow Book
@app.post("/books/{book_id}/borrow", response_model=schemas.BookBorrow)
def borrow_book(
        book_id: int,
        borrow_request: schemas.BookBorrowRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    """Borrow a book."""
    try:
        return crud.BookRepository.borrow_book(db=db, book_id=book_id, user_id=borrow_request.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Return Book
@app.post("/books/{book_id}/return", response_model=schemas.Book)
def return_book(
        book_id: int,
        return_request: schemas.BookReturnRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):

    """Return a borrowed book."""
    try:
        return crud.BookRepository.return_book(db=db, book_id=book_id, user_id=return_request.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

# Return borrowed books
@app.get("/books/borrowed", response_model=List[schemas.BookBorrowedResponse])
def get_borrowed_books(
        db: Session = Depends(get_db)):

    """Get a list of borrowed books."""
    try:
        return crud.BookRepository.get_borrowed_books(db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
