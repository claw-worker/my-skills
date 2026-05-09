---
name: gpt-imagegen
description: Generate and edit images with gpt-image-2 through a unified Python raw-HTTP CLI. Use when Codex needs OpenAI-compatible image generation, image-to-image editing, /v1/images/generations, /v1/images/edits, optional /v1/responses image_generation tool support, fixed in-script API key/base URL defaults, retry handling, and reproducible request/response JSON artifacts.
---

# GPT ImageGen

## Overview

Use `scripts/generate-image-unified.py` as the primary workflow for image generation and image editing through the configured OpenAI-compatible `gpt-image-2` endpoint.

Important defaults live at the top of the script:

- `OPENAI_API_KEY`
- `BASE_URL`

The script does not read API credentials from environment variables. It still accepts `-ApiKey` and `-BaseUrl` for explicit one-off overrides.

## Workflow

1. Choose an output path under this skill, usually `skills/gpt-imagegen/output/<name>.png`, unless the user gives a path.
2. Use `-Prompt` for short prompts or `-PromptFile` for longer prompts.
3. For text-to-image, omit `-Image`; the script uses `POST /v1/images/generations`.
4. For image-to-image editing, pass one or more `-Image` values; the script uses `POST /v1/images/edits`.
5. Use `-Mode responses` only when the user explicitly asks to test or use the Responses API path.
6. Let the script write `<name>-request.json` and `<name>-response.json` beside the image.
7. Report the image path and the artifact paths.

## Examples

Text-to-image:

```text
python scripts/generate-image-unified.py -Prompt "2K horizontal cyberpunk city wallpaper, high detail, no text" -OutFile output/cyberpunk-city-2k.png -Size 2048x1152 -Quality high -OutputFormat png -Background opaque -Force
```

Image-to-image edit:

```text
python scripts/generate-image-unified.py -Prompt "Keep the subject, replace the background with a rainy neon city street at night." -Image output/source.png -OutFile output/edited.png -Size 2048x1152 -Quality high -OutputFormat png -Background opaque -Force
```

Responses API path:

```text
python scripts/generate-image-unified.py -Mode responses -Prompt "Generate a cinematic anime sci-fi wallpaper." -OutFile output/responses-scene.png -Size 2048x1152 -Quality high -OutputFormat png -Force
```

## Script Behavior

- Text-to-image sends JSON to `/images/generations` and requests `response_format: b64_json`.
- Image-to-image sends multipart form data to `/images/edits` with `image[]` fields and optional `-Mask`.
- Responses mode sends JSON to `/responses` with an `image_generation` tool and embeds local images as data URLs.
- Retry covers network errors and HTTP `408`, `409`, `429`, `500`, `502`, `503`, and `504`.
- If `-N` is greater than 1, additional files are written as `<stem>-2.png`, `<stem>-3.png`, and so on.

Useful flags:

- `-Size`: use `auto` or dimensions such as `2048x1152`.
- `-Quality`: usually `auto`, `medium`, or `high`, depending on endpoint support.
- `-OutputFormat`: usually `png`.
- `-Background`: use `auto` or `opaque`; `gpt-image-2` rejects `transparent`.
- `-ResponseFormat`: default `b64_json` for `/images/generations`.
- `-MaxAttempts` and `-Timeout`: tune retry behavior for unstable networks.
- `-Force`: overwrite existing output and artifact files.

## Notes

- Prefer this skill for new `gpt-image-2` work that needs both text-to-image and image-to-image.
- Keep generated images and artifacts in `output/`; create the directory as needed.
- Do not paste API keys in chat. Update the script constants locally when needed.
