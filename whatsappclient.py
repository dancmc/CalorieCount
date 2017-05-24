from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_presence.protocolentities import AvailablePresenceProtocolEntity, \
    UnavailablePresenceProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities import OutgoingAckProtocolEntity

from yowsup.stacks import YowStackBuilder
from yowsup.layers.auth import AuthError
from yowsup.layers import YowLayerEvent
from yowsup.layers.network import YowNetworkLayer
import sys, os, threading, time, requests
from random import randint
from flask import json
from config import *

credentials = WHATSAPP_CREDENTIALS
import traceback


class MyLayer(YowInterfaceLayer):
    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):

        print(messageProtocolEntity.getFrom())

        # send receipt otherwise we keep receiving the same message over and over
        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(),
                                                False, messageProtocolEntity.getParticipant())
        self.toLower(receipt)

        # route based on message type
        if messageProtocolEntity.getType() == 'text':
            self.onTextMessage(messageProtocolEntity)
        elif messageProtocolEntity.getType() == 'media':
            self.onMediaMessage(messageProtocolEntity)

        # to store in database, send grouped receipts later on when going online
        store = (messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), messageProtocolEntity.getParticipant())
        time.sleep(randint(3,5))
        self.toLower(AvailablePresenceProtocolEntity())
        receipt = OutgoingReceiptProtocolEntity(store[0], store[1], True, store[2])
        self.toLower(receipt)
        time.sleep(randint(3,5))
        self.toLower(UnavailablePresenceProtocolEntity())

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
        self.toLower(ack)

    def onTextMessage(self, textEntity):
        url = 'http://localhost:5000/msgplatform/whatsapp/new'
        # everything has to be encoded as multipart form
        r = requests.post(url,
                          data={"json": json.dumps({"text": textEntity.getBody(), "username": textEntity.getFrom()})})
        print(r.text)

    def onMediaMessage(self, mediaEntity):
        if mediaEntity.getMediaType() == "image":

            try:
                data = mediaEntity.getMediaContent()
                caption = mediaEntity.getCaption()

                # TODO theoretically have to save to disk if POSTing fails so can try again later
                # but practically Whatsapp is not a viable long term solution anyway....

                # filename = "%d.jpg" % int(time.time()*1000)
                # outPath = os.path.join("/Users/daniel/Downloads", filename)
                # f = open(outPath, 'wb')
                # f.write(data)
                # f.close()

                url = 'http://localhost:5000/msgplatform/whatsapp/new'
                files = {'image': ('filename', data, 'image/jpeg')}
                # everything has to be encoded as multipart form
                r = requests.post(url, files=files,
                                  data={"json": json.dumps({"text": caption, "username": mediaEntity.getFrom()})})
                print(r.text)
            except:
                print(traceback.format_exc())


class WhatsappInstance:
    def __init__(self):
        self.stack = YowStackBuilder() \
            .pushDefaultLayers(True) \
            .push(MyLayer) \
            .build()

    def start(self):

        self.stack.setCredentials(credentials)
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))  # sending the connect signal

        def startThread():
            try:
                self.stack.loop(timeout=0.5, discrete=0.5)
            except AuthError as e:
                print("Auth Error, reason %s" % e)
            except KeyboardInterrupt:
                print("\nYowsdown KeyboardInterrupt")
                sys.exit(0)
            except Exception as e:
                print("\nYowsdown General Exception")
                print(traceback.format_exc())

        t1 = threading.Thread(target=startThread)
        t1.daemon = True
        t1.start()

    def sendmessage(self, user_id, message):

        mylayer = self.stack.getLayer(8)
        mylayer.toLower(AvailablePresenceProtocolEntity())

        outgoingMessageProtocolEntity = TextMessageProtocolEntity(message, to=user_id)
        mylayer.send(outgoingMessageProtocolEntity)

        time.sleep(5)
        mylayer.toLower(UnavailablePresenceProtocolEntity())
