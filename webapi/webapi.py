# Ref:
# https://github.com/Desmond0804/melotts-server
# https://github.com/Ikaros-521/MeloTTS

import os
import json
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

# Custom models configuration
custom_models = {}  # Dictionary to store custom model configurations
custom_model_instances = {}  # Dictionary to store loaded custom model instances

# Path to the models configuration file
MODELS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "models.json")

def load_custom_models():
    """Load custom model configurations from models.json file"""
    global custom_models
    try:
        if os.path.exists(MODELS_CONFIG_PATH):
            with open(MODELS_CONFIG_PATH, 'r') as f:
                config = json.load(f)
                if 'custom_models' in config:
                    # Create a dictionary with model_id as key for easy lookup
                    for model_config in config['custom_models']:
                        model_id = model_config.get('model_id')
                        if model_id:
                            custom_models[model_id] = model_config
                    print(f"Loaded {len(custom_models)} custom model configurations")
        else:
            print(f"Custom models configuration file not found at {MODELS_CONFIG_PATH}")
    except Exception as e:
        print(f"Error loading custom models configuration: {str(e)}")

def get_custom_model(model_id):
    """Get or load a custom model instance based on model_id"""
    global custom_model_instances
    
    # If model is already loaded, return it
    if model_id in custom_model_instances and custom_model_instances[model_id] is not None:
        return custom_model_instances[model_id]
    
    # If model configuration exists, load it
    if model_id in custom_models:
        config = custom_models[model_id]
        try:
            # Create a new TTS instance with the custom configuration
            custom_tts = TTS(
                language=config['language'],
                config_path=config['config_path'],
                ckpt_path=config['ckpt_path'],
                device=device
            )
            custom_model_instances[model_id] = custom_tts
            print(f"Loaded custom model: {model_id}")
            return custom_tts
        except Exception as e:
            print(f"Error loading custom model {model_id}: {str(e)}")
    
    return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    global speaker_ids
    global custom_models
    
    # Load custom model configurations
    load_custom_models()
    
    # load default TTS model
    model = TTS(language="EN", device=device)
    speaker_ids = model.hps.data.spk2id
    yield
    
    # clean up TTS model & release resources
    del model
    
    # Clean up any custom model instances
    global custom_model_instances
    for model_id in custom_model_instances:
        if custom_model_instances[model_id] is not None:
            del custom_model_instances[model_id]

class TTSRequest(BaseModel):
    model: str = Field("tts-1", description="The model to use for text-to-speech, can be a custom model ID from models.json")
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
    # Check if a custom model is requested
    custom_tts = None
    if request.model != "tts-1" and request.model in custom_models:
        custom_tts = get_custom_model(request.model)
        if custom_tts:
            print(f"Using custom model: {request.model}")
    
    # If custom model is requested but config_path and ckpt_path are provided, they take precedence
    if request.config_path and request.ckpt_path:
        try:
            custom_tts = TTS(
                language=request.voice.split('/')[0] if '/' in request.voice else "EN",
                config_path=request.config_path,
                ckpt_path=request.ckpt_path,
                device=device
            )
            print(f"Using custom model with provided config and checkpoint paths")
        except Exception as e:
            print(f"Error loading custom model with provided paths: {str(e)}")
            custom_tts = None

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
    # Format can be "lang/speaker" or just a speaker ID or a custom model name
    text_lang = None
    voice = request.voice
    
    # Check if the voice parameter is a custom model name
    is_custom_voice = voice in custom_models
    
    # Check if voice parameter contains language/speaker format
    if "/" in request.voice:
        parts = request.voice.split("/")
        if len(parts) == 2:
            text_lang = parts[0].lower()
            voice = parts[1]
            # Check if the voice part is a custom model name
            is_custom_voice = voice in custom_models
    
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
    # Skip this check if the voice is a custom model name
    if not is_custom_voice and voice not in speaker_ids:
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
        
        # Check if the voice parameter is a custom model name and load it if needed
        if is_custom_voice and not custom_tts:
            custom_tts = get_custom_model(voice)
            if custom_tts:
                print(f"Using custom model for voice: {voice}")
        
        # Use custom model if available, otherwise use default model
        if custom_tts:
            # For custom models, use the speaker_id from the configuration if available
            if is_custom_voice:
                speaker_id = custom_models.get(voice, {}).get('speaker_id', 0)
            else:
                speaker_id = custom_models.get(request.model, {}).get('speaker_id', 0) if request.model in custom_models else 0
            
            # If using direct config_path and ckpt_path, use the first available speaker
            if request.config_path and request.ckpt_path:
                speaker_id = 0
                
            custom_tts.tts_to_file(
                request.input,
                speaker_id=speaker_id,
                output_path=output_path,
                speed=request.speed,
                format=request.response_format if request.response_format in ["mp3", "flac", "wav"] else "mp3"
            )
        else:
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
