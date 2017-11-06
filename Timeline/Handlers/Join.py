from Timeline.Server.Constants import TIMELINE_LOGGER, LOGIN_SERVER, WORLD_SERVER
from Timeline import Username, Password
from Timeline.Utils.Events import Event, PacketEventHandler, GeneralEvent

from twisted.internet.defer import inlineCallbacks, returnValue

from collections import deque
import logging
from time import time

logger = logging.getLogger(TIMELINE_LOGGER)

@PacketEventHandler.onXT('s', 'j#js', WORLD_SERVER)
@inlineCallbacks
def handleJoinServer(client, _id, passd, lang):
	if _id != client.penguin.id or passd != client.penguin.password:
		client.send('e', 101)
		returnValue(client.disconnect())

	# User logged in!
	GeneralEvent.call("penguin-logged", client)
	yield client.engine.redis.server.hincrby('server:{}'.format(client.engine.id), 'population', 1)

	client.initialize()
	client.send('js', *(map(int, [client['member'] > 0, client['moderator'], client['epf']])))

	client.canRecvPacket = True # Start receiving XT Packets

	client.send('lp', client, client['coins'], 0, 1024, int(time() * 1000), client['age'], 0, client['age'], client['member'], '', client['cache'].playerWidget, client['cache'].mapCategory, client['cache'].igloo)

	#TODO
	client.send('gps', client['id'])

	client.engine.roomHandler.joinRoom(client, 100, 'ext') # TODO Check for max-users limit

@PacketEventHandler.onXT('s', 'j#jr', WORLD_SERVER)
def handleJoinRoom(client, _id, x, y):
	client.penguin.x, client.penguin.y = x, y

	client.engine.roomHandler.joinRoom(client, _id, 'ext')

@PacketEventHandler.onXT('s', 'j#jp', WORLD_SERVER)
@inlineCallbacks
def handleJoinIgloo(client, _id, _type):
	room = yield client['iglooHandler'].createPenguinIgloo(_id)
	if room is None:
		return

	if client['room'] is not None:
		client['room'].remove(client)

	if client['waddling'] or client['playing']:
		client.send('e', 200)

	room.append(client)

def init():
	logger.debug('Join(j#j_) Packet handlers initiated!')