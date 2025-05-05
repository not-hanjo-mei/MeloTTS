# Tutorial: Deploying MeloTTS on Android using Termux + proot Debian + Micromamba

MeloTTS is designed to be lightweight and efficient, making it an viable choice for deployment on Android devices.

This guide details how to install and run MeloTTS on an Android device using Termux, a Debian environment managed by `proot-distro`, and Micromamba for isolated Python environment management.

**Disclaimer:** This setup is primarily for experimental purposes, don't use it for production.

## Prerequisites

1. **Android Device:** A reasonably capable Android phone. (recommended to use flagship phones released after 2022)
   - **Important for Android 12+ users:** Before installing Termux, you should disable phantom process killing to prevent background processes from being terminated unexpectedly. This requires either root access or ADB with proper permissions. See the [Troubleshooting section](#troubleshooting-and-tips) for detailed instructions.
2. **Termux App:** Installed on your device. Download the latest release from the [official GitHub repository](https://github.com/termux/termux-app/releases)
3. **Internet Connection**
4. **Storage Space:** Sufficient free space for Termux, Debian rootfs, Micromamba environments, Python dependencies (PyTorch), and MeloTTS source/models
5. **Basic Linux Command Line Familiarity:** Helpful

## Step 1: Install and Prepare Termux

1. **Download and Install Termux:** Go to the [Termux GitHub Releases page](https://github.com/termux/termux-app/releases), download the latest `.apk` file appropriate for your device's architecture (usually `arm64-v8a`), and install it. Enable installation from unknown sources in Android settings if needed.
2. **Open Termux.**
3. **Update and upgrade Termux packages:** Run this command and answer `Y` (yes) to any prompts.
   ```bash
   pkg update && pkg upgrade -y
   ```
4. **Install `proot-distro`, `git`, and `curl`:** `proot-distro` manages Linux distributions, `git` clones repositories, and `curl` downloads files.
   ```bash
   pkg install proot-distro git curl -y
   ```
5. **Grant Storage Access:** Allows Termux/Debian to access your phone's shared storage.
   ```bash
   termux-setup-storage
   ```
   Confirm the permission request from Android. Shared storage is typically at `~/storage/shared/`.

## Step 2: Install Debian Environment

1. **Install Debian using `proot-distro`:** Downloads the Debian filesystem.
   ```bash
   proot-distro install debian
   ```

## Step 3: Enter Debian, Install Micromamba and System Dependencies

1. **Log in to Debian:**
   ```bash
   proot-distro login debian
   ```
   Your prompt should change (e.g., `root@localhost:~#`). **All subsequent commands in Steps 3-5 are run inside this Debian environment unless stated otherwise.**
2. **Update Debian's package list and upgrade packages:**
   ```bash
   apt update && apt upgrade -y
   ```
3. **Install essential build tools and runtime dependencies:**
   ```bash
   yes | apt install build-essential libsndfile1 ffmpeg curl bzip2 git nano mecab libmecab-dev mecab-ipadic-utf8
   ```
4. **Install Micromamba:** Run the official installation script.
   ```bash
   "${SHELL}" <(curl -L micro.mamba.pm/install.sh)
   ```
   *Follow any on-screen instructions. Defaults are usually fine.*
5. **Initialize Shell for Micromamba:** Ensure the `micromamba` command is accessible.
   ```bash
   source ~/.bashrc
   ```
   *(Or exit and re-login to Debian: `exit`, then `proot-distro login debian`)*.
6. **Verify Micromamba Installation:**
   ```bash
   micromamba --version
   ```

## Step 4: Create Micromamba Environment and Install MeloTTS

1. **Create a dedicated environment:** Use Python 3.10.
   ```bash
   micromamba create -n melotts python=3.10 -c conda-forge -y
   ```
2. **Activate the environment:** **Crucial step before proceeding.**
   ```bash
   micromamba activate melotts
   ```
   Your prompt should now be prefixed with `(melotts)`.
3. **Clone the MeloTTS Repository:** Navigate to a suitable directory (e.g., `~/`) and clone the repo.
   ```bash
   # Example: Clone into ~/MeloTTS
   cd ~
   git clone https://github.com/not-hanjo-mei/MeloTTS.git
   ```
4. **Navigate into the Cloned Directory:**
   ```bash
   cd MeloTTS
   ```
5. **Install MeloTTS and Dependencies:**
   ```bash
   pip install -e .
   ```
6. **Download Japanese Dictionary Data (UniDic):**
   ```bash
   python -m unidic download
   ```
7. ***(Optional) Install eunjeon (for Korean support):***
   ```bash
   pip install eunjeon python-mecab-ko python-mecab-ko-dic
   ```
8. **Download NLTK tagger:**
   ```bash
   python -m nltk.downloader averaged_perceptron_tagger_eng
   ```
   If the NLTK download fails, try this alternative method:
   ```bash
   # Ensure you're in the MeloTTS directory and have NLTK installed
   python webapi/nltk_res.py
   ```
## Step 5: Use MeloTTS (Inside Activated Environment)

**IMPORTANT:** Ensure the `melotts` environment is active (`micromamba activate melotts`). Check for the `(melotts)` prefix in your prompt.

**Note:** Example scripts and test resources are available in the `test/` directory of the MeloTTS repository. You can use these files (such as `test_base_model_tts_package.py` and various example text files) to quickly verify your installation or experiment with the TTS functionality. See the contents of the `test/` folder for ready-to-use scripts and sample inputs.

For the latest and most detailed usage instructions (including WebUI, CLI, and Python API), please refer to the **Usage** section in [install.md](./install.md#usage).

This section covers how to:

- Launch and use the WebUI
- Use the command-line interface (CLI) for TTS
- Use the Python API for programmatic access
- Find example scripts and test resources

## Step 6: Accessing Output Files from Android (Inside Debian)

1. **Identify File Location:** Use `pwd` (e.g., `~/MeloTTS/`).
2. **Copy Files to Shared Storage:**
   * Example: Copy `output.wav` to Downloads folder:
     ```bash
     # Adjust path if needed
     cp ./output.wav /sdcard/Download/output.wav
     ```
3. **Access on Android:** Use a File Manager app.

## Step 7: Exiting and Re-entering (Inside Debian)

1. **To fully exit:** `exit` at Termux prompt or close app.
2. **To re-enter:**
   * Open Termux.
   * `proot-distro login debian`
   * `micromamba activate melotts`
   * `cd ~/MeloTTS` (if needed)
   * Run commands.
   * `micromamba deactivate`, `exit` when done.

## Troubleshooting and Tips

* **Check Environment Activation:** Always ensure `(melotts)` prefix is present.
* **MeCab Issues:** If you see "RuntimeError: Could not configure working env. Have you installed MeCab?" during `pip install -e .` or runtime, this could be due to:
  - Missing system packages: Ensure `mecab`, `libmecab-dev`, and `mecab-ipadic-utf8` are properly installed via `apt`.
  - Python version mismatch: Make sure you created the Micromamba environment with Python 3.10 as specified in [Step 4](#step-4-create-micromamba-environment-and-install-melotts).
* **Phantom Process Killing (Android 12+):** Android 12 and newer versions limit background processes, which can affect Termux. If you experience processes being killed unexpectedly:
  - **Using ADB from a PC (Recommended):** Connect your Android device to a PC with ADB installed and run:
    ```bash
    # Disable phantom process killing
    adb shell settings put global settings_enable_monitor_phantom_procs 0

    # Set max_phantom_processes to maximum value to permanently disable killing of phantom processes
    adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
    ```
  - Alternatively, for Android 12+, you can disable phantom process killing by running these commands in Termux (not in Debian):
    ```bash
    # Disable phantom process killing
    settings put global settings_enable_monitor_phantom_procs 0
    
    # Disable device config sync to prevent settings from being reset
    device_config set_sync_disabled_for_tests persistent
    
    # Verify settings
    settings get global settings_enable_monitor_phantom_procs
    device_config get_sync_disabled_for_tests
    ```
  - These commands require either root access or ADB with proper permissions.
  - This is especially important for long-running processes or when multiple processes are spawned.
  - For more detailed instructions on disabling phantom process killing, refer to [this comprehensive guide](https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md#commands-to-disable-phantom-process-killing-and-tldr).
* **Performance/RAM:** Significant limitations remain on mobile devices.
