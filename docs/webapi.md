# MeloTTS Web API

[This fork](https://github.com/not-hanjo-mei/MeloTTS) of MeloTTS provides an OpenAI-compatible web API for text-to-speech conversion, allowing you to use MeloTTS with the OpenAI Python SDK or any other client that supports the OpenAI API format.

## Starting the Web API Server

To start the web API server, run the following command from the MeloTTS root directory:

```bash
python webapi/webapi.py
```

This will start the server on port 18000 by default. You can access a simple API documentation at `http://localhost:18000/docs`.

## API Endpoint

The API implements the OpenAI-compatible endpoint for text-to-speech:

```
POST /v1/audio/speech
```

### Request Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|--------|
| `model` | string | The model to use for text-to-speech, currently does nothing | `"tts-1"` |
| `input` | string | The text to convert to speech | Required |
| `voice` | string | The voice to use, format can be `"lang/speaker"` or just a speaker ID | `"EN/EN-Default"` |
| `response_format` | string | The format of the response (mp3, flac, wav) | `"mp3"` |
| `speed` | float | The speed of the speech | `1.0` |

### Voice Format

The `voice` parameter can be specified in two formats:

1. `"language/speaker"` - e.g., `"EN/EN-Default"`, `"ZH/ZH"`, etc.
2. Just the speaker ID - e.g., `"EN-Default"`, `"ZH"`, etc.

If only the speaker ID is provided, the language will be auto-detected from the input text.

### Supported Languages and Voices

The API supports the following languages and voices:

- English (EN): `EN-Default`, `EN-US`, `EN-BR`, `EN_INDIA`, `EN-AU`
- Spanish (ES): `ES`
- French (FR): `FR`
- Chinese (ZH): `ZH` (supports mixed Chinese and English)
- Japanese (JP): `JP`
- Korean (KR): `KR`

## Example Usage with OpenAI Python SDK

You can use the MeloTTS web API with the OpenAI Python SDK as follows:

```python
# You might want run this file in other environment with the OpenAI Python SDK

from pathlib import Path
import openai

client = openai.OpenAI(api_key="sk-xxx", base_url="http://localhost:18000/v1")

speech_file_path = Path(__file__).parent / "speech.mp3"

with client.audio.speech.with_streaming_response.create(
  model="tts-1",
  voice="",
  input="Dirty deeds done dirt cheap.",
) as response:
  response.stream_to_file(speech_file_path)
```

## Language Auto-detection

The API includes automatic language detection. If the language is not specified in the `voice` parameter, it will be detected from the input text. If the detected language doesn't match the specified language, the API will use the appropriate model for the detected language.

## Error Handling

If an error occurs during speech generation, the API will return a 500 error with details about the error.

## Notes

- The API automatically selects the appropriate hardware (CPU/GPU) for inference.
- Temporary files are automatically cleaned up after streaming.
- For best performance, specify the language in the `voice` parameter.
