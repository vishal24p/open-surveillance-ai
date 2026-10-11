# Evidence Preservation Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove a fresh recorder preserves existing evidence and allocates folder `2` when `1` exists.

**Architecture:** Add one unittest beside existing evidence tests. Reuse FakeVideoWriter and a temporary directory; production behavior already works.

**Tech Stack:** Python 3.11, unittest, NumPy, existing OpenCV dependency.

**Spec:** User-approved review annotation 1 in this chat; MILESTONES.md Milestone 1.

## Global Constraints

- Keep unrelated files and user changes untouched.
- No runtime changes or new dependencies.
- Callers, fixtures, configuration, and exports need no changes.

## Review Focus

Existing video and JSON must survive recorder startup and shutdown. The writer and new metadata must target folder `2`.

### Task 1: Preserve evidence after restart

**Files:** Modify and test `tests/test_evidence.py`.
**Interfaces:** Consume existing EvidenceRecorder, ConfirmedIncident, and FakeVideoWriter; produce one unittest.

- [x] Seed `1/incident.mp4` and `1/incident.json`, start a fresh recorder, close it, and assert folder `2`, writer path, new JSON, and unchanged old files.
- [x] Run evidence tests; all 9 pass.
- [x] Disable collision skipping in memory only; new test fails on folder `1` versus `2` as expected.
- [x] Run full unittest suite and `git diff --check`; 37 tests pass, whitespace check clean.
- [x] Read-only subagent review found no defects. Changes left uncommitted for user review.
