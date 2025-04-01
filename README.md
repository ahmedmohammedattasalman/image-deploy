# Image Editing with Gemini AI and Supabase Storage

This application allows you to edit images using Google's Gemini AI model. It stores images in Supabase for cloud storage instead of local storage.

## Features

- Upload images and edit them with natural language prompts
- See side-by-side comparisons of original and edited images  
- Store all images in Supabase cloud storage
- Continue editing images with sequential prompts
- View your edit history

## Setup

### Prerequisites

- Python 3.8+
- Flask
- Google Gemini AI API key
- Supabase project

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ahmedmohammedattasalman/image-editing.git
   cd image-editing
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Supabase resources:
   ```bash
   python setup_supabase.py
   ```

   This script will:
   - Check if the needed storage bucket exists and create it if not
   - Provide SQL to create the necessary database table

4. Create the following table in your Supabase SQL editor:
   ```sql
   CREATE TABLE images (
     id UUID PRIMARY KEY,
     file_path TEXT NOT NULL,
     image_type TEXT NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
   );
   ```

5. Create a storage bucket named "images" in Supabase with public access.

6. Run the application:
   ```bash
   python main.py
   ```

7. Open your browser to [http://localhost:5000](http://localhost:5000)

## Configuration

The main configuration is in `main.py`:

- `API_KEY`: Your Google Gemini AI API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key

## How It Works

1. Upload an image or continue editing a previous one
2. Enter a natural language prompt describing the edit you want
3. The application sends your image and prompt to Google's Gemini AI
4. The edited image is returned and displayed alongside the original
5. Both original and edited images are stored in Supabase for future reference
6. You can continue editing the result with additional prompts

## Storage Structure

Images are stored in Supabase with:
- Storage bucket: "images"
- Folders: "original" and "edited"
- Database table: "images" that tracks all stored images

## License

[MIT](https://choosealicense.com/licenses/mit/) 