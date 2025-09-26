"""
Monitoring and Analytics Dashboard Service
Real-time metrics, performance tracking, and system health monitoring
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json

from ..database.supabase_client import get_supabase_client
from ..config import get_settings

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float

@dataclass
class APIMetrics:
    """API performance metrics"""
    timestamp: datetime
    requests_total: int
    requests_per_minute: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    error_rate: float
    active_connections: int
    cache_hit_rate: float

@dataclass
class ServiceMetrics:
    """Service-specific metrics"""
    timestamp: datetime
    service_name: str
    status: str
    requests_count: int
    success_rate: float
    avg_processing_time_ms: float
    last_error: Optional[str] = None
    uptime_minutes: float = 0

@dataclass
class Alert:
    """System alert"""
    id: str
    type: str
    severity: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class MonitoringService:
    """
    Comprehensive monitoring service for SCRIBE
    Tracks system health, performance, and generates alerts
    """

    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()

        # Metrics storage (in-memory for real-time, DB for persistence)
        self.system_metrics_history = deque(maxlen=1440)  # 24 hours at 1min intervals
        self.api_metrics_history = deque(maxlen=1440)
        self.service_metrics_history = defaultdict(lambda: deque(maxlen=1440))
        self.alerts = deque(maxlen=100)

        # Service tracking
        self.service_start_times = {}
        self.service_stats = defaultdict(lambda: {
            'requests': 0,
            'errors': 0,
            'total_time': 0,
            'last_request': None
        })

        # Thresholds for alerts
        self.thresholds = {
            'cpu_high': 80.0,
            'memory_high': 85.0,
            'disk_low': 10.0,  # GB free
            'response_time_high': 2000.0,  # ms
            'error_rate_high': 5.0,  # %
            'cache_hit_rate_low': 30.0  # %
        }

    async def start_monitoring(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self._collect_system_metrics())
        asyncio.create_task(self._collect_api_metrics())
        asyncio.create_task(self._check_service_health())
        asyncio.create_task(self._process_alerts())

        print("✅ Monitoring service started")

    async def _collect_system_metrics(self):
        """Collect system performance metrics every minute"""
        while True:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()

                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / 1024 / 1024,
                    memory_total_mb=memory.total / 1024 / 1024,
                    disk_usage_percent=(disk.total - disk.free) / disk.total * 100,
                    disk_free_gb=disk.free / 1024 / 1024 / 1024,
                    network_sent_mb=network.bytes_sent / 1024 / 1024,
                    network_recv_mb=network.bytes_recv / 1024 / 1024
                )

                self.system_metrics_history.append(metrics)

                # Check for alerts
                await self._check_system_alerts(metrics)

                # Store in database every 5 minutes
                if len(self.system_metrics_history) % 5 == 0:
                    await self._persist_system_metrics(metrics)

            except Exception as e:
                print(f"Error collecting system metrics: {e}")

            await asyncio.sleep(60)  # Every minute

    async def _collect_api_metrics(self):
        """Collect API performance metrics"""
        while True:
            try:
                # Get metrics from performance middleware
                # This would integrate with the performance middleware

                # Mock data for now - in real implementation, get from middleware
                metrics = APIMetrics(
                    timestamp=datetime.now(),
                    requests_total=len(self.system_metrics_history) * 10,  # Mock
                    requests_per_minute=10.0,
                    avg_response_time_ms=150.0,
                    p95_response_time_ms=300.0,
                    error_rate=1.5,
                    active_connections=5,
                    cache_hit_rate=75.0
                )

                self.api_metrics_history.append(metrics)

                # Check for API alerts
                await self._check_api_alerts(metrics)

            except Exception as e:
                print(f"Error collecting API metrics: {e}")

            await asyncio.sleep(60)

    async def _check_service_health(self):
        """Check health of all services"""
        services = ['upload', 'chat', 'search', 'rag', 'embedding', 'realtime']

        while True:
            try:
                for service in services:
                    health = await self._check_individual_service(service)

                    service_metrics = ServiceMetrics(
                        timestamp=datetime.now(),
                        service_name=service,
                        status=health['status'],
                        requests_count=health.get('requests', 0),
                        success_rate=health.get('success_rate', 100.0),
                        avg_processing_time_ms=health.get('avg_time', 100.0),
                        last_error=health.get('last_error'),
                        uptime_minutes=health.get('uptime', 0)
                    )

                    self.service_metrics_history[service].append(service_metrics)

            except Exception as e:
                print(f"Error checking service health: {e}")

            await asyncio.sleep(120)  # Every 2 minutes

    async def _check_individual_service(self, service_name: str) -> Dict[str, Any]:
        """Check health of individual service"""
        try:
            # Mock health check - in real implementation, ping actual services
            return {
                'status': 'healthy',
                'requests': self.service_stats[service_name]['requests'],
                'success_rate': 98.5,
                'avg_time': 120.0,
                'uptime': 1440  # minutes
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'last_error': str(e),
                'requests': 0,
                'success_rate': 0,
                'avg_time': 0,
                'uptime': 0
            }

    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check system metrics for alert conditions"""

        # CPU alert
        if metrics.cpu_percent > self.thresholds['cpu_high']:
            await self._create_alert(
                type="cpu_high",
                severity="warning",
                message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                details={"cpu_percent": metrics.cpu_percent}
            )

        # Memory alert
        if metrics.memory_percent > self.thresholds['memory_high']:
            await self._create_alert(
                type="memory_high",
                severity="warning",
                message=f"High memory usage: {metrics.memory_percent:.1f}%",
                details={
                    "memory_percent": metrics.memory_percent,
                    "memory_used_mb": metrics.memory_used_mb
                }
            )

        # Disk space alert
        if metrics.disk_free_gb < self.thresholds['disk_low']:
            await self._create_alert(
                type="disk_low",
                severity="critical",
                message=f"Low disk space: {metrics.disk_free_gb:.1f} GB free",
                details={"disk_free_gb": metrics.disk_free_gb}
            )

    async def _check_api_alerts(self, metrics: APIMetrics):
        """Check API metrics for alert conditions"""

        # Response time alert
        if metrics.avg_response_time_ms > self.thresholds['response_time_high']:
            await self._create_alert(
                type="response_time_high",
                severity="warning",
                message=f"High response time: {metrics.avg_response_time_ms:.0f}ms",
                details={"avg_response_time_ms": metrics.avg_response_time_ms}
            )

        # Error rate alert
        if metrics.error_rate > self.thresholds['error_rate_high']:
            await self._create_alert(
                type="error_rate_high",
                severity="critical",
                message=f"High error rate: {metrics.error_rate:.1f}%",
                details={"error_rate": metrics.error_rate}
            )

        # Cache hit rate alert
        if metrics.cache_hit_rate < self.thresholds['cache_hit_rate_low']:
            await self._create_alert(
                type="cache_hit_rate_low",
                severity="info",
                message=f"Low cache hit rate: {metrics.cache_hit_rate:.1f}%",
                details={"cache_hit_rate": metrics.cache_hit_rate}
            )

    async def _create_alert(self, type: str, severity: str, message: str, details: Dict[str, Any]):
        """Create new alert"""
        alert = Alert(
            id=f"{type}_{int(time.time())}",
            type=type,
            severity=severity,
            message=message,
            details=details,
            timestamp=datetime.now()
        )

        self.alerts.append(alert)

        # Log alert
        print(f"🚨 ALERT [{severity.upper()}]: {message}")

        # Store in database
        try:
            await self.supabase.table('alerts').insert(asdict(alert)).execute()
        except Exception as e:
            print(f"Failed to store alert: {e}")

    async def _process_alerts(self):
        """Process and manage alerts"""
        while True:
            try:
                # Auto-resolve alerts that are no longer relevant
                current_time = datetime.now()

                for alert in self.alerts:
                    if not alert.resolved and self._should_auto_resolve(alert, current_time):
                        alert.resolved = True
                        alert.resolved_at = current_time

            except Exception as e:
                print(f"Error processing alerts: {e}")

            await asyncio.sleep(300)  # Every 5 minutes

    def _should_auto_resolve(self, alert: Alert, current_time: datetime) -> bool:
        """Check if alert should be auto-resolved"""
        # Auto-resolve alerts older than 1 hour for certain types
        auto_resolve_types = ['cpu_high', 'memory_high', 'response_time_high']

        if alert.type in auto_resolve_types:
            time_diff = current_time - alert.timestamp
            return time_diff.total_seconds() > 3600  # 1 hour

        return False

    async def _persist_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        try:
            await self.supabase.table('system_metrics').insert(asdict(metrics)).execute()
        except Exception as e:
            print(f"Failed to persist system metrics: {e}")

    # Public API methods

    def track_service_request(self, service_name: str, processing_time: float, success: bool):
        """Track service request for metrics"""
        stats = self.service_stats[service_name]
        stats['requests'] += 1
        stats['total_time'] += processing_time
        stats['last_request'] = datetime.now()

        if not success:
            stats['errors'] += 1

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        current_time = datetime.now()

        # Get latest metrics
        latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
        latest_api = self.api_metrics_history[-1] if self.api_metrics_history else None

        # Active alerts
        active_alerts = [alert for alert in self.alerts if not alert.resolved]

        # Service statuses
        service_statuses = {}
        for service, metrics_list in self.service_metrics_history.items():
            latest = metrics_list[-1] if metrics_list else None
            service_statuses[service] = {
                'status': latest.status if latest else 'unknown',
                'uptime': latest.uptime_minutes if latest else 0,
                'success_rate': latest.success_rate if latest else 0
            }

        return {
            'timestamp': current_time.isoformat(),
            'system': asdict(latest_system) if latest_system else None,
            'api': asdict(latest_api) if latest_api else None,
            'services': service_statuses,
            'alerts': {
                'active_count': len(active_alerts),
                'critical_count': len([a for a in active_alerts if a.severity == 'critical']),
                'recent': [asdict(alert) for alert in list(active_alerts)[-5:]]
            },
            'health_score': self._calculate_health_score()
        }

    def get_metrics_history(self, hours: int = 24) -> Dict[str, List[Dict]]:
        """Get historical metrics"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter metrics by time
        system_metrics = [
            asdict(m) for m in self.system_metrics_history
            if m.timestamp > cutoff_time
        ]

        api_metrics = [
            asdict(m) for m in self.api_metrics_history
            if m.timestamp > cutoff_time
        ]

        return {
            'system': system_metrics,
            'api': api_metrics,
            'timerange_hours': hours
        }

    def get_service_analytics(self) -> Dict[str, Any]:
        """Get service performance analytics"""
        analytics = {}

        for service, stats in self.service_stats.items():
            total_requests = stats['requests']
            total_errors = stats['errors']
            total_time = stats['total_time']

            analytics[service] = {
                'total_requests': total_requests,
                'error_rate': (total_errors / max(total_requests, 1)) * 100,
                'avg_response_time_ms': total_time / max(total_requests, 1),
                'success_rate': ((total_requests - total_errors) / max(total_requests, 1)) * 100,
                'last_request': stats['last_request'].isoformat() if stats['last_request'] else None
            }

        return analytics

    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        if not self.system_metrics_history or not self.api_metrics_history:
            return 50.0  # Unknown state

        latest_system = self.system_metrics_history[-1]
        latest_api = self.api_metrics_history[-1]

        # Health factors (weighted)
        factors = {
            'cpu': max(0, 100 - latest_system.cpu_percent),  # Lower CPU is better
            'memory': max(0, 100 - latest_system.memory_percent),
            'disk': min(100, latest_system.disk_free_gb * 10),  # Scale disk space
            'response_time': max(0, 100 - (latest_api.avg_response_time_ms / 20)),
            'error_rate': max(0, 100 - latest_api.error_rate * 10),
            'cache': latest_api.cache_hit_rate
        }

        weights = {
            'cpu': 0.2,
            'memory': 0.2,
            'disk': 0.15,
            'response_time': 0.2,
            'error_rate': 0.15,
            'cache': 0.1
        }

        health_score = sum(factors[key] * weights[key] for key in factors)
        return min(100, max(0, health_score))

    async def get_cost_analytics(self) -> Dict[str, Any]:
        """Get cost analytics and projections"""
        # This would integrate with cloud provider APIs for real cost data
        # For now, estimate based on usage patterns

        total_requests = sum(stats['requests'] for stats in self.service_stats.values())

        # Estimated costs (mock data)
        estimated_costs = {
            'openai_api': total_requests * 0.002,  # $0.002 per request estimate
            'claude_api': total_requests * 0.003,
            'perplexity_api': total_requests * 0.001,
            'supabase': 25.0,  # Fixed monthly
            'redis': 15.0,
            'hosting': 20.0
        }

        total_monthly = sum(estimated_costs.values())

        return {
            'current_month_estimate': total_monthly,
            'breakdown': estimated_costs,
            'requests_this_period': total_requests,
            'avg_cost_per_request': total_monthly / max(total_requests, 1),
            'projected_monthly': total_monthly * (30 / datetime.now().day)
        }

# Global monitoring service instance
_monitoring_service = None

def get_monitoring_service() -> MonitoringService:
    """Get singleton monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service