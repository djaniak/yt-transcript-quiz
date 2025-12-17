# YouTube Transcript Quiz Generator

Generate Anki flashcards from YouTube video transcripts using Google Gemini.

## Setup

1.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script with a YouTube URL (video or playlist) and your Gemini API key.

```bash
python main.py "https://www.youtube.com/watch?v=..." --api-key "YOUR_KEY"
```

### Options
- `--output`: Specify output filename (default: `output.apkg`)
- `--num-questions`: Number of questions per video (default: 5)
