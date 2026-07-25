# Hugging Face Spaces Deployment Guide

## Step 1: Clean Up Your Project

Delete these files/folders before uploading:
```bash
# Remove virtual environment
rm -rf .venv/

# Remove Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Remove local database
rm -f user_context.db

# Remove your local .env file (contains secrets)
rm -f .env
```

## Step 2: Create Hugging Face Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Fill in details:
   - **Space name**: `blood-report-analyzer` (or your preferred name)
   - **License**: MIT
   - **SDK**: Streamlit
   - **Hardware**: CPU basic (free tier)
   - **Visibility**: Public or Private

## Step 3: Upload Your Files

Upload these files to your Space:
- `app.py` (main entry point)
- `requirements.txt` (dependencies)
- `packages.txt` (system packages)
- `src/` folder (all source code)
- `config/` folder (configuration files)
- `README_HF.md` (rename to README.md in the Space)

## Step 4: Configure Environment Variables

In your Hugging Face Space settings, add these secrets:

### Required:
- `HF_API_TOKEN`: Your Hugging Face API token
  - Get from: https://huggingface.co/settings/tokens
  - Needs "Read" permission

### Optional (for better OCR):
- `OCR_SPACE_API_KEY`: Free OCR API key
  - Get from: https://ocr.space/ocrapi/freekey
  - 500 free requests/day

### Automatic Configuration:
These are set automatically in the Dockerfile:
- `LLM_PROVIDER_PRIORITY=hf_only` (uses HF API only)
- `OCR_PROVIDER_PRIORITY=api_first` (prefers cloud OCR)

## Step 5: Model Configuration

Your app is already configured to use:
- **Model**: `mistralai/Mistral-7B-Instruct-v0.2`
- **API**: Hugging Face Inference API (no download needed)
- **Fallback**: Automatic error handling

## Step 6: Test Your Deployment

1. Wait for the Space to build (2-5 minutes)
2. Test with a sample blood report
3. Verify OCR extraction works
4. Test AI chat functionality

## Troubleshooting

### Common Issues:

1. **Model Loading Error**:
   - Wait 1-2 minutes for model to warm up
   - Check HF_API_TOKEN is set correctly

2. **OCR Not Working**:
   - Add OCR_SPACE_API_KEY for better results
   - Tesseract is included as fallback

3. **Memory Issues**:
   - Upgrade to CPU basic+ if needed
   - Optimize image processing in code

### Environment Variables Summary:

```bash
# Required
HF_API_TOKEN=hf_your_token_here

# Optional (recommended)
OCR_SPACE_API_KEY=your_ocr_key_here

# Auto-set by Dockerfile
LLM_PROVIDER_PRIORITY=hf_only
OCR_PROVIDER_PRIORITY=api_first
```

## Benefits of This Setup:

1. **No Model Download**: Uses HF Inference API
2. **Automatic Scaling**: HF handles model loading
3. **Cost Effective**: Free tier available
4. **Easy Updates**: Just push code changes
5. **Built-in OCR**: Multiple OCR providers supported

## File Structure for Upload:

```
your-hf-space/
├── app.py                 # Main entry point
├── requirements.txt       # Python dependencies  
├── packages.txt          # System packages
├── README.md             # Space description
├── src/                  # Source code
│   ├── core/
│   ├── ui/
│   ├── utils/
│   └── ...
└── config/               # Configuration files
```

Your app will be available at: `https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME`