# KC-001 — Future Cobra Core Vision API Contract

**Status:** Design only. **Not** connected to production Cobra Computer.

## Example request

```json
{
  "model": "cobra-core-vision-dev",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Describe the evidence visible in this image."
        },
        {
          "type": "input_image",
          "image_url": "https://example.invalid/evidence.png"
        }
      ]
    }
  ],
  "max_output_tokens": 512,
  "stream": false
}
```

## Semantics

| Field | Rule |
|-------|------|
| `model` | Versioned ID, e.g. `cobra-core-vision-dev@sha` / checkpoint UUID |
| `input_text` | UTF-8 text parts |
| `input_image` | HTTPS URL, `data:` URL, or vault reference (future) |
| Supported types | JPEG, PNG, WEBP, BMP |
| Max bytes | 8 MiB default (align with KC-001 safety) |
| Max pixels | 20M decoded |
| Max images | 4 (reject above) |
| Multiple images | Ordered; each becomes a visual token block with separators (TBD) |
| Streaming | SSE token deltas; usage in final event |
| Errors | `{ "ok": false, "error": { "code": "...", "message": "..." } }` |
| Usage | `input_tokens`, `output_tokens`, `image_tokens`, `cost_usd` |
| Safety metadata | `moderation` flags; no EXIF execution |
| Evidence citations | Optional `citations[]` pointing to vault object IDs when available |

## Error codes (initial)

- `image_too_large`  
- `image_malformed`  
- `unsupported_mime`  
- `too_many_images`  
- `context_overflow`  
- `model_unavailable`  
- `timeout`

## Non-goals for KC-001

- No production route registration  
- No billing hooks live  
- No user-facing model picker entry  
