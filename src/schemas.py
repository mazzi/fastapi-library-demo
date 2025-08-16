from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


# Schema for the login request body (email and password)
class Login(BaseModel):
    email: str
    password: str

# Schema for the response of the login endpoint (access token)
class Token(BaseModel):
    access_token: str
    token_type: str

# Base User Schema - Shared by UserCreate and UserUpdate
class UserBase(BaseModel):
    email: EmailStr
    username: str
    # Validate email format explicitly if needed
    @field_validator('email')
    @staticmethod
    def email_must_contain_at(  v):
        if "@" not in v:
            raise ValueError("Email must contain @")
            # Add database or in-memory checks for uniqueness if needed
        return v

# User Creation Schema
class UserCreate(UserBase):
    password: str  # Password field for user creation
    email: str

    # Validate username is not empty
    @field_validator('username')
    @staticmethod
    def username_must_not_be_empty( v):
        if not v or len(v) == 0:
            raise ValueError('Username must not be empty')
        return v

    @field_validator('password')
    @staticmethod
    def password_strength(v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserMinimal(BaseModel):
    id: int
    email: str
    username: str

    model_config = ConfigDict(from_attributes=True)

# User Update Schema (Optional Fields for Update)
class UserUpdate(BaseModel):
    username: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None  # Optional password field for updating

class UserDeletionResponse(BaseModel):
    user_id: int
    status: str
    message: str

# Complete User Schema (includes response data)
class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime  # Date when user was created
    updated_at: Optional[datetime]  # Date when user was last updated

    model_config = ConfigDict(from_attributes=True)

# Base Book Schema - Shared by BookCreate and BookUpdate
class BookBase(BaseModel):
    title: str
    author: str
    isbn: str

    # ISBN Validation (if necessary, based on standard)
    @field_validator('isbn')
    @staticmethod
    def isbn_length( v):
        if len(v) != 13:
            raise ValueError('ISBN must be exactly 13 characters')
        return v

# Book Creation Schema
class BookCreate(BookBase):
    pass

# Complete Book Schema (includes response data)
class Book(BookBase):
    id: int
    is_available: bool
    created_at: datetime  # When the book was added
    updated_at: Optional[datetime]  # Last update to the book data
    borrow_date: Optional[datetime] = None  # Add borrow_date as an optional field
    due_date: Optional[datetime] = None
    return_date: Optional[datetime] = None


    # Set from_attributes=True in model_config
    model_config = ConfigDict(from_attributes=True)


# Book Borrow Request Schema
class BookBorrowRequest(BaseModel):
    user_id: int

# Book Return Request Schema
class   BookReturnRequest(BaseModel):
    user_id: int

# Book Borrow Record Schema (Response)
class BookBorrow(BaseModel):
    id: int
    book_id: int
    user_id: int
    borrow_date: datetime
    due_date: datetime

    model_config = ConfigDict(from_attributes=True)

# Book Borrowed Response Schema
class BookBorrowedResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    borrow_date: datetime
    due_date: datetime

    model_config = ConfigDict(from_attributes=True)
