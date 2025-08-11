# 📚 FastAPI Library Demo

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-brightgreen)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

## 📖 Overview
A simple API for managing a library, built with **FastAPI**.

Users can manage books and perform typical library actions like borrowing and returning.

The two main resource types are **Users** and **Books**.

### User Features
- Create a new user
- List all users
- Update existing users
- Delete users

### Book Features
- Add new books
- Borrow books
- Return books

---

## 🛠 Tech Stack & Structure

### API
- **FastAPI** with token-based authentication

### Database
- **SQLAlchemy** ORM

### Testing
- Basic test suite in `/tests`

### Requirements
- Python **3.12+**
- Dependencies listed in `requirements.txt`

---

## 🚀 Quick Start

| Action                | Command                                                                                   |
|-----------------------|-------------------------------------------------------------------------------------------|
| **Install deps**      | `pip install -r requirements.txt`                                                         |
| **Run (Uvicorn)**     | `uvicorn main:app --host 0.0.0.0 --port 5010 --reload`                                     |
| **Run (Docker)**      | `docker build --no-cache --build-arg JT_ENCODE_ARG=my_secret -t library-api .` <br> `docker run -d --name library-api -p 5010:5010 library-api` |
| **Run (FastAPI CLI)** | `fastapi run main.py`                                                                     |
| **Tests**             | `pytest`                                                                                  |

---

## 📜 API Documentation
- Swagger UI: [http://localhost:5010/docs](http://localhost:5010/docs)
- ReDoc: [http://localhost:5010/redoc](http://localhost:5010/redoc)

You can try endpoints directly in Swagger UI with **HTTPBearer authentication**.

---

## 📝 Notes
- Depending on your system, use `localhost` instead of `0.0.0.0`.
- Replace `JT_ENCODE_ARG` in Docker builds with any string of your choice.

---

## 📄 License
This project is licensed under the MIT License.
