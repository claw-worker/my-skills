---
name: ciii-responses-imagegen
description: Generate images through the custom OpenAI-compatible Responses endpoint at https://codex.ciii.club/v1/responses using top-level model gpt-5.4 and the image_generation tool with gpt-image-2. Use when Codex needs a deterministic Python CLI workflow, explicit request and response JSON artifacts, or the user explicitly asks to use this endpoint/API path instead of the built-in image tool.
---

# CIII Responses ImageGen

## Overview

Use the bundled Python scripts to turn a text prompt into a saved image through the validated `POST /v1/responses` flow. Prefer this skill when the user wants the custom endpoint, the exact `gpt-5.4` + `image_generation` + `gpt-image-2` path, or reproducible request/response files.

For normal image generation, **prefer `scripts/generate-image-sdk.py`**. Use `scripts/generate-image.py` only as a raw-HTTP fallback when the SDK script is unavailable/incompatible, or when the user explicitly asks for the non-SDK path.

The validated request body shape is:

```json
{
  "model": "gpt-5.4",
  "input": "<prompt text>",
  "tools": [
    {
      "type": "image_generation",
      "model": "gpt-image-2",
      "action": "generate",
      "size": "1536x1024",
      "quality": "high",
      "output_format": "png",
      "background": "opaque"
    }
  ],
  "tool_choice": "required"
}
```

## API Key Storage

Store `OPENAI_API_KEY` in the workspace `.env` file so shell runs can load it without relying on `.bashrc`:

```bash
/home/ubuntu/.zeroclaw/workspace/.env
```

Expected format:

```bash
OPENAI_API_KEY="sk-..."
```

Set restrictive permissions after creating/updating it:

```bash
chmod 600 /home/ubuntu/.zeroclaw/workspace/.env
```

Before running generation from shell, load the file like this:

```bash
set -a
[ -f /home/ubuntu/.zeroclaw/workspace/.env ] && source /home/ubuntu/.zeroclaw/workspace/.env
set +a
```

Never print, echo, log, or include secret values such as `OPENAI_API_KEY` in user-visible output or request artifacts beyond normal Authorization headers handled internally by the scripts.

## Workflow

1. Read the user's prompt and choose an output path in the workspace.
2. Ensure `OPENAI_API_KEY` is available from the process environment. For shell runs, load `/home/ubuntu/.zeroclaw/workspace/.env` first if present.
3. Prefer `scripts/generate-image-sdk.py` for generation.
4. Pass the prompt with `-Prompt` for short text or `-PromptFile` for multiline prompts.
5. Let the script write `<name>-request.json` and `<name>-response.json` beside the final image unless the user asks for different paths.
6. Report the final image path and keep the JSON artifacts when they help debugging or reproducibility.
7. If `generate-image-sdk.py` is unavailable or incompatible, fall back to `scripts/generate-image.py` using the same prompt/output arguments.

## Script

Run the preferred SDK script like this:

```bash
set -a
[ -f /home/ubuntu/.zeroclaw/workspace/.env ] && source /home/ubuntu/.zeroclaw/workspace/.env
set +a

python3 skills/ciii-responses-imagegen/scripts/generate-image-sdk.py \
  -PromptFile output/prompt.txt \
  -OutFile output/scene.png \
  -Force
```

If `python3` is not on PATH, try:

```bash
python skills/ciii-responses-imagegen/scripts/generate-image-sdk.py \
  -PromptFile output/prompt.txt \
  -OutFile output/scene.png \
  -Force
```

Raw-HTTP fallback:

```bash
python3 skills/ciii-responses-imagegen/scripts/generate-image.py \
  -PromptFile output/prompt.txt \
  -OutFile output/scene.png \
  -Force
```

PowerShell equivalent for Windows-style runs:

```powershell
python .\scripts\generate-image-sdk.py `
  -PromptFile .\prompt.txt `
  -OutFile .\output\scene.png `
  -Force
```

If `python` is not on PATH in PowerShell, try:

```powershell
py -3 .\scripts\generate-image-sdk.py `
  -PromptFile .\prompt.txt `
  -OutFile .\output\scene.png `
  -Force
```

Important defaults:

- Endpoint: `https://codex.ciii.club/v1/responses`
- Top-level model: `gpt-5.4`
- Image tool model: `gpt-image-2`
- Action: `generate`
- Tool choice: `required`
- Size: `1536x1024`
- Quality: `high`
- Output format: `png`
- Background: `opaque`

Useful flags:

- `-ApiKey` overrides `OPENAI_API_KEY`
- `OPENAI_API_KEY` should come from the current process env; for this workspace, prefer loading `/home/ubuntu/.zeroclaw/workspace/.env`
- `-Size`, `-Quality`, `-OutputFormat`, and `-Background` override image settings
- `-TextModel`, `-ImageModel`, and `-ToolChoice` override the validated request body fields
- `-RequestFile` and `-ResponseFile` change where JSON artifacts are saved
- `-Force` allows overwriting existing outputs

## Notes

- Prefer `generate-image-sdk.py` for all normal image generation.
- Use `generate-image.py` only as the non-SDK/raw-HTTP fallback.
- Do not print API keys or secret-bearing environment variables.
- Store `OPENAI_API_KEY` in `/home/ubuntu/.zeroclaw/workspace/.env` and load it before shell runs.
- Write request JSON as UTF-8 without BOM. This is required for this endpoint in this Windows environment; BOM can cause `Failed to parse request body`.
- Keep the request payload aligned with the validated structure above unless the user explicitly asks for a deliberate change.
- Keep this skill narrow. It currently bundles the validated text-to-image flow only.
- If the user asks for image editing, reuse the same endpoint family only after rebuilding the payload around `input_image` content and validating the response shape.

## Resources

### scripts/

- `generate-image-sdk.py` performs the validated request flow through the OpenAI Python SDK, saves the JSON request and response, extracts `image_generation_call.result`, and writes the final image file.
- `generate-image.py` performs the same validated request flow through the non-SDK/raw-HTTP path and is the fallback option.
