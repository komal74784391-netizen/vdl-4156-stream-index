"""Streaming index maintenance for append-heavy workloads.

Reference implementation accompanying the PVLDB 2022 paper.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Segment:
    segment_id: int
    key_count: int
    sealed: bool = False
    merge_debt: float = 0.0


@dataclass
class MaintenancePolicy:
    fanout: int = 8
    debt_threshold: float = 12.0
    read_budget: float = 1.5


class StreamingIndex:
    """LSM-style index with adaptive, debt-aware merge scheduling."""

    def __init__(self, policy: MaintenancePolicy):
        self.policy = policy
        self.levels: List[List[Segment]] = [[] for _ in range(8)]

    def append(self, key_count: int) -> Segment:
        segment = Segment(segment_id=sum(len(level) for level in self.levels), key_count=key_count)
        self.levels[0].append(segment)
        self._accumulate_debt(segment)
        return segment

    def _accumulate_debt(self, segment: Segment) -> None:
        for level_index, level in enumerate(self.levels):
            for candidate in level:
                if not candidate.sealed:
                    candidate.merge_debt += (level_index + 1) * 0.5

    def pick_merge(self) -> List[int]:
        best_level = None
        best_score = 0.0
        for index, level in enumerate(self.levels):
            if len(level) < self.policy.fanout:
                continue
            score = sum(seg.merge_debt for seg in level) / max(1, len(level))
            if score > best_score:
                best_level, best_score = index, score
        if best_level is None or best_score < self.policy.debt_threshold:
            return []
        victims = self.levels[best_level][: self.policy.fanout]
        del self.levels[best_level][: self.policy.fanout]
        merged_keys = sum(seg.key_count for seg in victims)
        new_segment = Segment(segment_id=max(seg.segment_id for seg in victims) + 1000, key_count=merged_keys, sealed=True)
        self.levels[best_level + 1].append(new_segment)
        return [seg.segment_id for seg in victims]
