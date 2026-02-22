# Reorganizing the Unknown Folder

This guide shows you how to use the enhanced `--reorganize-unknown` feature to move files from your Unknown folder into properly organized date-based folders.

## What's New?

The enhanced version now checks **multiple date sources**:

1. ✅ **EXIF DateTimeOriginal** (when photo was taken)
2. ✅ **EXIF CreateDate** (when file was created - helps with PNG/screenshots)
3. ✅ **EXIF ModifyDate** (when file was modified - fallback for edited files)
4. ✅ **File modification time** (with safety checks - optional)

## Quick Start (Copy to Another Computer)

### Step 1: Copy the Tool

Copy the entire `google-takeout-metadata-embedder` folder to your other computer:
- Via USB drive, network share, or cloud storage
- Make sure to copy the entire folder including the `lib/` subdirectory

### Step 2: Install Dependencies

On the other computer, open Terminal and run:

```bash
# macOS
brew install exiftool
brew install python3

# Linux (Ubuntu/Debian)
sudo apt install libimage-exiftool-perl python3 python3-venv

# Windows
# Download Python from python.org
# Download exiftool from exiftool.org
```

### Step 3: Set Up Python Environment

```bash
cd google-takeout-metadata-embedder
./setup.sh
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Run the Reorganization

**Basic usage** (recommended):
```bash
source venv/bin/activate
python main.py --reorganize-unknown /path/to/Output/Unknown
```

**EXIF only** (no file modification time):
```bash
python main.py --reorganize-unknown /path/to/Output/Unknown --no-file-mtime
```

**Custom minimum age** (stricter validation):
```bash
python main.py --reorganize-unknown /path/to/Output/Unknown --min-age-days 60
```

## Examples

### Example 1: Reorganize Unknown Folder on External Drive

```bash
# Activate environment
source venv/bin/activate

# Run reorganization
python main.py --reorganize-unknown /Volumes/PortableSSD/Media/Output/Unknown
```

Output:
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

### Example 2: Conservative Mode (EXIF Only)

If you don't trust file modification times:

```bash
python main.py --reorganize-unknown /Volumes/PortableSSD/Media/Output/Unknown --no-file-mtime
```

This will **only** use EXIF data (DateTimeOriginal, CreateDate, ModifyDate) and skip the file modification time fallback.

### Example 3: Stricter Validation

Require files to be at least 60 days old:

```bash
python main.py --reorganize-unknown /Volumes/PortableSSD/Media/Output/Unknown --min-age-days 60
```

This rejects any file modification dates from the last 60 days (likely from recent copy operations).

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

The `--reorganize-unknown` feature is designed to safely move files from Unknown to proper date folders using multiple fallback methods. It's conservative by default and includes safety checks to avoid incorrect dates.

**Recommended command:**
```bash
python main.py --reorganize-unknown /path/to/Output/Unknown
```

This should successfully organize 60-80% of your Unknown folder!
