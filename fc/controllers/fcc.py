from fc.lib.base import *
from fc.model import *
from sqlalchemy.orm import eagerload
from sqlalchemy.sql import and_, or_, not_
from sqlalchemy.orm import class_mapper
import sqlalchemy
import os
import cgi
import shutil
import datetime
import time
import Image
import os
import hashlib
import re
from beaker.cache import CacheManager
from wakabaparse import WakabaParser
from fc.lib.miscUtils import *
from fc.lib.constantValues import *
from fc.lib.fileHolder import AngryFileHolder
from OrphieBaseController import OrphieBaseController
from mutagen.easyid3 import EasyID3

import logging
log = logging.getLogger(__name__)

#TODO: new debug system. Don't forget about c.log and c.sum

class FccController(OrphieBaseController):
    def __before__(self):
        OrphieBaseController.__before__(self)
        c.userInst = self.userInst
        c.destinations = destinations

        c.currentURL = request.path_info.decode('utf-8')
        if not c.currentURL.endswith('/'):
            c.currentURL = u'%s/' % c.currentURL

        if not self.currentUserIsAuthorized():
            return redirect_to(('%sauthorize' % c.currentURL).encode('utf-8'))
        if self.userInst.isBanned():
            #abort(500, 'Internal Server Error')     # calm hidden ban
            return redirect_to('/youAreBanned')
        c.currentUserCanPost = self.currentUserCanPost()
        if self.userInst.isAdmin() and not checkAdminIP():
            return redirect_to('/')
        self.initEnvironment()

    #parser callback
    def cbGetPostAndUser(self, id):
        return (Post.getPost(id), self.userInst.uidNumber)

    def selfBan(self, confirm):
        if g.OPT.spiderTrap:
            if confirm:
                self.userInst.ban(2, _("[AUTOMATIC BAN] Security alert type 2"), -1)
                redirect_to('/')
            else:
                return self.render('selfBan')
        else:
            return redirect_to('/')

    def showPosts(self, threadFilter, tempid='', page=0, board='', tags=[], tagList=[]):
        if isNumber(page):
            page = int(page)
        else:
            page = 0

        c.board = board
        c.uidNumber = self.userInst.uidNumber
        c.enableAllPostDeletion = self.userInst.canDeleteAllPosts()
        c.isAdmin = self.userInst.isAdmin()

        #TODO: move into GLOBAL object???
        extensions = Extension.getList(True)
        extList = []
        for ext in extensions:
            extList.append(ext.ext)
        c.extLine = ', '.join(extList)

        count = threadFilter.count()
        tpp = self.userInst.threadsPerPage()
        if page*tpp >= count and count > 0:
            c.errorText = _("Incorrect page")
            return self.render('error')
        self.paginate(count, page, tpp)

        if count > 1:
            c.threads = threadFilter.order_by(Post.bumpDate.desc())[page * tpp: (page + 1)* tpp]
            if self.userInst.mixOldThreads() and not board == '@':
                oldThread = threadFilter.filter(Post.bumpDate < c.threads[-1].bumpDate).order_by(sqlalchemy.func.random()).first()
                #log.debug(oldThread)
                if oldThread:
                    oldThread.mixed = True
                    c.threads.insert(1, oldThread)

        elif count == 1:
            c.threads = [threadFilter.one()]
        elif count == 0:
            c.threads = []

        if tagList and len(tagList) == 1 and tags:
            currentBoard = tags[0]
            c.boardName = currentBoard.options and currentBoard.options.comment or (u"/%s/" % currentBoard.tag)
            c.tagLine   = currentBoard.tag
        elif not tagList and tags:
            names = []
            rawNames = []
            for t in tags:
                names.append(t.options and t.options.comment or (u"/%s/" % t.tag))
                rawNames.append(t.tag)
            c.boardName = " + ".join(names)
            c.tagLine ="+".join(rawNames)
        else:
            c.boardName = board
            c.tagLine = c.boardName
            if board == '~':
                c.boardName = _('Overview')
            if board == '@':
                c.boardName = _('Related threads')

        c.boardOptions = Tag.conjunctedOptionsDescript(tags)
        c.tagList = ' '.join(tagList)

        hiddenThreads = self.userInst.hideThreads()
        for thread in c.threads:
            thread.hidden = (str(thread.id) in hiddenThreads)
            if thread.hidden:
                tl = []
                for tag in thread.tags:
                    tl.append(tag.tag)
                thread.tagLine = ', '.join(tl)

            if count > 1:
                replyCount = thread.replyCount
                #replyCount = Post.query.options(eagerload('file')).filter(Post.parentid==thread.id).count()
                replyLim   = replyCount - self.userInst.repliesPerThread()
                if replyLim < 0:
                    replyLim = 0
                thread.omittedPosts = replyLim
                thread.Replies = thread.filterReplies()[replyLim:]
            else:
                thread.Replies = thread.filterReplies().all()
                thread.omittedPosts = 0
                thread.hidden = False

        if tempid:
            oekaki = Oekaki.get(tempid)
            c.oekaki = oekaki
        else:
            c.oekaki = False

        c.curPage = page
        return self.render('posts')


    def GetBoard(self, board, tempid, page=0):
        if board == '!':
            if g.OPT.devMode:
                ct = time.time()

            c.totalPostsCount = 0
            mstat = False
            vts = False
            chTime = g.OPT.statsCacheTime

            if chTime > 0:
                cm = CacheManager(type='memory')
                cch = cm.get_cache('home_stats')
                c.totalPostsCount = cch.get_value(key="totalPosts", createfunc=Post.getPostsCount, expiretime=chTime)
                mstat = cch.get_value(key="mainStats", createfunc=Tag.getStats, expiretime=chTime)
                vts = cch.get_value(key="vitalSigns", createfunc=Post.vitalSigns, expiretime=chTime)
            else:
                c.totalPostsCount = Post.getPostsCount()
                mstat = Tag.getStats()
                vts = Post.vitalSigns()

            def taglistcmp(a, b):
                return cmp(b.count, a.count) or cmp(a.board.tag, b.board.tag)

            c.boards = sorted(mstat.boards, taglistcmp)
            c.tags = sorted(mstat.tags, taglistcmp)
            c.stags = sorted(mstat.stags, taglistcmp)
            c.totalBoardsThreads = mstat.totalBoardsThreads
            c.totalBoardsPosts = mstat.totalBoardsPosts
            c.totalTagsThreads = mstat.totalTagsThreads
            c.totalTagsPosts = mstat.totalTagsPosts
            c.totalSTagsThreads = mstat.totalSTagsThreads
            c.totalSTagsPosts = mstat.totalSTagsPosts

            c.last1KUsersCount = vts.last1KUsersCount
            c.prev1KUsersCount = vts.prev1KUsersCount
            c.lastWeekMessages = vts.lastWeekMessages
            c.prevWeekMessages = vts.prevWeekMessages

            c.boardName = _('Home')

            if g.OPT.devMode:
                c.log.append("home: " + str(time.time() - ct))
            return self.render('home')

        board = filterText(board)
        c.PostAction = board

        if isNumber(page):
            page = int(page)
        else:
            page = 0

        filter = Post.buildMetaboardFilter(board, self.userInst)
        tags = Tag.getAllByNames(filter[1])
        return self.showPosts(threadFilter=filter[0], tempid=tempid, page=int(page), board=board, tags=tags, tagList=filter[1])

    def GetThread(self, post, tempid):
        thePost = Post.getPost(post)
        #if thePost isn't op-post, redirect to op-post instead
        if thePost and thePost.parentPost:
            if isNumber(tempid) and not int(tempid) == 0:
                redirect_to('/%d/%d' % (thePost.parentid, int(tempid)))
            else:
                redirect_to('/%d#i%d' % (thePost.parentid, thePost.id))

        if not thePost:
            c.errorText = _("No such post exist.")
            return self.render('error')

        c.PostAction = thePost.id
        filter = Post.buildThreadFilter(self.userInst, thePost.id)
        return self.showPosts(threadFilter=filter, tempid=tempid, page=0, board='', tags=thePost.tags)

    def gotoDestination(self, post, postid):
        tagLine = request.POST.get('tagLine', '~')

        dest = int(request.POST.get('goto', 0))
        if isNumber(dest):
            dest = int(dest)
        else:
            dest = 0

        curPage = request.POST.get('curPage', 0)
        if isNumber(curPage):
            curPage = int(curPage)
        else:
            curPage = 0

        ##log.debug('%s %s %s' % (tagLine, str(dest), str(curPage)))
        redirectAddr = '~'

        if dest == 4: # destination board
            if not post.parentid:
                tags = []
                for tag in post.tags:
                    tags.append(tag.tag)
                postTagline = "+".join(tags)

                redirectAddr = '%s/' % (postTagline)
            else:
                dest = 1

        if dest == 0: #current thread
            if postid:
                return redirect_to(action='GetThread', post=post.parentid, board=None)
            else:
                return redirect_to(action='GetThread', post=post.id, board=None)
        elif dest == 1 or dest == 2: # current board
            if  tagLine:
                if dest == 1:
                    curPage = 0
                redirectAddr = "%s/page/%d" % (tagLine, curPage)
        elif dest == 3: # overview
            pass
        elif dest == 5: #referrer
            return redirect_to(request.headers.get('REFERER', tagLine.encode('utf-8')))

        ##log.debug(redirectAddr)
        return redirect_to(str('/%s' % redirectAddr.encode('utf-8')))

    def showProfile(self):
        if self.userInst.Anonymous and not g.OPT.allowAnonProfile:
            c.errorText = _("Profile is not avaiable to Anonymous users.")
            return self.render('error')

        c.templates = g.OPT.templates
        c.styles    = g.OPT.styles
        c.profileChanged = False
        c.boardName = _('Profile')
        if request.POST.get('update', False):
            self.userInst.hideLongComments(request.POST.get('hideLongComments',False))
            self.userInst.useAjax(bool(request.POST.get('useAjax', False)))
            self.userInst.expandImages(request.POST.get('expandImages', False))
            self.userInst.mixOldThreads(bool(request.POST.get('mixOldThreads', False)))
            self.userInst.oekUseSelfy(bool(request.POST.get('oekUseSelfy', False)))
            self.userInst.oekUseAnim(bool(request.POST.get('oekUseAnim', False)))
            self.userInst.oekUsePro(bool(request.POST.get('oekUsePro', False)))
            threadsPerPage = request.POST.get('threadsPerPage',self.userInst.threadsPerPage())
            if isNumber(threadsPerPage) and (0 < int(threadsPerPage) < 30):
                self.userInst.threadsPerPage(int(threadsPerPage))
            repliesPerThread = request.POST.get('repliesPerThread',self.userInst.repliesPerThread())
            if isNumber(repliesPerThread) and (0 < int(repliesPerThread) < 100):
                self.userInst.repliesPerThread(int(repliesPerThread))
            maxExpandWidth = request.POST.get('maxExpandWidth', self.userInst.maxExpandWidth())
            if isNumber(maxExpandWidth) and (0 < int(maxExpandWidth) < 4096):
                self.userInst.maxExpandWidth(int(maxExpandWidth))
            maxExpandHeight = request.POST.get('maxExpandHeight', self.userInst.maxExpandHeight())
            if isNumber(maxExpandHeight) and (0 < int(maxExpandHeight) < 4096):
                self.userInst.maxExpandHeight(int(maxExpandHeight))
            template = request.POST.get('template', self.userInst.template())
            if template in c.templates:
                self.userInst.template(template)
            style = filterText(request.POST.get('style', self.userInst.style()))
            if style in c.styles:
                self.userInst.style(style)
            gotodest = filterText(request.POST.get('defaultGoto', self.userInst.defaultGoto()))
            if isNumber(gotodest) and (int(gotodest) in destinations.keys()):
                self.userInst.defaultGoto(int(gotodest))
            homeExcludeTags = Tag.stringToTagList(request.POST.get('homeExclude', u''), False)
            #log.debug(homeExcludeTags)
            homeExcludeList = []
            for t in homeExcludeTags:
                homeExcludeList.append(t.id)
            self.userInst.homeExclude(homeExcludeList)

            if not c.userInst.Anonymous:
                c.profileMsg = _('Password was NOT changed.')
                key = request.POST.get('key','').encode('utf-8')
                key2 = request.POST.get('key2','').encode('utf-8')
                currentKey = request.POST.get('currentKey', '').encode('utf-8')
                passwdRet = self.userInst.passwd(key, key2, False, currentKey)
                if passwdRet == True:
                    c.profileMsg = _('Password was successfully changed.')
                elif passwdRet == False:
                    c.message = _('Incorrect security codes')
                else:
                    c.boardName = _('Error')
                    c.errorText = passwdRet
                    return self.render('error')
                meta.Session.commit()

            c.profileChanged = True
            c.profileMsg += _(' Profile was updated.')

        homeExcludeTags = Tag.getAllByIds(self.userInst.homeExclude())
        homeExcludeList = []
        for t in homeExcludeTags:
            homeExcludeList.append(t.tag)
        c.homeExclude = ', '.join(homeExcludeList)
        c.hiddenThreads = Post.filter(Post.id.in_(self.userInst.hideThreads())).options(eagerload('file')).options(eagerload('tags')).all()
        for t in c.hiddenThreads:
            tl = []
            for tag in t.tags:
                tl.append(tag.tag)
            t.tagLine = ', '.join(tl)
        c.userInst = self.userInst
        return self.render('profile')

    def DeletePost(self, board):
        if not self.currentUserCanPost():
            c.errorText = _("Deletion disabled")
            return self.render('error')

        fileonly = 'fileonly' in request.POST
        redirectAddr = board

        opPostDeleted = False
        reason = filterText(request.POST.get('reason', '???'))

        remPass = ''
        if self.userInst.Anonymous:
            remPass = hashlib.md5(request.POST.get('remPass', '')).hexdigest()

        retest = re.compile("^\d+$")
        for i in request.POST:
            if retest.match(request.POST[i]):
                post = Post.getPost(request.POST[i])
                if post:
                    res = post.deletePost(self.userInst, fileonly, True, reason, remPass)
                opPostDeleted = opPostDeleted or res

        tagLine = request.POST.get('tagLine', False)
        if opPostDeleted:
            if tagLine:
                redirectAddr = tagLine
            else:
                redirectAddr = '~'

        return redirect_to(str('/%s' % redirectAddr.encode('utf-8')))

    def search(self, text, page = 0):
        rawtext = text
        if not text:
            rawtext = request.POST.get('query', u'')
            text = filterText(rawtext)

        minLen = 3
        if not text or len(rawtext) < minLen:
            c.boardName = _('Error')
            c.errorText = _("Query too short (minimal length: %d)") % minLen
            return self.render('error')

        if isNumber(page):
            page = int(page)
        else:
            page = 0

        pp = self.userInst.threadsPerPage()
        c.boardName = _("Search")
        c.query = text

        tagfilter = False
        filteredQueryRe = re.compile("^(([^:]+):){1}(.+)$").match(text)
        if filteredQueryRe:
            groups = filteredQueryRe.groups()
            filterName = groups[1]
            text = groups[2]
            tagfilter = Post.buildMetaboardFilter(filterName, self.userInst)[2]

        if not tagfilter:
            tagfilter = Post.buildMetaboardFilter(False, self.userInst)[2]

        base = Post.filter(or_(tagfilter,
                                    Post.parentPost.has(tagfilter),
                               ))
        #else:


        filter = base.filter(Post.message.like('%%%s%%' % text))
        count = filter.count()
        self.paginate(count, page, pp)
        posts = filter.order_by(Post.date.desc())[(page * pp):(page + 1)* pp]

        c.posts = []
        for p in posts:
            parent = p
            if p.parentid:
                parent = p.parentPost

            pt = []
            pt.append(p)
            if not p.parentid:
                pt.append(p)
            else:
               pt.append(parent)
            c.posts.append(pt)

        return self.render('search')

    def Anonimyze(self, post):
        postid = request.POST.get('postId', False)
        batch = request.POST.get('batchFA', False)
        if postid and isNumber(postid):
            c.FAResult = self.processAnomymize(int(postid), batch)
        else:
            c.boardName = _('Final Anonymization')
            c.FAResult = False
            c.postId = post
        return self.render('finalAnonymization')

    def processAnomymize(self, postid, batch):
        if not g.OPT.enableFinalAnonymity:
            return _("Final Anonymity is disabled")

        if self.userInst.Anonymous:
            return _("Final Anonymity available only for registered users")

        result = []
        post = Post.getPost(postid)
        if post:
            posts = []
            if not batch:
                posts = [post]
            else:
                posts = Post.filter(and_(Post.uidNumber == self.userInst.uidNumber, Post.date <= post.date)).all()
            for post in posts:
                if post.uidNumber != self.userInst.uidNumber:
                    result.append(_("You are not author of post #%s") % post.id)
                else:
                    delay = g.OPT.finalAHoursDelay
                    timeDelta = datetime.timedelta(hours=delay)
                    if post.date < datetime.datetime.now() - timeDelta:
                        post.uidNumber = 0
                        result.append(_("Post #%d successfully anonymized") % post.id)
                    else:
                        params = (post.id, str(h.modifyTime(post.date, self.userInst, g.OPT.secureTime) + timeDelta), str(datetime.datetime.now()))
                        result.append(_("Can't anomymize post #%d now, it will be allowed after %s (now: %s)" % params))
            meta.Session.commit()
        else:
            result = [_("Nothing to anonymize")]

        return result

    def viewLog(self, page):
        if g.settingsMap['usersCanViewLogs'].value == 'true':
            c.boardName = 'Logs'
            page = int(page)
            count = LogEntry.count(disabledEvents)
            tpp = 50
            self.paginate(count, page, tpp)
            c.logs = LogEntry.getRange(page*tpp, (page+1)*tpp, disabledEvents)
            rv = re.compile('(\d+\.){3}\d+')
            for le in c.logs:
                le.entry = rv.sub('<font color="red">[IP REMOVED]</font>', le.entry)
            return self.render('logs')
        else:
            return redirect_to('/')

    def oekakiDraw(self, url, selfy, anim, tool):
        if not self.currentUserCanPost():
            c.errorText = _("Posting is disabled")
            return self.render('error')

        c.url = url
        enablePicLoading = not (request.POST.get('oekaki_type', 'Reply') == 'New')
        c.selfy = request.POST.get('selfy', False) or selfy == '+selfy'
        c.animation = request.POST.get('animation', False) or anim == '+anim'

        oekType = ''
        if request.POST.get('oekaki_painter', False) == 'shiPro' or tool=='shiPro':
            oekType = 'Shi pro'
            c.oekakiToolString = 'pro'
        else:
            oekType = 'Shi normal'
            c.oekakiToolString = 'normal';

        c.canvas = False
        c.width  = request.POST.get('oekaki_x','300')
        c.height = request.POST.get('oekaki_y','300')

        if not (isNumber(c.width) or isNumber(c.height)) or (int(c.width)<=10 or int(c.height)<=10):
           c.width = 300
           c.height = 300
        c.tempid = str(long(time.time() * 10**7))

        oekSource = 0
        if isNumber(url) and enablePicLoading:
           post = Post.getPost(url)

           if post.picid:
              pic = Picture.getPicture(post.picid)

              if pic and pic.width:
                 oekSource = post.id
                 c.canvas = h.modLink(pic.path, c.userInst.secid())
                 c.width  = pic.width
                 c.height = pic.height
                 if pic.animpath:
                     c.pchPath = h.modLink(pic.animpath, c.userInst.secid())
        oekaki = Oekaki.create(c.tempid, session.get('uidNumber', -1), oekType, oekSource, c.selfy)
        return self.render('spainter')

    def viewAnimation(self, source):
        post = Post.getPost(source)
        if not post or not post.file or not post.file.animpath:
            c.errorText = _("No animation associated with this post")
            return self.render('error')

        c.pchPath = h.modLink(post.file.animpath, c.userInst.secid())
        return self.render('shiAnimation')

    def processFile(self, file, thumbSize=250):
        if isinstance(file, cgi.FieldStorage) or isinstance(file, FieldStorageLike):
           name = str(long(time.time() * 10**7))
           ext  = file.filename.rsplit('.', 1)[:0:-1]

           #ret: [FileHolder, PicInfo, Picture, Error]

           # We should check whether we got this file already or not
           # If we dont have it, we add it
           if ext:
              ext = ext[0].lstrip(os.sep).lower()
           else:    # Panic, no extention found
              ext = ''
              return [False, False, False, _("Can't post files without extension")]

           # Make sure its something we want to have
           extParams = Extension.getExtension(ext)
           if not extParams or not extParams.enabled:
              return [False, False, False, _(u'Extension "%s" is disallowed') % ext]

           relativeFilePath = h.expandName('%s.%s' % (name, ext))
           localFilePath = os.path.join(g.OPT.uploadPath, relativeFilePath)
           targetDir = os.path.dirname(localFilePath)
           #log.debug(localFilePath)
           #log.debug(targetDir)
           if not os.path.exists(targetDir):
               os.makedirs(targetDir)

           localFile = open(localFilePath, 'w+b')
           shutil.copyfileobj(file.file, localFile)
           localFile.seek(0)
           md5 = hashlib.md5(localFile.read()).hexdigest()
           file.file.close()
           localFile.close()
           fileSize = os.stat(localFilePath)[6]

           picInfo = empty()
           picInfo.localFilePath = localFilePath
           picInfo.relativeFilePath = relativeFilePath
           picInfo.fileSize = fileSize
           picInfo.md5 = md5
           picInfo.sizes = []
           picInfo.extId = extParams.id

           pic = Picture.getByMd5(md5)
           if pic:
               os.unlink(localFilePath)
               picInfo.sizes = [pic.width, pic.height, pic.thwidth, pic.thheight]
               picInfo.thumbFilePath = pic.thumpath
               picInfo.relativeFilePath = pic.path
               picInfo.localFilePath = os.path.join(g.OPT.uploadPath, picInfo.relativeFilePath)
               return [False, picInfo, pic, False]

           thumbFilePath = False
           localThumbPath = False
           try:
               if not extParams.type in ('image', 'image-jpg'):
                 thumbFilePath = extParams.path
                 picInfo.sizes = [None, None, extParams.thwidth, extParams.thheight]
               elif extParams.type == 'image':
                   thumbFilePath = h.expandName('%ss.%s' % (name, ext))
               else:
                  thumbFilePath = h.expandName('%ss.jpg' % (name))
               localThumbPath = os.path.join(g.OPT.uploadPath, thumbFilePath)
               picInfo.thumbFilePath = thumbFilePath
               if not picInfo.sizes:
                   picInfo.sizes = Picture.makeThumbnail(localFilePath, localThumbPath, (thumbSize, thumbSize))
           except:
                os.unlink(localFilePath)
                return [False, False, False, _(u"Broken picture. Maybe it is interlaced PNG?")]

           return [AngryFileHolder((localFilePath, localThumbPath)), picInfo, False, False]
        else:
           return False

    def PostReply(self, post):
        return self.processPost(postid=post)

    def PostThread(self, board):
        return self.processPost(board=board)

    def processPost(self, postid=0, board=u''):
        if not self.currentUserCanPost():
            c.errorText = _("Posting is disabled")
            return self.render('error')

        fileHolder = False
        postRemovemd5 = None
        if self.userInst.Anonymous:
            captchaOk = False
            anonCaptId = session.get('anonCaptId', False)
            captcha = Captcha.getCaptcha(anonCaptId)
            #log.debug("captcha id: " + str(anonCaptId))
            #log.debug("captcha object: " + str(captcha))
            if captcha:
                captchaOk = captcha.test(request.POST.get('captcha', False))

            if not captchaOk:
                c.errorText = _("Incorrect Captcha value")
                return self.render('error')

            remPass = request.POST.get('remPass', False)
            if remPass:
                postRemovemd5 = hashlib.md5(remPass).hexdigest()

        thread = None
        tags = []
        if postid:
            thePost = Post.getPost(postid)

            if not thePost:
                c.errorText = _("Can't post into non-existent thread")
                return self.render('error')

            if thePost.parentid:
                thread = thePost.parentPost
            else:
                thread = thePost
            tags = thread.tags
        else:
            tagstr = request.POST.get('tags', False)
            tags = Tag.stringToTagList(tagstr)
            if not tags:
                c.errorText = _("You should specify at least one board")
                return self.render('error')

            maxTagsCount = int(g.settingsMap['maxTagsCount'].value)
            if len(tags) > maxTagsCount:
                c.errorText = _("Too many tags. Maximum allowed: %s") % (maxTagsCount)
                return self.render('error')

            permCheckRes = Tag.checkForConfilcts(tags)
            if not permCheckRes[0]:
                c.errorText = _("Tags restrictions violations:<br/> %s") % ('<br/>'.join(permCheckRes[1]))
                return self.render('error')

        options = Tag.conjunctedOptionsDescript(tags)
        if not options.images and ((not options.imagelessThread and not postid) or (postid and not options.imagelessPost)):
            c.errorText = "Unacceptable combination of tags"
            return self.render('error')

        postMessageInfo = None
        tempid = request.POST.get('tempid', False)
        animPath = None
        if tempid: # TODO FIXME : move into parser
           oekaki = Oekaki.get(tempid)
           animPath = oekaki.animPath
           file = FieldStorageLike(oekaki.path, os.path.join(g.OPT.uploadPath, oekaki.path))
           postMessageInfo = u'<span class="postInfo">Drawn with <b>%s%s</b> in %s seconds</span>' \
                            % (oekaki.type, oekaki.selfy and "+selfy" or "", str(int(oekaki.time/1000)))
           if oekaki.source:
              postMessageInfo += ", source " + self.formatPostReference(oekaki.source)
           oekaki.delete()
        else:
           file = request.POST.get('file', False)

        # VERY-VERY BIG CROCK OF SHIT !!!
        # VERY-VERY BIG CROCK OF SHIT !!!
        postMessage = filterText(request.POST.get('message', u'')).replace('&gt;','>') #XXX: TODO: this must be fixed in parser
        # VERY-VERY BIG CROCK OF SHIT !!!
        # VERY-VERY BIG CROCK OF SHIT !!!!

        postMessageShort = None
        postMessageRaw = None
        if postMessage:
           if len(postMessage) <= 15000:
               parser = WakabaParser(g.OPT, thread and thread.id or -1)
               maxLinesInPost = int(g.settingsMap['maxLinesInPost'].value)
               cutSymbols = int(g.settingsMap["cutSymbols"].value)
               parsedMessage = parser.parseWakaba(postMessage, self, lines=maxLinesInPost, maxLen=cutSymbols)
               fullMessage = parsedMessage[0]
               postMessageShort = parsedMessage[1]

               #FIXME: not best solution
               #if not fullMessage[5:].startswith(post.message):
               if (not postMessage in fullMessage) or postMessageShort:
                   postMessageRaw = postMessage

               postMessage = fullMessage
           else:
               c.errorText = _('Message is too long')
               return self.render('error')

        postTitle = filterText(request.POST.get('title', u''))

        fileDescriptors = self.processFile(file, options.thumbSize)
        fileHolder = False
        existentPic = False
        picInfo = False
        if fileDescriptors:
            fileHolder = fileDescriptors[0] # Object for file auto-removing
            picInfo = fileDescriptors[1]
            existentPic = fileDescriptors[2]
            errorMessage = fileDescriptors[3]
            if errorMessage:
                c.errorText = errorMessage
                return self.render('error')

        if picInfo:
            if not options.images:
                c.errorText = _("Files are not allowed on this board")
                return self.render('error')
            if picInfo.fileSize > options.maxFileSize:
                c.errorText = _("File size (%d) exceeds the limit (%d)") % (picInfo.fileSize, options.maxFileSize)
                return self.render('error')
            if picInfo.sizes and picInfo.sizes[0] and picInfo.sizes[1] and (picInfo.sizes[0] < options.minPicSize or picInfo.sizes[1] < options.minPicSize):
                c.errorText = _("Image is too small. At least one side should be %d or more pixels.") % (options.minPicSize)
                return self.render('error')

            try:
                audio = EasyID3(picInfo.localFilePath)
                trackInfo = '<span class="postInfo">ID3 info:</span><br/>'
                taglist = sorted(audio.keys())
                taglist.reverse()
                tagsToShow = taglist
                for tag in tagsToShow:
                    #log.debug(tag)
                    #log.debug(audio[tag])
                    value = audio[tag]
                    if value and isinstance(value, list) and tag in id3FieldsNames.keys():
                        value = ' '.join(value)
                        trackInfo += u'<b>%s</b>: %s<br/>' % (filterText(id3FieldsNames[tag]), filterText(value))
                if not postMessageInfo:
                    postMessageInfo = trackInfo
                else:
                    postMessageInfo += '<br/>%s' % trackInfo
            except:
                pass

        if not postMessage and not picInfo and not postMessageInfo:
            c.errorText = _("At least message or file should be specified")
            return self.render('error')

        postSpoiler = False
        if options.enableSpoilers:
            postSpoiler = request.POST.get('spoiler', False)

        postSage = request.POST.get('sage', False)
        if postid:
            if not picInfo and not options.imagelessPost:
                c.errorText = _("Replies without image are not allowed")
                return self.render('error')
        else:
            if not picInfo and not options.imagelessThread:
                c.errorText = _("Threads without image are not allowed")
                return self.render('error')

        postParams = empty()
        postParams.message = postMessage
        postParams.messageShort = postMessageShort
        postParams.messageRaw = postMessageRaw
        postParams.messageInfo = postMessageInfo
        postParams.title = postTitle
        postParams.spoiler = postSpoiler
        postParams.uidNumber = self.userInst.uidNumber
        postParams.removemd5 = postRemovemd5
        postParams.postSage = postSage
        #postParams.replyTo = postid
        postParams.thread = thread
        postParams.tags = tags
        postParams.existentPic = existentPic
        postParams.picInfo = picInfo
        if postParams.picInfo:
            postParams.picInfo.animPath = animPath

        post = Post.create(postParams)

        if fileHolder:
            fileHolder.disableDeletion()
        self.gotoDestination(post, postid)
