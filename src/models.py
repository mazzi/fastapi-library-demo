import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from database import Base


# User model - representing users in the system
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)  # Specify length for email
    username = Column(String(50))  # Specify length for username
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String(128))  # Storing password hashes, make sure to hash passwords
    created_at = Column(DateTime, default=datetime.datetime.now)  # Timestamp of user creation
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)  # Updated timestamp

    books = relationship("BookBorrow", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

# Book model - representing books in the system
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))  # Specify length for title
    author = Column(String(100))  # Specify length for author
    isbn = Column(String(13), unique=True)  # ISBN should follow the 13-character format
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now)  # Timestamp of book creation
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)  # Updated timestamp

    borrows = relationship("BookBorrow", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book(id={self.id}, title={self.title}, author={self.author})>"

# BookBorrow model - representing the relationship between books and users
class BookBorrow(Base):
    __tablename__ = "book_borrows"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    borrow_date = Column(DateTime, default=datetime.datetime.now)
    due_date = Column(DateTime, nullable=True)
    return_date = Column(DateTime, nullable=True)  # Add return_date column

    # Relationships
    book = relationship("Book", back_populates="borrows")
    user = relationship("User", back_populates="books")

    def __repr__(self):
        return f"<BookBorrow(id={self.id}, book_id={self.book_id}, user_id={self.user_id}, borrow_date={self.borrow_date})>"