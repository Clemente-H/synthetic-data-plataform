# Deployment Guide - Synthetic Data Platform

## Server Prerequisites

### Operating System
- Ubuntu 20.04+ / CentOS 8+ / macOS
- Python 3.8+
- Node.js 16+
- 8GB RAM minimum (16GB recommended for llama3.2:8b)
- 20GB free space (for models + datasets)

### System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-pip nodejs npm git curl

# CentOS/RHEL  
sudo yum install -y python3-pip nodejs npm git curl

# macOS
brew install python node git curl
```

## Ollama Setup

### Installation
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### Required Models
```bash
# Base model (3B - faster)
ollama pull llama3.2:3b

# Advanced model (8B - better quality) - OPTIONAL
ollama pull llama3.2:8b

# Verify installed models
ollama list
```

### Service Configuration
```bash
# Start Ollama as service (Linux)
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify it's running on port 11434
curl http://localhost:11434/api/version
```

## Project Setup

### 1. Clone and Preparation
```bash
# Repository clone
git clone [YOUR_REPO_URL] synthetic-data-platform
cd synthetic-data-platform

# Create directory structure if missing
mkdir -p logs temp_uploads
```

### 2. Backend Setup
```bash
cd backend

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Verify configuration
python -c "import yaml; print('YAML OK')"
python -c "import httpx; print('HTTPX OK')"
```

### 3. Frontend Setup
```bash
cd ../frontend

# Instalar dependencias
npm install

# Production build
npm run build

# Verify build
ls -la dist/
```

## Production Configuration

### 1. Environment Variables
```bash
# Create configuration file
cat > backend/.env << EOF
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b

# Server Configuration  
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://your-domain.com

# WebSocket Configuration
WS_MAX_CONNECTIONS=100
WS_PING_INTERVAL=30

# Upload Configuration
MAX_UPLOAD_SIZE=10485760
UPLOAD_TEMP_DIR=./temp_uploads

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
EOF
```

### 2. Model Configuration (config/models.yaml)
```yaml
# Server-optimized configuration
default_model: "llama3.2:3b"
ollama_url: "http://localhost:11434"
temperature: 0.7
max_tokens: 2048
timeout: 300

models:
  concept_extraction:
    model: "llama3.2:3b"
    temperature: 0.3
    max_tokens: 1024
  
  characterization:
    model: "llama3.2:3b"  # Use 8b if you have enough RAM
    temperature: 0.5
    max_tokens: 1024
  
  generation:
    model: "llama3.2:8b"  # Change to 3b if you have memory issues
    temperature: 0.7
    max_tokens: 2048
```

## Execution

### Development Mode (Testing)
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2: Frontend (if you need development server)
cd frontend
npm run dev
```

### Production Mode

#### Option 1: Direct
```bash
# Backend con Uvicorn
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

# Serve static frontend (with Python)
cd frontend
python3 -m http.server 3000 --directory dist
```

#### Option 2: With PM2 (Recommended)
```bash
# Instalar PM2
npm install -g pm2

# Create PM2 configuration
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'synthetic-data-backend',
      script: 'uvicorn',
      args: 'main:app --host 0.0.0.0 --port 8000',
      cwd: './backend',
      interpreter: './backend/venv/bin/python',
      env: {
        PATH: './backend/venv/bin:' + process.env.PATH
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_file: './logs/backend.log'
    },
    {
      name: 'synthetic-data-frontend',
      script: 'serve',
      args: '-s dist -l 3000',
      cwd: './frontend',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
EOF

# Start services
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Nginx Configuration (Optional)

```nginx
# /etc/nginx/sites-available/synthetic-data-platform
server {
    listen 80;
    server_name your-domain.com;

    # Static frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API Backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Upload files size limit
    client_max_body_size 10M;
}
```

## Verification and Testing

### Health Checks
```bash
# Verificar Ollama
curl http://localhost:11434/api/version

# Verificar Backend
curl http://localhost:8000/api/extraction/health

# Verificar WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws

# Verificar Frontend
curl http://localhost:3000
```

### Complete Pipeline Test
```bash
cd backend
source venv/bin/activate
python ../scripts/test_agents_sequential.py
```

## Monitoring

### Important Logs
```bash
# Backend logs
tail -f backend/logs/app.log

# PM2 logs
pm2 logs synthetic-data-backend
pm2 logs synthetic-data-frontend

# Ollama logs
journalctl -u ollama -f
```

### System Metrics
```bash
# Memory usage (important for LLM models)
free -h
htop

# Disk space
df -h

# Procesos Ollama
ps aux | grep ollama
```

## Troubleshooting

### Common Issues

#### 1. "Connection refused" al conectar con Ollama
```bash
# Verify that Ollama is running
systemctl status ollama
ollama list

# Restart if necessary
sudo systemctl restart ollama
```

#### 2. "Out of memory" during generation
```bash
# Change to smaller model in config/models.yaml
default_model: "llama3.2:3b"

# Or reduce parameters
max_tokens: 512
```

#### 3. WebSocket connection errors
```bash
# Verify CORS origins in backend/.env
CORS_ORIGINS=http://localhost:3000,http://your-domain.com

# Verify firewall
sudo ufw allow 8000
```

#### 4. Frontend no carga
```bash
# Rebuild frontend
cd frontend
npm run build

# Verify permissions
chmod -R 755 dist/
```

## Security (Production)

### Basics
- Cambiar puertos default
- Configurar firewall (ufw/iptables)
- Usar HTTPS con certificados SSL
- Configurar rate limiting
- Logs de seguridad

### Security configuration file
```bash
# Basic firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8000  # Internal access only
sudo ufw deny 11434  # Internal access only
```

---

**With this configuration you'll have the platform running in production mode, ready to generate 50K+ sample datasets!**