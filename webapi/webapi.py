# Ref:
# https://github.com/Desmond0804/melotts-server
# https://github.com/Ikaros-521/MeloTTS

import os
import tempfile
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from melo.api import TTS
from py3langid import classify


DEFAULT_EN_VOICE = "EN-Default"

# Voice configuration
TTS_VOICE = "tts-1"  # Default voice ID matching the model field default

# Device configuration for model inference
device = "auto"  # Automatically selects available hardware (CPU/GPU)
model = None     # Global model instance placeholder

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    global speaker_ids
    # load TTS model
    model = TTS(language="EN", device=device)
    speaker_ids = model.hps.data.spk2id
    yield
    # clean up TTS model & release resources
    del model

class TTSRequest(BaseModel):
    model: str = Field("tts-1", description="The model to use for text-to-speech")
    input: str = Field("The text to convert to speech", description="The text to convert to speech")
    voice: str = Field("EN/EN-Default", description="The voice to use for text-to-speech")
    instructions: str = Field(None, description="The instructions for the voice, this thing is not working yet")
    response_format: str = Field("mp3", description="The format of the response")
    speed: float = Field(1.0, description="The speed of the speech")
    config_path: str = Field(None, description="The path to the config file", example="melo/logs/example/config.json")
    ckpt_path: str = Field(None, description="The path to the checkpoint file", example="melo/logs/example/G_69420.pth")

app = FastAPI(lifespan=lifespan)

@app.post("/v1/audio/speech", response_class=StreamingResponse)
async def generate_speech(request: TTSRequest):

    response_format = request.response_format
    # Set the Content-Type header based on the requested format
    if response_format == "mp3":
        media_type = "audio/mpeg"
    elif response_format == "flac":
        media_type = "audio/flac"
    elif response_format == "wav":
        media_type = "audio/wav"
    else:
        media_type = "audio/mpeg"
        print(f"Invalid response format: {response_format}. Using default format: mp3")

    # Parse voice parameter for language/speaker selection
    # Format can be "lang/speaker" or just a speaker ID
    text_lang = None
    voice = request.voice
    
    # Check if voice parameter contains language/speaker format
    if "/" in request.voice:
        parts = request.voice.split("/")
        if len(parts) == 2:
            text_lang = parts[0].lower()
            voice = parts[1]
    
    # If language not specified in voice parameter, auto-detect from input text
    detected_lang = None
    if text_lang is None:
        try:
            # Auto-detect language using classify
            detected_lang, confidence = classify(request.input)
            text_lang = detected_lang
            print(f"Auto-detected language: {text_lang} (confidence: {confidence})")
        except Exception as e:
            # Fallback to default language if auto-detection fails
            text_lang = "en"
            print(f"Language detection failed: {str(e)}. Using default language.")
    else:
        # Store the detected language for later comparison
        try:
            detected_lang, confidence = classify(request.input)
            print(f"User specified language: {text_lang}, detected language: {detected_lang} (confidence: {confidence})")
        except Exception as e:
            print(f"Language detection failed: {str(e)}. Using specified language.")
    
    # Normalize language code
    if text_lang == "en" or text_lang == "es" or text_lang == "fr" or text_lang == "zh":
        text_lang = text_lang.upper()
    elif text_lang == "ja":
        text_lang = "JP"
    elif text_lang == "ko":
        text_lang = "KR"
    else:
        # Fallback for unsupported languages
        text_lang = "EN"
        
    # Special condition: If text is in Chinese but language is specified as English, force Chinese model
    if detected_lang == "zh" and text_lang == "EN":
        print(f"Text detected as Chinese but language specified as English. Forcing Chinese model.")
        text_lang = "ZH"
    
    # Set default voice based on language if not specified
    if voice == TTS_VOICE or voice == text_lang:
        voice = text_lang
        if text_lang == "EN":
            voice = DEFAULT_EN_VOICE

    global model
    global speaker_ids
    # Reload model if language changed
    current_model_lang = model.language.split('_')[0]
    if text_lang != current_model_lang:
        try:
            model = TTS(language=text_lang, device=device)
            speaker_ids = model.hps.data.spk2id
            print(f"Model reloaded for language: {text_lang}")
        except Exception as e:
            # If loading the model for detected language fails, fallback to current model
            print(f"Failed to load model for {text_lang}: {str(e)}. Using current model.")
            # Reset voice to default if it's not available
            if voice not in speaker_ids:
                # 
                if text_lang == "EN" and current_model_lang in ["ZH", "ZH_MIX_EN"]:
                    voice = "ZH"
                else:
                    voice = current_model_lang
                    if current_model_lang == "EN":
                        voice = DEFAULT_EN_VOICE

    # Ensure the voice exists in the available speaker IDs after model loading
    if voice not in speaker_ids:
        print(f"Voice '{voice}' not found in available speakers. Available speakers: {list(speaker_ids.keys())}")
        # Fallback to default voice for the current language
        voice = model.language.split('_')[0]
        # Special handling for Chinese text forced to use Chinese model
        if detected_lang == "zh" and text_lang == "ZH":
            voice = "ZH"
        elif voice == "EN":
            voice = DEFAULT_EN_VOICE
        # If still not found, use the first available speaker
        if voice not in speaker_ids:
            voice = list(speaker_ids.keys())[0]
        print(f"Using fallback voice: {voice}")
    
    # Generate speech & save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{request.response_format}") as tmp:
        output_path = tmp.name
        print(f"Generating speech with: Language={text_lang}, Voice={voice}, Speed={request.speed}")
        model.tts_to_file(
            request.input, 
            speaker_id=speaker_ids[voice], 
            output_path=output_path, 
            speed=request.speed,
            format=request.response_format if request.response_format in ["mp3", "flac", "wav"] else "mp3"
        )
    
    # Alternative implementation with error handling and cleanup
    try:
        def generate():
            with open(output_path, mode="rb") as audio_file:
                yield from audio_file
            # Perform cleanup of temporary files after streaming
            try:
                os.unlink(output_path)
            except:
                pass

        return StreamingResponse(content=generate(), media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=18000)
    # Access API documentation at {host-ip}:{port}/docs
    # For IPv6 support, use:
    # uvicorn.run(app, host="::", port=18000)
