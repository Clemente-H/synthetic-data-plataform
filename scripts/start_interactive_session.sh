#!/bin/bash
#
# Script para iniciar una sesión de desarrollo interactiva en un clúster SLURM.
#

# --- Configuración de Recursos para SLURM ---
GPUS_REQUESTED=1          # Número de GPUs que quieres solicitar (puedes poner 4 si lo necesitas)
CPUS_REQUESTED=8          # Número de núcleos de CPU
MEM_REQUESTED="128G"      # Cantidad de RAM (e.g., "32G", "128G")
TIME_LIMIT="02:00:00"     # Límite de tiempo para la sesión (HH:MM:SS)

# --- Lógica del Script ---

# Obtener la ruta absoluta del directorio raíz del proyecto.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# 1. Imprimir las instrucciones ANTES de iniciar srun.
echo "================================================="
echo "✅ Preparando para iniciar sesión interactiva de SLURM."
echo "================================================="
echo ""
echo "La siguiente pantalla solicitará los recursos a SLURM."
echo "Una vez que se conecte, tu terminal actual se convertirá en la consola del nodo de cómputo."
echo ""
echo "--- Comandos para ejecutar DENTRO de la nueva consola ---"
echo "1. Iniciar Ollama:      ollama serve &"
echo "2. Iniciar Backend:      python ${PROJECT_ROOT}/backend/main.py &"
echo "3. Iniciar Frontend:     npm --prefix ${PROJECT_ROOT}/frontend run dev &"
echo "-------------------------------------------------"
echo ""

# 2. Ejecutar srun con el comando más simple y robusto.
#    Esto inicia una shell de bash interactiva directamente.
echo "Solicitando una sesión interactiva a SLURM... Puede tardar unos momentos."
srun --gpus=$GPUS_REQUESTED --cpus-per-task=$CPUS_REQUESTED --mem=$MEM_REQUESTED --time=$TIME_LIMIT --pty bash -i

echo ""
echo "Sesión de SLURM finalizada. Todos los recursos han sido liberados."
