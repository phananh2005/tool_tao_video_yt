# TubeChain

TubeChain is a local-first tool for managing a YouTube video-production workflow. The current app uses **Python and FastAPI**, stores structured project data in **SQLite**, serves a local web UI from `web/`, and uses **FFmpeg** for basic video assembly.

## Pipeline

1. **Idea Engine** — brainstorm, deduplication, and Rabbit Hole planning.
2. **Script Generator** — structured script content and timing.
3. **Voiceover Writer** — spoken-text generation.
4. **Scene Illustrator** — scene breakdown and image prompts/assets.
5. **Video Assembler** — sequential static-image assembly.
6. **SEO Optimizer** — titles, descriptions, tags, chapters, and thumbnail concepts.

The codebase also contains a **legacy Phase 3.5 voice-synthesis path**. Phase 3 is voiceover text generation; those stages are separate. See `system-description.md` for broader product context and verify described behavior against the implementation.

## Project principles

- Local UI/API and SQLite; no cloud database or deployment.
- Prior-video history uses text/metadata/topics/embeddings, not retained old media.
- Rabbit Hole series are capped at three videos. Dedup policy: `>85%` blocks, `60–85%` warns, `<60%` passes.
- Video assembly is intentionally simple: static images in sequence, without animation or transitions.

## Run locally

The application entry point is `app.py`; it binds the FastAPI server to `127.0.0.1:8000` when run directly:

```bash
python app.py
```

Install the dependencies used by the project in your Python environment before starting it. This repository currently has no root `requirements.txt` or `pyproject.toml`, so dependency installation is not specified here. FFmpeg must be available on `PATH` for video rendering.

Open `http://127.0.0.1:8000` in a browser.

## Tests

Tests are in `tests/` and use pytest. If pytest is installed in the active environment:

```bash
python -m pytest
```

## Development with Claude Code

Project rules and task routing are documented in [`CLAUDE.md`](CLAUDE.md). The optional `youtube-strategist` and `prompt-engineer` subagents support content strategy and prompt quality during development; they are not part of the runtime video pipeline. Other subagents cover architecture, implementation, and independent QA review. Loadable skills live in `.claude/skills/<name>/SKILL.md`; hooks are configured in `.claude/settings.json` and implemented in `.claude/hooks/`. Hooks are defense-in-depth and do not replace review, tests, or normal permission controls.
