import requests
import json
import os
from datetime import datetime

# Test the updated API with different voice parameter formats
url = 'http://localhost:18000/v1/audio/speech'

# Test cases
tests = [
    # Test 1: Auto-detect Chinese and English hybrid text
    {
        'model': 'tts-1',
        'input': "我能 eat glass 而不傷身體。",
        'response_format': 'mp3',
        'speed': 1.0
    },
    # Test 2: Specify language / speaker format, different response format
    {
        'model': 'tts-1',
        'input': "I can eat glass and it doesn't hurt me.",
        'voice': 'EN/EN-US',
        'response_format': 'wav',
        'speed': 1.0
    },
    # Test 3: Auto-detect Spanish, different response format
    {
        'model': 'tts-1',
        'input': "Puedo comer vidrio, no me hace daño.",
        'response_format': 'flac',
        'speed': 1.0
    },
    # Test 4: Auto-detect Japanese, different response format
    {
        'model': 'tts-1',
        'input': "私はガラスを食べられます。それでも傷つかないです。",
        'response_format': 'mp3',
        'speed': 1.0
    },
    # # Test 5: Auto-detect Korean, default voice, default speed, default format
    # {
    #      'model': 'tts-1',
    #      'input': "나는 유리를 먹을 수 있어요. 그래도 아프지 않아요.",
    # },
    # Test 6: Auto-detect French, different speed
    {
        'model': 'tts-1',
        'input': "Je peux manger du verre, je ne le touche pas.",
        'speed': 0.8
    },
    # Test 7: Defined EN language / ZH speaker, but language doesn't match speaker
    {
        'model': 'tts-1',
        'input': "我能 eat glass 而不傷身體。",
        'voice': 'EN/ZH',
        'response_format':'mp3',
        'speed': 1.0
    }
]

print('Starting API tests...')
print('Note: These tests will only work if the API server is running.')
print('If the server is not running, start it with: python webapi/webapi.py')
print('\nTest results:')

test_path = "./test"
# Remove previous test audio files
for file in os.listdir(test_path):
    if file.startswith('test_') and (file.endswith('.mp3') or file.endswith('.wav') or file.endswith('.flac')):
        os.remove(os.path.join(test_path, file))

for i, test in enumerate(tests):
    try:
        if 'voice' not in test:
            test['voice'] = 'auto'
        if 'response_format' not in test:
            test['response_format'] = 'mp3'
        print(f"\nTest {i+1}: {test['voice']} - {test['input'][:30]}...")
        print(f"Request data: {json.dumps(test)}")
        response = requests.post(url, json=test)
        print(f'Response status: {response.status_code}')
        
        # Save the output to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{test_path}/test_{timestamp}.{test['response_format']}"

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f'Output saved to: {output_path}')
    except Exception as e:
        print(f'Error: {str(e)}')
