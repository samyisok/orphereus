﻿################################################################################
#  Copyright (C) 2009 Johan Liebert, Mantycore, Hedger, Rusanon                #
#  < anoma.team@gmail.com ; http://orphereus.anoma.ch >                        #
#                                                                              #
#  This file is part of Orphereus, an imageboard engine.                       #
#                                                                              #
#  This program is free software; you can redistribute it and/or               #
#  modify it under the terms of the GNU General Public License                 #
#  as published by the Free Software Foundation; either version 2              #
#  of the License, or (at your option) any later version.                      #
#                                                                              #
#  This program is distributed in the hope that it will be useful,             #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of              #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
#  GNU General Public License for more details.                                #
#                                                                              #
#  You should have received a copy of the GNU General Public License           #
#  along with this program; if not, write to the Free Software                 #
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA. #
################################################################################


from pylons.i18n import _, ungettext, N_

decimalVersion = "1.0.3"
engineVersion = "Orphereus %s" % decimalVersion

#this are the default values, the real ones are stored in the database
settingsDef = {
    "title"         : u'Orphereus',
    "invisibleBump" : u'true',
    "maxTagsCount"  : u'5',
    "maxTagLen"     : u'6',
    "disabledTags"  : u'logout|authorize|register|youAreBanned|userProfile|holySynod|frameMenu|!',
    "adminOnlyTags" : u'synod|logs',
    "maxLinesInPost": u'15',
    "cutSymbols"    : u'5000',
    "usersCanViewLogs"  : u'false',
    "additionalLinks" : u'http://orphereus.anoma.ch|Orphereus,http://anoma.ch|Anoma',
    "sectionNames" : u'Main',
}

settingsDescription = {
    "title"         : (N_("Board title"), str),
    "invisibleBump" : (N_("Invisible bumps"), bool),
    "maxTagsCount"  : (N_("Max tags per thread"), int),
    "maxTagLen"     : (N_("Max tag length"), int),
    "disabledTags"  : (N_("Disallowed tag names"), list),
    "adminOnlyTags" : (N_("Admin-only tags"), list),
    "maxLinesInPost": (N_("Cut post after X lines"), int),
    "cutSymbols"    : (N_("Cut post after Y symbols"), int),
    "usersCanViewLogs"  : (N_("Logs available to users"), bool),
    "additionalLinks" : (N_("Additional links"), list),
    "sectionNames" : (N_("Menu section names"), list),
}

id3FieldsNames = {
"album" : N_("Album"),
"title" : N_("Title"),
"artist" : N_("Artist"),
}

LOG_EVENT_SECURITY_IP = 0x00000001
LOG_EVENT_INVITE = 0x00010001
LOG_EVENT_INVITE_USED = 0x00010002
LOG_EVENT_BOARD_EDIT = 0x00020001
LOG_EVENT_BOARD_DELETE = 0x00020002
LOG_EVENT_USER_EDIT = 0x00030001
LOG_EVENT_USER_DELETE = 0x00030002
LOG_EVENT_USER_ACCESS = 0x00030003
LOG_EVENT_USER_BAN = 0x00030004
LOG_EVENT_USER_UNBAN = 0x00030005
LOG_EVENT_USER_GETUID = 0x00030006
LOG_EVENT_USER_PASSWD = 0x00030007
LOG_EVENT_SETTINGS_EDIT = 0x00040001
LOG_EVENT_POSTS_DELETE = 0x00050001
LOG_EVENT_EXTENSION_EDIT = 0x00060001
LOG_EVENT_MTN_BEGIN = 0x00070001
LOG_EVENT_MTN_END = 0x00070002
LOG_EVENT_MTN_UNBAN = 0x00070002
LOG_EVENT_MTN_DELINVITE = 0x00070003
LOG_EVENT_MTN_ERROR = 0x00070003
LOG_EVENT_RICKROLLD = 0x00080001
LOG_EVENT_EDITEDPOST = 0x00090001
LOG_EVENT_INTEGR = 0x00100000
LOG_EVENT_INTEGR_RC = 0x00100001
LOG_EVENT_BAN_ADD = 0x00110001
LOG_EVENT_BAN_DISABLE = 0x00110002
LOG_EVENT_BAN_REMOVE = 0x00110003
LOG_EVENT_BAN_EDIT = 0x00110004

disabledEvents = [LOG_EVENT_RICKROLLD, LOG_EVENT_SECURITY_IP, LOG_EVENT_INTEGR]

destinations = {0 : N_("Thread"),
                1 : N_("First page of current board"),
                2 : N_("Current page of current board"),
                3 : N_("Overview"),
                4 : N_("First page of destination board"),
                5 : N_("Referrer"),
                }