import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import eagerload

from fc.model import meta
from fc.model.TagOptions import TagOptions
from fc.lib.miscUtils import empty
import datetime
import re

import logging
log = logging.getLogger(__name__)

from fc.model import meta

t_tags = sa.Table("tags", meta.metadata,
    sa.Column("id"       , sa.types.Integer, primary_key=True),
    sa.Column("tag"      , sa.types.UnicodeText, nullable=False),
    sa.Column("replyCount" , sa.types.Integer, nullable=False, server_default='0'),
    sa.Column("threadCount" , sa.types.Integer, nullable=False, server_default='0'),
    )

t_tagsToPostsMap = sa.Table("tagsToPostsMap", meta.metadata,
#    sa.Column("id"          , sa.types.Integer, primary_key=True),
    sa.Column('postId'  , sa.types.Integer, sa.ForeignKey('posts.id')),
    sa.Column('tagId'   , sa.types.Integer, sa.ForeignKey('tags.id')),
    )

class Tag(object):
    def __init__(self, tag):
        self.tag = tag
        self.replyCount = 0
        self.threadCount = 0
        self.options = TagOptions()

    def save(self):
        meta.Session.commit()
    """
    def __le__(self, other):
        return cmp(self.tag, other.tag)

    def __ge__(self, other):
        return ncmp(other.tag, self.tag)
    """
    @staticmethod
    def getBoards():
        return Tag.query.join('options').filter(TagOptions.persistent==True).order_by(TagOptions.sectionId).all()

    @staticmethod
    def getTag(tagName):
        return Tag.query.options(eagerload('options')).filter(Tag.tag == tagName).first()

    @staticmethod
    def getById(tagId):
        return Tag.query.options(eagerload('options')).filter(Tag.id == tagId).first()

    @staticmethod
    def getAll():
        return Tag.query.options(eagerload('options')).all()

    @staticmethod
    def getAllByIds(idList):
        return Tag.query.options(eagerload('options')).filter(Tag.id.in_(idList)).all()

    @staticmethod
    def getAllByNames(names):
        return Tag.query.options(eagerload('options')).filter(Tag.tag.in_(names)).all()

    @staticmethod
    def stringToTagList(tagstr):
        tags = []
        tagsl= []
        if tagstr:
            tagstr = tagstr.replace('&amp;', '&')
            regex = re.compile(r"""([^,@~\#\+\-\&\s\/\\\(\)<>'"%\d][^,@~\#\+\-\&\s\/\\\(\)<>'"%]*)""")
            tlist = regex.findall(tagstr)
            for t in tlist:
                if not t in tagsl:
                    tag = Tag.getTag(t)

                    if tag:
                        tags.append(tag)
                    else:
                        tags.append(Tag(t))
                    tagsl.append(t)
        return tags

    @staticmethod
    def csStringToExTagIdList(string):
        result = []
        tags = string.split(',')
        for tag in tags:
            aTag = Tag.query.options(eagerload('options')).filter(Tag.tag==tag).first()
            if aTag:
                result.append(aTag.id)
        return result

    @staticmethod
    def conjunctedOptionsDescript(tags):
        options = empty()
        optionsFlag = True
        rulesList = []
        for t in tags:
            if t.options:
                if optionsFlag:
                    options.imagelessThread = t.options.imagelessThread
                    options.imagelessPost   = t.options.imagelessPost
                    options.images   = t.options.images
                    options.enableSpoilers = t.options.enableSpoilers
                    options.maxFileSize = t.options.maxFileSize
                    options.minPicSize = t.options.minPicSize
                    options.thumbSize = t.options.thumbSize
                    options.canDeleteOwnThreads = t.options.canDeleteOwnThreads
                    options.selfModeration = t.options.selfModeration
                    optionsFlag = False
                else:
                    options.imagelessThread = options.imagelessThread & t.options.imagelessThread
                    options.imagelessPost = options.imagelessPost & t.options.imagelessPost
                    options.enableSpoilers = options.enableSpoilers & t.options.enableSpoilers
                    options.canDeleteOwnThreads = options.canDeleteOwnThreads & t.options.canDeleteOwnThreads
                    options.images = options.images & t.options.images
                    options.selfModeration = options.selfModeration | t.options.selfModeration

                    perm = meta.globj.OPT.permissiveFileSizeConjunction
                    if (perm and t.options.maxFileSize > options.maxFileSize) or (not perm and t.options.maxFileSize < options.maxFileSize):
                        options.maxFileSize = t.options.maxFileSize

                    if t.options.minPicSize > options.minPicSize:
                        options.minPicSize = t.options.minPicSize
                    if t.options.thumbSize < options.thumbSize:
                        options.thumbSize = t.options.thumbSize

                tagRulesList = t.options.specialRules.split(';')
                for rule in tagRulesList:
                    if rule and not rule in rulesList:
                        rulesList.append(rule)

        options.rulesList = rulesList

        if optionsFlag:
            options.imagelessThread = meta.globj.OPT.defImagelessThread
            options.imagelessPost   = meta.globj.OPT.defImagelessPost
            options.images = meta.globj.OPT.defImages
            options.enableSpoilers = meta.globj.OPT.defEnableSpoilers
            options.canDeleteOwnThreads = meta.globj.OPT.defCanDeleteOwnThreads
            options.maxFileSize = meta.globj.OPT.defMaxFileSize
            options.minPicSize = meta.globj.OPT.defMinPicSize
            options.thumbSize = meta.globj.OPT.defThumbSize
            options.selfModeration = meta.globj.OPT.defSelfModeration
            options.specialRules = u''
        return options

    @staticmethod
    def getStats():
        boards = Tag.getAll()
        ret = empty()
        ret.boards=[]
        ret.tags=[]
        ret.totalBoardsThreads = 0
        ret.totalTagsThreads = 0
        ret.totalBoardsPosts = 0
        ret.totalTagsPosts = 0
        for b in boards:
            if not b.id in meta.globj.forbiddenTags:
                bc = empty()
                bc.count = b.threadCount
                bc.postsCount = b.replyCount
                bc.board = b

                if b.options and b.options.persistent:
                    ret.boards.append(bc)
                    ret.totalBoardsThreads += bc.count
                    ret.totalBoardsPosts += bc.postsCount
                else:
                    ret.tags.append(bc)
                    ret.totalTagsThreads += bc.count
                    ret.totalTagsPosts += bc.postsCount
        return ret

