# AI-Powered Intelligent Code Reviewer

An AI-powered tool that analyzes code repositories and provides comprehensive insights including security vulnerabilities, code quality issues, architectural problems, and improvement recommendations.

## 🏗️ Architecture

- **Backend**: Python FastAPI with AI agent orchestration, RAG pipeline, and multiple analysis tools
- **Frontend**: Next.js React application for user interface
- **Database**: SQLite for job tracking and results storage
- **AI**: OpenAI GPT integration for intelligent code analysis

## 📋 Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 18+** (for frontend) 
- **OpenAI API Key** (required for AI analysis)
- **Git** (for repository cloning)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd intelligent-code-reviewer
```

### 2. Backend Setup

#### Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt  # or install via pyproject.toml
```

#### Configure Environment

Create a `.env` file in the `backend` folder:

```bash
cd backend
touch .env
```

Add your OpenAI API key to the `.env` file:

```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
DATABASE_URL=sqlite:///./intelligent_code_reviewer.db
```

**Get Your OpenAI API Key:**
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. Paste it in your `.env` file

#### Run Backend Server

```bash
cd backend
python run.py
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

Open a new terminal window:

```bash
cd frontend
npm install
# or
yarn install
```

#### Run Frontend Development Server

```bash
npm run dev
# or
yarn dev
```

The frontend will be available at `http://localhost:3000`

## 🧪 Testing the System

### Manual Testing Script

Test the complete analysis pipeline:

```bash
cd backend
python manual_scripts/test_analysis.py
```

This will:
- ✅ Check your configuration (including OpenAI API key)
- 🗂️ Create a test analysis job in the database
- 🧠 Simulate the complete RAG pipeline
- 🤖 Run all 13 AI analysis tools
- 📊 Generate a detailed report
- 📝 Create a comprehensive log file

### Simple Integration Test

For a quick test:

```bash
cd backend
python manual_scripts/test_analysis_simple.py
```

## 📊 Monitoring & Admin API

With the backend running, you can monitor jobs via admin endpoints:

### API Endpoints

- **All Jobs**: `GET http://localhost:8000/api/admin/jobs/all`
- **Active Jobs**: `GET http://localhost:8000/api/admin/jobs/active`  
- **Job Details**: `GET http://localhost:8000/api/admin/jobs/{task_id}/details`
- **Job Logs**: `GET http://localhost:8000/api/admin/jobs/{task_id}/logs`
- **System Stats**: `GET http://localhost:8000/api/admin/stats`

### Using curl

```bash
# Get all recent jobs
curl http://localhost:8000/api/admin/jobs/all

# Get details for a specific job
curl http://localhost:8000/api/admin/jobs/{task_id}/details

# Get system statistics
curl http://localhost:8000/api/admin/stats
```

## 🔧 Analysis Features

The system includes 13 AI-powered analysis tools:

### Core Analysis Tools (7)
1. **Static Code Analysis** - Code quality and best practices
2. **Security Scanner** - Vulnerability detection
3. **Performance Analyzer** - Performance bottlenecks
4. **Dependency Analyzer** - Dependency health and risks
5. **Complexity Analyzer** - Code complexity metrics
6. **Architecture Analyzer** - Architectural insights
7. **Code Quality Checker** - Overall quality assessment

### Specialized Playbooks (6)
1. **Circular Dependencies** - Dependency cycle detection
2. **God Classes** - Overly complex class identification
3. **High Complexity** - Complex function detection
4. **Hardcoded Secrets** - Security credential scanning
5. **IDOR Vulnerabilities** - Access control issues
6. **Dependency Health** - Third-party dependency analysis

## 🐛 Troubleshooting

### ❌ OpenAI API Key Issues

**Error**: `❌ OpenAI API key not configured`

**Solution**:
1. Ensure `.env` file exists in `backend` folder
2. Verify it contains: `OPENAI_API_KEY=sk-your-actual-key`
3. Restart the backend server

### ❌ Database Issues

**Error**: Database connection errors

**Solution**:
```bash
# Delete and recreate database
rm backend/intelligent_code_reviewer.db
python manual_scripts/test_analysis.py
```

### ❌ Import Errors

**Error**: Module import errors

**Solution**:
```bash
# Ensure you're in the correct directory
cd backend
python manual_scripts/test_analysis.py
```

### ❌ Frontend Build Issues

**Error**: Next.js build or runtime errors

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### ❌ Port Conflicts

**Error**: Port already in use

**Solutions**:
- Backend (8000): Change port in `backend/run.py`
- Frontend (3000): Use `npm run dev -- --port 3001`

## 📁 Project Structure

```
intelligent-code-reviewer/
├── backend/                 # Python FastAPI backend
│   ├── app/                # Application code
│   │   ├── api/           # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── models/        # Data models
│   │   └── tools/         # Analysis tools
│   ├── manual_scripts/    # Testing scripts
│   └── tests/             # Backend tests
├── frontend/               # Next.js React frontend
│   ├── src/
│   │   ├── app/          # Next.js app router
│   │   └── components/   # React components
│   └── public/           # Static assets
└── docs/                  # Documentation
```

## 📝 Log Files

The system creates detailed log files for debugging:
- `analysis_test_YYYYMMDD_HHMMSS.log` - Complete analysis logs
- Located in `backend/` directory
- Contains step-by-step analysis details

## 🤝 Development

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests (if configured)
cd frontend
npm test
```

### Development Workflow

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && npm run dev`  
3. Test changes with: `python manual_scripts/test_analysis.py`
4. Monitor via admin API endpoints

## 📖 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🎯 Usage

1. **Submit Analysis**: Upload code via frontend or API
2. **Monitor Progress**: Check status in real-time
3. **View Results**: Comprehensive analysis report
4. **Download Reports**: Export findings and recommendations

## 🛡️ Security

- API keys stored in environment variables
- No sensitive data logged
- Temporary files cleaned up after analysis
- Isolated analysis environments per job

---

For detailed implementation information, see `docs/` directory. 