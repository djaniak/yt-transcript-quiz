import typer
import os
import json
from typing import Optional
from rich.console import Console
from rich.progress import Progress
from src.downloader import get_transcript, get_playlist_videos, extract_video_id
from src.generator import QuizGenerator
from src.anki_exporter import create_deck

app = typer.Typer()
console = Console()

@app.command()
def process(
    url: str = typer.Argument(..., help="YouTube Video or Playlist URL"),
    api_key: str = typer.Option(..., envvar="GEMINI_API_KEY", help="Google Gemini API Key"),
    output: str = typer.Option("output.apkg", help="Output Anki file name"),
    num_questions: int = typer.Option(50, help="Number of questions per video")
):
    """
    Download transcripts, generate quiz questions, and create an Anki deck.
    """
    
    video_ids = []
    
    if "list=" in url:
        console.print("[bold blue]Detected Playlist URL[/bold blue]")
        video_ids = get_playlist_videos(url)
        console.print(f"Found {len(video_ids)} videos in playlist.")
    else:
        vid = extract_video_id(url)
        if vid:
            video_ids = [vid]
        else:
            console.print("[bold red]Invalid YouTube URL[/bold red]")
            raise typer.Exit(code=1)

    if not video_ids:
        console.print("[bold red]No videos found to process.[/bold red]")
        raise typer.Exit(code=1)

    generator = QuizGenerator(api_key)
    all_cards = []

    with Progress() as progress:
        task = progress.add_task("[green]Processing videos...", total=len(video_ids))
        
        for vid in video_ids:
            progress.update(task, description=f"Processing video {vid}")
            
            transcript = get_transcript(vid)
            if not transcript:
                console.print(f"[yellow]Skipping video {vid} (No transcript found)[/yellow]")
                progress.advance(task)
                continue
            
            # Inner progress bar for question generation
            gen_task = progress.add_task(f"Generating questions for {vid}...", total=100)
            
            def update_gen_progress(current, total):
                # Update total if it changes (effectively sets it on first call) and current progress
                progress.update(gen_task, completed=current, total=total)
                
            questions = generator.generate_quiz(
                transcript, 
                num_questions=num_questions, 
                on_progress=update_gen_progress
            )
            
            progress.remove_task(gen_task)
            all_cards.extend(questions)
            
            progress.advance(task)

    if all_cards:
        # Create Anki Deck
        create_deck(all_cards, output_file=output)
        
        # Create JSON dump
        json_output = os.path.splitext(output)[0] + ".json"
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(all_cards, f, indent=4, ensure_ascii=False)
            
        console.print(f"[bold green]Success! Created {len(all_cards)} cards.[/bold green]")
        console.print(f" - Anki Deck: {output}")
        console.print(f" - JSON:      {json_output}")
    else:
        console.print("[bold yellow]No cards were generated.[/bold yellow]")

if __name__ == "__main__":
    app()
