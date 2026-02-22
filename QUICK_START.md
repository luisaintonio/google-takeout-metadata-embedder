# Quick Start: Reorganizing Your Unknown Folder

## The Simple Way (3 Steps)

### 1. Run the tool
```bash
./run.sh
```

### 2. Enter your folder path
```
Enter the path to your Google Takeout folder:
> /Volumes/PortableSSD/Media
```

### 3. Choose what to do
If the tool finds an Unknown folder, you'll see:

```
Found existing Unknown folder with 11,235 media file(s)

Would you like to:
  1. Reorganize Unknown folder with enhanced date detection
  2. Process the entire folder normally

Enter choice (1 or 2):
> 1

Use file modification time as fallback? (y/n):
Recommended: y - Uses EXIF + safe file dates (older than 30 days)
> y
```

**That's it!** The tool handles everything else.

## What Gets Fixed

The enhanced version now checks:
- ✅ EXIF DateTimeOriginal (camera date)
- ✅ EXIF CreateDate (file creation - helps with screenshots)
- ✅ EXIF ModifyDate (last modified in app)
- ✅ File modification time (with safety checks)

**Expected results:**
- ~8,000-9,000 files moved from Unknown → proper date folders
- ~2,000-3,000 files stay in Unknown (truly undatable)
- Unknown folder: 112GB → ~20-30GB
- Processing time: 2-4 minutes

## Safety Checks

File modification time is ONLY used if:
- ✅ Date is between 2000-2026
- ✅ Date is not in the future
- ✅ Date is older than 30 days (not recent copy)

Files that fail these checks stay in Unknown.

## Running on Another Computer

### Copy the folder
Transfer the entire `google-takeout-metadata-embedder` folder to your other computer (USB/network/cloud).

### Install exiftool
```bash
# macOS
brew install exiftool

# Linux
sudo apt install libimage-exiftool-perl
```

### Run setup
```bash
cd google-takeout-metadata-embedder
./setup.sh
```

### Run the tool
```bash
./run.sh
```

That's the entire process!

## Tips

**When to answer 'y' to file modification time:**
- Files from Google Takeout (dates are preserved)
- Files from camera SD card
- Files older than 30 days

**When to answer 'n':**
- You recently copied files (last week)
- You don't trust file timestamps
- You want to be extra conservative

## Troubleshooting

**"exiftool not found"**
```bash
brew install exiftool  # macOS
```

**"No module named 'rich'"**
```bash
./setup.sh
# or
source venv/bin/activate
```

**Check what happened:**
```bash
tail -100 metadata_embedder.log
```

---

**Full documentation:** See `REORGANIZE_UNKNOWN.md` for details
