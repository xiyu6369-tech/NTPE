"""Tests for Checkpoint Validator (RM-6.3.2)."""

import pytest

from core.runtime_checkpoint.models import (
    CheckpointSnapshot,
    CheckpointIntegrityError,
    CheckpointSessionMismatchError,
    CheckpointSnapshotMismatchError,
)
from core.runtime_checkpoint.validator import CheckpointValidator


def make_valid_checkpoint(session_id="s1"):
    return CheckpointSnapshot(session_id=session_id).with_hash()


class TestValidate:
    def test_valid_checkpoint(self):
        validator = CheckpointValidator()
        cp = make_valid_checkpoint()
        result = validator.validate(cp, "s1")
        assert result == cp

    def test_missing_hash(self):
        validator = CheckpointValidator()
        cp = CheckpointSnapshot(session_id="s1")
        with pytest.raises(CheckpointIntegrityError):
            validator.validate(cp, "s1")

    def test_corrupted_hash(self):
        validator = CheckpointValidator()
        cp = CheckpointSnapshot(
            session_id="s1",
            state_hash="abcdef",
        )
        with pytest.raises(CheckpointIntegrityError):
            validator.validate(cp, "s1")

    def test_wrong_session(self):
        validator = CheckpointValidator()
        cp = make_valid_checkpoint(session_id="s1")
        with pytest.raises(CheckpointSessionMismatchError) as exc:
            validator.validate(cp, "s2")
        assert "s1" in str(exc.value)
        assert "s2" in str(exc.value)

    def test_null_metadata(self):
        validator = CheckpointValidator()
        cp = CheckpointSnapshot(
            session_id="s1",
            metadata=None,
        )
        cp = cp.with_hash()
        with pytest.raises(CheckpointIntegrityError):
            validator.validate(cp, "s1")


class TestValidateSessionMatch:
    def test_matching_session(self):
        validator = CheckpointValidator()
        cp = make_valid_checkpoint()
        result = validator.validate_session_match(cp, "s1")
        assert result == cp

    def test_mismatching_session(self):
        validator = CheckpointValidator()
        cp = make_valid_checkpoint()
        with pytest.raises(CheckpointSessionMismatchError):
            validator.validate_session_match(cp, "wrong")


class TestValidateSnapshotMatch:
    def test_matching_snapshot(self):
        validator = CheckpointValidator()
        cp = make_valid_checkpoint()
        result = validator.validate_snapshot_match(cp, cp.snapshot_id)
        assert result == cp

    def test_mismatching_snapshot(self):
        validator = CheckpointValidator()
        cp = make_valid_checkpoint()
        with pytest.raises(CheckpointSnapshotMismatchError) as exc:
            validator.validate_snapshot_match(cp, "other-snap")
        assert cp.snapshot_id in str(exc.value)
        assert "other-snap" in str(exc.value)


class TestValidateChain:
    def test_empty_chain(self):
        validator = CheckpointValidator()
        assert validator.validate_chain([]) is True

    def test_valid_chain(self):
        validator = CheckpointValidator()
        cps = [make_valid_checkpoint() for _ in range(3)]
        assert validator.validate_chain(cps) is True

    def test_chain_with_corrupted(self):
        validator = CheckpointValidator()
        cps = [make_valid_checkpoint() for _ in range(2)]
        bad = CheckpointSnapshot(session_id="s1", state_hash="bad")
        cps.append(bad)
        with pytest.raises(CheckpointIntegrityError):
            validator.validate_chain(cps)


class TestRecoveryValidation:
    def test_validate_before_restore(self):
        validator = CheckpointValidator()
        cp = make_valid_checkpoint()
        result = validator.validate(cp, "s1")
        assert result.state_hash == cp.compute_hash()

    def test_corrupted_hash_recovery_fails(self):
        validator = CheckpointValidator()
        cp = CheckpointSnapshot(
            session_id="s1",
            chunk_index=5,
            state_hash="tampered-hash",
        )
        with pytest.raises(CheckpointIntegrityError):
            validator.validate(cp, "s1")

    def test_session_mismatch_recovery_fails(self):
        validator = CheckpointValidator()
        cp = make_valid_checkpoint()
        with pytest.raises(CheckpointSessionMismatchError):
            validator.validate(cp, "s2")


class TestErrorMessages:
    def test_integrity_error(self):
        err = CheckpointIntegrityError("cp-1")
        assert "cp-1" in str(err)
        assert err.checkpoint_id == "cp-1"

    def test_session_mismatch_error(self):
        err = CheckpointSessionMismatchError("cp-2", "s1", "s2")
        assert "cp-2" in str(err)
        assert "s1" in str(err)
        assert "s2" in str(err)
        assert err.expected_session == "s1"
        assert err.actual_session == "s2"

    def test_snapshot_mismatch_error(self):
        err = CheckpointSnapshotMismatchError("cp-3", "snap-a", "snap-b")
        assert "cp-3" in str(err)
        assert "snap-a" in str(err)
        assert "snap-b" in str(err)
        assert err.expected_snapshot == "snap-a"
        assert err.actual_snapshot == "snap-b"