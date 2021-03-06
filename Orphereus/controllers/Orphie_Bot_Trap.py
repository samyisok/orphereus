# -*- coding: utf-8 -*-
################################################################################
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

from Orphereus.lib.base import N_, g, redirect_to
from Orphereus.lib.BasePlugin import BasePlugin
from OrphieBaseController import OrphieBaseController

import logging
log = logging.getLogger(__name__)

class BotTrapPlugin(BasePlugin):
    def __init__(self):
        config = {'name' : N_('Automatic ban for download spiders'),
                 }
        BasePlugin.__init__(self, 'bottrap', config)

    # Implementing BasePlugin
    def initRoutes(self, map):
        map.connect('botTrap1',
                    '/ajax/stat/{confirm}',
                    controller = 'Orphie_Bot_Trap',
                     action = 'selfBan',
                     confirm = '')
        map.connect('botTrap2', '/holySynod/stat/{confirm}',
                    controller = 'Orphie_Bot_Trap',
                    action = 'selfBan',
                    confirm = '')

class OrphieBotTrapController(OrphieBaseController):
    def __before__(self):
        OrphieBaseController.__before__(self)
        self.initiate()
        self.disableMenu("topMenu")

    def selfBan(self, confirm):
        if g.OPT.spiderTrap and not self.userInst.Anonymous:
            if confirm:
                self.userInst.ban(2, "[AUTOMATIC BAN] Security alert type 2", -1)
                redirect_to('boardBase')
            else:
                return self.render('selfBan')
        else:
            return redirect_to('boardBase')
