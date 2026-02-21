#!/usr/bin/env python3
"""Google Takeout Metadata Embedder - Main Entry Point

Embeds JSON metadata from Google Takeout exports back into media files
and organizes them by date in a clean folder structure.
"""

import sys
import logging
import os
from pathlib import Path
import shutil
from datetime import datetime
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich import box

from lib.scanner import scan_folder, guess_date_from_similar_files
from lib.metadata import (
    parse_json,
    extract_datetime,
    extract_gps,
    extract_people,
    extract_description,
    extract_url
)
from lib.organizer import get_output_path, ensure_output_directory
from lib.exiftool import check_exiftool, embed_metadata
from lib.exif_reader import read_exif_date, has_matching_metadata
from lib.state import ProcessingState

# Setup logging
# File handler: logs everything (INFO and above) to file for debugging
file_handler = logging.FileHandler('metadata_embedder.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Console handler: only show warnings and errors, not every file processed
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

console = Console()


def print_banner():
    """Display welcome banner."""
    banner = """
[bold cyan]Google Takeout Metadata Embedder[/bold cyan]
[dim]Embed JSON metadata back into your photos and videos[/dim]
"""
    console.print(Panel(banner, box=box.DOUBLE, border_style="cyan"))


def get_input_folder() -> Path:
    """Prompt user for input folder and validate.

    Returns:
        Validated Path object
    """
    while True:
        console.print("\n[yellow]Enter the path to your Google Takeout folder:[/yellow]")
        user_input = input("> ").strip()

        # Expand ~ and handle quotes
        user_input = user_input.strip('"').strip("'")
        folder_path = Path(user_input).expanduser().resolve()

        if not folder_path.exists():
            console.print(f"[red]✗[/red] Folder does not exist: {folder_path}")
            continue

        if not folder_path.is_dir():
            console.print(f"[red]✗[/red] Not a directory: {folder_path}")
            continue

        console.print(f"[green]✓[/green] Using folder: {folder_path}")
        return folder_path


def display_scan_summary(
    files_with_json: List[Tuple[Path, Path]],
    files_without_json: List[Path]
):
    """Display summary table of scanned files.

    Args:
        files_with_json: List of (media_file, json_file) tuples
        files_without_json: List of media files without JSON
    """
    total = len(files_with_json) + len(files_without_json)

    if total == 0:
        console.print("\n[yellow]No media files found.[/yellow]")
        return

    console.print(f"\n[green]Found {total} media file(s)[/green]")
    console.print(f"  • {len(files_with_json)} with JSON metadata")
    console.print(f"  • {len(files_without_json)} without JSON metadata\n")

    # Show first 10 files as preview
    table = Table(title="Files to Process (Preview)", box=box.SIMPLE)
    table.add_column("Media File", style="cyan")
    table.add_column("Metadata", style="dim")

    preview_count = 0
    for media_file, json_file in files_with_json[:10]:
        table.add_row(media_file.name, f"✓ {json_file.name}")
        preview_count += 1

    remaining = 10 - preview_count
    for media_file in files_without_json[:remaining]:
        table.add_row(media_file.name, "✗ No JSON")
        preview_count += 1

    if total > 10:
        table.add_row("...", "...", style="dim")
        table.add_row(f"{total - 10} more files", "", style="dim")

    console.print(table)


def process_file(
    media_file: Path,
    json_file: Path,
    input_root: Path
) -> Tuple[bool, str]:
    """Process a single media file: copy and embed metadata.

    Args:
        media_file: Path to media file
        json_file: Path to JSON metadata file
        input_root: Root input directory

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Parse JSON metadata
        metadata = parse_json(json_file)
        if metadata is None:
            return False, "Failed to parse JSON"

        # Extract metadata
        dt = extract_datetime(metadata)
        gps = extract_gps(metadata)
        people = extract_people(metadata)
        description = extract_description(metadata)
        url = extract_url(metadata)

        # Smart detection: Check if file already has matching metadata
        if dt and has_matching_metadata(media_file, dt):
            # File already processed, just copy to organized location
            output_path = get_output_path(input_root, media_file, dt)

            if not ensure_output_directory(output_path):
                return False, "Failed to create output directory"

            try:
                shutil.copy2(media_file, output_path)
            except IOError as e:
                return False, f"Failed to copy file: {e}"

            # Update file system timestamp
            try:
                timestamp = dt.timestamp()
                os.utime(output_path, (timestamp, timestamp))
            except OSError as e:
                logger.warning(f"Could not update file timestamp: {e}")

            return True, f"Already has metadata (Date: {dt.strftime('%Y-%m-%d')})"

        # Calculate output path
        output_path = get_output_path(input_root, media_file, dt)

        # Ensure output directory exists
        if not ensure_output_directory(output_path):
            return False, "Failed to create output directory"

        # Copy file to output location
        try:
            shutil.copy2(media_file, output_path)
        except IOError as e:
            return False, f"Failed to copy file: {e}"

        # Embed metadata using exiftool
        success = embed_metadata(output_path, dt, gps, people, description, url)

        if success:
            # Update file system timestamp to match EXIF date
            if dt:
                try:
                    timestamp = dt.timestamp()
                    os.utime(output_path, (timestamp, timestamp))
                except OSError as e:
                    logger.warning(f"Could not update file timestamp: {e}")

            # Build metadata summary
            parts = []
            if dt:
                parts.append(f"Date: {dt.strftime('%Y-%m-%d')}")
            if gps:
                parts.append(f"GPS: {gps[0]:.4f}, {gps[1]:.4f}")
            if people:
                parts.append(f"People: {len(people)}")
            if description:
                parts.append(f"Desc: Yes")

            summary = ", ".join(parts) if parts else "No metadata"
            return True, summary
        else:
            return False, "Failed to embed metadata"

    except Exception as e:
        logger.exception(f"Unexpected error processing {media_file.name}")
        return False, f"Unexpected error: {e}"


def process_file_without_json(
    media_file: Path,
    input_root: Path,
    guessed_date: Optional[datetime] = None
) -> Tuple[bool, str]:
    """Process a media file without JSON metadata.

    Tries to use existing EXIF data, guessed date, or Unknown folder.

    Args:
        media_file: Path to media file
        input_root: Root input directory
        guessed_date: Guessed datetime or None

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Try to read existing EXIF date from the file
        exif_date = read_exif_date(media_file)

        # Determine date to use (priority: EXIF > guessed > None)
        date_to_use = exif_date or guessed_date
        date_source = None

        if exif_date:
            date_source = "EXIF"
        elif guessed_date:
            date_source = "guessed"

        # Calculate output path (will use Unknown folder if no date)
        output_path = get_output_path(input_root, media_file, date_to_use)

        # Ensure output directory exists
        if not ensure_output_directory(output_path):
            return False, "Failed to create output directory"

        # Copy file to output location
        try:
            shutil.copy2(media_file, output_path)
        except IOError as e:
            return False, f"Failed to copy file: {e}"

        # Update file system timestamp if we have a date
        if date_to_use:
            try:
                timestamp = date_to_use.timestamp()
                os.utime(output_path, (timestamp, timestamp))
            except OSError as e:
                logger.warning(f"Could not update file timestamp: {e}")

            return True, f"{date_source} date: {date_to_use.strftime('%Y-%m-%d')}"
        else:
            return True, "No date (moved to Unknown)"

    except Exception as e:
        logger.exception(f"Unexpected error processing {media_file.name}")
        return False, f"Unexpected error: {e}"


def display_final_summary(total: int, successful: int, failed: int):
    """Display final processing summary.

    Args:
        total: Total files processed
        successful: Number of successful files
        failed: Number of failed files
    """
    console.print("\n")

    # Summary table
    table = Table(title="Processing Summary", box=box.DOUBLE, border_style="green")
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("Total Files", str(total))
    table.add_row("Successful", f"[green]{successful}[/green]")
    table.add_row("Failed", f"[red]{failed}[/red]" if failed > 0 else "0")

    console.print(table)

    # Success message
    if failed == 0:
        console.print("\n[bold green]✓ All files processed successfully![/bold green]")
    elif successful > 0:
        console.print(f"\n[yellow]⚠ {failed} file(s) failed to process[/yellow]")
    else:
        console.print("\n[red]✗ No files were processed successfully[/red]")

    console.print(f"\n[dim]Check metadata_embedder.log for detailed information[/dim]")


def main():
    """Main entry point."""
    print_banner()

    # Check for exiftool
    console.print("\n[cyan]Checking dependencies...[/cyan]")
    if not check_exiftool():
        console.print("[red]✗ exiftool not found![/red]")
        console.print("Please install exiftool: brew install exiftool")
        sys.exit(1)
    console.print("[green]✓ exiftool is available[/green]")

    # Get input folder
    input_folder = get_input_folder()

    # Scan for media files
    with console.status("[cyan]Scanning directory tree for photos and videos...[/cyan]", spinner="dots"):
        files_with_json, files_without_json = scan_folder(input_folder)

    total_files = len(files_with_json) + len(files_without_json)
    if total_files == 0:
        console.print("\n[yellow]✗ No media files found.[/yellow]")
        console.print("Make sure you're pointing to a Google Takeout export folder.")
        sys.exit(0)

    console.print(f"[green]✓ Scan complete: found {total_files} media file(s)[/green]")

    # Display scan summary
    display_scan_summary(files_with_json, files_without_json)

    # Ask about date guessing if there are files without JSON
    enable_date_guessing = False
    if files_without_json:
        console.print(f"\n[yellow]Found {len(files_without_json)} file(s) without JSON metadata.[/yellow]")
        console.print("Do you want to guess dates based on similar filenames? (y/n):")
        console.print("[dim]Example: IMG_3689 with metadata can help date IMG_3690[/dim]")
        guess_response = input("> ").strip().lower()
        enable_date_guessing = (guess_response == 'y')

        if enable_date_guessing:
            console.print("[green]✓ Date guessing enabled[/green]")
        else:
            console.print("[dim]Files without metadata will go to 'Unknown' folder[/dim]")

    # Confirm processing
    console.print("\n[yellow]Ready to process files. Continue? (y/n):[/yellow]")
    confirm = input("> ").strip().lower()
    if confirm != 'y':
        console.print("[dim]Cancelled by user[/dim]")
        sys.exit(0)

    # Build list of files with dates for guessing
    files_with_dates = []
    if enable_date_guessing:
        with console.status(f"[cyan]Analyzing {len(files_with_json)} files to build date reference index...[/cyan]", spinner="dots"):
            for media_file, json_file in files_with_json:
                metadata = parse_json(json_file)
                if metadata:
                    dt = extract_datetime(metadata)
                    if dt:
                        files_with_dates.append((media_file, dt))
        console.print(f"[green]✓ Built date index: {len(files_with_dates)} files with dates available for guessing[/green]")

    # Initialize processing state for resume capability
    state_file = input_folder / ".processing_state.json"
    state = ProcessingState(state_file)

    # Filter out already-processed files
    files_to_process_with_json = [(m, j) for m, j in files_with_json if not state.is_processed(m)]
    files_to_process_without_json = [m for m in files_without_json if not state.is_processed(m)]

    already_processed = (len(files_with_json) - len(files_to_process_with_json)) + \
                       (len(files_without_json) - len(files_to_process_without_json))

    if already_processed > 0:
        console.print(f"\n[cyan]Resume detected: {already_processed} file(s) already processed[/cyan]")
        console.print(f"[green]✓ Skipping {already_processed} previously completed files[/green]")

    files_remaining = len(files_to_process_with_json) + len(files_to_process_without_json)

    if files_remaining == 0:
        console.print("\n[green]✓ All files already processed![/green]")
        console.print("\n[dim]To reprocess, delete .processing_state.json in the input folder[/dim]")
        output_folder = input_folder / "Output"
        console.print(f"\n[cyan]Output location:[/cyan] {output_folder}")
        sys.exit(0)

    # Process files with progress bar using parallel workers
    console.print(f"\n[cyan]Processing {files_remaining} file(s) with parallel workers...[/cyan]\n")

    successful = 0
    failed = 0
    current_file = 0
    lock = threading.Lock()

    # Determine number of workers (4-8 based on CPU count)
    import multiprocessing
    max_workers = min(8, max(4, multiprocessing.cpu_count() - 1))
    console.print(f"[dim]Using {max_workers} parallel workers[/dim]\n")

    def process_with_state(args):
        """Wrapper to process file and update state."""
        media_file, json_file, input_root, guessed_date = args

        # Process the file
        if json_file:
            success, message = process_file(media_file, json_file, input_root)
        else:
            success, message = process_file_without_json(media_file, input_root, guessed_date)

        # Update state on success
        if success:
            with lock:
                state.mark_processed(media_file)

        return media_file, success, message

    # Prepare all tasks
    tasks = []

    # Add files with JSON
    for media_file, json_file in files_to_process_with_json:
        tasks.append((media_file, json_file, input_folder, None))

    # Add files without JSON
    for media_file in files_to_process_without_json:
        guessed_date = None
        if enable_date_guessing:
            guessed_date = guess_date_from_similar_files(media_file, files_with_dates)
        tasks.append((media_file, None, input_folder, guessed_date))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:

        task = progress.add_task("Processing...", total=files_remaining)

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {executor.submit(process_with_state, args): args[0] for args in tasks}

            # Process completed tasks as they finish
            for future in as_completed(future_to_file):
                media_file, success, message = future.result()

                with lock:
                    current_file += 1
                    progress.update(task, description=f"[{current_file}/{files_remaining}] {media_file.name[:30]}...")

                    if success:
                        successful += 1
                        logger.info(f"✓ {media_file.name}: {message}")
                    else:
                        failed += 1
                        logger.error(f"✗ {media_file.name}: {message}")

                    progress.advance(task)

    # Save final state
    state.save_state()
    console.print(f"\n[dim]Saved processing state to {state_file.name}[/dim]")

    # Display final summary
    display_final_summary(files_remaining, successful, failed)

    # Show completion message
    if failed == 0 and files_remaining > 0:
        console.print("\n[green]✓ Processing complete! Cleaning up state file...[/green]")
        state.clear()
    elif already_processed > 0:
        console.print(f"\n[cyan]Session complete. Total processed: {already_processed + successful} files[/cyan]")

    # Show output location
    output_folder = input_folder / "Output"
    console.print(f"\n[cyan]Output location:[/cyan] {output_folder}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ Interrupted by user[/yellow]")
        console.print("[green]✓ Progress has been saved. Run again to resume from where you left off.[/green]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        logger.exception("Fatal error in main()")
        sys.exit(1)
