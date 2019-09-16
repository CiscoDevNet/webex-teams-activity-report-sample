# webex-teams-activity-report-sample 

# Copyright (c) 2019 Cisco and/or its affiliates.
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sqlite3
from webexteamssdk import WebexTeamsAPI
from datetime import datetime, timedelta
from tzlocal import get_localzone
import json

def importData( conn, teamsAccessToken, startDate, endDate ):

    c = conn.cursor()

    resp = c.execute( 'SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name="messages"' )

    if resp.fetchone()[0] == 0:

        resp = c.execute(
            '''
            CREATE TABLE messages (
                roomTitle text, 
                created text, 
                id text UNIQUE, 
                roomId text, 
                roomType text, 
                text text, 
                personId text, 
                personEmail text, 
                html text, 
                mentionedPeople text,
                mentionedGroups text )
            '''
        )

        conn.commit

    api = WebexTeamsAPI( access_token = teamsAccessToken )

    print( '\nRetrieving active spaces...\n')

    rooms = api.rooms.list( sortBy = 'lastactivity' )

    localTimeZone = get_localzone()

    startTime = localTimeZone.localize( datetime.strptime( startDate, '%Y-%m-%d' ) )
    endTime = localTimeZone.localize( datetime.strptime( endDate, '%Y-%m-%d' ) + timedelta( days = 1 ) )

    roomCount = 0
    messageCount = 0

    print( '\nImporting messages...\n')

    for room in rooms:

        if room.lastActivity < startTime:
            break

        roomCount += 1

        messages = api.messages.list( roomId = room.id, before = endTime.strftime('%Y-%m-%dT%H:%M:%S.%f%z') )

        data = []

        for message in messages:

            if message.created < startTime: break

            if message.created > endTime: continue

            messageCount += 1

            print( '\rProcessing (spaces/messages): {} / {}'.format( roomCount, messageCount), end = '' )

            mentionedPeople = message.mentionedPeople if hasattr( message, 'mentionedPeople' ) else None
            mentionedGroups = message.mentionedGroups if hasattr( message, 'mentionedGroups' ) else None

            data.append( (
                room.title,
                message.created.strftime('%Y-%m-%dT%H:%M:%S.%f%z'), 
                message.id, 
                message.roomId, 
                message.roomType, 
                message.text, 
                message.personId, 
                message.personEmail, 
                message.html, 
                json.dumps( mentionedPeople ),
                json.dumps( mentionedGroups )
                ) )

        try:

            c.executemany( 'INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?)', data )

            conn.commit()

        except sqlite3.IntegrityError: pass

    print('\n\nImport complete\n')