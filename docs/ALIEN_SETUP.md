# Alien Chat Setup Guide

## Getting Your Google Gemini API Key

1. **Visit Google AI Studio**: Go to https://makersuite.google.com/app/apikey
2. **Sign in**: Use your Google account
3. **Create API Key**: Click "Create API Key" 
4. **Copy the key**: Copy the generated API key

## Adding to Your Bot

1. **Edit your .env file**:
   ```bash
   # Add this line to your .env file
   GEMINI_API_KEY=your_actual_api_key_here
   ```

2. **Restart the bot** after adding the API key

## Testing the Commands

Once configured, you can use:
- `/alien <message>` - Chat with the alien