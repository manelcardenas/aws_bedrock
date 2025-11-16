# AWS Bedrock Playground - Frontend

A beautiful, modern web interface for interacting with AWS Bedrock AI models.

## Features

✨ **Text Summarization** - Summarize long texts into key points using Amazon Titan Text Express
🎨 **Image Generation** - Generate images from text descriptions using Amazon Titan Image Generator
⚙️ **Configuration Management** - Save API endpoints and keys locally in your browser
📱 **Responsive Design** - Works on desktop, tablet, and mobile devices
🎯 **Modern UI/UX** - Beautiful gradients, animations, and intuitive interface

## Local Development

To test the frontend locally before deployment:

1. **Open the HTML file directly in your browser:**
   ```bash
   # macOS
   open index.html
   
   # Linux
   xdg-open index.html
   
   # Windows
   start index.html
   ```

2. **Or use a local server (recommended):**
   ```bash
   # Python 3
   python3 -m http.server 8000
   
   # Then open: http://localhost:8000
   ```

## Configuration

Before using the playground, you need to configure:

1. **Text Summary API URL** - Your API Gateway endpoint for text summarization
2. **Image Generation API URL** - Your API Gateway endpoint for image generation  
3. **API Key** - Your API key for authentication

### Getting Your API Endpoints

After deploying the backend stacks:

```bash
# Get Text Summary API URL
cd ../infra
cdk deploy --outputs-file outputs.json
# Look for ApiEndpoint in outputs

# Get Image Generation API URL
cd ../infra_images
cdk deploy --outputs-file outputs.json
# Look for ApiEndpoint in outputs
```

### Getting Your API Keys

```bash
# For Text Summary API
aws apigateway get-api-key --api-key YOUR_KEY_ID --include-value --region eu-west-3

# For Image Generation API
aws apigateway get-api-key --api-key YOUR_KEY_ID --include-value --region us-west-2
```

## File Structure

```
src/frontend/
├── index.html          # Main HTML structure
├── css/
│   └── styles.css      # All styling and animations
├── js/
│   ├── config.js       # Configuration management
│   └── app.js          # Main application logic
└── README.md           # This file
```

## Technologies Used

- **HTML5** - Semantic markup
- **CSS3** - Modern styling with gradients, animations, flexbox
- **Vanilla JavaScript** - No frameworks, pure JS
- **Fetch API** - For API calls
- **LocalStorage API** - For configuration persistence

## Usage

### Text Summarization

1. Enter or paste text (up to 5000 characters)
2. Select number of summary points (1-10)
3. Click "Summarize"
4. Copy the result to clipboard

### Image Generation

1. Describe the image you want to generate
2. Click "Generate Image"
3. Download or open in new tab

## Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Opera (latest)

## Security

- API keys are stored locally in browser's LocalStorage
- All API calls are made over HTTPS
- No sensitive data is logged or stored on servers
- CORS is properly configured

## Deployment

The frontend is automatically deployed to AWS when you push changes:

```bash
git add .
git commit -m "Update frontend"
git push origin main
```

GitHub Actions will:
1. Build and package the frontend
2. Deploy to S3
3. Invalidate CloudFront cache
4. Make changes live globally

See `infra_frontend/` for deployment infrastructure.

## Troubleshooting

### API calls failing
- Check that API endpoints are correct
- Verify API key is valid
- Check browser console for errors
- Ensure CORS is properly configured on API Gateway

### Images not loading
- Check that the image API region is correct (us-west-2)
- Verify S3 bucket permissions
- Check that pre-signed URL hasn't expired

### Configuration not saving
- Check browser's LocalStorage is enabled
- Try clearing cache and reloading

## Contributing

1. Make changes in `src/frontend/`
2. Test locally
3. Commit and push to trigger deployment
4. Monitor GitHub Actions for deployment status

## License

This project is part of the AWS Bedrock learning repository.

