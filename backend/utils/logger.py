"""
Structured logging configuration for Plume & Mimir
Uses structlog for better debugging and monitoring
"""

import structlog
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import json

from ..config import settings

def setup_logging():
    """Configure structured logging for the application"""

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.value),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.processors.TimeStamper(fmt="ISO"),
            # Add log level
            structlog.stdlib.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Format stack info if present
            structlog.processors.format_exc_info,
            # Add request context (will be added by middleware)
            add_request_context,
            # JSON formatting for production, pretty for development
            structlog.processors.JSONRenderer()
            if settings.is_production
            else structlog.dev.ConsoleRenderer(colors=True)
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def add_request_context(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request context to log entries"""
    # This will be populated by the request middleware
    # For now, just ensure the structure is consistent
    if "request_id" not in event_dict:
        event_dict["request_id"] = None

    return event_dict

def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a configured logger instance"""
    return structlog.get_logger(name)

class RequestLogger:
    """Logger with request context"""

    def __init__(self, request_id: str, logger: structlog.BoundLogger):
        self.request_id = request_id
        self.logger = logger.bind(request_id=request_id)

    def debug(self, msg: str, **kwargs):
        """Log debug message with request context"""
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs):
        """Log info message with request context"""
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        """Log warning message with request context"""
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        """Log error message with request context"""
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        """Log critical message with request context"""
        self.logger.critical(msg, **kwargs)

    def bind(self, **kwargs):
        """Bind additional context to logger"""
        return RequestLogger(
            self.request_id,
            self.logger.bind(**kwargs)
        )

class AgentLogger:
    """Logger for agent operations"""

    def __init__(self, agent_name: str, session_id: Optional[str] = None):
        self.agent_name = agent_name
        self.session_id = session_id
        self.logger = get_logger(f"agent.{agent_name}")

        if session_id:
            self.logger = self.logger.bind(session_id=session_id)

    def log_agent_start(self, task: str, **kwargs):
        """Log agent task start"""
        self.logger.info(
            f"{self.agent_name} task started",
            task=task,
            agent=self.agent_name,
            status="started",
            **kwargs
        )

    def log_agent_complete(self, task: str, duration_ms: float, **kwargs):
        """Log agent task completion"""
        self.logger.info(
            f"{self.agent_name} task completed",
            task=task,
            agent=self.agent_name,
            status="completed",
            duration_ms=duration_ms,
            **kwargs
        )

    def log_agent_error(self, task: str, error: str, **kwargs):
        """Log agent task error"""
        self.logger.error(
            f"{self.agent_name} task failed",
            task=task,
            agent=self.agent_name,
            status="failed",
            error=error,
            **kwargs
        )

    def log_llm_call(self, model: str, tokens_used: int, cost: float, **kwargs):
        """Log LLM API call"""
        self.logger.info(
            "LLM API call",
            agent=self.agent_name,
            model=model,
            tokens_used=tokens_used,
            cost_eur=cost,
            **kwargs
        )

class PerformanceLogger:
    """Logger for performance monitoring"""

    def __init__(self):
        self.logger = get_logger("performance")

    def log_database_query(self, query_type: str, duration_ms: float, **kwargs):
        """Log database query performance"""
        self.logger.info(
            "Database query executed",
            query_type=query_type,
            duration_ms=duration_ms,
            **kwargs
        )

    def log_cache_operation(self, operation: str, hit: bool, duration_ms: float, **kwargs):
        """Log cache operation"""
        self.logger.info(
            "Cache operation",
            operation=operation,
            cache_hit=hit,
            duration_ms=duration_ms,
            **kwargs
        )

    def log_api_call(self, service: str, endpoint: str, duration_ms: float, status_code: int, **kwargs):
        """Log external API call"""
        self.logger.info(
            "External API call",
            service=service,
            endpoint=endpoint,
            duration_ms=duration_ms,
            status_code=status_code,
            **kwargs
        )

class CostLogger:
    """Logger for cost tracking"""

    def __init__(self):
        self.logger = get_logger("costs")

    def log_token_usage(self, service: str, model: str, tokens: int, cost: float, **kwargs):
        """Log token usage and cost"""
        self.logger.info(
            "Token usage",
            service=service,
            model=model,
            tokens_used=tokens,
            cost_eur=cost,
            **kwargs
        )

    def log_daily_costs(self, total_cost: float, breakdown: Dict[str, float], **kwargs):
        """Log daily cost summary"""
        self.logger.info(
            "Daily cost summary",
            total_cost_eur=total_cost,
            cost_breakdown=breakdown,
            **kwargs
        )

    def log_budget_alert(self, alert_type: str, current_cost: float, budget_limit: float, **kwargs):
        """Log budget alert"""
        self.logger.warning(
            "Budget alert",
            alert_type=alert_type,
            current_cost_eur=current_cost,
            budget_limit_eur=budget_limit,
            utilization_percent=(current_cost / budget_limit) * 100,
            **kwargs
        )

# Pre-configured logger instances for common use cases
main_logger = get_logger("plume_mimir")
performance_logger = PerformanceLogger()
cost_logger = CostLogger()

# Agent loggers (will be initialized when needed)
def get_agent_logger(agent_name: str, session_id: Optional[str] = None) -> AgentLogger:
    """Get an agent logger instance"""
    return AgentLogger(agent_name, session_id)

def get_request_logger(request_id: str) -> RequestLogger:
    """Get a request logger instance"""
    return RequestLogger(request_id, main_logger)