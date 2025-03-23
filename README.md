# Create a virtual environment
`python -m venv your_venv`
# Activate your virtual environment (assuming Linux)
`source your_venv/bin/activate` 
# Install the dependencies
`pip install requirements.txt`
# Run a server
`uvicorn app.main:app --host 127.0.0.1 --port 8000`
# Run a test suite (optional)
`pytest`