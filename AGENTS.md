# Repository Guidelines

## Project Structure & Module Organization

```
vids/
├── app.py                  # Flask web server (entry point)
├── main_tk.py              # Tkinter GUI client (alternative entry point)
├── models.py               # Pydantic & SQLAlchemy models
├── utils.py                # DB helper functions (get/set settings)
├── api_tests.http          # HTTP request examples for manual testing
├── shell.nix               # Nix shell with Python dependencies
├── services/
│   └── chaturbate.py       # Chaturbate API client (fetch rooms)
├── utils/
│   └── yt.py               # yt-dlp wrapper for stream URL extraction
├── templates/
│   ├── layout.html         # Jinja2 base layout + menu/filter UI
│   └── video_gallery.html  # Gallery view (extends layout)
├── static/
│   ├── css/styles.css
│   ├── js/script.js
│   └── favicon.ico
└── instance/                # SQLite DB (gitignored)
```

- **Source code** lives at the repo root (`app.py`, `main_tk.py`, `models.py`) and in `services/` and `utils/` packages.
- **Assets** (CSS, JS, favicon) are under `static/`.
- **Templates** use Jinja2 inheritance via `layout.html`.

## Build, Test, and Development Commands

There is no build step. The project runs directly with Python 3.

```bash
# Flask web UI (http://127.0.0.1:5001)
python app.py

# Tkinter desktop GUI
python main_tk.py

# Nix shell (installs all dependencies)
nix-shell

# Manual API testing (VS Code REST Client)
# Open api_tests.http and click "Send Request"
```

Dependencies: `flask`, `flask-sqlalchemy`, `yt-dlp`, `cloudscraper`, `httpx`, `pydantic`, `pillow`, `tkinter`.

## Coding Style & Naming Conventions

- **Language:** Python 3.12+.
- **Indentation:** 4 spaces per level.
- **Naming:** `snake_case` for functions, variables, and modules; `PascalCase` for classes and Pydantic models.
- **Imports:** Standard library first, third-party second, local modules third — separated by blank lines.
- **Comments:** Inline and block comments are in French.
- **No linter or formatter** is currently configured. Prefer clean, readable code with descriptive names.

## Testing Guidelines

There is no test framework or test suite currently set up. Tests are performed manually:

- Run `python app.py` or `python main_tk.py` and verify the UI loads.
- Use `api_tests.http` to manually exercise the Chaturbate API endpoint.

> **Contributors:** Adding `pytest` tests for `services/chaturbate.py` and `models.py` would be a welcome improvement.

## Commit & Pull Request Guidelines

Commit messages are currently informal (mostly French, single lines). There is no strict convention in place.

**Suggested convention for future contributions:**

- Use **English** for commit messages.
- Prefix commits with a category when relevant: `feat:`, `fix:`, `refactor:`, `chore:`.
- Keep the subject line under 72 characters.

**Pull request expectations:**

- Describe what the change does and why.
- Reference any related issues.
- Screenshots are helpful for UI changes.

## Security & Configuration Tips

- Secrets (API keys, tokens) must **never** be committed. Add them to `.env` and gitignore it.
- The `instance/` directory (SQLite DB) is gitignored — do not track it manually.
- User-Agent headers in `services/chaturbate.py` should be kept up to date to avoid blocking.
