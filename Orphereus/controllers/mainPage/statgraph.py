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

from pylons.i18n import N_
from string import *
from beaker.cache import CacheManager
import datetime
import  sqlalchemy as sa
from sqlalchemy.sql import and_, or_, not_

from Orphereus.lib.BasePlugin import BasePlugin
from Orphereus.lib.base import *
from Orphereus.lib.constantValues import CFG_BOOL, CFG_INT, CFG_STRING, CFG_LIST
from Orphereus.model import *
from Orphereus.lib.interfaces.AbstractHomeExtension import AbstractHomeExtension

import logging
_log = logging.getLogger(__name__)

from paste.script import command
from Orphereus.config.environment import load_environment
from paste.deploy import appconfig
from pylons import config

class GraphsCommand(command.Command):
    max_args = 0
    min_args = 0

    usage = ""
    summary = "Build stat graphs"
    group_name = "Orphereus"

    parser = command.Command.standard_parser(verbose = True)
    parser.add_option('--config',
                      action = 'store',
                      dest = 'config',
                      help = 'config name (e.g. "development.ini")')

    parser.add_option('--path',
                      action = 'store',
                      dest = 'path',
                      help = 'working dir (e.g. ".")')

    @staticmethod
    def setup_config(filename, relative_to):
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[GRAPHS] %(asctime)s %(name)s:%(levelname)s: %(message)s")
        ch.setFormatter(formatter)
        corelog = logging.getLogger("CORE")
        ormlog = logging.getLogger("ORM")
        corelog.addHandler(ch)
        ormlog.addHandler(ch)

        if not relative_to or not os.path.exists(relative_to):
            relative_to = "."
        print 'Loading config "%s" at path "%s"...' % (filename, relative_to)
        conf = appconfig('config:' + filename, relative_to = relative_to)
        load_environment(conf.global_conf, conf.local_conf, False)
        g._push_object(meta.globj) #zomg teh h4x

    def command(self):
        #devIni = self.args[0]
        self.setup_config(self.options.config, self.options.path)
        birthdate = meta.Session.query(sa.sql.functions.max(Post.date)).scalar()
        lastdate = datetime.datetime.now()
        currentdate = birthdate
        xsvals = []
        ysvals = []
        dayscount = (lastdate - birthdate).days
        ccount = 0
        while currentdate < lastdate:
            nextdate = (currentdate + datetime.timedelta(days = 1))
            countfordate = Post.query.filter(and_(Post.date <= nextdate, Post.date >= currentdate)).count()
            xsvals.append(currentdate.date())
            ysvals.append(countfordate)
            currentdate = nextdate
            print "%d/%d" % (ccount, dayscount)
            ccount += 1

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.dates import date2num
        fig = plt.figure(1)
        plt.suptitle("Total posts count")
        ax = fig.add_subplot(1, 1, 1)
        color = (0, 0, 1)
        line = plt.plot_date(xsvals, ysvals, '-', color = color, linewidth = 1.5)
        fig.autofmt_xdate()
        imgdata = StringIO.StringIO()
        plt.savefig(imgdata, format = 'png')
        plt.close()
        imgdata.seek(0)
        out = imgdata.getvalue()
        path = os.path.join(g.OPT.staticPath, "stat_posts.png")
        print "Created:", path
        f = open(path, "wb+")
        f.write(out)
        f.close()

class HomeStatisticsPlugin(BasePlugin, AbstractHomeExtension):
    def __init__(self):
        config = {'name' : N_('Graphical statistics for main page'),
                 }

        BasePlugin.__init__(self, 'statgraph', config)
        AbstractHomeExtension.__init__(self, 'statgraph')

    def entryPointsList(self):
        return [('statgraphs', "GraphsCommand"), ]

    def prepareData(self, controller, container):
        pass