# Manual Testing Scripts

This folder contains scripts to manually test the AI Code Reviewer analysis pipeline.

## 🔧 Setup Instructions

### 1. Set up OpenAI API Key

Create a `.env` file in the `backend` folder with your OpenAI API key:

```bash
# Create .env file
cd backend
touch .env
```

Add this content to the `.env` file:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 2. Get Your OpenAI API Key

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. Paste it in your `.env` file

### 3. Install Dependencies

Make sure you have all dependencies installed:

```bash
cd backend
pip install -r requirements.txt  # or however your dependencies are managed
```

## 🧪 Running Tests

### Test the Analysis Pipeline

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

### Expected Output

You should see detailed logs like:

```
🚀 STARTING MANUAL ANALYSIS TEST
📅 Time: 2024-01-15T10:30:00
🔗 Repository: https://github.com/octocat/Hello-World
🆔 Task ID: abc123...

🔧 CHECKING CONFIGURATION
✅ OpenAI API key configured: sk-proj-abc...
✅ Database URL: sqlite:///./intelligent_code_reviewer.db
✅ All configuration looks good!

🧠 SIMULATING RAG PIPELINE
📥 Cloning repository...
✅ Repository cloned successfully
📁 Processing files...
✅ Processed 25 files
🔍 Building vector embeddings...
✅ Knowledge base built successfully

🤖 SIMULATING AI ANALYSIS
🔧 Running: Static Code Analysis
✅ Completed: Static Code Analysis - Found 3 issues
🔧 Running: Dependency Analysis
✅ Completed: Dependency Analysis - Found 5 issues
... (continues for all 13 tools)

📊 SIMULATING REPORT GENERATION
📈 Aggregating findings...
📝 Creating recommendations...
✅ Report generated successfully!

🎉 ANALYSIS COMPLETED SUCCESSFULLY!
```

## 🔍 Monitoring & Debugging

### Admin API Endpoints

Once your backend is running (`python run.py`), you can access:

- **All Jobs**: `GET http://localhost:8000/api/admin/jobs/all`
- **Active Jobs**: `GET http://localhost:8000/api/admin/jobs/active`
- **Job Details**: `GET http://localhost:8000/api/admin/jobs/{task_id}/details`
- **Job Logs**: `GET http://localhost:8000/api/admin/jobs/{task_id}/logs`
- **System Stats**: `GET http://localhost:8000/api/admin/stats`

### Using curl to check jobs

```bash
# Get all recent jobs
curl http://localhost:8000/api/admin/jobs/all

# Get details for a specific job
curl http://localhost:8000/api/admin/jobs/{task_id}/details

# Get system statistics
curl http://localhost:8000/api/admin/stats
```

## 🐛 Troubleshooting

### ❌ OpenAI API Key Issues

If you see: `❌ OpenAI API key not configured`

**Solution:**

1. Make sure you created the `.env` file in the `backend` folder
2. Make sure it contains: `OPENAI_API_KEY=sk-your-actual-key`
3. Restart the script

### ❌ Database Issues

If you see database connection errors:

**Solution:**

```bash
# Delete the database and let it recreate
rm backend/intelligent_code_reviewer.db
python manual_scripts/test_analysis.py
```

### ❌ Import Errors

If you see import errors:

**Solution:**

```bash
# Make sure you're running from the backend directory
cd backend
python manual_scripts/test_analysis.py
```

## 📁 Log Files

The script creates detailed log files:

- `analysis_test_YYYYMMDD_HHMMSS.log`
- Contains complete step-by-step analysis logs
- Great for debugging and understanding the process

## 🎯 What This Tests

1. **Configuration**: Checks all required settings
2. **Database**: Creates and tracks analysis jobs
3. **RAG Pipeline**: File processing and vector embeddings
4. **AI Tools**: All 13 analysis tools (7 tools + 6 playbooks)
5. **Progress Tracking**: Real-time status updates
6. **Report Generation**: Final analysis report creation
7. **Error Handling**: Proper error logging and recovery

This gives you complete visibility into whether your analysis pipeline is working correctly!
