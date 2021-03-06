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

import sqlalchemy as sa
from sqlalchemy import orm

from Orphereus.model import meta
import os
import Image

import logging
log = logging.getLogger(__name__)

def t_picture_init(dialectProps):
    t_piclist = sa.Table("picture", meta.metadata,
        sa.Column("id"       , sa.types.Integer, sa.Sequence('picture_id_seq'), primary_key = True),
        sa.Column("path"     , sa.types.String(255), nullable = True),
        sa.Column("thumpath" , sa.types.String(255), nullable = True),
        sa.Column("width"    , sa.types.Integer, nullable = True),
        sa.Column("height"   , sa.types.Integer, nullable = True),
        sa.Column("thwidth"  , sa.types.Integer, nullable = False),
        sa.Column("thheight" , sa.types.Integer, nullable = False),
        sa.Column("size"     , sa.types.Integer, nullable = False),
        sa.Column("md5"      , sa.types.String(32), nullable = False, index = True),
        sa.Column("extid"    , sa.types.Integer, sa.ForeignKey('extension.id')),
        sa.Column("pictureInfo"  , sa.types.UnicodeText, nullable = True),
        sa.Column("pInfoPic", sa.types.Text, nullable = True), # TODO: field for metadata
        #sa.Column("animpath" , sa.types.String(255), nullable = True), #TODO: XXX: dirty solution
        )

    t_filesToPostsMap = sa.Table("filesToPostsMap", meta.metadata,
        sa.Column("id"          , sa.types.Integer, sa.Sequence('filesToPostsMap_id_seq'), primary_key = True),
        #sa.Column('postId', sa.types.Integer, sa.ForeignKey('post.id'), primary_key = True),
        #sa.Column('fileId', sa.types.Integer, sa.ForeignKey('picture.id'), primary_key = True),
        sa.Column('postId', sa.types.Integer, sa.ForeignKey('post.id')),
        sa.Column('fileId', sa.types.Integer, sa.ForeignKey('picture.id')),
        sa.Column("spoiler", sa.types.Boolean, nullable = True),
        sa.Column("relationInfo"  , sa.types.UnicodeText, nullable = True),
        sa.Column("animpath" , sa.types.String(255), nullable = True),
        sa.Column("pInfoRel", sa.types.Text, nullable = True), # TODO: field for metadata
        )
    #sa.UniqueConstraint(t_filesToPostsMap.c.postId, t_filesToPostsMap.c.fileId)
    sa.Index('ix_filemap_postid_fileid', t_filesToPostsMap.c.postId, t_filesToPostsMap.c.fileId)

    return t_piclist, t_filesToPostsMap

class PictureAssociation(object):
    def __init__(self, spoiler, relationInfo, animPath):
        self.spoiler = spoiler
        self.relationInfo = relationInfo
        self.animpath = animPath

class Picture(object):
    def __init__(self, relativeFilePath, thumbFilePath, fileSize, picSizes, extId, md5, pictureInfo):
        self.path = relativeFilePath
        self.thumpath = thumbFilePath
        self.width = picSizes[0]
        self.height = picSizes[1]
        self.thwidth = picSizes[2]
        self.thheight = picSizes[3]
        self.extid = extId
        self.size = fileSize
        self.md5 = md5
        self.pictureInfo = pictureInfo

    @staticmethod
    def create(relativeFilePath, thumbFilePath, fileSize, picSizes, extId, md5, pictureInfo, commit = False):
        pic = Picture(relativeFilePath, thumbFilePath, fileSize, picSizes, extId, md5, pictureInfo)
        if commit:
            meta.Session.add(pic)
            meta.Session.commit()
        return pic

    @staticmethod
    def getPicture(id):
        return Picture.query.filter(Picture.id == id).first()

    @staticmethod
    def getByMd5(md5):
        q = Picture.query.filter(Picture.md5 == md5)
        cc = q.count()
        if cc > 1:
            log.error("Many pictures (%d) with md5 %s" % (cc, md5))
        return q.first()

    @staticmethod
    def makeThumbnail(source, dest, maxSize):
        sourceImage = Image.open(source)
        size = sourceImage.size
        if sourceImage:
            sourceImage.thumbnail(maxSize, Image.ANTIALIAS)
            sourceImage.save(dest)
            return size + sourceImage.size
        else:
            return []

    def pictureRefCount(self):
        from Orphereus.model.Post import Post
        return Post.query.filter(Post.attachments.any(PictureAssociation.attachedFile.has(Picture.id == self.id))).count()

    def deletePicture(self, commit = True):
        if self.id > 0 and self.pictureRefCount() == 0:
            filePath = os.path.join(meta.globj.OPT.uploadPath, self.path)
            thumPath = os.path.join(meta.globj.OPT.uploadPath, self.thumpath)
            if os.path.isfile(filePath):
                os.unlink(filePath)

            ext = self.extension
            if not ext.path:
                if os.path.isfile(thumPath):
                    os.unlink(thumPath)

            meta.Session.delete(self)
            if commit:
                meta.Session.commit()
