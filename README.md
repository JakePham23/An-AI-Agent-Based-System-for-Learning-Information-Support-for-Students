# LightRAG Service

This repository contains the setup for running the LightRAG service using Docker. We have streamlined the deployment process to a single script for Linux/macOS environments.

## 🚀 Quick Start (One-Click Deploy)

To get the service up and running immediately, follow these steps:

1. **Clone the repository** (if you haven't already).
2. **Navigate to the source directory**:
   ```bash
   cd src
   ```
3. **Run the deployment script**:
   ```bash
   ./deploy.sh
   ```

That's it! The script will automatically:
- Check if Docker and Docker Compose are installed.
- Setup necessary configuration files (`.env`, `config.ini`) from templates if missing.
- Create required data directories (`data/rag_storage`, etc.).
- Build and start the services in the background.

The API will be available at: `http://localhost:9621`

## 📋 Prerequisites

Before running the script, ensure you have the following installed:

- **Docker Engine**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Included with Docker Desktop or installed separately on Linux.

> **Note**: Make sure the Docker Daemon is running before executing the script.

> **Tip**: Please refer to `env.example2` for the detailed configuration required to run the system correctly.

## 🛠 Manual Configuration (Optional)

If you prefer to configure things manually or need to customize settings:

### Environment Variables
The `deploy.sh` script creates a `.env` file for you, but you can edit it to change settings:
- `PORT`: The port the API listens on (default: `9621`)
- `rag_embedding_model`: Model configuration for embeddings.
- `rag_llm_model`: LLM model configuration.

### Data Directories
The application persists data in the `./data` directory:
- `data/rag_storage`: Knowledge graph storage.
- `data/inputs`: Input files.
- `data/tiktoken`: Cache for tokenizers.

## 🔍 Management Commands

Once deployed, you can manage the application using standard Docker Compose commands:

```bash
# View real-time logs
docker compose logs -f

# Stop the application
docker compose down

# Restart the application
docker compose restart

# Rebuild the application (if you changed code)
docker compose up -d --build
```

## 🐛 Troubleshooting

**"Cannot connect to the Docker daemon"**
- Ensure Docker Desktop is open and running.
- On Linux, ensure the service is active (`sudo systemctl start docker`).

**Port Conflict**
- If port `9621` is in use, modify the `PORT` variable in your `.env` file.
