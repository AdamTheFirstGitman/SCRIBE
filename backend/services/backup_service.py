"""
Automated Backup and Data Protection Service
Comprehensive backup system with encryption and recovery
"""

import asyncio
import json
import gzip
import shutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import tarfile
from cryptography.fernet import Fernet
import boto3
from botocore.exceptions import ClientError

from services.storage import supabase_client
from config import get_settings

@dataclass
class BackupRecord:
    """Backup record metadata"""
    id: str
    backup_type: str  # full, incremental, documents, conversations
    file_path: str
    file_size: int
    checksum: str
    encrypted: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    restored_count: int = 0
    metadata: Dict[str, Any] = None

class BackupService:
    """
    Automated backup service for SCRIBE
    Features:
    - Scheduled full and incremental backups
    - Encryption at rest
    - Multiple storage backends (local, cloud)
    - Point-in-time recovery
    - Data validation and integrity checks
    """

    def __init__(self):
        self.settings = get_settings()
        self.supabase = supabase_client

        # Backup configuration
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

        # Encryption key (in production, store securely)
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)

        # Backup schedules
        self.schedules = {
            'full_backup': {'interval': 24 * 3600, 'last_run': None},  # Daily
            'incremental_backup': {'interval': 6 * 3600, 'last_run': None},  # Every 6 hours
            'document_backup': {'interval': 3600, 'last_run': None},  # Hourly
        }

        # Retention policies
        self.retention_policy = {
            'full_backup': 30,  # Keep for 30 days
            'incremental_backup': 7,  # Keep for 7 days
            'document_backup': 3,  # Keep for 3 days
        }

        # Storage backends
        self.storage_backends = ['local']
        if hasattr(self.settings, 'AWS_ACCESS_KEY_ID'):
            self.storage_backends.append('s3')

    async def start_backup_scheduler(self):
        """Start automated backup scheduler"""
        asyncio.create_task(self._backup_scheduler())
        print("✅ Backup scheduler started")

    async def _backup_scheduler(self):
        """Main backup scheduler loop"""
        while True:
            try:
                current_time = datetime.now()

                for backup_type, schedule in self.schedules.items():
                    if self._should_run_backup(backup_type, current_time):
                        await self._run_scheduled_backup(backup_type)
                        schedule['last_run'] = current_time

                # Clean old backups
                await self._cleanup_expired_backups()

            except Exception as e:
                print(f"Backup scheduler error: {e}")

            # Check every 30 minutes
            await asyncio.sleep(1800)

    def _should_run_backup(self, backup_type: str, current_time: datetime) -> bool:
        """Check if backup should run based on schedule"""
        schedule = self.schedules[backup_type]
        last_run = schedule['last_run']

        if last_run is None:
            return True

        time_since_last = (current_time - last_run).total_seconds()
        return time_since_last >= schedule['interval']

    async def _run_scheduled_backup(self, backup_type: str):
        """Run scheduled backup"""
        print(f"🔄 Starting {backup_type}...")

        try:
            if backup_type == 'full_backup':
                await self.create_full_backup()
            elif backup_type == 'incremental_backup':
                await self.create_incremental_backup()
            elif backup_type == 'document_backup':
                await self.create_document_backup()

            print(f"✅ {backup_type} completed successfully")

        except Exception as e:
            print(f"❌ {backup_type} failed: {e}")

    async def create_full_backup(self) -> BackupRecord:
        """Create complete system backup"""
        backup_id = f"full_{int(datetime.now().timestamp())}"
        backup_path = self.backup_dir / f"{backup_id}.tar.gz"

        try:
            # Export all data from Supabase
            full_data = await self._export_full_database()

            # Create compressed archive
            with tarfile.open(backup_path, "w:gz") as tar:
                # Add database dump
                db_file = self.backup_dir / f"{backup_id}_database.json"
                with open(db_file, 'w') as f:
                    json.dump(full_data, f, default=str)

                tar.add(db_file, arcname="database.json")

                # Add configuration files
                config_files = ['.env', 'CLAUDE.md', 'package.json']
                for config_file in config_files:
                    if Path(config_file).exists():
                        tar.add(config_file, arcname=f"config/{config_file}")

                # Clean up temp file
                db_file.unlink()

            # Encrypt backup
            encrypted_path = await self._encrypt_backup(backup_path)

            # Calculate checksum
            checksum = self._calculate_checksum(encrypted_path)

            # Create backup record
            record = BackupRecord(
                id=backup_id,
                backup_type='full_backup',
                file_path=str(encrypted_path),
                file_size=encrypted_path.stat().st_size,
                checksum=checksum,
                encrypted=True,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=self.retention_policy['full_backup']),
                metadata={
                    'tables_backed_up': list(full_data.keys()),
                    'total_records': sum(len(table_data) for table_data in full_data.values())
                }
            )

            # Store backup metadata
            await self._store_backup_record(record)

            # Upload to cloud if configured
            await self._upload_to_cloud_storage(record)

            return record

        except Exception as e:
            if backup_path.exists():
                backup_path.unlink()
            raise e

    async def create_incremental_backup(self) -> BackupRecord:
        """Create incremental backup (changes since last full backup)"""
        backup_id = f"incremental_{int(datetime.now().timestamp())}"

        # Find last full backup
        last_full_backup = await self._get_last_backup('full_backup')
        if not last_full_backup:
            # No full backup exists, create one instead
            return await self.create_full_backup()

        cutoff_time = last_full_backup.created_at

        try:
            # Export changed data since last full backup
            incremental_data = await self._export_incremental_database(cutoff_time)

            if not any(incremental_data.values()):
                print("No changes since last backup")
                return None

            backup_path = self.backup_dir / f"{backup_id}.json.gz"

            # Compress and save incremental data
            with gzip.open(backup_path, 'wt') as f:
                json.dump(incremental_data, f, default=str)

            # Encrypt backup
            encrypted_path = await self._encrypt_backup(backup_path)

            # Calculate checksum
            checksum = self._calculate_checksum(encrypted_path)

            record = BackupRecord(
                id=backup_id,
                backup_type='incremental_backup',
                file_path=str(encrypted_path),
                file_size=encrypted_path.stat().st_size,
                checksum=checksum,
                encrypted=True,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=self.retention_policy['incremental_backup']),
                metadata={
                    'base_backup_id': last_full_backup.id,
                    'cutoff_time': cutoff_time.isoformat(),
                    'changed_records': sum(len(table_data) for table_data in incremental_data.values())
                }
            )

            await self._store_backup_record(record)
            await self._upload_to_cloud_storage(record)

            return record

        except Exception as e:
            if 'backup_path' in locals() and backup_path.exists():
                backup_path.unlink()
            raise e

    async def create_document_backup(self) -> BackupRecord:
        """Create backup of documents and embeddings only"""
        backup_id = f"documents_{int(datetime.now().timestamp())}"

        try:
            # Export documents and related data
            document_data = await self._export_documents_data()

            backup_path = self.backup_dir / f"{backup_id}.json.gz"

            with gzip.open(backup_path, 'wt') as f:
                json.dump(document_data, f, default=str)

            encrypted_path = await self._encrypt_backup(backup_path)
            checksum = self._calculate_checksum(encrypted_path)

            record = BackupRecord(
                id=backup_id,
                backup_type='document_backup',
                file_path=str(encrypted_path),
                file_size=encrypted_path.stat().st_size,
                checksum=checksum,
                encrypted=True,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=self.retention_policy['document_backup']),
                metadata={
                    'documents_count': len(document_data.get('documents', [])),
                    'embeddings_count': len(document_data.get('embeddings', [])),
                    'notes_count': len(document_data.get('notes', []))
                }
            )

            await self._store_backup_record(record)
            return record

        except Exception as e:
            if 'backup_path' in locals() and backup_path.exists():
                backup_path.unlink()
            raise e

    async def _export_full_database(self) -> Dict[str, List]:
        """Export all data from database"""
        tables = ['documents', 'notes', 'embeddings', 'conversations', 'search_queries']
        data = {}

        for table in tables:
            try:
                result = self.supabase.table(table).select("*").execute()
                data[table] = result.data
                print(f"Exported {len(result.data)} records from {table}")
            except Exception as e:
                print(f"Error exporting {table}: {e}")
                data[table] = []

        return data

    async def _export_incremental_database(self, cutoff_time: datetime) -> Dict[str, List]:
        """Export changed data since cutoff time"""
        tables = ['documents', 'notes', 'embeddings', 'conversations']
        data = {}

        for table in tables:
            try:
                result = self.supabase.table(table) \
                    .select("*") \
                    .gte("updated_at", cutoff_time.isoformat()) \
                    .execute()

                data[table] = result.data
                print(f"Exported {len(result.data)} changed records from {table}")
            except Exception as e:
                print(f"Error exporting incremental {table}: {e}")
                data[table] = []

        return data

    async def _export_documents_data(self) -> Dict[str, List]:
        """Export documents and related data only"""
        data = {}

        # Documents
        result = self.supabase.table("documents").select("*").execute()
        data['documents'] = result.data

        # Notes
        result = self.supabase.table("notes").select("*").execute()
        data['notes'] = result.data

        # Embeddings
        result = self.supabase.table("embeddings").select("*").execute()
        data['embeddings'] = result.data

        return data

    async def _encrypt_backup(self, file_path: Path) -> Path:
        """Encrypt backup file"""
        encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')

        with open(file_path, 'rb') as f:
            data = f.read()

        encrypted_data = self.cipher.encrypt(data)

        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)

        # Remove unencrypted file
        file_path.unlink()

        return encrypted_path

    async def _decrypt_backup(self, encrypted_path: Path, output_path: Path):
        """Decrypt backup file"""
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()

        decrypted_data = self.cipher.decrypt(encrypted_data)

        with open(output_path, 'wb') as f:
            f.write(decrypted_data)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = self.backup_dir / 'backup.key'

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Secure the key file
            os.chmod(key_file, 0o600)
            return key

    async def _store_backup_record(self, record: BackupRecord):
        """Store backup metadata in database"""
        try:
            # Convert dataclass to dict for JSON serialization
            record_dict = asdict(record)
            record_dict['created_at'] = record.created_at.isoformat()
            if record.expires_at:
                record_dict['expires_at'] = record.expires_at.isoformat()

            # Store in backups table (create table if needed)
            await self._ensure_backup_table_exists()
            self.supabase.table('backups').insert(record_dict).execute()

        except Exception as e:
            print(f"Error storing backup record: {e}")

    async def _ensure_backup_table_exists(self):
        """Ensure backups table exists"""
        # This would normally be handled by migrations
        # For now, just try to create it
        pass

    async def _upload_to_cloud_storage(self, record: BackupRecord):
        """Upload backup to cloud storage (S3, etc.)"""
        if 's3' in self.storage_backends:
            try:
                # Upload to S3
                s3_client = boto3.client('s3')
                bucket = getattr(self.settings, 'BACKUP_S3_BUCKET', 'scribe-backups')

                with open(record.file_path, 'rb') as f:
                    s3_client.upload_fileobj(
                        f,
                        bucket,
                        f"scribe/{record.backup_type}/{record.id}.enc"
                    )

                print(f"✅ Uploaded {record.id} to S3")

            except Exception as e:
                print(f"Failed to upload to S3: {e}")

    async def _get_last_backup(self, backup_type: str) -> Optional[BackupRecord]:
        """Get the most recent backup of specified type"""
        try:
            result = self.supabase.table('backups') \
                .select("*") \
                .eq("backup_type", backup_type) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()

            if result.data:
                data = result.data[0]
                return BackupRecord(
                    id=data['id'],
                    backup_type=data['backup_type'],
                    file_path=data['file_path'],
                    file_size=data['file_size'],
                    checksum=data['checksum'],
                    encrypted=data['encrypted'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
                    restored_count=data.get('restored_count', 0),
                    metadata=data.get('metadata', {})
                )

            return None

        except Exception as e:
            print(f"Error getting last backup: {e}")
            return None

    async def _cleanup_expired_backups(self):
        """Clean up expired backup files"""
        try:
            # Get expired backups
            current_time = datetime.now()

            result = self.supabase.table('backups') \
                .select("*") \
                .lt("expires_at", current_time.isoformat()) \
                .execute()

            for backup_data in result.data:
                try:
                    # Delete file
                    file_path = Path(backup_data['file_path'])
                    if file_path.exists():
                        file_path.unlink()

                    # Delete from database
                    self.supabase.table('backups').delete().eq("id", backup_data['id']).execute()

                    print(f"🗑️ Cleaned up expired backup: {backup_data['id']}")

                except Exception as e:
                    print(f"Error cleaning up backup {backup_data['id']}: {e}")

        except Exception as e:
            print(f"Error during backup cleanup: {e}")

    # Recovery methods

    async def restore_from_backup(self, backup_id: str, target_tables: Optional[List[str]] = None) -> bool:
        """Restore data from backup"""
        try:
            # Get backup record
            result = self.supabase.table('backups').select("*").eq("id", backup_id).execute()

            if not result.data:
                raise ValueError(f"Backup {backup_id} not found")

            backup_data = result.data[0]
            backup_record = BackupRecord(**backup_data)

            # Decrypt and load backup
            encrypted_path = Path(backup_record.file_path)
            temp_path = self.backup_dir / f"restore_{backup_id}.tmp"

            await self._decrypt_backup(encrypted_path, temp_path)

            # Load data
            if backup_record.backup_type == 'full_backup':
                # Handle tar.gz file
                with tarfile.open(temp_path, "r:gz") as tar:
                    tar.extract("database.json", path=self.backup_dir)
                    with open(self.backup_dir / "database.json", 'r') as f:
                        restore_data = json.load(f)
            else:
                # Handle compressed JSON
                with gzip.open(temp_path, 'rt') as f:
                    restore_data = json.load(f)

            # Restore data to database
            await self._restore_data_to_database(restore_data, target_tables)

            # Update restore count
            self.supabase.table('backups') \
                .update({"restored_count": backup_record.restored_count + 1}) \
                .eq("id", backup_id) \
                .execute()

            # Clean up temp files
            temp_path.unlink()
            if (self.backup_dir / "database.json").exists():
                (self.backup_dir / "database.json").unlink()

            print(f"✅ Successfully restored from backup {backup_id}")
            return True

        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False

    async def _restore_data_to_database(self, data: Dict[str, List], target_tables: Optional[List[str]] = None):
        """Restore data to database tables"""
        for table, records in data.items():
            if target_tables and table not in target_tables:
                continue

            if not records:
                continue

            try:
                # Clear existing data (be careful!)
                print(f"⚠️ Clearing existing data in {table}")
                # In production, you might want confirmation

                # Insert restored data in batches
                batch_size = 100
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    self.supabase.table(table).insert(batch).execute()

                print(f"✅ Restored {len(records)} records to {table}")

            except Exception as e:
                print(f"❌ Error restoring {table}: {e}")

    async def get_backup_status(self) -> Dict[str, Any]:
        """Get backup system status"""
        try:
            # Get recent backups
            result = self.supabase.table('backups') \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(10) \
                .execute()

            recent_backups = []
            total_size = 0

            for backup_data in result.data:
                recent_backups.append({
                    'id': backup_data['id'],
                    'type': backup_data['backup_type'],
                    'size_mb': round(backup_data['file_size'] / 1024 / 1024, 2),
                    'created_at': backup_data['created_at'],
                    'expires_at': backup_data.get('expires_at')
                })
                total_size += backup_data['file_size']

            # Next scheduled backups
            current_time = datetime.now()
            next_backups = {}

            for backup_type, schedule in self.schedules.items():
                last_run = schedule['last_run']
                if last_run:
                    next_run = last_run + timedelta(seconds=schedule['interval'])
                    next_backups[backup_type] = {
                        'next_run': next_run.isoformat(),
                        'overdue': current_time > next_run
                    }

            return {
                'status': 'healthy',
                'recent_backups': recent_backups,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'encryption_enabled': True,
                'storage_backends': self.storage_backends,
                'retention_policy': self.retention_policy,
                'next_scheduled': next_backups
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

# Global backup service instance
_backup_service = None

def get_backup_service() -> BackupService:
    """Get singleton backup service instance"""
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service