# Splitwise Clone - Expense Tracker

A full-featured expense tracking and splitting application built with Flask, inspired by Splitwise. This application allows users to track shared expenses, manage friends, create groups, and settle debts efficiently.

## 🚀 Features

### Core Functionality
- **User Authentication**: Secure registration and login system
- **Expense Management**: Add, track, and split expenses with friends
- **Friend System**: Add/remove friends and manage relationships
- **Group Management**: Create groups for shared expenses (trips, roommates, etc.)
- **Balance Tracking**: Real-time calculation of who owes what to whom
- **Settle Up**: Mark expenses as settled between friends

### User Interface
- **Responsive Design**: Built with Tailwind CSS for mobile and desktop
- **Clean Dashboard**: Overview of balances, recent activity, and groups
- **Intuitive Navigation**: Easy-to-use interface for all features
- **Real-time Updates**: Dynamic balance calculations and expense tracking

## 🛠️ Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login for session management
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Security**: Werkzeug for password hashing
- **Validation**: Email validation for user registration

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## 🔧 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd splitwise-2
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your web browser and navigate to `http://127.0.0.1:5000`

## 📁 Project Structure

```
splitwise-2/
│
├── app.py                 # Main Flask application
├── init_db.py            # Database initialization script
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
│
├── instance/
│   └── splitwise.db      # SQLite database file
│
└── templates/            # HTML templates
    ├── base.html         # Base template with navigation
    ├── index.html        # Landing page
    ├── login.html        # User login page
    ├── register.html     # User registration page
    ├── dashboard.html    # Main dashboard
    ├── add_expense.html  # Add expense form
    ├── friends.html      # Friends management
    ├── groups.html       # Groups listing
    ├── create_group.html # Create group form
    └── view_group.html   # Group details view
```

## 🗄️ Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: User email address
- `password_hash`: Encrypted password

### Friends Table (Association Table)
- `user_id`: Foreign key to users
- `friend_id`: Foreign key to users

### Groups Table
- `id`: Primary key
- `name`: Group name
- `created_at`: Creation timestamp
- `created_by`: Foreign key to users

### Group Members Table
- `id`: Primary key
- `group_id`: Foreign key to groups
- `user_id`: Foreign key to users
- `joined_at`: Join timestamp

### Expenses Table
- `id`: Primary key
- `description`: Expense description
- `amount`: Expense amount
- `date`: Expense date
- `payer_id`: Foreign key to users (who paid)
- `group_id`: Foreign key to groups (optional)

### Expense Splits Table
- `id`: Primary key
- `expense_id`: Foreign key to expenses
- `user_id`: Foreign key to users (who owes)
- `amount`: Amount owed
- `is_settled`: Settlement status
- `settled_at`: Settlement timestamp

## 🎯 Usage Guide

### Getting Started
1. **Register**: Create a new account with username, email, and password
2. **Login**: Access your account using your credentials
3. **Add Friends**: Search and add friends to start splitting expenses

### Managing Expenses
1. **Add Expense**: 
   - Enter description and amount
   - Choose if you paid or someone else paid
   - Select friends to split with
   - Optionally assign to a group

2. **View Balances**: 
   - Dashboard shows who owes you money (green)
   - Shows who you owe money to (red)
   - Net balances are calculated automatically

3. **Settle Up**: 
   - Mark individual expenses as settled
   - Settle all debts with a specific friend at once

### Group Management
1. **Create Groups**: 
   - Name your group (e.g., "Trip to Goa", "Apartment 4B")
   - Add friends as members
   
2. **Group Expenses**: 
   - Add expenses within groups
   - Track group-specific balances
   - View group expense history

## 🔐 Security Features

- **Password Security**: Passwords are hashed using Werkzeug's security functions
- **Session Management**: Secure session handling with Flask-Login
- **Input Validation**: Server-side validation for all user inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection attacks

## 🚀 API Endpoints

### Authentication
- `GET /` - Landing page
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /register` - Registration page
- `POST /register` - Process registration
- `GET /logout` - Logout user

### Dashboard & Expenses
- `GET /dashboard` - Main dashboard
- `GET /add_expense` - Add expense form
- `POST /add_expense` - Process new expense
- `POST /settle_up` - Mark expenses as settled

### Friends Management
- `GET /friends` - Friends page
- `POST /add_friend/<id>` - Add friend
- `POST /remove_friend/<id>` - Remove friend

### Groups Management
- `GET /groups` - Groups listing
- `GET /create_group` - Create group form
- `POST /create_group` - Process new group
- `GET /groups/<id>` - View group details
- `POST /group/<id>/add_member` - Add member to group

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for session security
- `SQLALCHEMY_DATABASE_URI`: Database connection string

### Database Configuration
The application uses SQLite by default. To use a different database:
1. Update the `SQLALCHEMY_DATABASE_URI` in `app.py`
2. Install the appropriate database driver
3. Run the initialization script

## 🐛 Troubleshooting

### Common Issues

1. **Database not found**
   - Run `python init_db.py` to create the database

2. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check if virtual environment is activated

3. **Template errors**
   - Verify all template files are in the `templates/` directory
   - Check for missing `{% endblock %}` tags

4. **Friend relationship errors**
   - Database relationships are automatically handled
   - If issues persist, reinitialize the database

## 🚀 Future Enhancements

- **Mobile App**: React Native or Flutter mobile application
- **Email Notifications**: Notify users about new expenses and settlements
- **Receipt Upload**: Image upload for expense receipts
- **Currency Support**: Multi-currency expense tracking
- **Export Features**: Export expense reports to PDF/CSV
- **Advanced Splitting**: Unequal splits, percentage-based splits
- **Payment Integration**: Integration with payment gateways
- **Expense Categories**: Categorize expenses (food, travel, utilities)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

Created with ❤️ by [Your Name]

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Create an issue on GitHub
3. Contact the development team

---

**Happy Expense Tracking! 💰**