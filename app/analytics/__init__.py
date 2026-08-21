"""
Analytics Package tracking execution metrics and computing P50 / P70 / P100 latency telemetry.
"""

import numpy as np
from typing import List
from app.schemas import LatencyTelemetry


class LatencyTracker:
    """Telemetry collector and percentiles metric calculator."""

    def __init__(self) -> None:
        self._latencies_ms: List[float] = []

    def record_latency(self, elapsed_ms: float) -> None:
        """Record pipeline execution time in milliseconds."""
        self._latencies_ms.append(elapsed_ms)

    def get_telemetry(self, sla_ms: float = 200.0) -> LatencyTelemetry:
        """Compute P50, P70, P100 and SLA compliance rate."""
        if not self._latencies_ms:
            return LatencyTelemetry(
                sample_count=0,
                p50_ms=0.0,
                p70_ms=0.0,
                p100_ms=0.0,
                sla_compliance_rate=100.0,
            )

        samples = np.array(self._latencies_ms)
        p50 = float(np.percentile(samples, 50))
        p70 = float(np.percentile(samples, 70))
        p100 = float(np.max(samples))
        sla_compliant_count = np.sum(samples <= sla_ms)
        compliance_rate = float((sla_compliant_count / len(samples)) * 100.0)

        return LatencyTelemetry(
            sample_count=len(samples),
            p50_ms=p50,
            p70_ms=p70,
            p100_ms=p100,
            sla_compliance_rate=compliance_rate,
        )


latency_tracker = LatencyTracker()
