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

import logging

from paste.deploy import appconfig
from pylons import config
from Orphereus.model import *
import hashlib
from sqlalchemy.orm import eagerload
from sqlalchemy.orm import class_mapper

from Orphereus.config.environment import load_environment
import Orphereus.lib.app_globals as app_globals

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf, True)
    from Orphereus.model import meta
    log.info("Creating tables")
    #meta.metadata.drop_all(bind = meta.engine)
    meta.metadata.create_all(bind = meta.engine)
    log.info("Successfully setup")
    init_globals(meta.globj, False)

    disableInstantIdSetting = meta.dialectProps.get('disableInstantIdSetting', None)

    try:
        uc = meta.Session.query(User).count()
    except:
        uc = 0
    log.debug('users: %d' % uc)

    if uc == 0:
        log.info("Adding user with password 'first'")
        log.debug("Hash secret: %s" % config['core.hashSecret'])
        uid = hashlib.sha512('first' + hashlib.sha512(config['core.hashSecret']).hexdigest()).hexdigest()
        user = User.create(uid)
        uidNumber = user.uidNumber
        log.debug("Created UID: %s (%d)" % (uid, uidNumber))
        user.options.isAdmin = True
        user.options.canChangeRights = True

        log.info("Adding servive users 0 and -1")
        ulogger = User("Anonymous", None)
        umaintenance = User("Dummy user for maintenance purposes", None)

        meta.Session.add(ulogger)
        meta.Session.add(umaintenance)
        if disableInstantIdSetting:
            meta.Session.commit()

        ulogger.uidNumber = -1
        umaintenance.uidNumber = 0
        ulogger.options = UserOptions()
        umaintenance.options = UserOptions()
        UserOptions.initDefaultOptions(ulogger.options, meta.globj.OPT)
        UserOptions.initDefaultOptions(umaintenance.options, meta.globj.OPT)
        meta.Session.add(ulogger.options)
        meta.Session.add(umaintenance.options)
        meta.Session.commit()
    try:
        ec = meta.Session.query(Extension).count()
    except:
        ec = 0
    log.debug('extenions: %d' % ec)

    if ec == 0:
        log.info("Adding extensions")

        Extension.create('jpeg', True, True, 'image', '', 0, 0)
        Extension.create('jpg', True, True, 'image', '', 0, 0)
        Extension.create('gif', True, True, 'image', '', 0, 0)
        Extension.create('bmp', True, True, 'image-jpg', '', 0, 0)
        Extension.create('png', True, True, 'image', '', 0, 0)
        Extension.create('swf', True, True, 'flash', 'generic/flash.png', 128, 128)
        Extension.create('zip', True, True, 'archive', 'generic/archive.png', 128, 128)
        Extension.create('rar', True, True, 'archive', 'generic/archive.png', 128, 128)
        Extension.create('tar', True, True, 'archive', 'generic/archive.png', 128, 128)
        Extension.create('7z', True, True, 'archive', 'generic/archive.png', 128, 128)
        Extension.create('mp3', True, True, 'audio-playable', 'generic/sound.png', 128, 128)
        Extension.create('ogg', True, True, 'audio-playable', 'generic/sound.png', 128, 128)
        Extension.create('mid', True, True, 'audio', 'generic/sound.png', 128, 128)
        Extension.create('txt', True, True, 'text', 'generic/text.png', 128, 128)
        Extension.create('log', True, True, 'text', 'generic/text.png', 128, 128)

    try:
        tc = meta.Session.query(Tag).count()
    except:
        tc = 0
    log.debug('tags: %d' % tc)

    if tc == 0:
        log.info("Adding tag /b/")

        tag = Tag(u'b')
        tag.comment = u'Random'
        tag.sectionId = 1
        tag.persistent = True
        tag.specialRules = u"It is /b/, there is no rules"
        meta.Session.add(tag)
        meta.Session.commit()

    try:
        pc = meta.Session.query(Picture).count()
    except:
        pc = 0
    log.debug('pictures: %d' % tc)
    if tc == 0:
        log.info("Adding dummy picture #0")
        firstEx = meta.Session.query(Extension).first()
        pic = Picture('', '', 0, [None, None, 0, 0], firstEx.id, 'dummy', u"") # TODO: special extension?
        meta.Session.add(pic)
        if disableInstantIdSetting:
            meta.Session.commit()
        pic.id = 0
        meta.Session.commit()

    log.info("Completed")

    gvars = config['pylons.app_globals']
    log.debug('Calling deploy routines, registered plugins: %d' % (len(gvars.plugins)),)
    for plugin in gvars.plugins:
        plugin.deployCallback()

        #dh = plugin.deployHook()
        #if dh:
        #    log.debug('calling deploy routine %s from: %s' % (str(dh), plugin.pluginId()))
        #    dh(plugin.namespace())
    log.debug('DEPLOYMENT COMPLETED')
