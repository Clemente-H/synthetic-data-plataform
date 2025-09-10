#!/bin/bash
#
# Script para iniciar una sesión de desarrollo interactiva en un clúster SLURM.
#
# Este script solicita recursos a SLURM y luego proporciona una shell interactiva
# con instrucciones para iniciar manualmente los servicios.

# --- Configuración de Recursos para SLURM ---
GPUS_REQUESTED=1          # Número de GPUs que quieres solicitar (puedes poner 4 si lo necesitas)
CPUS_REQUESTED=8          # Número de núcleos de CPU
MEM_REQUESTED="128G"      # Cantidad de RAM (e.g., "32G", "128G")
TIME_LIMIT="02:00:00"     # Límite de tiempo para la sesión (HH:MM:SS)

# --- Lógica del Script ---

# Obtener la ruta absoluta del directorio raíz del proyecto.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Crear un script temporal que srun ejecutará.
# Esto evita el error "File name too long".
TMP_SCRIPT=$(mktemp /tmp/slurm_job_script.XXXXXX || exit 1)

# Escribir los comandos en el script temporal.
# Usamos 'EOF' entre comillas para que las variables como $PROJECT_ROOT
# se pasen literalmente y se expandan dentro del script temporal.
cat > "$TMP_SCRIPT" <<EOF
#!/bin/bash
# Este es el script temporal que se ejecuta dentro del nodo de SLURM.

export PROJECT_ROOT="$PROJECT_ROOT"

echo "================================================="
echo "✅ Sesión interactiva de SLURM iniciada."
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
echo "python \$PROJECT_ROOT/backend/main.py &"
echo ""
echo "# Para iniciar el Frontend:"
echo "npm --prefix \$PROJECT_ROOT/frontend run dev &"
echo ""
echo "# Para ver los trabajos en segundo plano:"
echo "jobs"
echo ""
echo "-------------------------------------------------"
echo ""
echo "Para terminar la sesión y detener todos los servicios, simplemente escribe: exit"
echo ""

# Iniciar una sesión de bash interactiva.
# 'exec' reemplaza el proceso actual, por lo que al salir de bash, la sesión termina.
exec bash
EOF

# Hacer que el script temporal sea ejecutable.
chmod +x "$TMP_SCRIPT"

# --- Ejecución de srun ---
echo "Solicitando una sesión interactiva a SLURM... Puede tardar unos momentos."

# srun ejecutará el script temporal, que a su vez iniciará una shell interactiva.
srun --gpus=$GPUS_REQUESTED --cpus-per-task=$CPUS_REQUESTED --mem=$MEM_REQUESTED --time=$TIME_LIMIT --pty "$TMP_SCRIPT"

# --- Limpieza ---
# Esto se ejecuta después de que salgas de la sesión de srun.
rm "$TMP_SCRIPT"
echo "Sesión de SLURM finalizada. Todos los recursos han sido liberados."
