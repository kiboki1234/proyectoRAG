"""
Sistema de logging estructurado para la aplicación RAG.
Configura logs con formato JSON y rotación de archivos.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Formateador JSON para logs estructurados"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Agregar campos extra si existen
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextLogger(logging.LoggerAdapter):
    """Logger que permite agregar contexto adicional"""
    
    def process(self, msg, kwargs):
        # Agregar campos extra al record
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = {"extra_fields": extra}
        return msg, kwargs


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_json: bool = False
) -> logging.Logger:
    """
    Configura y retorna un logger con handlers de consola y archivo.
    
    Args:
        name: Nombre del logger
        log_file: Ruta al archivo de log (opcional)
        log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Tamaño máximo del archivo antes de rotar
        backup_count: Número de backups a mantener
        use_json: Si usar formato JSON (útil para producción)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Formato para consola (más legible)
    console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_formatter = logging.Formatter(console_format)
    
    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler de archivo (con rotación)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        
        if use_json:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger ya configurado o crea uno nuevo con la configuración por defecto.
    
    Args:
        name: Nombre del módulo/componente
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


# Logger raíz de la aplicación
def setup_app_logger(log_file: Optional[Path] = None, log_level: str = "INFO") -> logging.Logger:
    """
    Configura el logger principal de la aplicación.
    
    Args:
        log_file: Ruta al archivo de log
        log_level: Nivel de log
    
    Returns:
        Logger principal configurado
    """
    return setup_logger(
        name="rag_offline",
        log_file=log_file,
        log_level=log_level,
        use_json=False  # JSON en producción, texto en desarrollo
    )
