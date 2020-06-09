from sanic import Blueprint
from sanic.response import json as json_result
from sanic import response

import json
import time
from pprint import pprint

import redis
import redis_circular_list
import requests

# import asyncio
# import websockets

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

# async def _websocket_send( host , message ):
# 	async with websockets.connect( host ) as websocket:
# 		await websocket.send( json.dumps( message ) )
# 		result = await websocket.recv()
# 		return result

# def websocket_send( host , message ):
# 	try:
# 		result = asyncio.get_event_loop().run_until_complete( _websocket_send( host , message ) )
# 		print( result )
# 		return result
# 	except Exception as e:
# 		print( e )
# 		return False

buttons_blueprint = Blueprint( 'buttons_blueprint' , url_prefix='/button' )

@buttons_blueprint.route( '/' )
def commands_root( request ):
	return response.text( "you are at the /button url\n" )

@buttons_blueprint.route( "/1" , methods=[ "GET" ] )
@buttons_blueprint.route( "/spotify/playlists/currated" , methods=[ "GET" ] )
def spotify_playlists_currated( request ):
	result = { "message": "failed" }
	try:
		# 1.) Get Current State
		redis_connection = redis_connect()
		current_mode = redis_connection.get( "STATE.MODE" )

		# 2.) Play Next Spotify Playlist in Circular List
		if current_mode is not None:
			current_mode = str( current_mode , 'utf-8' )
			current_mode = json.loads( current_mode )
			result["stop_current_mode_endpoint"] = current_mode["control_endpoints"]["stop"]
			result["stop_current_mode_response"] = get_json( result["stop_current_mode_endpoint"] )

		# 2.) Play
		result["play_endpoint"] = "http://127.0.0.1:11101/api/play"
		result["play_response"] = get_json( result["play_endpoint"] )

		# 3.) Get Play Status
		time.sleep( 1 )
		result["status_endpoint"] = "http://127.0.0.1:11101/api/get/playback/status"
		result["status_response"] = get_json( result["status_endpoint"] )

		mode = {
			"button": 1 ,
			"type": "spotify" ,
			"name": "Playing Spotify Curated Playlist" ,
			"status": result["status_response"] ,
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

		# 4.) Save State
		result["message"] = "success"
		result["mode"] = mode
		redis_connection.set( "STATE.MODE" , json.dumps( mode ) )
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@buttons_blueprint.route( "/2" , methods=[ "GET" ] )
@buttons_blueprint.route( "/tv" , methods=[ "GET" ] )
@buttons_blueprint.route( "/local" , methods=[ "GET" ] )
@buttons_blueprint.route( "/local/tv/next" , methods=[ "GET" ] )
def local_tv_next_episode( request ):
	result = { "message": "failed" }
	try:
		# 1.) Get Current State
		redis_connection = redis_connect()
		current_mode = redis_connection.get( "STATE.MODE" )
		if current_mode is not None:
			current_mode = str( current_mode , 'utf-8' )
			current_mode = json.loads( current_mode )

		# 2.) Stop Current State
		if "control_endpoints" in current_mode:
			if "stop" in current_mode["control_endpoints"]:
				result["stop_response"] = get_json( current_mode["control_endpoints"]["stop"] )

		mode = {
			"button": 2 ,
			"type": "local_tv" ,
			"name": "Playing Local TV Show , Next Episode" ,
			"file_path": None ,
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

		# 3.) Get Play Status
		time.sleep( 3 )
		result["status_response"] = get_json( mode["control_endpoints"]["status"] )
		mode["status"] = result["status_response"]

		# 4.) Save State
		print( "Local TV Show Started Playing via VLC" )
		result["message"] = "success"
		result["mode"] = mode
		redis_connection.set( "STATE.MODE" , json.dumps( mode ) )
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )

@buttons_blueprint.route( "/4" , methods=[ "GET" ] )
@buttons_blueprint.route( "/disney" , methods=[ "GET" ] )
@buttons_blueprint.route( "/websites/disney" , methods=[ "GET" ] )
def local_tv_next_episode( request ):
	result = { "message": "failed" }
	try:
		# 1.) Get Current State
		redis_connection = redis_connect()
		current_mode = redis_connection.get( "STATE.MODE" )
		if current_mode is not None:
			current_mode = str( current_mode , 'utf-8' )
			current_mode = json.loads( current_mode )

		# 2.) Stop Current State
		if "control_endpoints" in current_mode:
			if "stop" in current_mode["control_endpoints"]:
				result["stop_response"] = get_json( current_mode["control_endpoints"]["stop"] )

		# 3.) Create New State Object
		mode = {
			"button": 4 ,
			"type": "disney_plus" ,
			"name": "Playing Disney+ , Next Movie" ,
			"file_path": None ,
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

		# 4.) Play Next TV Episode in 'Next' TV Show Circular List
		result["play_endpoint"] = mode["control_endpoints"]["play"]
		result["play_response"] = get_json( result["play_endpoint"] )

		# 5.) Save State
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
		# 1.) Get Current State
		redis_connection = redis_connect()
		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in mode Mode" )

		# 2.) Press 'Pause Button' on Current Mode
		if "pause" in mode["control_endpoints"]:
			result["pause_result"] = get_json( mode["control_endpoints"]["pause"] )

		# 3.) Get Status
		time.sleep( 1 )
		result["status_response"] = get_json( mode["control_endpoints"]["status"] )
		mode["status"] = result["status_response"]

		# 4.) Save State
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
		# 1.) Get Current State
		redis_connection = redis_connect()
		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		# 2.) Press 'Previous Button' on Current State
		if "previous" in current_mode["control_endpoints"]:
			result["previous_result"] = get_json( current_mode["control_endpoints"]["previous"] )

		# 3.) Get Status
		time.sleep( 1 )
		result["status_response"] = get_json( mode["control_endpoints"]["status"] )
		mode["status"] = result["status_response"]

		# 4.) Save State
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
		# 1.) Get Current State
		redis_connection = redis_connect()
		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		# 2.) Press 'Stop Button' on Current State
		if "stop" in mode["control_endpoints"]:
			result["stop_result"] = get_json( mode["control_endpoints"]["stop"] )

		# 3.) Get Status
		time.sleep( 1 )
		result["status_response"] = get_json( mode["control_endpoints"]["status"] )
		mode["status"] = result["status_response"]

		# 4.) Save State
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
		# 1.) Get Current State
		redis_connection = redis_connect()
		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		# 2.) Press 'Next Button' on Current State
		if "next" in mode["control_endpoints"]:
			result["next_result"] = get_json( mode["control_endpoints"]["next"] )

		# 3.) Get Status
		time.sleep( 1 )
		result["status_response"] = get_json( mode["control_endpoints"]["status"] )
		mode["status"] = result["status_response"]

		# 4.) Save State
		result["message"] = "success"
		result["mode"] = mode
		redis_connection.set( "STATE.MODE" , json.dumps( mode ) )
	except Exception as e:
		print( e )
		result["error"] = str( e )
	return json_result( result )
