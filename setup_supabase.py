import os
import time
import random
import requests
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables (if using .env file)
load_dotenv()

# Supabase Configuration 
SUPABASE_URL = "https://ydmzuujthdrokuosbvyt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlkbXp1dWp0aGRyb2t1b3Nidnl0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzNDA0OTMsImV4cCI6MjA1ODkxNjQ5M30.YYtcgWWV59AcM30JUbq91yYVgGGkU8pk3kNofiZC19I"

# Initialize Supabase client with retry logic
def get_supabase_client(max_retries=3):
    """Get a Supabase client with retry logic"""
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, 0.5)
                sleep_time = retry_delay * (2 ** attempt) + jitter
                print(f"Connection error initializing Supabase client, retrying in {sleep_time:.2f} seconds... ({attempt+1}/{max_retries})")
                time.sleep(sleep_time)
            else:
                print(f"Failed to initialize Supabase client after {max_retries} attempts: {str(e)}")
                return None
        except Exception as e:
            print(f"Error initializing Supabase client: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return None
    
    return None

def setup_supabase():
    """Set up the required Supabase resources"""
    print("Setting up Supabase resources...")
    
    # Get a Supabase client
    supabase = get_supabase_client()
    if not supabase:
        print("ERROR: Could not initialize Supabase client. Please check your connection and credentials.")
        return False
    
    # Create the images table if it doesn't exist
    try:
        # Check if the images table exists
        response = supabase.table('images').select('id').limit(1).execute()
        print("Images table already exists.")
    except Exception as e:
        if "relation \"images\" does not exist" in str(e):
            print("Images table does not exist.")
            # Create the table using SQL
            print("Please create the images table in the Supabase dashboard with the following SQL:")
            print("""
            CREATE TABLE images (
              id UUID PRIMARY KEY,
              file_path TEXT NOT NULL,
              image_type TEXT NOT NULL,
              created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
            """)
        else:
            print(f"Error checking for images table: {str(e)}")
    
    # Create storage bucket for images if it doesn't exist
    bucket_created = False
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Check if the bucket exists by trying to get its details
            bucket_name = "images"
            buckets = supabase.storage.list_buckets()
            
            bucket_exists = any(bucket.name == bucket_name for bucket in buckets)
            
            if not bucket_exists:
                print(f"Creating '{bucket_name}' bucket...")
                # Create the storage bucket
                supabase.storage.create_bucket(
                    bucket_name,
                    {"public": True}  # Make the bucket public
                )
                print(f"Bucket '{bucket_name}' created successfully.")
                bucket_created = True
            else:
                print(f"Bucket '{bucket_name}' already exists.")
                bucket_created = True
            
            # If successful, break the retry loop
            break
                
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, 0.5)
                sleep_time = retry_delay * (2 ** attempt) + jitter
                print(f"Connection error checking storage bucket, retrying in {sleep_time:.2f} seconds... ({attempt+1}/{max_retries})")
                time.sleep(sleep_time)
                # Try to get a fresh client for the next attempt
                supabase = get_supabase_client()
                if not supabase:
                    print("Failed to reconnect to Supabase")
                    return False
            else:
                print(f"Error with storage bucket after {max_retries} attempts: {str(e)}")
        except Exception as e:
            print(f"Error with storage bucket: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                # Try to get a fresh client for the next attempt
                supabase = get_supabase_client()
                if not supabase:
                    print("Failed to reconnect to Supabase")
                    return False
            else:
                break
    
    return bucket_created

if __name__ == "__main__":
    success = setup_supabase()
    if success:
        print("Setup completed successfully. You can now run the main application.")
    else:
        print("Setup completed with some issues. Check the logs above for details.") 