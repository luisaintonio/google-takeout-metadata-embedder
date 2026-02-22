# Reorganizing the Unknown Folder

This guide shows you how to reorganize files from your Unknown folder into properly organized date-based folders.

## What's New?

The enhanced version now checks **multiple date sources**:

1. ✅ **EXIF DateTimeOriginal** (when photo was taken)
2. ✅ **EXIF CreateDate** (when file was created - helps with PNG/screenshots)
3. ✅ **EXIF ModifyDate** (when file was modified - fallback for edited files)
4. ✅ **File modification time** (with safety checks - optional)

## Quick Start (Easiest Way)

### Step 1: Copy to Another Computer

Copy the entire `google-takeout-metadata-embedder` folder:
- Via USB drive, network share, or cloud storage
- Make sure to copy the entire folder including the `lib/` subdirectory

### Step 2: Install Dependencies

On the other computer, open Terminal and run:

```bash
# macOS
brew install exiftool

# Linux (Ubuntu/Debian)
sudo apt install libimage-exiftool-perl

# Windows
# Download exiftool from exiftool.org
```

### Step 3: Run the Tool

**Just run it normally:**
```bash
cd google-takeout-metadata-embedder
./run.sh
```

**That's it!** The tool will:
1. Ask you for the folder path (e.g., `/Volumes/PortableSSD/Media`)
2. Detect if an Unknown folder exists
3. Ask if you want to reorganize Unknown or process normally
4. Guide you through the options

### Interactive Workflow

When you run `./run.sh`, you'll see:

```
Enter the path to your Google Takeout folder:
> /Volumes/PortableSSD/Media

Found existing Unknown folder with 11,235 media file(s)
Location: /Volumes/PortableSSD/Media/Output/Unknown

Would you like to:
  1. Reorganize Unknown folder with enhanced date detection
  2. Process the entire folder normally

Enter choice (1 or 2):
> 1

Use file modification time as fallback? (y/n):
Recommended: y - Uses EXIF + safe file dates (older than 30 days)
> y

Processing 11,235 file(s)...
```

**That's the entire workflow!** No complex commands to remember.

## What You'll See

When reorganizing, the tool shows:
```
✓ Found 11,235 media file(s) to reorganize

Date detection options:
  • EXIF DateTimeOriginal, CreateDate, ModifyDate: Enabled
  • File modification time fallback: Enabled
  • Minimum file age: 30 days

This will move files from Unknown to proper year/month folders. Continue? (y/n):
> y

Processing 11,235 file(s)...
⠋ [1234/11235] IMG_3904.HEIC... ━━━━━━━━━━━━━━━ 11% 0:02:34

Reorganization Summary
┌─────────────────────────┬───────┐
│ Metric                  │ Count │
├─────────────────────────┼───────┤
│ Total Files             │ 11235 │
│ Successfully Reorganized│  8456 │
│ Remain in Unknown       │  2779 │
│ Failed                  │     0 │
└─────────────────────────┴───────┘

✓ 8,456 file(s) reorganized successfully!
○ 2,779 file(s) remain in Unknown (no date found)
```

## Options Explained

When prompted "Use file modification time as fallback?":

**Choose 'y' (Yes) if:**
- Files were copied from Google Takeout (preserves original dates)
- Files are from camera SD card (preserves modification times)
- Most files are older than 30 days

**Choose 'n' (No) if:**
- You recently copied/moved files (modification times might be wrong)
- You want to be conservative (EXIF only)
- You don't trust file system timestamps

## How It Works

### Safety Checks

The file modification time fallback includes safety checks:

✅ **Accepts:**
- Dates between 2000 and current year
- Dates older than minimum age (default: 30 days)
- Reasonable dates that look legitimate

❌ **Rejects:**
- Dates in the future
- Dates before year 2000
- Dates within last 30 days (likely from copying files)
- Invalid or corrupted timestamps

### What Gets Reorganized

**Example file:** `IMG_6400.JPG` in Unknown folder

**Priority order:**
1. Checks EXIF DateTimeOriginal → Not found
2. Checks EXIF CreateDate → Not found
3. Checks EXIF ModifyDate → Not found
4. Checks file modification time → **Found: 2015-07-15**
5. Validates: ✓ Between 2000-2026, ✓ Not in future, ✓ Older than 30 days
6. **Moves** to `/Output/2015/July/IMG_6400.JPG`

## File Modification Time: When to Trust It

### ✅ **Trustworthy scenarios:**

1. **Google Takeout preserves timestamps**
   - When Google exports your photos, file modification times often reflect the original date
   - Your 112GB Unknown folder likely has valid timestamps

2. **Camera photos copied directly**
   - Files copied from camera SD card preserve modification times

3. **Old archives extracted**
   - Unzipped archives often preserve original file times

### ⚠️ **Less trustworthy scenarios:**

1. **Recently copied files**
   - Files copied/moved in the last 30 days might have wrong timestamps
   - *Solution:* The tool automatically rejects dates < 30 days old

2. **Files from cloud sync**
   - Some cloud services update modification times
   - *Solution:* Use `--no-file-mtime` to disable this fallback

3. **Edited files**
   - Screenshots edited in an app
   - *Note:* Many apps preserve CreateDate even if ModifyDate changes

## What Stays in Unknown?

After reorganization, files remain in Unknown if:

1. ❌ No EXIF DateTimeOriginal, CreateDate, or ModifyDate
2. ❌ File modification time is invalid or too recent
3. ❌ File is genuinely undatable (e.g., fresh screenshot with no EXIF)

These are typically:
- Recent screenshots (< 30 days old)
- Files with corrupted metadata
- Downloaded images from the internet
- Files with modification dates after copying

## Troubleshooting

### "exiftool not found"

Install exiftool first:
```bash
# macOS
brew install exiftool

# Linux
sudo apt install libimage-exiftool-perl

# Windows
# Download from https://exiftool.org/
```

### "ModuleNotFoundError: No module named 'rich'"

Activate the virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Or reinstall dependencies:
```bash
pip install -r requirements.txt
```

### "Unknown folder not found"

Make sure you're pointing to the correct path:
```bash
# List Output contents to find Unknown
ls /path/to/Output/

# Should see:
# 2015/ 2016/ 2017/ ... Unknown/
```

### Files not moving

Check the log file for details:
```bash
tail -100 metadata_embedder.log
```

Look for:
- "File mtime too recent" → File was copied recently
- "No EXIF date found" → File has no metadata
- "File mtime in future" → Invalid timestamp

## Checking Results

After reorganization, verify the changes:

```bash
# Count files moved
ls -R /path/to/Output/2015 /path/to/Output/2016 | wc -l

# Check what's left in Unknown
ls /path/to/Output/Unknown | wc -l

# View log for details
tail -100 metadata_embedder.log
```

## Backup Recommendation

**Before running reorganization:**

```bash
# Create a backup of Unknown folder (optional but recommended)
cp -r /path/to/Output/Unknown /path/to/Output/Unknown.backup
```

If something goes wrong, restore:
```bash
rm -rf /path/to/Output/Unknown
mv /path/to/Output/Unknown.backup /path/to/Output/Unknown
```

## Performance

Expected processing speed:
- **~50-100 files per second** (depends on EXIF complexity)
- **11,235 files** → **~2-4 minutes**
- Parallel processing uses 4-8 workers automatically

## Summary

The reorganize feature is designed to safely move files from Unknown to proper date folders using multiple fallback methods. It's conservative by default and includes safety checks to avoid incorrect dates.

**Simple workflow:**
1. Run `./run.sh`
2. Point to your folder
3. Choose option 1 when prompted
4. Answer 'y' to use file modification time fallback

This should successfully organize **60-80%** of your Unknown folder!

## Advanced: Command-Line Usage

For power users who want to skip the interactive prompts:

```bash
# Reorganize with file mtime fallback
python main.py --reorganize-unknown /path/to/Output/Unknown

# EXIF only (no file mtime)
python main.py --reorganize-unknown /path/to/Output/Unknown --no-file-mtime

# Custom minimum age
python main.py --reorganize-unknown /path/to/Output/Unknown --min-age-days 60
```
