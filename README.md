# 📝 Notes App

A full-stack notes application with real-time collision detection and resolution, built with React and FastAPI.

## ✨ Features

- 🔐 **JWT Authentication** - Secure user registration and login
- 📝 **Full CRUD Operations** - Create, read, update, and delete notes
- ⚡ **Real-time Conflict Resolution** - Handles concurrent edits gracefully
- 🎨 **Modern UI** - Clean, responsive interface
- 🔒 **User Isolation** - Users can only access their own notes
- 💾 **Optimistic Locking** - Prevents data loss from simultaneous edits
- 📱 **Mobile Responsive** - Works on all device sizes

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for APIs
- **SQLite/PostgreSQL** - Database (SQLite for dev, PostgreSQL for production)
- **JWT** - JSON Web Tokens for stateless authentication
- **bcrypt** - Password hashing
- **Pydantic** - Data validation and serialization

### Frontend
- **React** - Component-based UI library
- **Lucide React** - Beautiful icons
- **Modern CSS** - Responsive styling with CSS-in-JS

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/notes-app.git
cd notes-app
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your settings

# Run the server
python -m uvicorn main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Edit .env with your API URL

# Start development server
npm start
```

Frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
notes-app/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application file
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example       # Environment template
│   └── notes.db           # SQLite database (auto-created)
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   └── index.js       # React entry point
│   ├── package.json       # Node.js dependencies
│   └── .env.example      # Environment template
├── .gitignore             # Git ignore rules
└── README.md             # This file
```

## 🔧 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login user |

### Notes (Requires Authentication)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notes` | Get all user's notes |
| POST | `/notes` | Create new note |
| GET | `/notes/{id}` | Get specific note |
| PUT | `/notes/{id}` | Update note (with collision detection) |
| DELETE | `/notes/{id}` | Delete note |

## 🔒 Authentication

The app uses JWT (JSON Web Tokens) for authentication:

1. **Register/Login** → Receive JWT token
2. **Include token** in `Authorization: Bearer <token>` header
3. **Token expires** after 30 minutes (configurable)

## ⚡ Collision Resolution

### How It Works
When multiple users edit the same note simultaneously:

1. **Detection**: Uses `updated_at` timestamps to detect conflicts
2. **Prevention**: Server returns `409 Conflict` if note was modified
3. **Resolution**: UI shows both versions with merge options

### Example Scenario
```
User A: Loads note (updated_at: 10:00 AM)
User B: Loads same note (updated_at: 10:00 AM)
User A: Saves changes → Success (updated_at: 10:05 AM)
User B: Tries to save → Conflict detected!
UI: Shows conflict resolution modal with both versions
```

## 🧪 Testing Collision Resolution

1. Open the app in **two browser tabs**
2. Login as the same user in both tabs
3. Open the same note in both tabs
4. Edit and save from tab 1
5. Try to save from tab 2 → Conflict modal appears!
6. Resolve by choosing or merging versions

## 🚀 Deployment

### Option 1: Railway + Netlify (Free)

**Backend (Railway):**
```bash
# Push backend to GitHub
cd backend
git init
git add .
git commit -m "Backend for deployment"
git remote add origin https://github.com/yourusername/notes-backend.git
git push -u origin main

# Deploy on railway.app
# 1. Connect GitHub repo
# 2. Railway auto-detects Python
# 3. Set environment variables
```

**Frontend (Netlify):**
```bash
cd frontend
npm run build

# Drag 'build' folder to netlify.com/drop
# Or use Netlify CLI: netlify deploy --prod --dir=build
```

### Option 2: Docker
```bash
# Coming soon - Docker setup
docker-compose up --build
```

## 🔧 Configuration

### Backend Environment (.env)
```env
SECRET_KEY=your-super-secret-256-bit-key
DATABASE_URL=sqlite:///./notes.db
FRONTEND_URL=http://localhost:3000
PORT=8000
```

### Frontend Environment (.env)
```env
REACT_APP_API_URL=http://localhost:8000
```

### Production Environment
```env
# Backend
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://user:password@host:5432/notes
FRONTEND_URL=https://your-frontend-domain.com

# Frontend  
REACT_APP_API_URL=https://your-backend-domain.com
```

## 🛡️ Security Features

- **Password Hashing** - bcrypt with salt
- **JWT Tokens** - Stateless authentication with expiration
- **User Isolation** - Users can only access their own notes
- **CORS Protection** - Configured for specific origins
- **Input Validation** - Pydantic models for data validation
- **SQL Injection Protection** - Parameterized queries

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Notes Table
```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

## 🧪 Testing

### Manual Testing
1. **Authentication Flow**
   - Register new user
   - Login with valid/invalid credentials
   - Access protected routes

2. **Notes CRUD**
   - Create notes with various content
   - Edit and update notes
   - Delete notes
   - Verify user isolation

3. **Collision Resolution**
   - Open same note in multiple tabs
   - Edit simultaneously
   - Verify conflict resolution UI

### API Testing
Use the built-in Swagger documentation at `http://localhost:8000/docs`

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check if virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

**Frontend won't start:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+
```

**CORS Errors:**
- Ensure backend is running on port 8000
- Check CORS origins in `main.py`
- Verify API URL in frontend `.env`

**Database Issues:**
- Delete `notes.db` file to reset database
- Check file permissions
- Ensure SQLite is available

## 🔄 Development Workflow

### Making Changes
1. **Backend changes**: FastAPI auto-reloads with `--reload` flag
2. **Frontend changes**: React hot-reloads automatically
3. **Database changes**: Delete `notes.db` to reset schema

### Adding New Features
1. **Backend**: Add routes in `main.py`, update Pydantic models
2. **Frontend**: Add components, update API service
3. **Database**: Modify schema in `init_db()` function

## 📈 Performance Considerations

- **Database**: SQLite for development, PostgreSQL for production
- **Caching**: Consider Redis for session storage in production
- **Rate Limiting**: Add rate limiting for auth endpoints
- **Connection Pooling**: Use connection pooling for database

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- React team for the powerful UI library
- Lucide for beautiful icons
- Railway and Netlify for easy deployment

## 📞 Support

If you encounter any issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the API documentation at `/docs`
3. Open an issue on GitHub
4. Check browser developer console for errors

---
