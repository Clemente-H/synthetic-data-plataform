#!/bin/bash

#SBATCH --job-name=synthetic-data-dev
#SBATCH --output=dev_session.log
#SBATCH --error=dev_session.err
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
# Para ver la salida de los servicios en tiempo real, usa:
#   tail -f dev_session.log
#
# Para detener todos los servicios, cancela el trabajo con:
#   scancel <JOBID>
# (Obtén el JOBID con 'squeue -u tu_usuario')
# -------------------


echo "================================================="
echo "Iniciando el entorno de desarrollo..."
echo "Job ID: $SLURM_JOB_ID"
echo "Nodo: $SLURM_NODELIST"
echo "Salida de logs en: $(pwd)/dev_session.log"
echo "================================================="

# Obtener la ruta absoluta del directorio raíz del proyecto.
# Esto es importante porque sbatch no siempre se ejecuta desde donde lo llamas.
PROJECT_ROOT=$(pwd)

# Cargar cualquier módulo o entorno necesario (descomenta si es necesario)
# echo "Cargando entorno micromamba..."
# source /path/to/your/micromamba/etc/profile.d/micromamba.sh
# micromamba activate your_env_name

# Iniciar los 3 servicios en segundo plano.
# Toda la salida (stdout y stderr) irá al archivo dev_session.log

echo "-> Lanzando Ollama serve..."
ollama serve & 
sleep 5 # Espera para que Ollama se inicie

echo "-> Lanzando Backend..."
python ${PROJECT_ROOT}/backend/main.py & 

echo "-> Lanzando Frontend..."
npm --prefix ${PROJECT_ROOT}/frontend run dev & 


echo ""
echo "Servicios iniciados en segundo plano."
echo "Monitorea la salida con: tail -f dev_session.log"
echo "El trabajo se mantendrá corriendo hasta que sea cancelado o se acabe el tiempo."

# Este truco mantiene el trabajo de sbatch vivo indefinidamente.
# El trabajo terminará cuando lo canceles con 'scancel' o cuando se cumpla el TIME_LIMIT.
sleep infinity
