from sanic import Blueprint
from sanic.response import json as json_result
from sanic import response

import json
import time
import redis
import requests

import redis_utils

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

json_headers = {
	'accept': 'application/json, text/plain, */*'
}

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
		uri = redis_utils.next_in_circular_list( redis_connection , "STATE.SPOTIFY.LIBRARY.PLAYLISTS.CURRATED" )

		headers = {
			'accept': 'application/json, text/plain, */*'
		}

		result["play_endpoint"] = "http://127.0.0.1:11101/api/play"
		play_params = {
			'uri': uri
		}
		play_response = requests.get( result["play_endpoint"] , headers=json_headers , params=play_params )
		play_response.raise_for_status()
		result["play_response"] = play_response.json()

		time.sleep( 1 )

		result["status_endpoint"] = "http://127.0.0.1:11101/api/get/playback/status"
		status_response = requests.get( result["status_endpoint"] , headers=json_headers )
		status_response.raise_for_status()
		result["status_response"] = status_response.json()

		mode = {
			"button": 1 ,
			"type": "spotify" ,
			"name": "Playing Spotify Curated Playlist" ,
			"uri": uri ,
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
			pause_response = requests.get( mode["control_endpoints"]["pause"] , headers=json_headers )
			pause_response.raise_for_status()
			result["pause_response"] = pause_response.json()
		else:
			resume_response = requests.get( mode["control_endpoints"]["resume"] , headers=json_headers )
			resume_response.raise_for_status()
			result["resume_response"] = resume_response.json()

		time.sleep( 1 )

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
def pause( request ):
	result = { "message": "failed" }
	try:

		redis_connection = redis_connect()

		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		previous_response = requests.get( mode["control_endpoints"]["previous"] , headers=json_headers )
		previous_response.raise_for_status()
		result["previous_response"] = previous_response.json()

		time.sleep( 1 )

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
def pause( request ):
	result = { "message": "failed" }
	try:

		redis_connection = redis_connect()

		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		stop_response = requests.get( mode["control_endpoints"]["stop"] , headers=json_headers )
		stop_response.raise_for_status()
		result["stop_response"] = stop_response.json()

		time.sleep( 1 )

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
def pause( request ):
	result = { "message": "failed" }
	try:

		redis_connection = redis_connect()

		mode = redis_connection.get( "STATE.MODE" )
		mode = json.loads( mode )
		if "control_endpoints" not in mode:
			raise Exception( "Control Endpoints" , "No Basic Control Endpoints Found in Current Mode" )

		next_response = requests.get( mode["control_endpoints"]["next"] , headers=json_headers )
		next_response.raise_for_status()
		result["next_response"] = next_response.json()

		time.sleep( 1 )

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