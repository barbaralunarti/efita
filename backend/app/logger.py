# backend/app/logger.py
"""
Configuração centralizada de logging para a aplicação EFITA.

Logs são enviados para:
- stdout (console)
- arquivo (backend/logs/app.log)
"""
import logging
import logging.handlers
import os
from pathlib import Path

# Criar diretório de logs se não existir
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Formato de log estruturado
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configurar logger raiz
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Handler para stdout (console)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
console_handler.setFormatter(console_formatter)
root_logger.addHandler(console_handler)

# Handler para arquivo com rotação
log_file = LOGS_DIR / "app.log"
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=5,
    encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
file_handler.setFormatter(file_formatter)
root_logger.addHandler(file_handler)

# Loggers específicos por módulo
logger_inscricao = logging.getLogger("app.routers.inscricao")
logger_admin = logging.getLogger("app.routers.admin")
logger_email = logging.getLogger("app.services.email")
logger_auth = logging.getLogger("app.auth")
logger_app = logging.getLogger("app.main")

# Função auxiliar para obter logger de um módulo
def get_logger(name: str) -> logging.Logger:
    """Obtém logger nomeado para um módulo específico."""
    return logging.getLogger(name)
