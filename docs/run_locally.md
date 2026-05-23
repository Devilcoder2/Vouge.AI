# Operations Guide: Running the Fashion Intelligence Pipeline Locally

This guide provides step-by-step instructions to configure your development IDE interpreter, install and run PostgreSQL locally on macOS, initialize database tables, and start the FastAPI service.

---

## 1. Fixing IDE "Cannot find module" Errors

When opening Python files in your IDE (VS Code, Pyrefly, PyCharm), you may see import errors such as `Cannot find module 'fastapi'`. 

This happens because the IDE is currently looking at your **Global System Python Interpreter** (`/opt/homebrew/...`). Our project dependencies are installed inside the **Local Virtual Environment (`venv/`)** to avoid cluttering your system packages.

### How to configure your IDE to scan the virtual environment:

#### A. In Visual Studio Code (VS Code)
1. Open any Python file (e.g. `app/main.py`).
2. Open the Command Palette using `Cmd + Shift + P` (Mac) or `Ctrl + Shift + P` (Windows).
3. Type and select **`Python: Select Interpreter`**.
4. Click **`Enter interpreter path...`** and select the binary inside the venv:
   `fashion-ai-service/venv/bin/python`
5. Press Enter. All red import warnings will resolve immediately.

#### B. In JetBrains PyCharm
1. Open PyCharm Settings (`Cmd + ,` on Mac).
2. Navigate to **Project: fashion-ai-service** $\rightarrow$ **Python Interpreter**.
3. Click the gear icon / **Add Interpreter** $\rightarrow$ **Add Local Interpreter...**
4. Choose **Existing Environment** and set the path to your virtual environment interpreter:
   `/Users/ramandeepsingh/Developer/Personal Projects/Vouge/fashion-ai-service/venv/bin/python`
5. Click **OK**.

---

## 2. Setting Up PostgreSQL on macOS

We use Homebrew to install and run PostgreSQL locally on macOS.

### Step 1: Install Homebrew (if not already present)
Paste this into your terminal to install the Homebrew package manager:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install PostgreSQL 15
Install PostgreSQL through Homebrew:
```bash
brew install postgresql@15
```

### Step 3: Start the PostgreSQL Service
Configure PostgreSQL to start and run automatically in the background as a system service:
```bash
brew services start postgresql@15
```

### Step 4: Verify Service Status
Run `pg_isready` to verify the local database server is online and accepting socket connections:
```bash
pg_isready
```
*Expected output:* `/tmp:5432 - accepting connections`

### Step 5: Configure the `postgres` User & Password
Our application configuration (`.env` file) uses the credentials `postgres` / `postgres`. Create this database superuser and set the password:
```bash
# 1. Create the postgres superuser role
createuser -s postgres

# 2. Assign the password 'postgres' to this role
psql postgres -c "ALTER USER postgres PASSWORD 'postgres';"
```

### Step 6: Create the `vouge` Database
Create the database named `vouge` and assign its ownership to the `postgres` user:
```bash
createdb vouge -O postgres
```

---

## 3. Running and Testing the FastAPI Service

Once the database is set up and running, execute these commands inside your project root directory:

### Step 1: Initialize the Database Schemas
This asynchronously connects to your local PostgreSQL instance and builds the `clothing_items` table:
```bash
cd "/Users/ramandeepsingh/Developer/Personal Projects/Vouge/fashion-ai-service"
PYTHONPATH=. ./venv/bin/python app/database/init_db.py
```

### Step 2: Run the Test Suite
To confirm all routers, file validation rules, color engines, and database configurations pass:
```bash
PYTHONPATH=. ./venv/bin/pytest tests/test_endpoints.py
```

### Step 3: Run the Local Uvicorn Server
Launch the local reload server:
```bash
PYTHONPATH=. ./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Explore the Swagger UI Dashboard
Open your web browser and navigate to:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

You will find the fully interactive Swagger API docs where you can test uploads, run the complete clothing pipeline, and query processed records!
