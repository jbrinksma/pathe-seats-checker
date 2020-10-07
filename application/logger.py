import logging
from datetime import datetime


db_logger = logging.getLogger("db_updates")
db_logger.setLevel(level=logging.WARNING)
fh = logging.FileHandler("application/logs/db_update_warn_err.log")
fh.setLevel(logging.WARNING)
db_logger.addHandler(fh)

db_logger_all = logging.getLogger("db_updates_all")
db_logger_all.setLevel(level=logging.INFO)
fh2 = logging.FileHandler("application/logs/db_update_info.log")
fh2.setLevel(logging.INFO)
db_logger_all.addHandler(fh2)

def log_info(msg):
    db_logger_all.info(f"[Info] {str(datetime.now())[:-7]} - {msg}")

def log_warn(msg):
    db_logger.warning(f"[WARN] {str(datetime.now())[:-7]} - {msg}")

def log_err(msg):
    db_logger.error(f"[ERR!] {str(datetime.now())[:-7]} - {msg}")