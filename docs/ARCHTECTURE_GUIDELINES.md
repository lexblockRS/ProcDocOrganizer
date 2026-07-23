# ProcDocOrganizer - Architecture Guidelines

## Project Purpose

ProcDocOrganizer is a desktop application that helps organize documentary evidence to support the preparation of an RSC (Reconhecimento de Saberes e Competências) Memorial.

The software is NOT intended to automatically write the memorial.

Its purpose is to:

- organize documents;
- extract information from PDFs;
- build a reliable knowledge base;
- assist the user during memorial preparation.

AI is an optional assistant.

---

# Development Philosophy

Always evolve the existing architecture.

Never rewrite large portions of the project without necessity.

Small, incremental improvements are preferred.

The application must remain functional after every sprint.

---

# Architecture

Current layers:

MainWindow
    ↓
ProjectController
    ↓
Repositories
    ↓
Models

Business rules belong in controllers and services.

The UI must remain as thin as possible.

Models should not depend on the UI.

Repositories should only persist data.

---

# Current Domain

Project

contains

Documents

Later versions will introduce:

- Suggestions
- Timeline
- Memorial Export

Do not implement these until planned.

---

# Documents

Documents are the central entity of the system.

Each document should eventually contain:

- name
- relative_path
- imported_at
- pages
- sha256
- status

Documents are immutable after import except for metadata.

---

# AI Integration

AI is optional.

The application must work perfectly without any AI provider.

Future providers:

- OpenAI
- Gemini
- Claude
- Ollama

AI never modifies project data directly.

AI only generates suggestions.

The user always confirms.

---

# Coding Principles

Prefer composition over duplication.

Keep methods small.

Avoid large classes.

Avoid unnecessary inheritance.

Avoid global state.

Use dataclasses where appropriate.

---

# UI Principles

The interface should remain simple.

Avoid modal dialogs whenever possible.

Prefer progressive disclosure.

The user should always understand:

- what is happening;
- what is being processed;
- what remains to be done.

---

# Project Rules

Never break compatibility with existing projects.

Never remove existing functionality without replacement.

Prefer extending existing classes instead of replacing them.

Keep persistence backwards compatible whenever possible.

---

# Sprint Rules

Each sprint must:

- compile successfully;
- preserve existing features;
- include basic testing;
- leave the repository in a runnable state.

No sprint should depend on unfinished code.

---

# Long-Term Vision

Workflow:

Project

↓

Import Documents

↓

Process Documents

↓

Generate Suggestions

↓

User Review

↓

Timeline

↓

Export Material for RSC Memorial