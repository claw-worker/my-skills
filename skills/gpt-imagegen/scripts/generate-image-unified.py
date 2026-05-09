#!/usr/bin/env python3
import argparse
import base64
import json
import locale
import mimetypes
import os
import http.client
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

RETRY_STATUSES = {408, 409, 429, 500, 502, 503, 504}
SIZE_PATTERN = re.compile(r"^(\d+)x(\d+)$")
OPENAI_API_KEY = "sk-xxxxx"
BASE_URL = "https://example.com/v1"


def resolve_absolute_path(path_value):
    return os.path.abspath(os.path.expanduser(path_value))


def get_api_key_value(explicit_api_key):
    if explicit_api_key and explicit_api_key.strip():
        return explicit_api_key

    if OPENAI_API_KEY and OPENAI_API_KEY.strip():
        return OPENAI_API_KEY

    raise RuntimeError(
        "OPENAI_API_KEY constant is empty. Set it at the top of this file or pass -ApiKey."
    )


def read_text_file(path):
    data = Path(path).read_bytes()
    encodings = ["utf-8-sig", locale.getpreferredencoding(False) or "utf-8"]
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def get_prompt_text(prompt, prompt_file):
    if prompt and prompt_file:
        raise RuntimeError("Use -Prompt or -PromptFile, not both.")

    if prompt_file:
        prompt_path = resolve_absolute_path(prompt_file)
        if not os.path.exists(prompt_path):
            raise RuntimeError(f"Prompt file not found: {prompt_path}")
        return read_text_file(prompt_path)

    if prompt:
        return prompt

    raise RuntimeError("Missing prompt. Use -Prompt or -PromptFile.")


def ensure_parent_directory(path_value):
    parent = Path(path_value).parent
    parent.mkdir(parents=True, exist_ok=True)


def ensure_writable_target(path_value, force):
    if os.path.exists(path_value) and not force:
        raise RuntimeError(
            f"File already exists: {path_value}. Use -Force to overwrite."
        )


def output_path_for_index(output_path, index):
    output = Path(output_path)
    if index == 0:
        return output
    suffix = output.suffix or ".png"
    return output.parent / f"{output.stem}-{index + 1}{suffix}"


def ensure_writable_output_targets(output_path, count, force):
    for index in range(count):
        ensure_writable_target(str(output_path_for_index(output_path, index)), force)


def write_json_utf8(path_value, payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    Path(path_value).write_text(text, encoding="utf-8", newline="\n")


def normalize_base_url(base_url):
    normalized = base_url.rstrip("/")
    for suffix in ("/images/generations", "/images/edits", "/responses"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    if not normalized:
        raise RuntimeError("Base URL is empty.")
    return normalized


def endpoint_for_mode(base_url, mode):
    if mode == "generate":
        return f"{base_url}/images/generations"
    if mode == "edit":
        return f"{base_url}/images/edits"
    if mode == "responses":
        return f"{base_url}/responses"
    raise RuntimeError(f"Unsupported mode: {mode}")


def validate_size(size):
    if size == "auto":
        return

    match = SIZE_PATTERN.match(size)
    if not match:
        raise RuntimeError(
            'Size must be "auto" or WIDTHxHEIGHT, for example 1024x1024.'
        )

    width = int(match.group(1))
    height = int(match.group(2))
    if width <= 0 or height <= 0:
        raise RuntimeError("Size dimensions must be positive.")
    if width > 3840 or height > 3840:
        raise RuntimeError("Size dimensions must not exceed 3840.")
    if width % 16 != 0 or height % 16 != 0:
        raise RuntimeError("Size dimensions must be multiples of 16.")

    long_side = max(width, height)
    short_side = min(width, height)
    if long_side / short_side > 3:
        raise RuntimeError("Size aspect ratio must not exceed 3:1.")

    pixels = width * height
    if pixels < 655360 or pixels > 8294400:
        raise RuntimeError("Size total pixels must be between 655360 and 8294400.")


def validate_args(args):
    if args.max_attempts < 1:
        raise RuntimeError("MaxAttempts must be at least 1.")
    if args.timeout <= 0:
        raise RuntimeError("Timeout must be greater than 0.")
    if args.n < 1:
        raise RuntimeError("N must be at least 1.")
    if args.output_compression is not None and not 0 <= args.output_compression <= 100:
        raise RuntimeError("OutputCompression must be between 0 and 100.")
    if args.model == "gpt-image-2" and args.background == "transparent":
        raise RuntimeError(
            "gpt-image-2 does not support transparent background. Use -Background auto or opaque."
        )

    validate_size(args.size)

    for image_path in args.images:
        absolute_path = resolve_absolute_path(image_path)
        if not os.path.exists(absolute_path):
            raise RuntimeError(f"Image file not found: {absolute_path}")
        if not os.path.isfile(absolute_path):
            raise RuntimeError(f"Image path is not a file: {absolute_path}")

    if args.mask:
        mask_path = resolve_absolute_path(args.mask)
        if not os.path.exists(mask_path):
            raise RuntimeError(f"Mask file not found: {mask_path}")
        if not os.path.isfile(mask_path):
            raise RuntimeError(f"Mask path is not a file: {mask_path}")


def infer_mode(args):
    if args.mode != "auto":
        mode = args.mode
    elif args.images or args.mask:
        mode = "edit"
    else:
        mode = "generate"

    if mode == "generate" and (args.images or args.mask):
        raise RuntimeError(
            "Generate mode does not accept -Image or -Mask. Use -Mode edit or responses."
        )
    if mode == "edit" and not args.images:
        raise RuntimeError("Edit mode requires at least one -Image.")
    if mode == "responses" and args.mask:
        raise RuntimeError(
            "Responses mode does not support -Mask in this script. Use -Mode edit."
        )
    return mode


def mime_type_for_path(path_value):
    return mimetypes.guess_type(path_value)[0] or "application/octet-stream"


def encode_image_as_data_url(path_value):
    image_path = resolve_absolute_path(path_value)
    mime_type = mime_type_for_path(image_path)
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def add_common_image_options(payload, args, include_n, include_output_format=True):
    payload["size"] = args.size
    payload["quality"] = args.quality
    if include_output_format:
        payload["output_format"] = args.output_format
    if include_n:
        payload["n"] = args.n
    if args.background != "auto":
        payload["background"] = args.background
    if args.output_compression is not None:
        payload["output_compression"] = args.output_compression


def build_generation_payload(args, prompt_text):
    payload = {"model": args.model, "prompt": prompt_text}
    add_common_image_options(payload, args, include_n=True, include_output_format=False)
    payload["response_format"] = args.response_format
    return payload


def build_edit_fields(args, prompt_text):
    fields = {"model": args.model, "prompt": prompt_text}
    add_common_image_options(fields, args, include_n=True)
    return fields


def build_responses_payload(args, prompt_text):
    content = [{"type": "input_text", "text": prompt_text}]

    for image_path in args.images:
        content.append(
            {"type": "input_image", "image_url": encode_image_as_data_url(image_path)}
        )

    tool = {"type": "image_generation", "model": args.model, "action": args.action}
    add_common_image_options(tool, args, include_n=False)

    return {
        "model": args.text_model,
        "input": [{"role": "user", "content": content}],
        "tools": [tool],
        "tool_choice": args.tool_choice,
    }


def json_request_bytes(payload):
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def quote_disposition_value(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_multipart_body(fields, files):
    boundary = f"----codex-imagegen-{uuid.uuid4().hex}"
    chunks = []

    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            f'Content-Disposition: form-data; name="{quote_disposition_value(name)}"\r\n\r\n'.encode(
                "utf-8"
            )
        )
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    for file_item in files:
        field_name = file_item["field_name"]
        file_path = file_item["path"]
        filename = os.path.basename(file_path)
        mime_type = mime_type_for_path(file_path)
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                "Content-Disposition: form-data; "
                f'name="{quote_disposition_value(field_name)}"; '
                f'filename="{quote_disposition_value(filename)}"\r\n'
            ).encode("utf-8")
        )
        chunks.append(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        chunks.append(Path(file_path).read_bytes())
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def build_edit_multipart(args, prompt_text):
    fields = build_edit_fields(args, prompt_text)
    files = []
    for image_path in args.images:
        files.append(
            {"field_name": "image[]", "path": resolve_absolute_path(image_path)}
        )
    if args.mask:
        files.append({"field_name": "mask", "path": resolve_absolute_path(args.mask)})
    return build_multipart_body(fields, files), fields, files


def summarize_file_item(file_item):
    file_path = file_item["path"]
    return {
        "field_name": file_item["field_name"],
        "path": file_path,
        "filename": os.path.basename(file_path),
        "mime_type": mime_type_for_path(file_path),
        "size_bytes": os.path.getsize(file_path),
    }


def write_request_artifact(
    path_value, endpoint, mode, content_type, payload=None, fields=None, files=None
):
    artifact = {
        "endpoint": endpoint,
        "method": "POST",
        "mode": mode,
        "content_type": content_type,
    }
    if payload is not None:
        artifact["payload"] = payload
    if fields is not None:
        artifact["fields"] = fields
    if files is not None:
        artifact["files"] = [summarize_file_item(file_item) for file_item in files]
    write_json_utf8(path_value, artifact)


def write_network_error_response(path_value, message):
    write_json_utf8(
        path_value, {"error": {"type": "network_error", "message": str(message)}}
    )


def post_bytes(
    endpoint, api_key, body, content_type, response_path, timeout, max_attempts
):
    response_body = b""
    status_code = None

    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": content_type,
                "Accept": "application/json",
                "User-Agent": "CodexImageGen/1.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_body = response.read()
                status_code = response.status
        except urllib.error.HTTPError as exc:
            response_body = exc.read()
            status_code = exc.code
        except urllib.error.URLError as exc:
            reason = exc.reason if exc.reason else exc
            if attempt == max_attempts:
                write_network_error_response(response_path, reason)
                raise RuntimeError(
                    f"HTTP request failed after {max_attempts} attempt(s): {reason}. Response artifact: {response_path}"
                ) from exc
            print(f"Attempt {attempt}/{max_attempts} failed: {reason}", file=sys.stderr)
        except (
            http.client.HTTPException,
            TimeoutError,
            ConnectionError,
            OSError,
        ) as exc:
            if attempt == max_attempts:
                write_network_error_response(response_path, exc)
                raise RuntimeError(
                    f"HTTP request failed after {max_attempts} attempt(s): {exc}. Response artifact: {response_path}"
                ) from exc
            print(f"Attempt {attempt}/{max_attempts} failed: {exc}", file=sys.stderr)
        else:
            if status_code not in RETRY_STATUSES:
                break
            preview = response_body.decode("utf-8", errors="replace")[:500].replace(
                "\n", "\\n"
            )
            if attempt == max_attempts:
                break
            print(
                f"Attempt {attempt}/{max_attempts} returned HTTP {status_code}: {preview}",
                file=sys.stderr,
            )

        if status_code in RETRY_STATUSES and attempt == max_attempts:
            break

        if attempt < max_attempts:
            time.sleep(min(2**attempt, 30))

    Path(response_path).write_bytes(response_body)
    return status_code


def load_response_json(response_path):
    try:
        return json.loads(Path(response_path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        preview = (
            Path(response_path)
            .read_text(encoding="utf-8", errors="replace")[:500]
            .replace("\n", "\\n")
        )
        raise RuntimeError(
            f"Failed to parse JSON response: {exc}. Response preview: {preview}"
        ) from exc


def summarize_api_error(response):
    if isinstance(response.get("error"), dict):
        error = response["error"]
        message = error.get("message") or error.get("code") or error
        return json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    if response.get("code") and response.get("message"):
        return json.dumps(
            {"code": response["code"], "message": response["message"]},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return json.dumps(response, ensure_ascii=False, separators=(",", ":"))[:500]


def raise_for_http_or_api_error(status_code, response, response_path):
    if status_code is not None and status_code >= 400:
        summary = summarize_api_error(response)
        raise RuntimeError(
            f"HTTP {status_code}: {summary}. Response artifact: {response_path}"
        )

    if response.get("error"):
        summary = summarize_api_error(response)
        raise RuntimeError(f"API error: {summary}. Response artifact: {response_path}")

    if response.get("code") and response.get("message"):
        summary = summarize_api_error(response)
        raise RuntimeError(f"API error: {summary}. Response artifact: {response_path}")


def extract_images_base64_from_image_api(response):
    images = []
    image_urls = []
    for item in response.get("data") or []:
        if not isinstance(item, dict):
            continue
        if item.get("b64_json"):
            images.append(item["b64_json"])
        elif item.get("url"):
            image_urls.append(item["url"])

    if images:
        return images
    if image_urls:
        raise RuntimeError(
            "Response returned image URL(s) instead of b64_json. Use a gpt-image model that returns b64_json."
        )
    raise RuntimeError("No data[].b64_json found in the response.")


def append_response_result(images, result):
    if isinstance(result, str) and result:
        images.append(result)
    elif isinstance(result, list):
        for item in result:
            append_response_result(images, item)
    elif isinstance(result, dict):
        if result.get("b64_json"):
            images.append(result["b64_json"])
        elif result.get("image_base64"):
            images.append(result["image_base64"])


def extract_images_base64_from_responses(response):
    images = []
    for item in response.get("output") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "image_generation_call":
            append_response_result(images, item.get("result"))

    if images:
        return images
    raise RuntimeError("No image_generation_call.result found in the response.")


def write_output_images(output_path, image_base64_values):
    written_paths = []

    for index, image_base64 in enumerate(image_base64_values):
        target_path = output_path_for_index(output_path, index)
        image_bytes = base64.b64decode(image_base64)
        target_path.write_bytes(image_bytes)
        written_paths.append(str(target_path))

    return written_paths


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate or edit images through OpenAI-compatible gpt-image-2 APIs."
    )
    parser.add_argument("-Prompt", "--prompt", dest="prompt")
    parser.add_argument("-PromptFile", "--prompt-file", dest="prompt_file")
    parser.add_argument(
        "-OutFile", "--out-file", dest="out_file", default=".\\output.png"
    )
    parser.add_argument("-BaseUrl", "--base-url", dest="base_url", default=BASE_URL)
    parser.add_argument("-ApiKey", "--api-key", dest="api_key")
    parser.add_argument(
        "-Model",
        "--model",
        "-ImageModel",
        "--image-model",
        dest="model",
        default="gpt-image-2",
    )
    parser.add_argument(
        "-TextModel", "--text-model", dest="text_model", default="gpt-5.5"
    )
    parser.add_argument("-Size", "--size", dest="size", default="auto")
    parser.add_argument("-Quality", "--quality", dest="quality", default="auto")
    parser.add_argument(
        "-OutputFormat", "--output-format", dest="output_format", default="png"
    )
    parser.add_argument(
        "-ResponseFormat",
        "--response-format",
        dest="response_format",
        default="b64_json",
    )
    parser.add_argument(
        "-OutputCompression",
        "--output-compression",
        dest="output_compression",
        type=int,
    )
    parser.add_argument(
        "-Background",
        "--background",
        dest="background",
        default="auto",
        choices=["auto", "opaque", "transparent"],
    )
    parser.add_argument("-N", "--n", dest="n", type=int, default=1)
    parser.add_argument("-Image", "--image", dest="images", action="append", default=[])
    parser.add_argument("-Mask", "--mask", dest="mask")
    parser.add_argument(
        "-Mode",
        "--mode",
        dest="mode",
        default="auto",
        choices=["auto", "generate", "edit", "responses"],
    )
    parser.add_argument("-Action", "--action", dest="action", default="generate")
    parser.add_argument(
        "-ToolChoice", "--tool-choice", dest="tool_choice", default="required"
    )
    parser.add_argument("-RequestFile", "--request-file", dest="request_file")
    parser.add_argument("-ResponseFile", "--response-file", dest="response_file")
    parser.add_argument("-Timeout", "--timeout", dest="timeout", type=int, default=300)
    parser.add_argument(
        "-MaxAttempts", "--max-attempts", dest="max_attempts", type=int, default=5
    )
    parser.add_argument("-Force", "--force", dest="force", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    validate_args(args)
    mode = infer_mode(args)
    api_key = get_api_key_value(args.api_key)
    prompt_text = get_prompt_text(args.prompt, args.prompt_file)
    output_path = resolve_absolute_path(args.out_file)
    ensure_parent_directory(output_path)
    ensure_writable_output_targets(output_path, args.n, args.force)

    output_dir = str(Path(output_path).parent)
    base_name = Path(output_path).stem
    request_path = (
        resolve_absolute_path(args.request_file)
        if args.request_file
        else os.path.join(output_dir, f"{base_name}-request.json")
    )
    response_path = (
        resolve_absolute_path(args.response_file)
        if args.response_file
        else os.path.join(output_dir, f"{base_name}-response.json")
    )

    for path_value in (request_path, response_path):
        ensure_parent_directory(path_value)
        ensure_writable_target(path_value, args.force)

    base_url = normalize_base_url(args.base_url)
    endpoint = endpoint_for_mode(base_url, mode)

    if mode == "generate":
        payload = build_generation_payload(args, prompt_text)
        body = json_request_bytes(payload)
        content_type = "application/json"
        write_request_artifact(
            request_path, endpoint, mode, content_type, payload=payload
        )
    elif mode == "edit":
        (body, content_type), fields, files = build_edit_multipart(args, prompt_text)
        write_request_artifact(
            request_path, endpoint, mode, content_type, fields=fields, files=files
        )
    else:
        payload = build_responses_payload(args, prompt_text)
        body = json_request_bytes(payload)
        content_type = "application/json"
        write_request_artifact(
            request_path, endpoint, mode, content_type, payload=payload
        )

    status_code = post_bytes(
        endpoint,
        api_key,
        body,
        content_type,
        response_path,
        args.timeout,
        args.max_attempts,
    )
    response = load_response_json(response_path)
    raise_for_http_or_api_error(status_code, response, response_path)

    if mode == "responses":
        image_base64_values = extract_images_base64_from_responses(response)
    else:
        image_base64_values = extract_images_base64_from_image_api(response)

    output_files = write_output_images(output_path, image_base64_values)

    result = {
        "output_files": output_files,
        "request_file": request_path,
        "response_file": response_path,
        "endpoint": endpoint,
        "mode": mode,
        "model": args.model,
        "status_code": status_code,
        "image_count": len(output_files),
    }
    if response.get("id"):
        result["response_id"] = response.get("id")
    if response.get("created"):
        result["created"] = response.get("created")
    if response.get("status"):
        result["status"] = response.get("status")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
