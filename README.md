# Furever Match

Find the right home for every dog, and the right dog for every home.

Furever Match is a bilingual adoption matching app built for rescue teams and adopters who want a warmer, smarter way to make adoption decisions. It turns adopter needs, home context, lifestyle details, and dog profiles into practical match recommendations that are easy to understand and act on.

The app combines a Hebrew-first onboarding flow, a Flask API, Supabase-backed dog and adoption-request data, and a rules-based matching engine with optional LLM-assisted personality reasoning.

## What It Feels Like

An adopter moves through a friendly quiz about their home, schedule, family, other pets, experience, and preferences. Behind the scenes, Furever Match filters out unsafe or unsuitable matches, scores the remaining dogs, and presents compatible candidates with clear explanations instead of a flat catalogue.

For rescue teams, the goal is simple: fewer generic applications, better conversations, and matches that respect both the adopter's reality and each dog's needs.

## Why It Matters

Good adoption matching is not just about breed, size, or age. It depends on daily rhythm, energy, training expectations, children, other pets, living space, and personality. Furever Match keeps those signals visible, structured, and explainable.

## Highlights

- Hebrew-first adopter experience with English-normalized backend data
- Lifestyle quiz for home, care routine, activity level, and preferences
- Hard filters for clear incompatibilities like young children or existing pets
- Weighted soft scoring for better-fit recommendations
- Optional LLM reasoning for personality and character alignment
- Supabase integration for dogs, images, and adoption requests
- Lightweight Flask API that also serves the frontend prototype

## Tech Snapshot

- Python, Flask, and Flask-CORS
- Supabase for persistence
- PyYAML-driven matching rules
- Optional Ollama or Gemini-backed LLM analysis
- Static HTML/CSS/JavaScript frontend
- `uv` for repeatable local and CI setup

## Run It Locally

```bash
uv sync --extra dev
uv run python run.py
```

Open `http://localhost:8000`.

Database-backed screens and API routes require:

```bash
SUPABASE_URL=...
SUPABASE_KEY=...
```

To run the test suite:

```bash
uv run python -m pytest
```

## Project Status

This is an early-stage DataHackIL prototype focused on making dog adoption matching more thoughtful, transparent, and inviting. The product direction is intentionally practical: help shelters and adopters reach better first conversations, then better forever matches.
