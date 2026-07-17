"""Result envelope for an offline Windows report evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WindowsLocalEvaluationResult:
    output_dir: str
    collector_record_count: int
    pup_match_count: int
    persistence_node_count: int
    persistence_edge_count: int
    execution_gating_eligible_count: int = 0
    collector_execution_performed: bool = False
    runtime_network_access: bool = False
    uploaded: bool = False
    system_modification_performed: bool = False

    def to_dict(self) -> dict:
        return {
            "output_dir": self.output_dir,
            "collector_record_count": self.collector_record_count,
            "pup_match_count": self.pup_match_count,
            "persistence_node_count": self.persistence_node_count,
            "persistence_edge_count": self.persistence_edge_count,
            "execution_gating_eligible_count": self.execution_gating_eligible_count,
            "collector_execution_performed": self.collector_execution_performed,
            "runtime_network_access": self.runtime_network_access,
            "uploaded": self.uploaded,
            "system_modification_performed": self.system_modification_performed,
        }
