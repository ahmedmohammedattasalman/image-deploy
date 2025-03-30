# AI Image Editor Web App

A web application that allows users to upload images and edit them using Google's Gemini AI.

## Features

- User-friendly web interface for image editing
- Upload images via drag-and-drop or file selection
- Describe edits using natural language
- View before and after images side by side
- Download edited images

## Setup Instructions

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python main.py
   ```

3. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Usage

1. Upload an image using the upload area
2. Enter a description of the edit you want to make
   - Examples: "Remove the background", "Change hair color to blonde", "Make it look like a cartoon"
3. Click "Generate Edited Image"
4. View the result and download the edited image if desired

## Requirements

- Python 3.7+
- Flask
- Google GenerativeAI API
- Pillow

## Note

The application uses Google's Gemini AI API for image generation. Make sure your API key in main.py is valid. 