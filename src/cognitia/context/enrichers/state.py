"""Observable state reconstruction enricher.

Reconstructs observable state variables surrounding an observation based strictly
on recorded observations. Explicitly represents unknown states and preserves conflicts.
"""

from __future__ import annotations

import datetime
from typing import Any
from cognitia.abi.types import Observation
from cognitia.context.types import StateReconstruction, StateVariable


def parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    """Safely parse ISO timestamp into timezone-aware datetime."""
    try:
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(normalized)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


def extract_variables(payload: Any, prefix: str = "") -> dict[str, Any]:
    """Extract explicit variable key-value pairs from observation payload."""
    results: dict[str, Any] = {}
    if not isinstance(payload, dict):
        return results

    for key, val in payload.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(val, dict) and not key.startswith("_"):
            results.update(extract_variables(val, prefix=full_key))
        else:
            results[full_key] = val
    return results


class StateReconstructionEnricher:
    """Computes deterministic observable state reconstruction without semantic guessing."""

    def reconstruct_state(
        self,
        reference_observation: Observation,
        chronological_observations: list[Observation],
        known_variable_names: set[str] | None = None,
    ) -> StateReconstruction:
        """Reconstructs state history up to the reference observation timestamp."""
        ref_time = parse_iso_timestamp(reference_observation.created_at)

        # Collect observations occurring at or before the reference observation
        relevant_obs = [
            o for o in chronological_observations
            if parse_iso_timestamp(o.created_at) <= ref_time
        ]

        var_history: dict[str, list[tuple[datetime.datetime, Any, str, str]]] = {}
        # Entry: (timestamp_dt, value, timestamp_str, obs_id)

        for obs in relevant_obs:
            obs_dt = parse_iso_timestamp(obs.created_at)
            flat_vars = extract_variables(obs.payload)
            for var_name, var_val in flat_vars.items():
                if var_name not in var_history:
                    var_history[var_name] = []
                var_history[var_name].append((obs_dt, var_val, obs.created_at, obs.id))

        # Check for requested or known variables not present in observation history
        all_var_names = set(var_history.keys())
        if known_variable_names:
            all_var_names.update(known_variable_names)

        state_variables: list[StateVariable] = []

        for var_name in sorted(all_var_names):
            if var_name not in var_history or not var_history[var_name]:
                # Variable was known/requested but never observed
                state_variables.append(
                    StateVariable(
                        name=var_name,
                        latest_value="UNKNOWN",
                        is_unknown=True,
                    )
                )
                continue

            history = var_history[var_name]
            first_val = history[0][1]
            latest_val = history[-1][1]
            prev_val = history[-2][1] if len(history) >= 2 else None
            obs_at = history[-1][2]

            # Check if conflicting values exist at the exact same latest timestamp
            latest_dt = history[-1][0]
            same_ts_values = [v for dt, v, _, _ in history if dt == latest_dt]
            is_conflicted = len(set(str(v) for v in same_ts_values)) > 1

            # Validity interval calculation
            validity_interval: float | None = None
            if len(history) >= 2:
                validity_interval = round(
                    abs((history[-1][0] - history[-2][0]).total_seconds()), 6
                )

            state_variables.append(
                StateVariable(
                    name=var_name,
                    latest_value=latest_val,
                    previous_value=prev_val,
                    first_known_value=first_val,
                    observed_at=obs_at,
                    validity_interval_seconds=validity_interval,
                    is_conflicted=is_conflicted,
                    is_unknown=False,
                )
            )

        return StateReconstruction(
            variables=tuple(state_variables),
            reconstructed_at=reference_observation.created_at,
        )
