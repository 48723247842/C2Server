from sanic import Blueprint
from sanic.response import json as json_result
from sanic import response

import json
import time
from pprint import pprint

import redis
import redis_circular_list
import requests

import asyncio
import websockets

json_headers = {
	'accept': 'application/json, text/plain, */*'
}

def redis_connect():
	try:
		redis_connection = redis.StrictRedis(
			host="127.0.0.1" ,
			port="6379" ,
			db=1 ,
			#password=ConfigDataBase.self[ 'redis' ][ 'password' ]
			)
		return redis_connection
	except Exception as e:
		return False

def get_json( url , headers=json_headers , params={} ):
	try:
		result = requests.get( url , headers=headers , params=params )
		result.raise_for_status()
		result = result.json()
		return result
	except Exception as e:
		return False

async def _websocket_send( host , message ):
	async with websockets.connect( host ) as websocket:
		await websocket.send( json.dumps( message ) )
		result = await websocket.recv()
		return result

def websocket_send( host , message ):
	try:
		result = asyncio.get_event_loop().run_until_complete( _websocket_send( host , message ) )
		print( result )
		return result
	except Exception as e:
		print( e )
		return False


buttons_blueprint = Blueprint( 'buttons_blueprint' , url_prefix='/button' )

@buttons_blueprint.route( '/' )
def commands_root( request ):
	return response.text( "you are at the /button url\n" )

@buttons_blueprint.route( "/1" , methods=[ "GET" ] )
@buttons_blueprint.route( "/spotify/playlists/currated" , methods=[ "GET" ] )
def spotify_playlists_currated( request ):
	result = { "message": "failed" }
	try:

		redis_connection = redis_connect()

		current_mode = redis_connection.get( "STATE.MODE" )

		# Stop Previous 'Mode'
		if current_mode is not None:
			current_mode = str( current_mode , 'utf-8' )
			current_mode = json.loads( current_mode )
			if "websocket" in current_mode["control_endpoints"]:
				websocket_send( current_mode["control_endpoints"]["websocket"]["host"] , current_mode["control_endpoints"]["websocket"]["stop"] )
			else:
				result["stop_current_mode_endpoint"] = current_mode["control_endpoints"]["stop"]
				result["stop_current_mode_response"] = get_json( result["stop_current_mode_endpoint"] )

		result["play_endpoint"] = "http://127.0.0.1:11101/api/play"
		result["play_response"] = get_json( result["play_endpoint"] )

		time.sleep( 1 )

		result["status_endpoint"] = "http://127.0.0.1:11101/api/get/playback/status"
		result["status_response"] = get_json( result["status_endpoint"] )

		mode = {
			"button": 1 ,
			"type": "spotify" ,
			"name": "Playing Spotify Curated Playlist" ,
			"state": False ,
			"status_object": result["status_response"] ,
			"control_endpoints": {
				"pause": "http://127.0.0.1:11101/api/pause" ,
				"resume": "http://127.0.0.1:11101/api/resume" ,
				"play": "http://127.0.0.1:11101/api/play" ,
				"stop": "http://127.0.0.1:11101/api/stop" ,
				"previous": "http://127.0.0.1:11101/api/previous" ,
				"next": "http://127.0.0.1:11101/api/next" ,
				"status": "http://127.0.0.1:11101/api/get/playback/status"
			}
		}

		if result["status_response"]["status"].lower() == "playing":
			mode["state"] = "playing"
			result["message"] = "success"
			result["mode"] = mode
			redis_connection.set( "STATE.MODE" , json.dumps( mode ) )
		else:
			raise Exception( "Could Not Get Spotify To Start Playing" )

		# pprint( result )
		# mode["state"] = "playing"
		# result["message"] = "success"
		# result["mode"] = mode
		# redis_connection.set( "STATE.MODE" , json.dumps( mode ) )

	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@buttons_blueprint.route( "/2" , methods=[ "GET" ] )
@buttons_blueprint.route( "/local/tv/next" , methods=[ "GET" ] )
def local_tv_next_episode( request ):
	result = { "message": "failed" }
	try:
		redis_connection = redis_connect()

		current_mode = redis_connection.get( "STATE.MODE" )

		# 1.) Stop Previous 'Mode'
		if current_mode is not None:
			current_mode = str( current_mode , 'utf-8' )
			current_mode = json.loads( current_mode )
			if "websocket" in current_mode["control_endpoints"]:
				websocket_send( current_mode["control_endpoints"]["websocket"]["host"] , current_mode["control_endpoints"]["websocket"]["stop"] )
			else:
				result["stop_current_mode_endpoint"] = current_mode["control_endpoints"]["stop"]
				result["stop_current_mode_response"] = get_json( result["stop_current_mode_endpoint"] )

		mode = {
			"button": 2 ,
			"type": "local" ,
			"name": "Playing Local TV Show , Next Episode" ,
			"file_path": None ,
			"state": False ,
			"status": None ,
			"control_endpoints": {
				"pause": "http://127.0.0.1:11301/api/tv/pause" ,
				"resume": "http://127.0.0.1:11301/api/tv/resume" ,
				"play": "http://127.0.0.1:11301/api/tv/play" ,
				"stop": "http://127.0.0.1:11301/api/tv/stop" ,
				"previous": "http://127.0.0.1:11301/api/tv/previous" ,
				"next": "http://127.0.0.1:11301/api/tv/next" ,
				"status": "http://127.0.0.1:11301/api/tv/status" ,
				"fullscreen": "http://127.0.0.1:11301/vlc/fullscreen/on"
			}
		}

		# 2.) Play Next TV Episode in 'Next' TV Show Circular List
		result["play_endpoint"] = "http://127.0.0.1:11301/api/tv/play"
		result["play_response"] = get_json( result["play_endpoint"] )

		#time.sleep( 1 )
		time.sleep( 3 )

		result["status_endpoint"] = "http://127.0.0.1:11301/api/tv/status"
		result["status_response"] = get_json( result["status_endpoint"] )
		mode["status"] = result["status_response"]

		if result["status_response"] == False:
			raise Exception( "No Status Response from :11301/api/tv/status" )
		if "status" not in result["status_response"]:
			raise Exception( "No Status Response from :11301/api/tv/status" )
		if "state" not in result["status_response"]["status"]:
			raise Exception( "No State Stored in Status Response from :11301/api/tv/status" )

		if result["status_response"]["status"]["state"].lower() == "playing":

			print( "Local TV Show Started Playing via VLC" )
			mode["state"] = "playing"
			result["message"] = "success"
			result["mode"] = mode

			# VLC Full Screen
			result["full_screen_response"] = get_json( mode["control_endpoints"]["fullscreen"] )

			redis_connection.set( "STATE.MODE" , json.dumps( mode ) )
		else:
			raise Exception( "Could Not Get Next Local TV Show Episode to Start Playing" )

	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@buttons_blueprint.route( "/4" , methods=[ "GET" ] )
@buttons_blueprint.route( "/websites/disney" , methods=[ "GET" ] )
def local_tv_next_episode( request ):
	result = { "message": "failed" }
	try:
		redis_connection = redis_connect()

		current_mode = redis_connection.get( "STATE.MODE" )
		if current_mode is not None:
			current_mode = str( current_mode , 'utf-8' )
			current_mode = json.loads( current_mode )
			if "websocket" in current_mode["control_endpoints"]:
				websocket_send( current_mode["control_endpoints"]["websocket"]["host"] , current_mode["control_endpoints"]["websocket"]["stop"] )
			else:
				result["stop_current_mode_endpoint"] = current_mode["control_endpoints"]["stop"]
				result["stop_current_mode_response"] = requests.get( result["stop_current_mode_endpoint"] , headers=json_headers )
				result["stop_current_mode_response"].raise_for_status()
				result["stop_current_mode_response"] = result["stop_current_mode_response"].json()
				#time.sleep( 1 )

		mode = {
			"button": 4 ,
			"type": "websites" ,
			"name": "Playing Disney+ , Next Movie" ,
			"file_path": None ,
			"state": False ,
			"status": None ,
			"control_endpoints": {
				"websocket": {
					"host": "ws://127.0.0.1:10081" ,
					"pause": { "channel": "disney_plus" , "message": "pause" } ,
					"resume": { "channel": "disney_plus" , "message": "resume" } ,
					"play": { "channel": "disney_plus" , "message": "start" } ,
					"stop": { "channel": "disney_plus" , "message": "stop" } ,
					"previous": { "channel": "disney_plus" , "message": "previous" } ,
					"next": { "channel": "disney_plus" , "message": "next" } ,
					"status": { "channel": "disney_plus" , "message": "status" }
				}
			}
		}

		result["play_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["play"] )

		print( "DisneyPlus Playing via Chrome" )
		mode["state"] = "playing"
		result["message"] = "success"
		result["mode"] = mode
		redis_connection.set( "STATE.MODE" , json.dumps( mode ) )

	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@buttons_blueprint.route( "/6" , methods=[ "GET" ] )
@buttons_blueprint.route( "/pause" , methods=[ "GET" ] )
def pause( request ):
	result = { "message": "failed" }
	try:
		redis_connection = redis_connect()

		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		if mode["state"] == "playing":
			if "websocket" in mode["control_endpoints"]:
				result["pause_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["pause"] )
			else:
				pause_response = requests.get( mode["control_endpoints"]["pause"] , headers=json_headers )
				pause_response.raise_for_status()
				result["pause_response"] = pause_response.json()
		else:
			if "websocket" in mode["control_endpoints"]:
				result["resume_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["resume"] )
			else:
				resume_response = requests.get( mode["control_endpoints"]["resume"] , headers=json_headers )
				resume_response.raise_for_status()
				result["resume_response"] = resume_response.json()

		time.sleep( 1 )

		if "websocket" in mode["control_endpoints"]:
			result["status_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["status"] )
		else:
			status_response = requests.get( mode["control_endpoints"]["status"] , headers=json_headers )
			status_response.raise_for_status()
			result["status_response"] = status_response.json()

		mode["status_object"] = result["status_response"]
		mode["state"] = mode["status_object"]["status"].lower()

		result["message"] = "success"
		result["mode"] = mode
		redis_connection.set( "STATE.MODE" , json.dumps( mode ) )

	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@buttons_blueprint.route( "/7" , methods=[ "GET" ] )
@buttons_blueprint.route( "/previous" , methods=[ "GET" ] )
def previous( request ):
	result = { "message": "failed" }
	try:
		redis_connection = redis_connect()

		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		if "websocket" in mode["control_endpoints"]:
			result["previous_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["previous"] )
		else:
			previous_response = requests.get( mode["control_endpoints"]["previous"] , headers=json_headers )
			previous_response.raise_for_status()
			result["previous_response"] = previous_response.json()

		time.sleep( 1 )

		if "websocket" in mode["control_endpoints"]:
			result["status_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["status"] )
		else:
			status_response = requests.get( mode["control_endpoints"]["status"] , headers=json_headers )
			status_response.raise_for_status()
			result["status_response"] = status_response.json()

		mode["status_object"] = result["status_response"]
		mode["state"] = mode["status_object"]["status"].lower()

		result["message"] = "success"
		result["mode"] = mode
		redis_connection.set( "STATE.MODE" , json.dumps( mode ) )

	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@buttons_blueprint.route( "/8" , methods=[ "GET" ] )
@buttons_blueprint.route( "/stop" , methods=[ "GET" ] )
def stop( request ):
	result = { "message": "failed" }
	try:
		redis_connection = redis_connect()

		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		if "websocket" in mode["control_endpoints"]:
			result["stop_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["stop"] )
		else:
			stop_response = requests.get( mode["control_endpoints"]["stop"] , headers=json_headers )
			stop_response.raise_for_status()
			result["stop_response"] = stop_response.json()

		time.sleep( 1 )

		if "websocket" in mode["control_endpoints"]:
			result["status_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["status"] )
		else:
			status_response = requests.get( mode["control_endpoints"]["status"] , headers=json_headers )
			status_response.raise_for_status()
			result["status_response"] = status_response.json()

		mode["status_object"] = result["status_response"]
		mode["state"] = mode["status_object"]["status"].lower()

		result["message"] = "success"
		result["mode"] = mode
		redis_connection.set( "STATE.MODE" , json.dumps( mode ) )

	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@buttons_blueprint.route( "/9" , methods=[ "GET" ] )
@buttons_blueprint.route( "/next" , methods=[ "GET" ] )
def next( request ):
	result = { "message": "failed" }
	try:

		redis_connection = redis_connect()

		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		if "websocket" in mode["control_endpoints"]:
			result["next_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["next"] )
		else:
			next_response = requests.get( mode["control_endpoints"]["next"] , headers=json_headers )
			next_response.raise_for_status()
			result["next_response"] = next_response.json()

		time.sleep( 1 )

		if "websocket" in mode["control_endpoints"]:
			result["status_response"] = websocket_send( mode["control_endpoints"]["websocket"]["host"] , mode["control_endpoints"]["websocket"]["status"] )
		else:
			status_response = requests.get( mode["control_endpoints"]["status"] , headers=json_headers )
			status_response.raise_for_status()
			result["status_response"] = status_response.json()

		mode["status_object"] = result["status_response"]
		mode["state"] = mode["status_object"]["status"].lower()

		result["message"] = "success"
		result["mode"] = mode
		redis_connection.set( "STATE.MODE" , json.dumps( mode ) )

	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )
