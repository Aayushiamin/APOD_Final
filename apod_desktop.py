from datetime import date
import os
import datetime
import sys
import requests
import re
import hashlib
import urllib
import sqlite3
import argparse
import image_lib
import inspect
import pafy
from pathlib import Path


# Global variables
image_cache_directory = None  # Full path of image cache folder
image_cache_database = None   # Full path of image cache database
api_key_amod = 'JveOLPbUHcMdJhmjku3EqsTgUgJLsjWUtlIVyaxK'

def main():
    ## DO NOT CHANGE THIS FUNCTION ##
    # Get the APOD date from the command line
    apod_date = get_apod_date()    

    # Get the path of the directory in which this script resides
    script_dir = get_script_dir()

    # Initialize the image cache
    init_apod_cache(script_dir)

    # Add the APOD for the specified date to the cache
    apod_id = add_apod_to_cache(apod_date)

    # Get the information for the APOD from the DB
    apod_info = get_apod_info(apod_id)

    # Set the APOD as the desktop background image
    if apod_id != 0:
        result = image_lib.set_desktop_background_image(apod_info['img_file_path'])
        if result:
            print("Setting desktop to"+apod_info['img_file_path']+"...success")
def get_apod_date():
    # TODO: Complete function body
    parser = argparse.ArgumentParser(description='APOD Desktop')
    parser.add_argument('date', nargs='?', default=datetime.date.today().strftime('%Y-%m-%d'),
                    help='APOD date  should be format: YYYY-MM-DD')
    args = parser.parse_args()

    try:
        apod_date = datetime.datetime.strptime(args.date, '%Y-%m-%d').date()
        if apod_date < datetime.date(1995, 6, 16) or apod_date > datetime.date.today():
            raise ValueError()
    except ValueError:
        print('Error: Invalid APOD date specified.')
        print('Script execution aborted')
        sys.exit(1)
    return apod_date



def get_script_dir():
    ## DO NOT CHANGE THIS FUNCTION ##
    script_path = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
    return os.path.dirname(script_path)

def init_apod_cache(parent_dir):
    global image_cache_directory
    global image_cache_database

    # TODO: Determine the path of the image cache directory
    image_cache_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
   
    print(f"Image cache directory: {image_cache_directory}") 
    # TODO: Create the image cache directory if it does not already exist
    image_cache_path = Path(image_cache_directory)
    if not image_cache_path.exists():
        image_cache_path.mkdir(parents=True)
        print(f"Image Cache Directory Created")
    else:
        print(f"Image Cache Directory already exists.")

    # Determine the path of image cache DB
    image_cache_database = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'apod_project.db')
    print(f"Image cache database: {image_cache_database}") 

    # Create the DB if it does not already exist
    if not os.path.exists(image_cache_database):
        os.makedirs(os.path.dirname(image_cache_database), exist_ok=True)
        print("Image Cache DB Created")
    else:
        print("Image Cache DB already exists.")    


    # Connect to the SQLite database and create the table if it doesn't already exist
    connection = sqlite3.connect(image_cache_database)
    c = connection.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS apod_images_data
             (id INTEGER PRIMARY KEY, adob_Title TEXT, adob_Explanation TEXT, adob_Img_File_Path TEXT, hash TEXT)''')



# Check if an image with the same SHA-256 hash value already exists in the cache
def hash_file(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
        return hashlib.sha256(data).hexdigest()

def thumbnail_gen(videos_url):
    # regular expression pattern
    embed_pattern = r'https://www\.youtube\.com/embed/([a-zA-Z0-9_-]+)\?.*'      
    # Define the  for the thumbnail URL
    thumbnail_pattern = r'https://img.youtube.com/vi/\1/0.jpg'
    # replace the pattern in the input URL with the thumbnail URL
    image_url = re.sub(embed_pattern, thumbnail_pattern, videos_url)
    return image_url


def add_apod_to_cache(apod_date):
    print("APOD date : ", apod_date.isoformat())
    # TODO: Download the APOD information from the NASA API
    # TODO: Download the APOD image
    # TODO: Check whether the APOD already exists in the image cache
    # TODO: Save the APOD file to the image cache directory
    # TODO: Add the APOD information to the DB

    apod_img_url = f'https://api.nasa.gov/planetary/apod?api_key={api_key_amod}&date={apod_date.isoformat()}'
    response = requests.get(apod_img_url)
    data_apod = response.json()
    if data_apod['media_type'] == 'image':
        # Download the high-definition image file if it doesn't already exist in the cache
        image_url = data_apod['hdurl']
        print("Getting "+ apod_date.isoformat() +" APOD information from NASA...success")
        print("APOD title:",data_apod['title'])
        print("APOD URL:",image_url)
        print("Downloading image from ",image_url,"..success")
        
        image_title = re.sub(r'[^a-zA-Z0-9\s_]+', '', data_apod['title']).strip().replace(' ', '_')
        image_file_path = determine_apod_file_path(image_title,image_url)
        image_hash = hash_file(image_file_path) if os.path.exists(image_file_path) else None
        if not image_hash:
            image_hash = hash_file(image_file_path)
        print("APOD SHA-256:",image_hash)
        id = get_apod_id_from_db(image_hash)
        if id:
            print('Image already exists in cache.')
            return id[0]
        else:
            new_Last_Img_Id = add_apod_to_db(data_apod['title'], data_apod['explanation'], image_file_path, image_hash)
            print("APOD image is not already in cache.")
            print("APOD file path:",image_file_path)
            print("Saving image file as ",image_file_path, "...success")
            print("Adding APOD to image cache DB...success")
            return new_Last_Img_Id
    
    else:
        videos_url = data_apod['url']
        image_url = thumbnail_gen(videos_url)
        print("Getting "+ apod_date.isoformat() +" APOD information from NASA...success")
        print("APOD title:",data_apod['title'])
        print("APOD URL:",image_url)
        print("Downloading image from ",image_url,"..success")        
        image_title = re.sub(r'[^a-zA-Z0-9\s_]+', '', data_apod['title']).strip().replace(' ', '_')
        image_file_path = determine_apod_file_path(image_title,image_url)
        image_hash = hash_file(image_file_path) if os.path.exists(image_file_path) else None
        if not image_hash:
            image_hash = hash_file(image_file_path)
        print("APOD SHA-256:",image_hash)
        id = get_apod_id_from_db(image_hash)

        if id:
            print('Image already exists in cache.')
            return  id[0]
        else:
            new_Last_Img_Id = add_apod_to_db(data_apod['title'], data_apod['explanation'], image_file_path, image_hash)
            print("APOD image is not already in cache.")
            print("APOD file path:",image_file_path)
            print("Saving image file as ",image_file_path, "...success")
            print("Adding APOD to image cache DB...success")
            return new_Last_Img_Id


    return 0

def add_apod_to_db(title, explanation, file_path, sha256):
    # TODO: Complete function body
            # Add the image to the database 
    connection = sqlite3.connect(image_cache_database)
    c = connection.cursor()
    c.execute('INSERT INTO apod_images_data (adob_Title, adob_Explanation, adob_Img_File_Path, hash) VALUES (?, ?, ?, ?)',
                (title, explanation, file_path, sha256))
    new_Last_Id = c.lastrowid
    connection.commit()
    return new_Last_Id

def get_apod_id_from_db(image_sha256):
    # TODO: Complete function body
    connection = sqlite3.connect(image_cache_database)
    c = connection.cursor()
    c.execute('SELECT id FROM apod_images_data WHERE hash=?', (image_sha256,))
    existing_image_id = c.fetchone()
    connection.commit()
    return existing_image_id

def determine_apod_file_path(image_title, image_url):
   
    # TODO: Complete function body
    image_ext = os.path.splitext(urllib.parse.urlparse(image_url).path)
    image_ext = image_ext[1]
    image_title = re.sub(r'[^a-zA-Z0-9\s_]+', '', image_title)
    image_title = image_title.strip().replace(' ', '_')
    image_file_name = f'{image_title}{image_ext}'
    image_file_path = os.path.join(image_cache_directory, image_file_name)
    response = requests.get(image_url)
    with open(image_file_path, 'wb') as f:
        f.write(response.content)
    return image_file_path

def get_apod_info(image_id):
    # TODO: Query DB for image info
    # TODO: Put information into a dictionary
    connection = sqlite3.connect(image_cache_database)
    cursor = connection.cursor()
    cursor.execute('SELECT adob_Title, adob_Explanation, adob_Img_File_Path FROM apod_images_data WHERE id = ?', (image_id,))
    result = cursor.fetchone()

    apod_info = {
        'title': result[0], 
        'img_file_path': result[2],
        'explanation': result[1]
        
    }
    return apod_info

def get_all_apod_titles():
    connection = sqlite3.connect(image_cache_database)
    cursor = connection.cursor()
    cursor.execute('SELECT adob_Title from apod_images_data')
    connection.commit()
    result = cursor.fetchall()
    title_list = [row[0] for row in result]
    data = {'title': title_list}

    # TODO: Complete function body
    # NOTE: This function is only needed to support the APOD viewer GUI
    return data

if __name__ == '__main__':
    main()

