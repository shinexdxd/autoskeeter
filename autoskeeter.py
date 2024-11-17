import obspython as obs
import requests
import json
import os
from datetime import datetime
from atproto import Client

# Settings for the script
bsky_username = "your_bluesky_username"  # BlueSky username for authentication
bsky_password = "your_bluesky_password"  # BlueSky password for authentication
skeet_message_template = "hey cuties, i'm 🔴 live now! 🔴 | {title} - come hang out: {link}"  # Template for the skeet message
last_skeet_time = None  # Keeps track of the last time a skeet was posted
thumbnail_url = ""  # URL for the thumbnail image (optional)
youtube_link = ""  # URL for the YouTube live stream
twitch_link = ""  # URL for the Twitch live stream
platform_selection = "YouTube"  # Default platform selection (YouTube, Twitch, or both)
live_description = "join me now for hangs, games, and good vibes 🍃"  # Default live stream description

# Initialize BlueSky client
client = Client()

# OBS script settings
def script_description():
    """
    Provides a description of the script for OBS Studio.
    """
    return "Automatically skeet to BlueSky when going live on YouTube or Twitch."

def script_properties():
    """
    Defines the properties (settings) for the OBS script, allowing the user to configure BlueSky credentials,
    skeet message template, and platform selection.
    """
    props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, "bsky_username", "BlueSky Username", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "bsky_password", "BlueSky Password", obs.OBS_TEXT_PASSWORD)
    obs.obs_properties_add_text(props, "skeet_message_template", "Skeet Message Template", obs.OBS_TEXT_MULTILINE)
    obs.obs_properties_add_text(props, "thumbnail_url", "Thumbnail URL (optional)", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "youtube_link", "YouTube Stream URL", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "twitch_link", "Twitch Stream URL", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "live_description", "Live Stream Description", obs.OBS_TEXT_MULTILINE)
    platform_options = obs.obs_properties_add_list(props, "platform_selection", "Platform Selection", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    obs.obs_property_list_add_string(platform_options, "YouTube", "youtube")
    obs.obs_property_list_add_string(platform_options, "Twitch", "twitch")
    obs.obs_property_list_add_string(platform_options, "Both", "both")
    return props

def script_update(settings):
    """
    Updates the script settings based on user input from OBS Studio.
    """
    global bsky_username, bsky_password, skeet_message_template, thumbnail_url, youtube_link, twitch_link, platform_selection, live_description
    bsky_username = obs.obs_data_get_string(settings, "bsky_username")
    bsky_password = obs.obs_data_get_string(settings, "bsky_password")
    skeet_message_template = obs.obs_data_get_string(settings, "skeet_message_template")
    thumbnail_url = obs.obs_data_get_string(settings, "thumbnail_url")
    youtube_link = obs.obs_data_get_string(settings, "youtube_link")
    twitch_link = obs.obs_data_get_string(settings, "twitch_link")
    platform_selection = obs.obs_data_get_string(settings, "platform_selection")
    live_description = obs.obs_data_get_string(settings, "live_description")

def authenticate_bsky():
    """
    Authenticates the BlueSky client using the provided username and password.
    """
    try:
        client.login(bsky_username, bsky_password)
        obs.script_log(obs.LOG_INFO, "BlueSky client logged in successfully.")
        return True
    except Exception as e:
        obs.script_log(obs.LOG_WARNING, f"Failed to authenticate with BlueSky: {e}")
        return False

def skeet_message(title, link):
    """
    Sends a skeet (post) to BlueSky with the given title and link. Optionally includes a thumbnail image.
    """
    global skeet_message_template, thumbnail_url, live_description
    post_text = skeet_message_template.format(title=title, link=link)
    obs.script_log(obs.LOG_INFO, f"Post text prepared: {post_text}")
    
    try:
        # Upload the thumbnail image to BlueSky if a valid URL is provided
        if thumbnail_url:
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                image_blob = client.upload_blob(response.content)
                obs.script_log(obs.LOG_INFO, f"Image uploaded successfully: {image_blob}")
                # Send post to BlueSky with the uploaded image and link embed
                client.send_post(text=post_text, embed={
                    '$type': 'app.bsky.embed.external',
                    'external': {
                        'uri': link,
                        'title': title,
                        'description': live_description
                    },
                    'images': [{
                        'alt': 'live stream thumbnail',
                        'image': image_blob.blob
                    }]
                })
                obs.script_log(obs.LOG_INFO, "Successfully skeeted to BlueSky!")
            else:
                obs.script_log(obs.LOG_ERROR, f"Failed to download thumbnail image: {response.status_code}")
        else:
            # Send post without an image if no thumbnail URL is provided
            client.send_post(text=post_text, embed={
                '$type': 'app.bsky.embed.external',
                'external': {
                    'uri': link,
                    'title': title,
                    'description': live_description
                }
            })
            obs.script_log(obs.LOG_INFO, "Successfully skeeted to BlueSky without an image!")
    except Exception as e:
        obs.script_log(obs.LOG_ERROR, f"Error sending post to BlueSky: {e}")

def on_event(event):
    """
    Handles OBS events. When streaming starts, it checks the selected platform(s) and sends skeets accordingly.
    """
    global last_skeet_time
    if event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTED:
        current_time = datetime.now()
        # Only post a skeet if enough time has passed since the last one (to avoid spamming)
        if last_skeet_time is None or (current_time - last_skeet_time).seconds > 300:
            if authenticate_bsky():
                # Send skeets based on platform selection
                if platform_selection == "youtube" and youtube_link:
                    youtube_title = "Live on YouTube!"
                    skeet_message(youtube_title, youtube_link)
                elif platform_selection == "twitch" and twitch_link:
                    twitch_title = "Live on Twitch!"
                    skeet_message(twitch_title, twitch_link)
                elif platform_selection == "both":
                    if youtube_link:
                        youtube_title = "Live on YouTube!"
                        skeet_message(youtube_title, youtube_link)
                    if twitch_link:
                        twitch_title = "Live on Twitch!"
                        skeet_message(twitch_title, twitch_link)
                
                last_skeet_time = current_time

# Register the event handler
obs.obs_frontend_add_event_callback(on_event)
