# Start with a lightweight official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your local code (the current directory '.') into the container's working directory ('/app')
COPY . .

# ✅ Mount all secrets in one command and build the .env file
RUN --mount=type=secret,id=FTRACK_SERVER \
    --mount=type=secret,id=FTRACK_API_USER \
    --mount=type=secret,id=FTRACK_API_KEY \
    sh -c 'echo "FTRACK_SERVER=$(cat /run/secrets/FTRACK_SERVER)" > .env && \
           echo "FTRACK_API_USER=$(cat /run/secrets/FTRACK_API_USER)" >> .env && \
           echo "FTRACK_API_KEY=$(cat /run/secrets/FTRACK_API_KEY)" >> .env'


# Set the command to run when the container starts
CMD ["python", "run_actions.py"]