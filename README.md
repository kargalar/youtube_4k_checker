# YouTube 4K Checker

Desktop GUI to check which videos in a YouTube playlist have 4K, and optionally remove them from your own playlists (with OAuth2).

## Setup

1) Create a virtual environment and install requirements.
2) Copy `.env.example` to `.env` and set `YOUTUBE_API_KEY`.
3) Place your `client_secret.json` locally (not committed). First login will create `token.pickle`.

## Secrets

- `.gitignore` excludes `.env`, `client_secret.json`, and `token.pickle`.
- The app reads `YOUTUBE_API_KEY` from environment.
- You can override paths via `CLIENT_SECRETS_FILE` and `TOKEN_FILE` env vars.

## Build (PyInstaller)

A `youtube_4k_checker.spec` is included. When packaging, ensure your runtime has access to env variables or embed a safe config mechanism.
