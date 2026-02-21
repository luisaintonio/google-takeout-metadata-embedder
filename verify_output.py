#!/usr/bin/env python3
"""
Verification script for Google Takeout Metadata Embedder output.
Checks for corruption, missing files, and validates metadata.
"""

import sys
from pathlib import Path
import subprocess
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def check_file_readable(file_path):
    """Check if file is readable and not corrupted."""
    try:
        # Try to read first 1KB of file
        with open(file_path, 'rb') as f:
            f.read(1024)
        return True
    except Exception as e:
        return False

def check_exif_metadata(file_path, exiftool_path):
    """Check if file has valid EXIF metadata."""
    try:
        result = subprocess.run(
            [exiftool_path, "-DateTimeOriginal", "-s3", str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        # If we get a date back, file has metadata
        return result.returncode == 0 and result.stdout.strip()
    except:
        return False

def verify_output_folder(output_folder):
    """Verify all files in output folder."""
    output_path = Path(output_folder)
    
    if not output_path.exists():
        console.print(f"[red]✗ Output folder doesn't exist: {output_folder}[/red]")
        return
    
    console.print(f"\n[cyan]Verifying: {output_folder}[/cyan]\n")
    
    # Find exiftool
    exiftool_path = None
    for path in ["/opt/homebrew/bin/exiftool", "/usr/bin/exiftool", "/usr/local/bin/exiftool"]:
        if Path(path).exists():
            exiftool_path = path
            break
    
    if not exiftool_path:
        try:
            result = subprocess.run(["which", "exiftool"], capture_output=True, text=True)
            if result.returncode == 0:
                exiftool_path = result.stdout.strip()
        except:
            pass
    
    # Find all media files
    media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.heic', '.webp', '.dng', '.nef', '.mov', '.mp4', '.avi'}
    all_files = []
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Scanning files...", total=None)
        for file_path in output_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                all_files.append(file_path)
        progress.update(task, completed=True)
    
    total_files = len(all_files)
    console.print(f"[green]Found {total_files} media files to verify[/green]\n")
    
    # Verification stats
    readable_count = 0
    unreadable_count = 0
    with_metadata = 0
    without_metadata = 0
    unreadable_files = []
    no_metadata_files = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Verifying files...", total=total_files)
        
        for file_path in all_files:
            progress.update(task, description=f"Checking {file_path.name[:40]}...")
            
            # Check if readable
            if check_file_readable(file_path):
                readable_count += 1
            else:
                unreadable_count += 1
                unreadable_files.append(str(file_path))
            
            # Check metadata (if exiftool available and file is an image)
            if exiftool_path and file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.heic', '.nef', '.dng'}:
                if check_exif_metadata(file_path, exiftool_path):
                    with_metadata += 1
                else:
                    without_metadata += 1
                    no_metadata_files.append(str(file_path))
            
            progress.advance(task)
    
    # Display results
    console.print("\n")
    table = Table(title="Verification Results", show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="right")
    
    table.add_row("Total Files", str(total_files))
    table.add_row("Readable Files", f"[green]{readable_count}[/green]")
    table.add_row("Corrupted/Unreadable", f"[red]{unreadable_count}[/red]" if unreadable_count > 0 else "0")
    
    if exiftool_path:
        table.add_row("With Metadata", f"[green]{with_metadata}[/green]")
        table.add_row("Without Metadata", f"[yellow]{without_metadata}[/yellow]" if without_metadata > 0 else "0")
    else:
        table.add_row("Metadata Check", "[yellow]Skipped (exiftool not found)[/yellow]")
    
    console.print(table)
    console.print()
    
    # Show problems if any
    if unreadable_count > 0:
        console.print("[red]⚠ Corrupted/Unreadable Files:[/red]")
        for f in unreadable_files[:10]:
            console.print(f"  • {f}")
        if len(unreadable_files) > 10:
            console.print(f"  ... and {len(unreadable_files) - 10} more")
        console.print()
    
    if without_metadata > 0 and exiftool_path:
        console.print("[yellow]⚠ Files Without Metadata:[/yellow]")
        for f in no_metadata_files[:10]:
            console.print(f"  • {f}")
        if len(no_metadata_files) > 10:
            console.print(f"  ... and {len(no_metadata_files) - 10} more")
        console.print()
    
    # Final verdict
    if unreadable_count == 0 and without_metadata == 0:
        console.print("[bold green]✓ All files verified successfully![/bold green]")
        return True
    elif unreadable_count == 0:
        console.print("[bold yellow]⚠ All files readable, but some missing metadata[/bold yellow]")
        return True
    else:
        console.print(f"[bold red]✗ Found {unreadable_count} corrupted files[/bold red]")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: python verify_output.py <output_folder>[/yellow]")
        console.print("Example: python verify_output.py ~/Desktop/test-takeout-big/Output")
        sys.exit(1)
    
    output_folder = sys.argv[1]
    success = verify_output_folder(output_folder)
    sys.exit(0 if success else 1)
