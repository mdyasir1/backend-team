# 🚀 Backend Project – User Data Management

## 📌 Overview
This backend project is about **collecting user details from the frontend and saving them in a database**.  

The details we need are:
- Name  
- Email  
- Location  
- Skills  

👉 The most important rule: **no two users can have the same email**.  

We will provide two main APIs:
- **POST /users/** → Add a new user  
- **GET /users/** → Retrieve all users  

---

## ⚙️ Technologies Used
- **FastAPI** → Backend framework  
- **SQLAlchemy** → ORM for database handling  
- **Alembic** → Database migrations  
- **Pydantic** → Data validation  
- **Email-validator** → Email format validation  
- **bcrypt** → (optional, if passwords are added later)  

---

## 📂 Project Structure
backend_project/
│── alembic/ → stores migration files
│── app/
│ ├── database.py → database setup
│ ├── models.py → user table definition
│ ├── schemas.py → input/output validation
│ ├── crud.py → database operations
│ ├── main.py → FastAPI entry point
│── alembic.ini → Alembic configuration
│── requirements.txt → project dependencies


---

## 🛠️ Process Explanation

### 1. Setup
- Install FastAPI, SQLAlchemy, Alembic, and other dependencies.  
- Configure the project to connect with a database (SQLite, PostgreSQL, or MySQL).  

### 2. Database Design
- Create a `users` table with columns:  
  - `id` (unique ID)  
  - `name` (string)  
  - `email` (string, must be unique)  
  - `location` (string)  
  - `skills` (string)  

### 3. Data Validation
- Validate inputs using Pydantic.  
- Ensure the email is valid using `EmailStr`.  
- Prevent duplicate emails using database constraints.  

### 4. Business Logic
- If a user tries to register with an already registered email → return an error.  
- If the data is valid → save the user into the database.  

### 5. API Endpoints
- **POST /users/** → Add a new user  
- **GET /users/** → Get list of all users  

### 6. Database Migrations
- Use Alembic to generate and apply migration files.  
- This allows safe updates to the database structure in the future.  

### 7. Running the Server
- Start the backend server with Uvicorn.  
- Access API documentation at `/docs` (Swagger UI).  

---

## 📌 Example Flow

1. Frontend sends user details:  
name: Alice
email: alice@example.com

location: India
skills: Python, FastAPI


2. Backend checks:
- Is the email format valid?  
- Is the email unique?  

3. If valid → Save the user to the database.  
4. If duplicate → Return error message: **"Email already registered"**.  
5. A GET request to `/users/` returns all saved users.  

---

## ✅ Summary
- The backend collects and stores user data.  
- **Email must be unique** for each user.  
- Two main APIs are available: **Add User** and **Get Users**.  
- Alembic is used for managing database migrations.  
- This project is simple, structured, and ready for future extensions.
