# News Recommendation Full-Stack Application

## Overview
This is a **News Recommendation Full-Stack Application** designed to provide personalized news recommendations to users. The application utilizes various technologies to handle frontend, backend, data storage, asynchronous task execution, and recommendation logic.

---

## Tech Stack
- **Frontend**: React
- **Backend Server**: Flask
- **Asynchronous Task Execution**: Celery
- **Message Broker**: Kafka
- **Database**: MongoDB (for storage and filtering)
- **Vector Database**: Qdrant
- **Machine Learning Models**: Hugging Face models

---

## Requirements
Before running the application, ensure the following prerequisites are met:
1. **Kafka** is pre-installed and configured on your system.
2. Proper connection to:
   - **MongoDB** for storage and filtering.
   - **Qdrant** as the vector database.
   - **Data Source**: [newsapi.com](https://newsapi.com), for fetching news articles.

---

## Data Source
The application fetches news articles from **[newsapi.com](https://newsapi.com)**. Ensure you have access to this API and the appropriate API key for integration.

---

## Setup Instructions

### Step 1: Setup Environment 
Create and activate the virtual environment using the provided `conda` environment file:
```bash
conda env create -f environment.yaml
conda activate <env_name>
```

### Step 2: Initialize Kafka

Start Kafka in the project directory. Ensure Kafka is configured and running correctly:
```bash
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
.\bin\windows\kafka-server-start.bat .\config\server.properties
```
### Step 3: Start the Flask Server

Run the Flask server as a producer from the `./app/app.py` directory:
```bash
python ./app/app.py
```


markdown
Copy code
### Step 4: Start Celery Workers

Initialize Celery workers using the provided commands in `celeryApp.py`:
```bash
celery -A celeryApp worker --loglevel=info
```

### Step 5: Launch the React Frontend

Start the React application from the `./app/frontend/bigData` directory:
```bash
cd ./app/frontend/bigData
npm install
npm start
```

## Project Workflow

1. **Backend**: Flask server serves as the main backend, handling API requests and managing data flow.
2. **Frontend**: React app provides an intuitive user interface for interacting with the recommendation system.
3. **Data Processing**:
   - Kafka serves as the broker for passing messages between components.
   - Celery handles background tasks for recommendations and feedback processing.
4. **Storage**:
   - MongoDB stores user feedback and articles.
   - Qdrant handles vector-based search and recommendations.
5. **Modeling**: Hugging Face models are used for generating embeddings and performing recommendation tasks.

---

## Notes

- Ensure all services (Kafka, MongoDB, Qdrant, Flask, and React) are up and running before testing the application.
- Periodically fetch new articles from `newsapi.com` to keep the recommendations up to date.

