# CODEX_INSTRUCTIONS.md

# ProcDocOrganizer - Instructions for Coding Agents

These instructions apply to every implementation task.

Read this file before making any code changes.

---

# Primary Goal

Your objective is to improve the existing application incrementally.

Do NOT redesign the project.

Do NOT replace the architecture.

Do NOT rewrite working code unless explicitly requested.

---

# Development Philosophy

Always evolve the existing codebase.

Small improvements are preferred over large refactorings.

Keep the application functional after every change.

Every completed task must leave the repository in a compilable and runnable state.

---

# Read Before Coding

Always review:

- docs/architecture_guidelines.md
- docs/SPRINTS.md

If there is a conflict between the sprint and architecture, follow the architecture.

---

# Scope Control

Implement ONLY the current sprint.

Do not implement planned future features.

Do not anticipate future requirements.

Avoid speculative development.

---

# Existing Architecture

Current layers:

MainWindow
    ↓
ProjectController
    ↓
Repositories
    ↓
Models

Respect this architecture.

Do not bypass controllers.

Business logic belongs in controllers or services.

Repositories only persist data.

Models should remain independent from the UI.

---

# Code Quality

Prefer small methods.

Prefer readable code.

Avoid duplication.

Avoid unnecessary abstractions.

Avoid unnecessary inheritance.

Avoid deeply nested code.

Avoid global variables.

Prefer dataclasses where appropriate.

Follow existing naming conventions.

---

# Backward Compatibility

Do not break existing projects.

Do not change project file formats unless required.

If persistence changes, maintain backward compatibility whenever possible.

Never remove existing fields without migration.

---

# File Changes

Modify only the files required.

Avoid touching unrelated files.

Do not reformat the entire repository.

Keep diffs as small as possible.

---

# Refactoring Rules

Allowed:

- rename local variables
- extract methods
- simplify code
- improve readability

Not allowed unless explicitly requested:

- rewrite entire modules
- replace architecture
- move large groups of files
- introduce new frameworks

---

# UI Rules

Keep the interface simple.

Avoid unnecessary dialogs.

Preserve current navigation.

Do not redesign the UI unless the sprint requires it.

---

# Error Handling

Prefer explicit exceptions.

Avoid silent failures.

Display meaningful error messages to the user.

Never swallow exceptions without logging.

---

# Logging

Preserve existing logging.

Add logs only when they provide useful diagnostic information.

Avoid excessive logging.

---

# Dependencies

Do not introduce new external dependencies unless absolutely necessary.

Reuse existing libraries whenever possible.

---

# Performance

Prefer efficient algorithms.

Avoid reading the same PDF multiple times.

Avoid unnecessary disk writes.

Cache expensive operations when appropriate.

---

# Documentation

Whenever a public API changes:

- update documentation
- update comments when necessary

Do not add redundant comments.

Good code should explain itself.

---

# Testing

Before finishing a task:

- ensure the project compiles
- ensure imports work
- ensure no obvious regressions were introduced

If tests exist, keep them passing.

---

# Completion Report

After every implementation, provide a concise report with:

## Files Modified

- file1
- file2

## Summary

Describe what was implemented.

## Architecture

Explain whether any architectural decision changed.

## Compatibility

State whether backward compatibility was preserved.

## Remaining Tasks

List unfinished items from the current sprint.

---

# When Unsure

If implementation details are unclear:

Prefer preserving the existing architecture.

Never invent large features.

Never redesign the project.

Choose the smallest solution that satisfies the sprint.

---

# Guiding Principle

The goal is not to produce the most sophisticated code.

The goal is to produce maintainable, stable, incremental software that evolves one sprint at a time while preserving the existing architecture.