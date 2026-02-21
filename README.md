# Google Takeout Metadata Embedder

A Python tool that **organizes ALL your photos by date** - whether they're from Google Takeout, your camera, or any other source. Embeds metadata, reads existing EXIF data, and intelligently handles files with or without metadata.

## What Makes This Special?

**It's not just for Google Takeout!** This tool organizes **ANY** photos:
- ✅ Google Takeout exports with JSON files
- ✅ Regular photos from your camera (uses EXIF)
- ✅ Photos you've manually edited
- ✅ Mixed collections from multiple sources

**Smart enough** to avoid duplicate work:
- Won't re-process files that already have metadata
- Won't overwrite good data with identical data
- Fast on second runs (skips what's done)

**Flexible** to handle missing data:
- Guess dates from sequential filenames
- Use existing EXIF when JSON missing
- Organize by any available date information

## Quick Start

```bash
# 1. Clone or download this repository
git clone https://github.com/luisaintonio/google-takeout-metadata-embedder.git
cd google-takeout-metadata-embedder

# 2. Run setup (installs dependencies)
./setup.sh

# 3. Run the tool
./run.sh
```

That's it! The tool will guide you through the rest.

## Problem

When you export your Google Photos library using Google Takeout, you get:
- Media files (photos and videos)
- Separate `.json` files containing valuable metadata:
  - Original capture dates
  - GPS coordinates
  - People tags
  - Descriptions
  - Google Photos URLs

This metadata is **not embedded** in the actual media files, which means:
- Photo apps can't read the original dates or locations
- Sorting by date uses file modification time (not capture time)
- People tags and descriptions are lost
- The files are difficult to organize

## Solution

This tool:
1. ✅ **Organizes ALL your photos by date** - not just Google Takeout exports
2. ✅ Finds files with JSON metadata and embeds it (Google Takeout)
3. ✅ **Smart detection** - Reads existing EXIF data and uses it to organize
4. ✅ **Date guessing** - Estimates dates for files without metadata (IMG_3689 → IMG_3690)
5. ✅ Extracts metadata (dates, GPS, people, descriptions) from JSON
6. ✅ Copies files to organized folder structure: `Output/YYYY/Month/`
7. ✅ Updates file system timestamps to match photo dates
8. ✅ Skips re-processing files that already have correct metadata
9. ✅ Keeps your originals completely untouched
10. ✅ Beautiful terminal UI with progress tracking

## Requirements

- **Python 3.7+** - [Download](https://www.python.org/downloads/)
- **exiftool** - Required for metadata embedding

### Installing exiftool

**macOS:**
```bash
brew install exiftool
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install libimage-exiftool-perl
```

**Windows:**
Download from [exiftool.org](https://exiftool.org/)

## Installation & Setup

### Automatic Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/luisaintonio/google-takeout-metadata-embedder.git
cd google-takeout-metadata-embedder

# Run setup script (checks dependencies, creates venv, installs packages)
./setup.sh
```

The setup script will:
- ✅ Check for Python 3 and exiftool
- ✅ Create a virtual environment
- ✅ Install all Python dependencies
- ✅ Verify everything is ready

### Manual Setup

If you prefer manual installation:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Easy Way

Simply run:
```bash
./run.sh
```

### Manual Way

```bash
source venv/bin/activate  # Activate virtual environment
python main.py
```

### Steps

1. When prompted, enter the path to your Google Takeout folder:
   ```
   Enter the path to your Google Takeout folder:
   > /Users/yourname/Downloads/Takeout
   ```

2. Review the scan results showing files found

3. If files without JSON are found, choose date guessing:
   ```
   Found 5 file(s) without JSON metadata.
   Do you want to guess dates based on similar filenames? (y/n):
   Example: IMG_3689 with metadata can help date IMG_3690
   > y
   ```

4. Confirm to start processing (type `y`)

5. Wait while the tool:
   - Copies files to `<YourFolder>/Output/YYYY/Month/`
   - Embeds all metadata into the copies
   - Guesses dates for files without JSON (if enabled)
   - Updates file system timestamps
   - Shows progress with a nice progress bar
   - Logs everything to `metadata_embedder.log`

6. Check your organized photos in the `Output/` folder!

## Output Structure

Files are organized by date:

```
YourTakeoutFolder/
├── Output/
│   ├── 2022/
│   │   ├── January/
│   │   │   ├── IMG_1234.JPG
│   │   │   └── IMG_5678.JPG
│   │   └── December/
│   │       └── VID_9012.MP4
│   ├── 2024/
│   │   └── March/
│   │       └── IMG_3456.JPG
│   └── Unknown/
│       └── file_without_date.JPG
└── [Original files remain untouched]
```

## Metadata Embedded

### For Images (JPG, PNG, HEIC, WEBP, DNG, NEF):
- ✅ Date/time (DateTimeOriginal, CreateDate, ModifyDate)
- ✅ GPS coordinates (GPSLatitude, GPSLongitude, GPSAltitude)
- ✅ People tags (XMP:PersonInImage, IPTC:Keywords)
- ✅ Description (ImageDescription)
- ✅ Google Photos URL (XMP:Identifier)

### For Videos (MOV, MP4, AVI):
- ✅ Date/time (QuickTime:CreateDate, QuickTime:ModifyDate, XMP:DateCreated)

## Supported File Types

**Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.heic`, `.webp`, `.dng`, `.nef`
**Videos**: `.mov`, `.mp4`, `.avi`

## How It Works

This tool is a **complete photo organizer**, not just a Google Takeout processor. It handles files intelligently based on what metadata is available:

### Processing Priority

For each photo, the tool checks in this order:

1. **Has JSON metadata?** → Extract and embed Google Photos data
2. **Already has correct EXIF data?** → Skip embedding, just organize
3. **Has EXIF data but no JSON?** → Use EXIF date to organize
4. **No metadata but can guess?** → Estimate date from similar files
5. **No date at all?** → Place in `Unknown/` folder

### Example Scenarios

```
Scenario 1: Google Takeout photo
  IMG_3689.JPG + IMG_3689.JPG.json
  → Extract JSON metadata → Embed in file → Organize by date ✓

Scenario 2: Already processed photo
  IMG_3689.JPG (has EXIF matching JSON)
  → Detect existing metadata → Skip embedding → Just organize ✓

Scenario 3: Random photo you copied in
  vacation.jpg (has EXIF DateTimeOriginal)
  → Read EXIF date → Organize by that date ✓

Scenario 4: Photo without metadata
  IMG_3690.JPG (no JSON, no EXIF)
  → Find similar IMG_3689.JPG → Guess date → Organize ✓

Scenario 5: Screenshot without date
  screenshot.png (no metadata, can't guess)
  → Place in Unknown/ folder ✓
```

**Result:** ALL your photos get organized, regardless of their source!

## Smart Features

### JSON Matching Logic

The tool is smart about finding JSON files. It searches in this order:

1. **Exact match**: `IMG_1234.JPG` → `IMG_1234.JPG.json`
2. **Numbered suffix**: `IMG_1234.JPG(1).json`, `IMG_1234.JPG(2).json`, etc.
   - Google Takeout adds these when multiple files have the same name
3. **Title field verification**: Checks if the JSON's `title` field matches the filename

### Date Guessing for Files Without JSON

If some of your media files don't have JSON metadata, the tool can guess their dates based on similar filenames!

**How it works:**
- Camera files are usually numbered sequentially (IMG_3689, IMG_3690, IMG_3691...)
- If IMG_3689 has metadata with a date, IMG_3690 can use a similar date
- The tool finds the closest numbered file with metadata (within 100 numbers)

**Example:**
```
IMG_3689.JPG + IMG_3689.JPG.json → Date: 2022-12-21
IMG_3690.JPG (no JSON) → Guessed date: 2022-12-21 ✓
```

**You choose:**
- **Enable guessing**: Files are dated based on nearby files
- **Disable guessing**: Files without metadata go to `Output/Unknown/` folder

This works with common naming patterns:
- `IMG_1234.JPG`, `IMG_1235.JPG`
- `DSC_5678.NEF`, `DSC_5679.NEF`
- `VID_20220101.mp4`, `VID_20220102.mp4`

## Verification

After processing, verify the metadata was embedded:

```bash
# Check a processed file
exiftool Output/2022/December/IMG_1234.JPG

# You should see:
# Date/Time Original    : 2022:12:15 14:30:45
# GPS Position          : 37.7749 N, 122.4194 W
# Person In Image       : John Doe
# Image Description     : Family vacation photo
```

## Safety Features

- ✅ **Never modifies originals** - Only works on copies
- ✅ **Handles name collisions** - Adds `_1`, `_2` suffixes if needed
- ✅ **Detailed logging** - Everything logged to `metadata_embedder.log`
- ✅ **Graceful error handling** - One bad file won't stop processing
- ✅ **Progress tracking** - Always know what's happening

## Troubleshooting

### "exiftool not found"
**Solution:** Install exiftool first
- macOS: `brew install exiftool`
- Linux: `sudo apt install libimage-exiftool-perl`
- Windows: Download from [exiftool.org](https://exiftool.org/)

### "Virtual environment not found"
**Solution:** Run the setup script first: `./setup.sh`

### "No media files with JSON metadata found"
**Possible causes:**
- Wrong folder selected - make sure it's your Google Takeout export folder
- JSON files don't exist - Google Takeout should create `.json` files alongside media files
- Already processed - the tool skips the `Output/` folder automatically

### Files go to "Unknown" folder
**Why:** Files don't have JSON metadata and date guessing was disabled (or couldn't guess)

This is normal for:
- Files without JSON metadata when date guessing is disabled
- Files with JSON but no valid timestamps
- Files where date guessing couldn't find similar files

**Solution:** Files in `Unknown/` are still copied safely, just not organized by date. You can manually sort them later.

### Some metadata not embedded
**Reasons:**
- Videos only support date/time (GPS and people tags aren't supported by video formats)
- Some file formats have limited metadata support
- File might have wrong extension (e.g., JPEG file named as .png)

**Solution:** Check `metadata_embedder.log` for detailed error messages

### Permission errors
**Solution:** Make sure you have read access to the input folder and write access to create the Output folder

## Example

```bash
$ python main.py

╔══════════════════════════════════════════════════════╗
║  Google Takeout Metadata Embedder                    ║
║  Embed JSON metadata back into your photos and videos ║
╚══════════════════════════════════════════════════════╝

Checking dependencies...
✓ exiftool is available

Enter the path to your Google Takeout folder:
> /Users/yourname/Downloads/Takeout

Scanning for media files...
Found 9 media file(s) with metadata

┌─────────────────────────────────────────┐
│ Files to Process (Preview)             │
├───────────────────────┬─────────────────┤
│ Media File            │ JSON File       │
├───────────────────────┼─────────────────┤
│ IMG_3689.JPG          │ IMG_3689.JPG.json │
│ PXL_20240318.jpg      │ PXL_20240318.jpg.json │
│ ...                   │ ...             │
└───────────────────────┴─────────────────┘

Ready to process files. Continue? (y/n):
> y

Processing files...

⠋ Processing IMG_3689.JPG... ━━━━━━━━━━━━━━━ 100% 0:00:05

┌──────────────────────────────────────┐
│ Processing Summary                   │
├────────────┬─────────────────────────┤
│ Total Files│                       9 │
│ Successful │                       9 │
│ Failed     │                       0 │
└────────────┴─────────────────────────┘

✓ All files processed successfully!

Check metadata_embedder.log for detailed information

Output location: /Users/yourname/Downloads/Takeout/Output
```

## License

MIT License - Feel free to use, modify, and distribute!

## Credits

Built with:
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal UI
- [exiftool](https://exiftool.org/) - Metadata manipulation

---

**Made with ❤️ for organizing your Google Photos exports**
