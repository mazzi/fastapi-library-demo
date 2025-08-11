from datetime import datetime
from typing import Optional, List
from datetime import timedelta
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import models
import schemas

# Password hashing context
pwd_context: CryptContext = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Repositories
class UserRepository:
    @staticmethod
    def get_user(db: Session, user_id: int):
        return db.query(models.User).filter_by(id=user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(models.User).filter_by(email=email).first()


    @staticmethod
    def create_user(db: Session, user: schemas.UserCreate):
        try:
            hashed_password: str = user.password
            db_user: models.User = models.User(
                email=user.email,
                username=user.username,
                hashed_password=hashed_password
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )

    @staticmethod
    def get_all_users(db: Session):
        """Retrieve all users from the database."""
        try:
            return db.query(models.User).all()
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve users: {str(e)}"
            )

    @staticmethod
    def delete_user(db: Session, user_id: int):
        db_user: Optional[models.User, None] = UserRepository.get_user(db, user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        try:
            db.delete(db_user)
            db.commit()
            return {
                "user_id": user_id,
                "status": "success",
                "message": "User deleted successfully"
            }
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {str(e)}"
            )


class BookRepository:
    @staticmethod
    def create_book(db: Session, book: schemas.BookCreate):
        try:
            db_book: models.Book = models.Book(
                title=book.title,
                author=book.author,
                isbn=book.isbn
            )
            db.add(db_book)
            db.commit()
            db.refresh(db_book)
            return db_book
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create book: {str(e)}"
            )

    @staticmethod
    def borrow_book(db: Session, book_id: int, user_id: int):
        book: Optional[models.Book, None] = db.query(models.Book).filter_by(id=book_id).first()
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

        if not book.is_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is already borrowed")

        try:
            borrow_date = datetime.now()

            due_date = borrow_date + timedelta(days=7)
            borrow: models.BookBorrow = models.BookBorrow(book_id=book_id, user_id=user_id,
                                                          borrow_date=borrow_date, due_date=due_date, return_date=None)
            book.is_available = False
            db.add(borrow)
            db.commit()
            db.refresh(borrow)
            return borrow
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to borrow book: {str(e)}"
            )

    @staticmethod
    def return_book(db: Session, book_id: int, user_id: int):
        borrow: Optional[models.BookBorrow, None] = db.query(models.BookBorrow).filter(
            models.BookBorrow.book_id == book_id,  # noqa
            models.BookBorrow.user_id == user_id,    # noqa
            models.BookBorrow.return_date.is_(None)  # Only consider borrow records without a return date
        ).first()
        if not borrow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active borrow found")

        try:
            borrow.due_date = datetime.now()
            borrow.return_date = datetime.now()
            book: Optional[models.Book, None] = db.query(models.Book).filter_by(id=book_id).first()
            if book:
                book.is_available = True
                db.commit()
                db.refresh(book)
                return book
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to return book: {str(e)}"
            )

    @staticmethod
    def get_all_books(db: Session) -> List[schemas.Book]:
        """Retrieve all books from the database."""
        books = (
            db.query(
                models.Book,
                models.BookBorrow.borrow_date,
                models.BookBorrow.due_date,
                models.BookBorrow.return_date
            )
            .outerjoin(models.BookBorrow, models.Book.id == models.BookBorrow.book_id)   # noqa
            .all()
        )
        return [
            schemas.Book.model_validate(
                {
                    **book[0].__dict__,  # Book fields
                    "borrow_date": book[1],  # borrow_date from BookBorrow
                    "due_date": book[2],  # due_date from BookBorrow
                    "return_date": book[3],  # due_date from BookBorrow
                }
            )
            for book in books
        ]

    @staticmethod
    def get_borrowed_books(db: Session) -> List[schemas.Book]:
        """Retrieve all borrowed books for a specific user."""
        borrowed_books = (
            db.query(
                models.Book.id,
                models.Book.title,
                models.Book.author,
                models.Book.isbn,
                models.BookBorrow.due_date,
                models.BookBorrow.borrow_date,
            )
            .join(models.BookBorrow, models.Book.id == models.BookBorrow.book_id)  # noqa
            .filter(models.Book.is_available == False)
            .all()
        )
        if not borrowed_books:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No borrowed books found")

        return [schemas.BookBorrowedResponse.model_validate(borrow) for borrow in borrowed_books]
