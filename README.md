# Tuross Tipping Competition Web Application

A full-stack web application built with Flask for managing a local rugby league tipping competition. This application enables participants to submit weekly tips, track their progress, compete on leaderboards, and engage with other participants through match-specific chat rooms.

## 🎯 Project Overview

The Tuross Tipping Competition is a local rugby league (NRL) tipping competition where participants buy in for $200 each. Throughout the NRL season, members submit weekly predictions on match outcomes, earning points for correct selections. The top 3 participants with the most points at the end of the regular season win prizes.

This application digitizes and automates the entire competition management process, replacing manual tracking with a modern, scalable web platform.

## ✨ Key Features

### Core Functionality
- **User Authentication & Authorization**: Secure login system with password hashing, session management, and role-based access control (admin/user)
- **Tip Submission System**: Intuitive interface for submitting weekly match predictions with validation and deadline enforcement
- **Real-time Leaderboard**: Dynamic rankings with aggregated statistics, running totals, and round-by-round performance tracking
- **Match-Specific Chat**: Live chat rooms for each match, enabling participants to discuss games and share predictions
- **Profile Management**: Customizable user profiles with avatar selection and password management
- **Tip Visibility Control**: Time-based visibility rules ensuring tips remain hidden until Thursday 5pm deadline
- **Automated Fixture Management**: Integration with external NRL fixture API for automatic match data updates and score tracking

### Advanced Features
- **SMS Reminders**: Automated Twilio integration for weekly tip submission reminders
- **Automated Default Tips**: System automatically assigns default tips for users who miss the submission deadline
- **Admin Dashboard**: Comprehensive admin interface for user management, tip oversight, and competition administration
- **Statistical Tracking**: Per-round and cumulative statistics for each participant
- **Database Migrations**: Version-controlled schema changes using Flask-Migrate and Alembic

## 🏗️ Architecture & Technical Stack

### Backend
- **Framework**: Flask 3.1.0
- **Database**: PostgreSQL (production) with SQLAlchemy ORM
- **Authentication**: Flask-Login with Werkzeug password hashing
- **Task Scheduling**: Flask-APScheduler for automated background jobs
- **API Integration**: External NRL fixture API for match data
- **SMS Service**: Twilio for automated notifications

### Frontend
- **Templating**: Jinja2 templates with responsive design
- **Static Assets**: Custom CSS styling with team logos and avatars
- **User Experience**: Intuitive navigation with flash messaging for user feedback

### Infrastructure
- **Production Server**: Gunicorn
- **Database Migrations**: Flask-Migrate with Alembic
- **Environment Management**: python-dotenv for configuration
- **Timezone Handling**: pytz for accurate Australian timezone management

## 📁 Project Structure

```
flask-tuross-tipping-comp-app/
├── app/
│   ├── __init__.py              # Application factory pattern
│   ├── models.py                # SQLAlchemy database models
│   ├── routes/                  # Blueprint-based route organization
│   │   ├── auth_routes.py       # Authentication endpoints
│   │   ├── tip_routes.py        # Tip submission and viewing
│   │   ├── leaderboard_routes.py # Rankings and statistics
│   │   ├── chat_routes.py       # Match-specific chat functionality
│   │   ├── profile_routes.py    # User profile management
│   │   ├── admin_routes.py     # Admin dashboard
│   │   └── main_routes.py      # Home page and core routes
│   ├── services/
│   │   └── fixtures.py          # Fixture API integration and business logic
│   ├── utils/
│   │   ├── helper_functions.py  # Utility functions
│   │   ├── send_sms.py          # Twilio SMS integration
│   │   └── team_logos.py        # Team logo mappings
│   ├── static/                  # CSS, images, logos, avatars
│   └── templates/               # Jinja2 HTML templates
├── migrations/                   # Database migration scripts
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── Procfile                     # Production deployment configuration
```

## 🔧 Key Technical Implementations

### Database Design
- **Normalized Schema**: Well-structured models with proper relationships and constraints
- **Unique Constraints**: Prevents duplicate tip submissions per user/match
- **Indexed Queries**: Optimized database queries for leaderboard calculations
- **Window Functions**: Advanced SQL window functions for ranking calculations

### Security Features
- **Password Hashing**: Werkzeug's secure password hashing (not storing plaintext)
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy ORM
- **Session Management**: Secure session handling with Flask-Login
- **Input Validation**: Form validation and sanitization

### Business Logic
- **Time-based Rules**: Complex timezone-aware logic for tip visibility and deadlines
- **Automated Scoring**: Background jobs for calculating and updating user statistics
- **Data Synchronization**: Automated fixture updates from external API
- **Error Handling**: Graceful error handling and user feedback

### Code Organization
- **Blueprint Pattern**: Modular route organization for maintainability
- **Application Factory**: Flexible app initialization pattern
- **Service Layer**: Separation of business logic from route handlers
- **Helper Functions**: Reusable utility functions for common operations

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Twilio account (for SMS features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd flask-tuross-tipping-comp-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   ```

5. **Database Setup**
   ```bash
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

The application will be available at `http://localhost:5000`

## 📊 Database Models

- **User**: User accounts with authentication, profile information, and admin flags
- **Tip**: Individual match predictions linked to users and fixtures
- **FixtureFree**: Match data including teams, scores, dates, and round information
- **UserTipStats**: Aggregated statistics per user per round (successful, failed, pending tips)
- **ChatMessage**: Match-specific chat messages with timestamps

## 🔄 Automated Processes

### Scheduled Tasks
- **Fixture Updates**: Regular updates from external NRL API
- **Statistics Calculation**: Automated recalculation of user tip statistics
- **SMS Reminders**: Weekly reminders for tip submission deadlines
- **Default Tip Assignment**: Automatic assignment of default tips for missed deadlines

## 🎨 User Interface

- Clean, intuitive design focused on usability
- Responsive layout for various screen sizes
- Team logos and custom avatars for personalization
- Real-time updates for chat and leaderboard
- Flash messaging for user feedback

## 🔮 Future Enhancements

### Planned Features
- **AI Tipper Bot**: An independent AI-powered tipping bot that will compete alongside human participants, leveraging machine learning models to make predictions based on historical data, team performance metrics, and other relevant factors. This will serve as both a competitive participant and a benchmark for human tippers.

### Potential Improvements
- Real-time notifications via WebSockets
- Advanced analytics and visualization dashboards
- Mobile app development
- Integration with additional sports data APIs
- Enhanced admin tools for competition management

## 👨‍💻 About the Developer

As a data analyst with a passion for building practical solutions, this project represents a combination of my analytical skills and growing expertise in software engineering and web development. I'm particularly interested in the intersection of data science and application development, with a focus on creating tools that solve real-world problems.

This application demonstrates:
- Full-stack web development capabilities
- Database design and optimization
- API integration and external service management
- Automated task scheduling and background processing
- User experience design and implementation
- Production deployment considerations

## 📝 License

This project is private and proprietary.

## 🤝 Contributing

This is a personal project for the Tuross Tipping Competition. For questions or suggestions, please contact the repository owner.

---

**Note**: This application is actively used in production for managing the Tuross Tipping Competition. The codebase is maintained and updated regularly to support the competition's needs and incorporate new features.
