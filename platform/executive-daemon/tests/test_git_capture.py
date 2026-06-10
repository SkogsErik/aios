"""
test_git_capture.py — Tests for git observation capture.
"""

import datetime
from pathlib import Path

import pytest

from capture.git_capture import (
    GitCaptureResult,
    GitRepoConfig,
    _compute_observation_id,
    _parse_timestamp,
)


class TestHelpers:
    def test_parse_timestamp(self):
        dt = _parse_timestamp("2026-06-10T14:30:00+02:00")
        assert dt.year == 2026
        assert dt.month == 6
        assert dt.day == 10

    def test_parse_timestamp_fallback_on_error(self):
        dt = _parse_timestamp("not-a-date")
        assert isinstance(dt, datetime.datetime)

    def test_compute_observation_id(self):
        oid = _compute_observation_id("20260610", 42)
        assert oid == "OBS-20260610-042"

    def test_compute_observation_id_pads(self):
        oid = _compute_observation_id("20260610", 5)
        assert oid == "OBS-20260610-005"
