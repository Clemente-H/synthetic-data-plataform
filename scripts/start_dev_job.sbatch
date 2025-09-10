#!/bin/bash

#SBATCH --job-name=synthetic-data-dev
#SBATCH --output=sbatch_orchestrator.log
#SBATCH --error=sbatch_orchestrator.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00

# --- INSTRUCCIONES ---
# Este es un script de sbatch. Se envía a la cola de SLURM con:
#   sbatch scripts/start_dev_job.sbatch
#
# Ahora se crearán 3 logs separados: ollama.log, backend.log, frontend.log
# Para ver la salida de un servicio en tiempo real, usa por ejemplo:
#   tail -f backend.log
#
# Para detener todos los servicios, cancela el trabajo con:
#   scancel <JOBID>
# -------------------


echo "================================================="
echo "Iniciando el entorno de desarrollo con logs separados..."
echo "Job ID: $SLURM_JOB_ID"
echo "Nodo: $SLURM_NODELIST"
echo "Logs de cada servicio en: $(pwd)/"
echo "================================================="

# Obtener la ruta absoluta del directorio raíz del proyecto.
PROJECT_ROOT=$(pwd)

# Limpiar logs antiguos antes de empezar
rm -f ollama.log backend.log frontend.log

# Iniciar los 3 servicios en segundo plano, cada uno con su propio log.
# El '2>&1' redirige tanto el output estándar como los errores al mismo archivo.

echo "-> Lanzando Ollama serve (logs en ollama.log)..."
ollama serve > ollama.log 2>&1 &
sleep 5 # Espera para que Ollama se inicie

echo "-> Lanzando Backend (logs en backend.log)..."
python ${PROJECT_ROOT}/backend/main.py > backend.log 2>&1 &

echo "-> Lanzando Frontend (logs en frontend.log)..."
npm --prefix ${PROJECT_ROOT}/frontend run dev > frontend.log 2>&1 &


echo ""
echo "Servicios iniciados en segundo plano."
echo "Monitorea los logs con: tail -f <nombre_del_log>"
echo "Te recomiendo empezar con: tail -f backend.log"
echo "El trabajo se mantendrá corriendo hasta que sea cancelado o se acabe el tiempo."

# Este truco mantiene el trabajo de sbatch vivo indefinidamente.
sleep infinity
