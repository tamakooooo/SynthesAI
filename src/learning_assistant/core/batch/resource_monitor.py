"""
Resource Monitor for Batch Processing.

Monitors system resources:
- Memory usage
- CPU usage
- Custom resource tracking
"""

import os
from dataclasses import dataclass
from typing import Any

import psutil


@dataclass
class ResourceUsage:
    """
    Resource usage snapshot.

    Attributes:
        memory_mb: Memory usage in MB
        memory_percent: Memory usage percentage
        cpu_percent: CPU usage percentage
        timestamp: Unix timestamp
    """

    memory_mb: float
    memory_percent: float
    cpu_percent: float
    timestamp: float


class ResourceMonitor:
    """
    System resource monitor.

    Tracks memory and CPU usage to prevent resource exhaustion.

    Example:
        >>> monitor = ResourceMonitor(memory_limit_mb=500)
        >>> usage = monitor.get_current_usage()
        >>> if usage.memory_mb > 450:
        ...     print("Warning: High memory usage")
    """

    def __init__(
        self,
        memory_limit_mb: float | None = None,
        cpu_limit_percent: float | None = None,
    ):
        """
        Initialize resource monitor.

        Args:
            memory_limit_mb: Memory limit in MB (optional)
            cpu_limit_percent: CPU limit percentage (optional)
        """
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_percent = cpu_limit_percent
        self._process = psutil.Process(os.getpid())
        self._usage_history: list[ResourceUsage] = []
        self._max_history = 100

    def get_current_usage(self) -> ResourceUsage:
        """
        Get current resource usage.

        Returns:
            ResourceUsage snapshot
        """
        # Get memory info
        memory_info = self._process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024  # Convert bytes to MB

        # Get memory percentage
        memory_percent = self._process.memory_percent()

        # Get CPU percentage
        cpu_percent = self._process.cpu_percent(interval=0.1)

        # Create snapshot
        import time

        usage = ResourceUsage(
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            cpu_percent=cpu_percent,
            timestamp=time.time(),
        )

        # Store in history
        self._usage_history.append(usage)
        if len(self._usage_history) > self._max_history:
            self._usage_history.pop(0)

        return usage

    def check_memory_available(self, required_mb: float = 100) -> bool:
        """
        Check if enough memory is available.

        Args:
            required_mb: Required memory in MB

        Returns:
            True if enough memory available
        """
        usage = self.get_current_usage()

        # If no limit set, always return True
        if self.memory_limit_mb is None:
            return True

        # Check if we have enough memory headroom
        available_mb = self.memory_limit_mb - usage.memory_mb
        return available_mb >= required_mb

    def is_over_limit(self) -> bool:
        """
        Check if resource usage is over limit.

        Returns:
            True if over limit
        """
        usage = self.get_current_usage()

        # Check memory limit
        if self.memory_limit_mb and usage.memory_mb > self.memory_limit_mb:
            return True

        # Check CPU limit
        if self.cpu_limit_percent and usage.cpu_percent > self.cpu_limit_percent:
            return True

        return False

    def get_average_usage(self, window: int = 10) -> ResourceUsage | None:
        """
        Get average resource usage over recent history.

        Args:
            window: Number of recent samples to average

        Returns:
            Average ResourceUsage or None if no history
        """
        if not self._usage_history:
            return None

        # Get recent samples
        recent = self._usage_history[-window:]

        # Calculate averages
        avg_memory_mb = sum(u.memory_mb for u in recent) / len(recent)
        avg_memory_percent = sum(u.memory_percent for u in recent) / len(recent)
        avg_cpu_percent = sum(u.cpu_percent for u in recent) / len(recent)
        avg_timestamp = sum(u.timestamp for u in recent) / len(recent)

        return ResourceUsage(
            memory_mb=avg_memory_mb,
            memory_percent=avg_memory_percent,
            cpu_percent=avg_cpu_percent,
            timestamp=avg_timestamp,
        )

    def get_peak_usage(self) -> ResourceUsage | None:
        """
        Get peak resource usage from history.

        Returns:
            Peak ResourceUsage or None if no history
        """
        if not self._usage_history:
            return None

        peak = max(self._usage_history, key=lambda u: u.memory_mb)
        return peak

    def clear_history(self) -> None:
        """Clear usage history."""
        self._usage_history.clear()

    @property
    def stats(self) -> dict[str, Any]:
        """Get resource monitor statistics."""
        usage = self.get_current_usage()
        avg = self.get_average_usage()
        peak = self.get_peak_usage()

        return {
            "current": {
                "memory_mb": usage.memory_mb,
                "memory_percent": usage.memory_percent,
                "cpu_percent": usage.cpu_percent,
            },
            "average": {
                "memory_mb": avg.memory_mb if avg else 0,
                "memory_percent": avg.memory_percent if avg else 0,
                "cpu_percent": avg.cpu_percent if avg else 0,
            }
            if avg
            else None,
            "peak": {
                "memory_mb": peak.memory_mb if peak else 0,
                "memory_percent": peak.memory_percent if peak else 0,
                "cpu_percent": peak.cpu_percent if peak else 0,
            }
            if peak
            else None,
            "limits": {
                "memory_limit_mb": self.memory_limit_mb,
                "cpu_limit_percent": self.cpu_limit_percent,
            },
            "history_size": len(self._usage_history),
        }