"""Deterministic statistical aggregates, recurrence, and contextual deviation enricher.

Computes descriptive aggregates over explicitly observed metrics, historical baselines,
contextual deviations, and recurrence patterns without inferring diagnoses or faults.

Statistical Convention:
- Sample standard deviation (N-1 degrees of freedom via statistics.stdev) is used when N >= 2.
- std_dev is 0.0 when N < 2.
"""

from __future__ import annotations

import datetime
import statistics
from typing import Any
from cognitia.abi.types import Observation
from cognitia.context.types import (
    AggregateContext,
    ContextDeviation,
    DeviationType,
    RecurrenceContext,
)


def parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    """Safely parse ISO timestamp into timezone-aware datetime."""
    try:
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(normalized)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


def extract_numeric_metrics(payload: Any, prefix: str = "") -> dict[str, float]:
    """Extract flat mapping of numerical metric values from payload."""
    results: dict[str, float] = {}
    if not isinstance(payload, dict):
        return results

    for key, val in payload.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            results[full_key] = float(val)
        elif isinstance(val, dict):
            results.update(extract_numeric_metrics(val, prefix=full_key))
    return results


class StatisticalEnricher:
    """Computes deterministic aggregates, deviations, and recurrence statistics."""

    def compute_recurrence(
        self,
        chronological_observations: list[Observation],
        subject_id: str | None,
        pattern_name: str = "observed_event",
    ) -> tuple[RecurrenceContext, ...]:
        """Calculates descriptive recurrence metrics and intervals."""
        if len(chronological_observations) < 2:
            return ()

        intervals: list[float] = []
        for i in range(1, len(chronological_observations)):
            t_prev = parse_iso_timestamp(chronological_observations[i - 1].created_at)
            t_curr = parse_iso_timestamp(chronological_observations[i].created_at)
            delta = max(0.0, (t_curr - t_prev).total_seconds())
            intervals.append(round(delta, 6))

        median_int = round(float(statistics.median(intervals)), 6) if intervals else None
        latest_int = intervals[-1] if intervals else None
        timespan = max(
            0.0,
            (
                parse_iso_timestamp(chronological_observations[-1].created_at)
                - parse_iso_timestamp(chronological_observations[0].created_at)
            ).total_seconds(),
        )

        rec = RecurrenceContext(
            subject_id=subject_id,
            event_pattern=pattern_name,
            occurrence_count=len(chronological_observations),
            window_seconds=round(timespan, 6),
            intervals_seconds=tuple(intervals),
            median_interval_seconds=median_int,
            latest_interval_seconds=latest_int,
        )
        return (rec,)

    def compute_aggregates_and_deviations(
        self,
        chronological_observations: list[Observation],
    ) -> tuple[tuple[AggregateContext, ...], tuple[ContextDeviation, ...]]:
        """Calculates deterministic descriptive statistics and contextual deviations."""
        aggregates: list[AggregateContext] = []
        deviations: list[ContextDeviation] = []

        metric_series: dict[str, list[float]] = {}
        for obs in chronological_observations:
            metrics = extract_numeric_metrics(obs.payload)
            for m_name, m_val in metrics.items():
                if m_name not in metric_series:
                    metric_series[m_name] = []
                metric_series[m_name].append(m_val)

        for metric_name in sorted(metric_series.keys()):
            vals = metric_series[metric_name]
            count = len(vals)
            min_v = round(min(vals), 6)
            max_v = round(max(vals), 6)
            mean_v = round(sum(vals) / count, 6)
            median_v = round(float(statistics.median(vals)), 6)
            range_v = round(max_v - min_v, 6)
            # Sample standard deviation when count >= 2
            std_v = round(float(statistics.stdev(vals)), 6) if count >= 2 else 0.0
            latest_v = round(vals[-1], 6)
            delta_prev = round(vals[-1] - vals[-2], 6) if count >= 2 else 0.0
            delta_mean = round(latest_v - mean_v, 6)

            agg = AggregateContext(
                metric=metric_name,
                count=count,
                min_value=min_v,
                max_value=max_v,
                mean_value=mean_v,
                median_value=median_v,
                range_value=range_v,
                std_dev=std_v,
                latest_value=latest_v,
                delta_from_previous=delta_prev,
                delta_from_mean=delta_mean,
            )
            aggregates.append(agg)

            # Historical baseline check (all values prior to latest)
            if count >= 2:
                historical_vals = vals[:-1]
                hist_min = round(min(historical_vals), 6)
                hist_max = round(max(historical_vals), 6)

                if latest_v > hist_max:
                    deviations.append(
                        ContextDeviation(
                            metric=metric_name,
                            current_value=latest_v,
                            baseline_reference=(hist_min, hist_max),
                            deviation_type=DeviationType.ABOVE_HISTORICAL_RANGE,
                            magnitude=round(latest_v - hist_max, 6),
                        )
                    )
                elif latest_v < hist_min:
                    deviations.append(
                        ContextDeviation(
                            metric=metric_name,
                            current_value=latest_v,
                            baseline_reference=(hist_min, hist_max),
                            deviation_type=DeviationType.BELOW_HISTORICAL_RANGE,
                            magnitude=round(hist_min - latest_v, 6),
                        )
                    )
                elif abs(delta_prev) > (range_v * 0.5) and count >= 3:
                    deviations.append(
                        ContextDeviation(
                            metric=metric_name,
                            current_value=latest_v,
                            baseline_reference=vals[-2],
                            deviation_type=DeviationType.RAPID_CHANGE,
                            magnitude=round(abs(delta_prev), 6),
                        )
                    )

        return tuple(aggregates), tuple(deviations)
