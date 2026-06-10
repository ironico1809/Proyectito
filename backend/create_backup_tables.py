from app.database import engine, Base
from app.models.backup import Backup, BackupConfig

Base.metadata.create_all(bind=engine)
print("✅ Tablas 'backups' y 'backup_config' creadas correctamente.")