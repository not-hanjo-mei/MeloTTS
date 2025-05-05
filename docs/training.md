## Training

Before training, please install MeloTTS in dev mode and required dependencies, then go to the `melo` folder. Note: This training process assumes a proper Linux environment. For debugging issues during installation, you may want to check the [deploy_on_android.md](deploy_on_android.md) guide for additional troubleshooting tips.
```bash
pip install -e .
pip install matplotlib==3.5.3
cd melo
```

### Data Preparation
To train a TTS model, we need to prepare the audio files and a metadata file. We recommend using 44100Hz audio files and the metadata file should have the following format:

```
path/to/audio_001.wav |<speaker_name>|<language_code>|<text_001>
path/to/audio_002.wav |<speaker_name>|<language_code>|<text_002>
```
The transcribed text can be obtained by ASR model, (e.g., [whisper](https://github.com/openai/whisper)). An example metadata can be found in `data/example/metadata.list`

We can then run the preprocessing code:
```bash
python preprocess_text.py --metadata data/example/metadata.list 
```
A config file `data/example/config.json` will be generated. Feel free to edit some hyper-parameters in that config file (for example, you may decrease the batch size if you have encountered the CUDA out-of-memory issue).

### Training
The training can be launched by:
```bash
bash train.sh <path/to/config.json> <num_of_gpus>
```

We have found for some machine the training will sometimes crash due to an [issue](https://github.com/pytorch/pytorch/issues/2530) of gloo. Therefore, we add an auto-resume wrapper in the `train.sh`.

### Inference
Simply run:
```
python infer.py --text "<some text here>" -m /path/to/checkpoint/G_<iter>.pth -o <output_dir>
```
