#!/usr/bin/env python
"""
Script para iniciar el servidor de desarrollo
"""
import sys
import subprocess

def main():
    """Inicia uvicorn con la configuración correcta"""
    cmd = [
        sys.executable, 
        "-m", 
        "uvicorn", 
        "app:app",  # Correcto: app:app, NO app.main:app
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    print("🚀 Iniciando RAG Backend...")
    print(f"📍 Comando: {' '.join(cmd)}")
    print(f"🌐 URL: http://127.0.0.1:8000")
    print(f"📚 Docs: http://127.0.0.1:8000/docs")
    print("\n" + "="*50 + "\n")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
