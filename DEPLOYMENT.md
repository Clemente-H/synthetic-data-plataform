# 🚀 Deployment Guide - Synthetic Data Platform

## 📋 Pre-requisitos del Servidor

### Sistema Operativo
- Ubuntu 20.04+ / CentOS 8+ / macOS
- Python 3.8+
- Node.js 16+
- 8GB RAM mínimo (16GB recomendado para llama3.2:8b)
- 20GB espacio libre (para models + datasets)

### Dependencias del Sistema
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-pip nodejs npm git curl

# CentOS/RHEL  
sudo yum install -y python3-pip nodejs npm git curl

# macOS
brew install python node git curl
```

## 🔧 Setup de Ollama

### Instalación
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Verificar instalación
ollama --version
```

### Modelos Requeridos
```bash
# Modelo base (3B - más rápido)
ollama pull llama3.2:3b

# Modelo avanzado (8B - mejor calidad) - OPCIONAL
ollama pull llama3.2:8b

# Verificar modelos instalados
ollama list
```

### Configuración de Servicio
```bash
# Iniciar Ollama como servicio (Linux)
sudo systemctl enable ollama
sudo systemctl start ollama

# Verificar que está corriendo en puerto 11434
curl http://localhost:11434/api/version
```

## 📦 Setup del Proyecto

### 1. Clone y Preparación
```bash
# Clone del repositorio
git clone [YOUR_REPO_URL] synthetic-data-platform
cd synthetic-data-platform

# Crear estructura de directorios si falta
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

# Verificar configuración
python -c "import yaml; print('YAML OK')"
python -c "import httpx; print('HTTPX OK')"
```

### 3. Frontend Setup
```bash
cd ../frontend

# Instalar dependencias
npm install

# Build para producción
npm run build

# Verificar build
ls -la dist/
```

## ⚙️ Configuración de Producción

### 1. Variables de Entorno
```bash
# Crear archivo de configuración
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

### 2. Configuración de Modelos (config/models.yaml)
```yaml
# Configuración optimizada para servidor
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
    model: "llama3.2:3b"  # Usar 8b si tienes RAM suficiente
    temperature: 0.5
    max_tokens: 1024
  
  generation:
    model: "llama3.2:8b"  # Cambiar a 3b si tienes problemas de memoria
    temperature: 0.7
    max_tokens: 2048
```

## 🏃‍♂️ Ejecución

### Modo Desarrollo (Testing)
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2: Frontend (si necesitas development server)
cd frontend
npm run dev
```

### Modo Producción

#### Opción 1: Directo
```bash
# Backend con Uvicorn
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

# Servir frontend estático (con Python)
cd frontend
python3 -m http.server 3000 --directory dist
```

#### Opción 2: Con PM2 (Recomendado)
```bash
# Instalar PM2
npm install -g pm2

# Crear configuración PM2
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

# Iniciar servicios
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 🌐 Configuración de Nginx (Opcional)

```nginx
# /etc/nginx/sites-available/synthetic-data-platform
server {
    listen 80;
    server_name your-domain.com;

    # Frontend estático
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

## 🔍 Verificación y Testing

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

### Test Completo del Pipeline
```bash
cd backend
source venv/bin/activate
python ../scripts/test_agents_sequential.py
```

## 📊 Monitoreo

### Logs Importantes
```bash
# Backend logs
tail -f backend/logs/app.log

# PM2 logs
pm2 logs synthetic-data-backend
pm2 logs synthetic-data-frontend

# Ollama logs
journalctl -u ollama -f
```

### Métricas del Sistema
```bash
# Uso de memoria (importante para modelos LLM)
free -h
htop

# Espacio en disco
df -h

# Procesos Ollama
ps aux | grep ollama
```

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. "Connection refused" al conectar con Ollama
```bash
# Verificar que Ollama está corriendo
systemctl status ollama
ollama list

# Reiniciar si es necesario
sudo systemctl restart ollama
```

#### 2. "Out of memory" durante generación
```bash
# Cambiar a modelo más pequeño en config/models.yaml
default_model: "llama3.2:3b"

# O reducir parámetros
max_tokens: 512
```

#### 3. WebSocket connection errors
```bash
# Verificar CORS origins en backend/.env
CORS_ORIGINS=http://localhost:3000,http://your-domain.com

# Verificar firewall
sudo ufw allow 8000
```

#### 4. Frontend no carga
```bash
# Rebuild frontend
cd frontend
npm run build

# Verificar permisos
chmod -R 755 dist/
```

## 🔐 Seguridad (Producción)

### Básicos
- Cambiar puertos default
- Configurar firewall (ufw/iptables)
- Usar HTTPS con certificados SSL
- Configurar rate limiting
- Logs de seguridad

### Archivo de configuración de seguridad
```bash
# Firewall básico
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8000  # Solo acceso interno
sudo ufw deny 11434  # Solo acceso interno
```

---

**🎯 Con esta configuración tendrás la plataforma corriendo en modo producción, lista para generar datasets de 50K+ samples!**