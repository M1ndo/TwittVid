import argparse
import shutil 

import requests 
from bs4 import BeautifulSoup
import json
import urllib.parse
import m3u8
from pathlib import Path
import re

import ffmpeg

##########################################
Green="\033[1;33m"
Blue="\033[1;34m"
Grey="\033[1;30m"
Reset="\033[0m"
Red="\033[1;31m"
##########################################


print("        "+Blue+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMMMNKWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMMNc.dWMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMWd. .kWMMMMMMMMMMMMMMMMMMMMMMW0KMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMk:;. 'OMMMMMMMMMMMMMMMMMMMMMWx.,0MMMMMMMMM")
print("        "+Blue+"MMMMMMMK:ok.  ,0MMMMMMMMMMMMMMMMMMMWO. .cXMMMMMMMM")
print("        "+Blue+"MMMMMMNl:KO.   ;KWNXK00O0000KXNWMMWO' .c;dWMMMMMMM")
print("        "+Blue+"MMMMMMx,xNk.    .;'...    ....';:l:.  ,0l,0MMMMMMM")
print("        "+Blue+"MMMMMK;,l;. .,:cc:;.                  .dx,lWMMMMMM")
print("        "+Blue+"MMMMWo    ,dKWMMMMWXk:.      .cdkOOxo,. ...OMMMMMM")
print("        "+Blue+"MMMM0'   cXMMWKxood0WWk.   .lkONMMNOOXO,   lWMMMMM")
print("        "+Blue+"MMMWl   ;XMMNo.    .lXWd. .dWk;;dd;;kWM0'  '0MMMMM")
print("        "+Blue+"kxko.   lWMMO.      .kMO. .OMMK;  .kMMMNc   oWMMMM")
print("        "+Blue+"X0k:.   ;KMMXc      :XWo  .dW0c,lo;;xNMK,   'xkkk0")
print("        "+Blue+"kko'     :KMMNkl::lkNNd.   .dkdKWMNOkXO,    .lOKNW")
print("        "+Blue+"0Kk:.     .lOXWMMWN0d,       'lxO0Oko;.     .ckkOO")
print("        "+Blue+"kkkdodo;.    .,;;;'.  .:ooc.     .        ...ck0XN")
print("        "+Blue+"0XWMMMMWKxc'.          ;dxc.          .,cxKK0OkkOO")
print("        "+Blue+"MMMMMMMMMMMN0d:'.  .'        .l'  .;lxKWMMMMMMMMMN")
print("        "+Blue+"MMMMMMMMMMMMMMMN0xo0O:,;;;;;;xN0xOXWMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMMMMMMMMMMMMMMMWWWWWMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM")
print("        "+Blue+"___________"+Green+"["+Reset+"  TwittVid"+Red+"]"+Blue+"___________")
print("      "+Blue+"_______"+Grey+" ["+Green+"Inspired From The Linux Choice"+Grey+"]"+Blue+"_______")
print("     "+Blue+"___________"+Grey+"["+Red+"Created By ybenel"+Grey+"]"+Blue+"___________"+Reset+"\n")


def download(video_url):
	video_player_url_prefix = 'https://twitter.com/i/videos/tweet/'
	video_host = ''
	output_dir = './output'

	# Parse the tweet ID
	video_url = video_url.split('?', 1)[0]
	tweet_user = video_url.split('/')[3]
	tweet_id = video_url.split('/')[5]
	tweet_dir = Path(output_dir + '/' + tweet_user + '/' + tweet_id)
	Path.mkdir(tweet_dir, parents = True, exist_ok = True)

	# Grab the video client HTML
	video_player_url = video_player_url_prefix + tweet_id
	video_player_response = requests.get(video_player_url)

	# Get the JS file with the Bearer token to talk to the API.
	# Twitter really changed things up.
	js_file_soup = BeautifulSoup(video_player_response.text, 'html.parser')
	js_file_url = js_file_soup.find('script')['src']
	js_file_response = requests.get(js_file_url)

	# Pull the bearer token out
	bearer_token_pattern = re.compile('Bearer ([a-zA-Z0-9%-])+')
	bearer_token = bearer_token_pattern.search(js_file_response.text)
	bearer_token = bearer_token.group(0)

	# Talk to the API to get the m3u8 URL
	player_config = requests.get('https://api.twitter.com/1.1/videos/tweet/config/' + tweet_id + '.json', headers={'Authorization': bearer_token})
	m3u8_url_get = json.loads(player_config.text)
	m3u8_url_get = m3u8_url_get['track']['playbackUrl']

	# Get m3u8
	m3u8_response = requests.get(m3u8_url_get, headers = {'Authorization': bearer_token})

	m3u8_url_parse = urllib.parse.urlparse(m3u8_url_get)
	video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname

	m3u8_parse = m3u8.loads(m3u8_response.text)

	if m3u8_parse.is_variant:
		print('Multiple resolutions found. Slurping all resolutions.')

		for playlist in m3u8_parse.playlists:
			resolution = str(playlist.stream_info.resolution[0]) + 'x' + str(playlist.stream_info.resolution[1])
			resolution_file = Path(tweet_dir) / Path(resolution + '.mp4')

			print('[+] Downloading ' + resolution)

			playlist_url = video_host + playlist.uri

			ts_m3u8_response = requests.get(playlist_url)
			ts_m3u8_parse = m3u8.loads(ts_m3u8_response.text)

			ts_list = []
			for ts_uri in ts_m3u8_parse.segments.uri:
				ts_list.append(video_host + ts_uri)

			# Convert TS to MP4
			ts_streams = [ ffmpeg.input(str(_)) for _ in ts_list ]
			(
			    ffmpeg
				.concat(*ts_streams)
				.output(str(resolution_file), strict=-2, loglevel='error')
				.overwrite_output()
				.run()
			)


if __name__ == '__main__':
	import sys

	if sys.version_info[0] == 2:
		print('Python3 is required.')
		sys.exit(1)

	parser = argparse.ArgumentParser()
	parser.add_argument('-v', '--video', dest='video_url', help='The video URL on Twitter (https://twitter.com/<user>/status/<id>).', required=True)

	args = parser.parse_args()

download(args.video_url)			
				
