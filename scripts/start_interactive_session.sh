#!/bin/bash
#
# Script para iniciar una sesión de desarrollo interactiva en un clúster SLURM.
#
# Uso: ./start_interactive_session.sh
#
# Este script solicita recursos a SLURM (GPUs, CPUs, RAM) y, una vez asignados,
# inicia automáticamente los servicios necesarios (Ollama, Backend, Frontend)
# en segundo plano, dejando una terminal lista para el desarrollo y testing.

# --- Configuración de Recursos para SLURM ---
# Siéntete libre de ajustar estos valores según tus necesidades.

GPUS_REQUESTED=1          # Número de GPUs que quieres solicitar (puedes poner 4 si lo necesitas)
CPUS_REQUESTED=8          # Número de núcleos de CPU
MEM_REQUESTED="128G"      # Cantidad de RAM (e.g., "32G", "128G")
TIME_LIMIT="02:00:00"     # Límite de tiempo para la sesión (HH:MM:SS)

# --- Comandos a ejecutar dentro de la sesión SLURM ---

# Usamos una función heredoc para pasar un bloque de comandos a srun.
# Esto es más limpio que escribir todo en una sola línea.
read -r -d '' COMMANDS_TO_RUN << EOM
echo "================================================="
echo "✅ Sesión interactiva de SLURM iniciada."
echo "Recursos asignados: $GPUS_REQUESTED GPU(s), $CPUS_REQUESTED CPU(s), $MEM_REQUESTED RAM."
echo "================================================="
echo ""
echo "El entorno está listo. Ahora puedes iniciar los servicios manualmente."
echo "Recuerda usar '&' para lanzarlos en segundo plano."
echo ""
echo "--- Comandos sugeridos ---"
echo ""
echo "# Para iniciar Ollama:"
echo "ollama serve &"
echo ""
echo "# Para iniciar el Backend:"
echo "python /Users/clemente/Documents/Proyectos Personales/openaihackaton/synthetic-data-plataform/backend/main.py &"
echo ""
echo "# Para iniciar el Frontend:"
echo "npm --prefix /Users/clemente/Documents/Proyectos Personales/openaihackaton/synthetic-data-plataform/frontend run dev &"
echo ""
echo "# Para ver los trabajos en segundo plano:"
echo "jobs"
echo ""
echo "-------------------------------------------------"
echo ""
echo "Para terminar la sesión y detener todos los servicios, simplemente escribe: exit"
echo ""

# Este comando mantiene la sesión de bash abierta para que puedas trabajar.
bash
EOM

# --- Ejecución de srun ---

echo "Solicitando una sesión interactiva a SLURM... Puede tardar unos momentos."

srun --gpus=$GPUS_REQUESTED --cpus-per-task=$CPUS_REQUESTED --mem=$MEM_REQUESTED --time=$TIME_LIMIT --pty "$COMMANDS_TO_RUN"

echo "Sesión de SLURM finalizada. Todos los recursos han sido liberados."
