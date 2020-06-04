# https://github.com/andymccurdy/redis-py/blob/1f857f0053606c23cb3f1abd794e3efbf6981e09/tests/test_commands.py
# https://github.com/ceberous/redis-manager-utils/blob/master/BaseClass.js
# https://redis.io/commands/sadd

def previous_in_circular_list( redis_connection , list_key ):
	list_key_index = f"{list_key}.INDEX"
	# 1.) Get Length
	circular_list_length = redis_connection.llen( list_key )
	if circular_list_length < 1:
		return False

	# 2.) Get Previous and Recylce in Necessary
	recycled = False
	circular_list_index = redis_connection.get( list_key_index )
	if circular_list_index is None:
		circular_list_index = ( circular_list_length - 1 )
		redis_connection.set( list_key_index , circular_list_index )
	else:
		circular_list_index = int( circular_list_index )
		circular_list_index -= 1
		redis_connection.decr( list_key_index )

	# 3.) Recycle Test
	if circular_list_index < 0:
		circular_list_index = ( circular_list_length - 1 )
		recycled = True
		redis_connection.set( list_key_index , circular_list_index )

	previous_in_circle = redis_connection.lindex( list_key , circular_list_index )
	previous_in_circle = str( previous_in_circle , 'utf-8' )
	return previous_in_circle

def next_in_circular_list( redis_connection , list_key ):
	list_key_index = f"{list_key}.INDEX"
	# 1.) Get Length
	circular_list_length = redis_connection.llen( list_key )
	circular_list_length = circular_list_length
	if circular_list_length < 1:
		return False

	# 2.) Get Next and Recycle if Necessary
	recycled = False
	circular_list_index = redis_connection.get( list_key_index )
	if circular_list_index is None:
		circular_list_index = 0
		redis_connection.set( list_key_index , '0' )
	else:
		circular_list_index = int( circular_list_index )
		circular_list_index += 1
		redis_connection.incr( list_key_index )

	# 3.) Recycle Test
	if circular_list_index > ( circular_list_length - 1 ):
		circular_list_index = 0
		recycled = True
		redis_connection.set( list_key_index , '0' )

	next_in_circle = redis_connection.lindex( list_key , circular_list_index )
	next_in_circle = str( next_in_circle , 'utf-8' )
	return next_in_circle
