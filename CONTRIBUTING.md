# Contributing to Google Takeout Metadata Embedder

Thank you for considering contributing to this project! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear description of the problem
- Steps to reproduce
- Your environment (OS, Python version, exiftool version)
- Relevant log output from `metadata_embedder.log`

### Suggesting Features

Feature requests are welcome! Please open an issue describing:
- The feature you'd like to see
- Why it would be useful
- How it might work

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Add docstrings to functions
- Keep functions focused and single-purpose
- Add comments for complex logic
- Update README if you change functionality

### Testing

Before submitting a PR:
- Test with various media formats (JPG, PNG, HEIC, MP4, etc.)
- Test with different JSON metadata scenarios
- Verify error handling works gracefully
- Check that originals remain untouched

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/google-takeout-metadata-embedder.git
cd google-takeout-metadata-embedder

# Run setup
./setup.sh

# Make your changes

# Test locally
./run.sh
```

## Questions?

Feel free to open an issue for any questions!
