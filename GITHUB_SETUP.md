# Pushing This Project to GitHub

This project is not yet a git repository (it was generated as a folder).
Follow these steps to get it onto GitHub.

## 1. Initialize git and make the first commit

```bash
cd customer-support-automation
git init
git add .
git commit -m "Initial commit: AI customer support automation POC"
```

## 2. Create a new repository on GitHub

Go to https://github.com/new and create an empty repository
(e.g. `ai-customer-support-automation`). **Do not** initialize it with a
README, .gitignore, or license — this project already has those.

## 3. Connect and push

```bash
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

## 4. Double-check what got pushed

Your `.env` file (if you created one with real API keys) is excluded by
`.gitignore` and will **not** be pushed — only `.env.example` is committed.
Confirm this on GitHub before sharing the repo link with anyone.

## 5. (Optional) Add a demo video / screenshots

The assignment asks for a demo video or walkthrough and screenshots. A simple
approach:
- Run `uvicorn app.main:app --reload --port 8000`, open `http://localhost:8000`,
  and screen-record yourself submitting 2-3 sample tickets from the dashboard.
- Also record `python scripts/demo.py` running in the terminal for the
  colorized CLI output.
- Upload the video to a hosting service you have access to and link it in the
  README under a "Demo" section, or attach short GIFs/screenshots directly in
  the README (GitHub renders images in Markdown automatically if you commit
  them to a `docs/screenshots/` folder and reference them with relative paths).

## 6. CI

A GitHub Actions workflow (`.github/workflows/ci.yml`) is already included and
will automatically run the test suite and a CLI smoke test on every push —
this shows up as a green checkmark on your repo once pushed, which is a nice
signal of production-readiness for reviewers.
