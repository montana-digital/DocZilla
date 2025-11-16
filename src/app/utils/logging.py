"""
Logging Service

Handles structured logging with CSV persistence, rotation, and correlation IDs.
"""

import csv
import logging
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import uuid

# Configure standard Python logging
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass
class LogEntry:
    """Log entry structure."""
    timestamp: datetime
    level: LogLevel
    message: str
    module: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    operation: Optional[str] = None
    duration_ms: Optional[float] = None
    status: str = "success"  # "success" | "failure" | "warning"
    file_path: Optional[str] = None
    error_details: Optional[str] = None
    
    def to_csv_row(self) -> list:
        """Convert log entry to CSV row."""
        return [
            self.timestamp.isoformat(),
            self.level.value,
            self.message,
            self.module,
            self.request_id or "",
            self.user_id or "",
            self.operation or "",
            str(self.duration_ms) if self.duration_ms else "",
            self.status,
            self.file_path or "",
            self.error_details or ""
        ]


class ActivityLogger:
    """
    Activity logger with CSV persistence and rotation.
    
    Logs are stored in CSV format in the logs/ directory.
    Rotation is handled based on file size (50MB) and time (daily).
    """
    
    CSV_HEADER = [
        "timestamp", "level", "message", "module", "request_id",
        "user_id", "operation", "duration_ms", "status", "file_path", "error_details"
    ]
    
    def __init__(
        self,
        log_dir: Path = Path("logs"),
        max_file_size_mb: int = 50,
        retention_days: int = 30
    ):
        """
        Initialize activity logger.
        
        Args:
            log_dir: Directory for log files
            max_file_size_mb: Maximum file size before rotation (MB)
            retention_days: Number of days to retain logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.retention_days = retention_days
        
        # Current log file
        self.current_log_file = self._get_current_log_file()
        self._ensure_header()
        
        # Cleanup old logs on initialization
        self._cleanup_old_logs()
    
    def _get_current_log_file(self) -> Path:
        """Get path to current log file (date-based naming)."""
        date_str = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"activity_{date_str}.csv"
    
    def _ensure_header(self):
        """Ensure CSV file has header if it doesn't exist."""
        if not self.current_log_file.exists():
            with open(self.current_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.CSV_HEADER)
        else:
            # Check if header exists
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line != ','.join(self.CSV_HEADER):
                    # Header doesn't match, recreate file
                    self.current_log_file = self._get_current_log_file()
                    with open(self.current_log_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(self.CSV_HEADER)
    
    def _check_rotation(self):
        """Check if log file needs rotation (size-based)."""
        if self.current_log_file.exists():
            file_size = self.current_log_file.stat().st_size
            if file_size > self.max_file_size_bytes:
                # Rotate to new file with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_file = self.log_dir / f"activity_{timestamp}.csv"
                self.current_log_file.rename(new_file)
                self.current_log_file = self._get_current_log_file()
                self._ensure_header()
    
    def _cleanup_old_logs(self):
        """Remove log files older than retention period."""
        if not self.log_dir.exists():
            return
        
        cutoff_date = datetime.now().timestamp() - (self.retention_days * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("activity_*.csv"):
            try:
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    logger.info(f"Removed old log file: {log_file}")
            except Exception as e:
                logger.warning(f"Failed to remove old log file {log_file}: {e}")
    
    def log(
        self,
        level: LogLevel | str,
        message: str,
        module: str,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status: str = "success",
        file_path: Optional[str] = None,
        error_details: Optional[str] = None
    ):
        """
        Write log entry to CSV file.
        
        Args:
            level: Log level (LogLevel enum or string)
            message: Log message
            module: Module name
            request_id: Request correlation ID
            user_id: User identifier
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            status: Status (success/failure/warning)
            file_path: Related file path
            error_details: Error details if applicable
        """
        # Convert string to LogLevel if needed
        if isinstance(level, str):
            try:
                level = LogLevel[level.upper()]
            except KeyError:
                level = LogLevel.INFO
        
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            module=module,
            request_id=request_id,
            user_id=user_id,
            operation=operation,
            duration_ms=duration_ms,
            status=status,
            file_path=file_path,
            error_details=error_details
        )
        
        # Check rotation before writing
        self._check_rotation()
        
        # Ensure we have current day's file
        new_log_file = self._get_current_log_file()
        if new_log_file != self.current_log_file:
            self.current_log_file = new_log_file
            self._ensure_header()
        
        # Write to CSV
        try:
            with open(self.current_log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(entry.to_csv_row())
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")
    
    def get_recent_logs(self, limit: int = 100) -> list[dict]:
        """
        Get recent log entries.
        
        Args:
            limit: Maximum number of entries to return
        
        Returns:
            List of log entries as dictionaries
        """
        logs = []
        
        # Get all log files, sorted by modification time (newest first)
        log_files = sorted(
            self.log_dir.glob("activity_*.csv"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        logs.append(dict(row))
                        if len(logs) >= limit:
                            return logs
            except Exception as e:
                logger.warning(f"Failed to read log file {log_file}: {e}")
        
        return logs


# Global logger instance
_activity_logger: Optional[ActivityLogger] = None


def get_logger(log_dir: Path = Path("logs")) -> ActivityLogger:
    """
    Get or create global activity logger instance.
    
    Args:
        log_dir: Directory for log files
    
    Returns:
        ActivityLogger instance
    """
    global _activity_logger
    if _activity_logger is None:
        _activity_logger = ActivityLogger(log_dir=log_dir)
    return _activity_logger


def generate_request_id() -> str:
    """Generate a new request ID (UUID v4)."""
    return str(uuid.uuid4())


def log_operation(
    operation: str,
    request_id: str,
    status: str = "success",
    duration_ms: Optional[float] = None,
    error_details: Optional[str] = None,
    module: Optional[str] = None
):
    """
    Log an operation with timing.
    
    Args:
        operation: Operation name
        request_id: Request correlation ID
        status: Status (success/failure/warning)
        duration_ms: Operation duration in milliseconds
        error_details: Error details if status is failure
        module: Module name (auto-detect if not provided)
    """
    if module is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            module = frame.f_back.f_globals.get('__name__', 'unknown')
    
    level = LogLevel.ERROR if status == "failure" else LogLevel.INFO
    
    logger = get_logger()
    logger.log(
        level=level,
        message=f"Operation: {operation}",
        module=module or "unknown",
        request_id=request_id,
        operation=operation,
        duration_ms=duration_ms,
        status=status,
        error_details=error_details
    )

