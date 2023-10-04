#azuracastreader.py

import requests
from bs4 import BeautifulSoup
import re
import json
from mutagen.mp3 import MP3
import os
import asyncio
from asyncio.tasks import sleep

# Sets global variable
firsttime = 0

async def main():
    # Gets the current song
    url = 'http://0.0.0.0:8000/'
    r = requests.get(url).text
    soup = BeautifulSoup(r, 'html.parser')
    cs = soup.find_all('td', 'streamdata')
    cs = cs[-1].renderContents()
    cs = str(cs).lstrip('b\'').rstrip('\'')
    cs.encode(encoding='utf-8', errors='xmlcharrefreplace')
    # Get filename
    title = cs+'.mp3'

    # Get json data
    with open('data.json', 'r') as data:
        jsondata = json.load(data)
        data.close()

    # Update the current song in the json
    jsondata['currentsong'] = title
    with open('data.json', 'w') as data:
        json.dump(jsondata, data, indent=4)
        data.close()

    # Check to make sure currentsong was updated
    print(f'Now Playing: {cs}')

    # Prepare title for cover art search
    cs = re.sub('.ft.*[a-zA-Z]*.-', '', cs)

    # Acquire cover art
    query = cs
    r = requests.get(f'https://musicstax.com/search?q={query}') 
    soup = BeautifulSoup(r.text, "html.parser")
    images = soup.find_all('img', src=True)
    src=""
    for image in images:
        if 'cover art' in image['alt']:
            src = image['src']
            break

    # Check to make sure the cover art is correct
    print(f'Cover art: {src}')

    # Prepare loop until next song
    name = jsondata['currentsong']
    audio = MP3(f'./music/{name}')
    duration = int(audio.info.length)

    # Starts loop
    await playing(name, duration)

# Loop to play the song
async def playing(csong, csduration):
    nsong = csong
    inplay = True

    # Deals with duration issues when first connecting to the radio (retries every 2 seconds, might cause rate limiting)
    global firsttime
    if firsttime == 0:
        # Check to make sure this loop only runs once
        print('first time loop')

        # The actual loop
        while nsong == csong:
            await sleep(2)
            url = 'http://0.0.0.0:8000/'
            r = requests.get(url).text
            soup = BeautifulSoup(r, 'html.parser')
            cs = soup.find_all('td', 'streamdata')
            cs = cs[-1].renderContents()
            cs = str(cs).lstrip('b\'').rstrip('\'')
            cs.encode(encoding='utf-8', errors='xmlcharrefreplace')
            cs = re.sub('.ft.*[a-zA-Z]*.-', '', cs)
            nsong = cs
        inplay = False

    # Should be running while song is playing
    while inplay:
        # Check to make sure that the 'inplay' loop has started
        print('inplay loop started')
        # waits until 3 seconds before the end of the song (to compensate for possible issues with first connecting)
        await sleep(csduration-3)
        # Checks every second to see if a new song is playing
        # If a new song is playing, both loops stop and main is called, repeating the process
        while nsong == csong:
            # Check to make sure a song update is being requested
            print('checking for song update')
            await sleep(1)
            url = 'http://0.0.0.0:8000/'
            r = requests.get(url).text
            soup = BeautifulSoup(r, 'html.parser')
            cs = soup.find_all('td', 'streamdata')
            cs = cs[-1].renderContents()
            cs = str(cs).lstrip('b\'').rstrip('\'')
            cs.encode(encoding='utf-8', errors='xmlcharrefreplace')
            cs = re.sub('.ft.*[a-zA-Z]*.-', '', cs)
            nsong = cs
        inplay=False
        # Check to make sure a new song has started
        print('new song started')
    await main()

# Begins async function from sync
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(main())
