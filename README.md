# AI Image Enhancement and Editing

A web application for enhancing and editing images using Google's Gemini AI. This application allows users to upload images and apply AI-driven edits through natural language prompts.

## Features

- **Natural Language Image Editing**: Edit images by describing what you want in plain language
- **Progressive Editing**: Continue editing the same image with multiple prompts
- **Image Comparison**: Slide to compare original and edited images
- **Gallery View**: Browse all your edited images
- **Image Storage**: Images are stored in Supabase cloud storage
- **Bilingual Support**: Available in English and Arabic
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: Flask (Python)
- **AI Model**: Google Gemini 2.0 Flash Experimental Image Generation
- **Cloud Storage**: Supabase
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Image Processing**: PIL (Python Imaging Library)
- **Deployment**: Railway

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ahmedmohammedattasalman/image-editing.git
   cd image-editing
   ```

2. Install the required packages:
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

7. Open your browser and navigate to `http://127.0.0.1:5000/`

## Railway Deployment

To deploy this application on Railway:

1. Create a new Railway project
2. Connect your GitHub repository
3. Configure the following environment variables in Railway:
   - `API_KEY`: Your Google Gemini API key
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase project API key

4. Railway will automatically detect the Dockerfile and deploy your application
5. Access your deployed application using the provided Railway URL

## Usage

1. Upload an image using the drag-and-drop area or file selector
2. Describe your desired edit in the text area (e.g., "Make it black and white", "Remove the background")
3. Click "Generate Edited Image" to process your request
4. Use the comparison slider to see the difference between original and edited images
5. Download the edited image or continue editing with another prompt
6. View your edit history in the gallery

## Configuration

The application uses the following environment variables:

- `API_KEY`: Google Gemini API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase project API key

## Error Handling

The application includes robust error handling for:
- Large images (automatic compression)
- API overload conditions (retries with exponential backoff)
- Network issues (automatic reconnection)

## License

MIT License

## Author

Ahmed Mohammed Atta Salman 