---
name: ciii-responses-imagegen
description: Generate images through the custom OpenAI-compatible Responses endpoint at https://codex.ciii.club/v1/responses using top-level model gpt-5.4 and the image_generation tool with gpt-image-2. Prefer the bundled OpenAI SDK workflow for deterministic Python CLI generation with explicit request and response JSON artifacts; fall back to the raw HTTP script only when the SDK path is unavailable or the user explicitly asks for it instead of the built-in image tool.
---

# CIII Responses ImageGen

## Overview

Use the bundled Python scripts to turn a text prompt into a saved image through the validated `POST /v1/responses` flow. Use `scripts/generate-image-sdk.py` by default. Fall back to `scripts/generate-image.py` only when the OpenAI SDK path is unavailable in the current environment or the user explicitly asks for the raw HTTP implementation. Prefer this skill when the user wants the custom endpoint, the exact `gpt-5.4` + `image_generation` + `gpt-image-2` path, or reproducible request/response files.

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

## Workflow

1. Read the user's prompt and choose an output path in the workspace.
2. Use `scripts/generate-image-sdk.py` by default.
3. Pass the prompt with `-Prompt` for short text or `-PromptFile` for multiline prompts.
4. Let the script write `<name>-request.json` and `<name>-response.json` beside the final image unless the user asks for different paths.
5. If the SDK script cannot call `client.responses.create(...)`, first try upgrading `openai`; use `scripts/generate-image.py` only as a compatibility fallback.
6. Report the final image path and keep the JSON artifacts when they help debugging or reproducibility.

## Preferred Script

Run the bundled script like this:

```powershell
python .\scripts\generate-image-sdk.py `
  -PromptFile .\prompt.txt `
  -OutFile .\output\scene.png
```

If `python` is not on PATH, try:

```powershell
py -3 .\scripts\generate-image-sdk.py `
  -PromptFile .\prompt.txt `
  -OutFile .\output\scene.png
```

This script uses `openai.OpenAI(...).responses.create(...)` and derives the SDK `base_url` from the configured endpoint.

If the installed SDK is missing Responses API support, upgrade it first:

```powershell
pip install --upgrade openai
```

## Fallback Script

Use the raw HTTP script only when the SDK path is unavailable or when the user explicitly asks for the non-SDK flow:

```powershell
python .\scripts\generate-image.py `
  -PromptFile .\prompt.txt `
  -OutFile .\output\scene.png
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
- `OPENAI_API_KEY` can come from the current process env or Windows User/Machine environment variables
- `-Size`, `-Quality`, `-OutputFormat`, and `-Background` override image settings
- `-TextModel`, `-ImageModel`, and `-ToolChoice` override the validated request body fields
- `-RequestFile` and `-ResponseFile` change where JSON artifacts are saved
- `-Force` allows overwriting existing outputs
- Both bundled scripts accept the same CLI flags so the fallback path stays interchangeable

## Notes

- Prefer `scripts/generate-image-sdk.py` for normal use.
- Write request JSON as UTF-8 without BOM. This is required for this endpoint in this Windows environment; BOM can cause `Failed to parse request body`.
- Keep the request payload aligned with the validated structure above unless the user explicitly asks for a deliberate change.
- Keep this skill narrow. It currently bundles the validated text-to-image flow only.
- If the user asks for image editing, reuse the same endpoint family only after rebuilding the payload around `input_image` content and validating the response shape.

## Resources

### scripts/
`generate-image-sdk.py` is the primary script. It performs the validated request flow through the OpenAI SDK, saves the JSON request and response, extracts `image_generation_call.result`, and writes the final image file.

`generate-image.py` is the compatibility fallback. It performs the same validated request flow through raw HTTP when the SDK path cannot be used.
