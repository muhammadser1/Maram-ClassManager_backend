# Maram-ClassManager_backend

Maram-ClassManager is a backend application designed to help educational institutes manage their lessons, teachers, and student progress efficiently. Built with **FastAPI**, this system provides authentication, lesson tracking, and administrative controls, supporting dynamic configurations.

## Features

- **Authentication & Authorization:** Secure login, signup, password reset, and email confirmation.
- **Lesson Management:** Teachers can submit lesson details, and admins can approve or reject them.
- **Tracking & Reporting:** Teachers track hours by education level, and admins monitor activities.


## Tech Stack

- **Backend:** FastAPI, Python
- **Database:** MongoDB Atlas
- **Render Deployment:** Hosted on Render


### Clone the Repository

```sh
git clone https://github.com/muhammadser1/Maram-ClassManager_backend.git
cd Maram-ClassManager_backend
```

### Install Dependencies

```sh
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file and configure the following:

```env
SECRET_KEY=your_secret_key  # Secret key used for JWT authentication and securing sensitive data.
EMAIL_USER=your_email@example.com  # Email address used for sending notifications.
EMAIL_PASSWORD=your_email_password  # Password or app-specific key for email authentication.
MONGO_CLUSTER_URL=mongodb+srv://your_cluster_url  # MongoDB Atlas cluster connection URL.
MONGO_DATABASE=your_database_name  # Name of the MongoDB database used for storing application data.
ALGO_HASH=your_hash_algorithm  # Hashing algorithm used for password encryption.
JWT_RESET_SECRET_KEY=your_jwt_reset_secret  # Secret key used for generating JWT tokens for password resets.
```


### Start the Server

```sh
uvicorn app.main:app --reload
```
### Project Structure
```
DynamicClassManager-API/
│── app/routes
│   ├── admin.py             # Admin-related actions (lesson approvals, management)
│   ├── group_lessons.py     # Group lessons management
│   ├── teacher.py           # Teacher-related endpoints
│   ├── user.py              # User-related endpoints
│
│   ├── core/
│   │   ├── auth.py          # Authentication logic (JWT, password handling)
│   │   ├── config.py        # General configuration settings (env variables)
│   │   ├── database.py      # Database connection and handling
│   │   ├── security.py      # Role-based security, authentication
│   │   ├── dependencies.py  # FastAPI dependencies (e.g., role-based permissions)
│
│   ├── models/              # 📦 Data models for MongoDB
│   │   ├── teacher.py       # Teacher model
│   │   ├── user.py          # User model
│   │   ├── admin.py         # Admin model
│
│   ├── schemas/             # 📄 Pydantic validation schemas
│   │   ├── teacher.py       # Teacher schema
│   │   ├── base_user.py     # User authentication schema
│   │   ├── admin.py         # Configuration schema for frontend styling
│
│   ├── utils/               # 🔧 Helper utilities
│   │   ├── email_utils.py   # Email handling utilities
│
│   ├── main.py              # 🚀 FastAPI application entry point
│
│── .env                     # 🔑 Environment variables (hidden in production)
│── requirements.txt          # 📦 Project dependencies
│── .gitignore                # 🚫 Files to ignore in version control
│── README.md                 # 📘 Project documentation
```

## Contribution

Feel free to open issues or submit pull requests if you have ideas for improvements!

---
