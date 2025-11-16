"""
Logging and Observability Configuration
Implements structured logging and tracing for ADK agents
"""

import logging
import sys
from typing import Dict, Any
from datetime import datetime
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON-like logs
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data"""

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent

        if hasattr(record, "operation"):
            log_data["operation"] = record.operation

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Format as readable string (not pure JSON for better CLI output)
        parts = [f"[{log_data['timestamp']}]", f"{log_data['level']:8s}"]

        if "agent" in log_data:
            parts.append(f"[{log_data['agent']}]")

        parts.append(log_data["message"])

        if "duration_ms" in log_data:
            parts.append(f"({log_data['duration_ms']}ms)")

        return " ".join(parts)


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Setup logging configuration for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path to write logs
    """

    # Create logs directory if using file logging
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}")
    if log_file:
        logger.info(f"Logging to file: {log_file}")


class AgentLogger:
    """
    Custom logger wrapper for agents with automatic context
    """

    def __init__(self, agent_name: str):
        """
        Initialize agent logger

        Args:
            agent_name: Name of the agent
        """
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")

    def info(self, message: str, **kwargs):
        """Log info message with agent context"""
        extra = {"agent": self.agent_name, **kwargs}
        self.logger.info(message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message with agent context"""
        extra = {"agent": self.agent_name, **kwargs}
        self.logger.debug(message, extra=extra)

    def warning(self, message: str, **kwargs):
        """Log warning message with agent context"""
        extra = {"agent": self.agent_name, **kwargs}
        self.logger.warning(message, extra=extra)

    def error(self, message: str, **kwargs):
        """Log error message with agent context"""
        extra = {"agent": self.agent_name, **kwargs}
        self.logger.error(message, extra=extra)

    def log_operation(self, operation: str, duration_ms: float, success: bool = True):
        """
        Log an operation with duration

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
        """
        level = "info" if success else "error"
        message = f"Operation '{operation}' {'completed' if success else 'failed'}"

        extra = {
            "agent": self.agent_name,
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "success": success
        }

        getattr(self.logger, level)(message, extra=extra)


class TraceContext:
    """
    Simple trace context for tracking operation flows
    """

    def __init__(self):
        self.traces: Dict[str, Any] = {}
        self.current_trace_id: str = None

    def start_trace(self, trace_id: str, operation: str, metadata: Dict[str, Any] = None):
        """
        Start a new trace

        Args:
            trace_id: Unique trace identifier
            operation: Operation being traced
            metadata: Optional metadata
        """
        self.current_trace_id = trace_id
        self.traces[trace_id] = {
            "trace_id": trace_id,
            "operation": operation,
            "start_time": datetime.now(),
            "metadata": metadata or {},
            "events": [],
            "status": "active"
        }

        logger = logging.getLogger(__name__)
        logger.info(f"Trace started: {trace_id} - {operation}")

    def add_event(self, event_name: str, data: Dict[str, Any] = None):
        """
        Add event to current trace

        Args:
            event_name: Event name
            data: Event data
        """
        if self.current_trace_id and self.current_trace_id in self.traces:
            self.traces[self.current_trace_id]["events"].append({
                "event": event_name,
                "timestamp": datetime.now().isoformat(),
                "data": data or {}
            })

    def end_trace(self, status: str = "success", result: Any = None):
        """
        End current trace

        Args:
            status: Final status (success, error, etc.)
            result: Optional result data
        """
        if self.current_trace_id and self.current_trace_id in self.traces:
            trace = self.traces[self.current_trace_id]
            trace["end_time"] = datetime.now()
            trace["duration_ms"] = (trace["end_time"] - trace["start_time"]).total_seconds() * 1000
            trace["status"] = status
            trace["result"] = result

            logger = logging.getLogger(__name__)
            logger.info(
                f"Trace completed: {self.current_trace_id} - "
                f"{trace['operation']} ({trace['duration_ms']:.2f}ms) - {status}"
            )

            self.current_trace_id = None

    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """Get trace by ID"""
        return self.traces.get(trace_id)

    def get_all_traces(self) -> Dict[str, Any]:
        """Get all traces"""
        return self.traces


# Global trace context
trace_context = TraceContext()
