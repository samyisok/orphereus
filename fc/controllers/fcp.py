import logging

from fc.lib.base import *
from fc.model import *
from sqlalchemy.orm import eagerload
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql import and_, or_, not_
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
from fc.lib.fuser import FUser
from fc.lib.miscUtils import *
from fc.lib.constantValues import *
from fc.lib.settings import *
from OrphieBaseController import OrphieBaseController

log = logging.getLogger(__name__)

class FcpController(OrphieBaseController):
    def __before__(self):
        settingsMap = getSettingsMap()
        c.title = settingsMap['title'].value
        c.devmode = devMode 
        
    def login(self, user):
        session['uidNumber'] = user.uidNumber
        session.save()
        
    def logout(self):
        session.delete()        
        redirect_to('/')
        
    def authorize(self, url):
        if url:
            c.currentURL = '/' + str(url.encode('utf-8')) + '/'
        else:
            c.currentURL = '/'
        if request.POST.get('code',False):
            code = self.genUid(request.POST['code'].encode('utf-8')) #hashlib.sha512(request.POST['code'].encode('utf-8') + hashlib.sha512(hashSecret).hexdigest()).hexdigest()
            user = meta.Session.query(User).options(eagerload('options')).filter(User.uid==code).first()
            if user:
                self.login(user)
                redirect_to(c.currentURL)
        c.boardName = _('Login')
        return self.render('login')
        
    def register(self,invite):
        if 'invite' not in session:
            invite_q = meta.Session.query(Invite).filter(Invite.invite==invite).first()
            if invite_q:
                meta.Session.delete(invite_q)
                meta.Session.commit()
                session['invite'] = invite
                session.save()
            else:
                c.currentURL = '/'
                return self.render('login')
                
        key = request.POST.get('key','').encode('utf-8')
        key2 = request.POST.get('key2','').encode('utf-8')
        uid = self.genUid(key) #hashlib.sha512(key + hashlib.sha512(hashSecret).hexdigest()).hexdigest()
        user = meta.Session.query(User).options(eagerload('options')).filter(User.uid==uid).first()
        if user:
            self.banUser(user, 7777, "Your Security Code was used during registration by another user. Contact administrator immediately please.")
            del session['invite']
            c.boardName = _('Error')
            c.errorText = _("You entered already existing password. Previous account was banned. Contact administrator please.")
            return self.render('error')
            
        if key:
            if len(key)>=24 and key == key2:                
                user = User()
                user.uid = uid
                meta.Session.save(user)
                meta.Session.commit()
                del session['invite']
                self.login(user)
                redirect_to('/')
        c.boardName = _('Register')
        return self.render('register')
        
    def oekakiSave(self, environ, start_response, url, tempid):
        start_response('200 OK', [('Content-Type','text/plain'),('Content-Length','2')])
        oekaki = meta.Session.query(Oekaki).filter(Oekaki.tempid==tempid).first()
        cl = int(request.environ['CONTENT_LENGTH'])
        if oekaki and cl:
            id = request.environ['wsgi.input'].read(1)
            if id == 'S':
                headerLength = int(request.environ['wsgi.input'].read(8))
                header = request.environ['wsgi.input'].read(headerLength)
                bodyLength = int(request.environ['wsgi.input'].read(8))
                request.environ['wsgi.input'].read(2)
                body = request.environ['wsgi.input'].read(bodyLength)
                headers = header.split('&')
                type = filterText(headers[0].split('=')[1])
                time = headers[1].split('=')[1]
                localFilePath = os.path.join(uploadPath, tempid + '.' + type)
                localFile = open(localFilePath,'wb')
                localFile.write(body)
                localFile.close()
                oekaki.time = time
                oekaki.path = tempid + '.' + type
                meta.Session.commit()
        return ['ok']
        
    def banned(self):
        self.userInst = FUser(session.get('uidNumber',-1))
        c.userInst = self.userInst
        if self.userInst.isBanned():
            c.boardName = _('Banned')
            return self.render('banned')
        else:
            c.boardName = _('Error')
            c.errorText = _("ORLY?")
            return self.render('error')
            
    def UnknownAction(self):      
        c.boardName = _('Error')
        c.errorText = _("Excuse me, WTF are you?")
        return self.render('error')
    
