# -*- coding: utf-8 -*-
<%page args="thread"/>

%if thread.file:
<span class="filesize">
    <a href="${g.OPT.filesPathWeb + h.modLink(thread.file.path, c.userInst.secid())}"
    %if thread.file.extension.newWindow:
        target="_blank"
    %endif
    >
    ${h.modLink(thread.file.path, c.userInst.secid(), True)}</a>

    (<em>${'%.2f' % (thread.file.size / 1024.0)}
    %if thread.file.width and thread.file.height:
        ${_('Kbytes')}, ${thread.file.width}x${thread.file.height}</em>)
    %else:
        ${_('Kbytes')}</em>)
    %endif
</span>

<br />
<a href="${g.OPT.filesPathWeb + h.modLink(thread.file.path, c.userInst.secid())}"
%if thread.file.extension.newWindow:
    target="_blank"
%endif
>
%if thread.spoiler:
    <img src="${g.OPT.staticPathWeb}images/spoiler.png" class="thumb" alt="Spoiler"/>
%elif 'image' in thread.file.extension.type:
    <img src="${g.OPT.filesPathWeb +  h.modLink(thread.file.thumpath, c.userInst.secid())}" width="${thread.file.thwidth}" height="${thread.file.thheight}" class="thumb"  alt="Preview" />
%else:
    <img src="${g.OPT.staticPathWeb +  h.modLink(thread.file.thumpath, c.userInst.secid())}" width="${thread.file.thwidth}" height="${thread.file.thheight}" class="thumb"  alt="Preview" />
%endif
</a>
%elif thread.picid == -1:
    <span class="thumbnailmsg">${_('Picture was removed by user or administrator')}</span><br/>
    <img src="${g.OPT.staticPathWeb}images/picDeleted.png" class="thumb" alt="Removed"/>
%endif
<a name="i${thread.id}"></a>
&nbsp;<a href="javascript:void(0)" onclick="showDeleteBoxes()"><img src="${g.OPT.staticPathWeb}images/delete.gif" border="0" alt="x" title="Delete"/></a>
<span style="display:none" class="delete">
%if thread.uidNumber == c.uidNumber or c.enableAllPostDeletion:
    <input type="checkbox" name="delete-${thread.id}" value="${thread.id}" />
    %if g.OPT.enableFinalAnonymity and not c.userInst.Anonymous and thread.uidNumber == c.uidNumber:
        <a href="/${thread.id}/anonymize">[FA]</a>
    %endif
%endif
%if c.userInst.isAdmin() and c.userInst.canManageUsers():
    <a href="/holySynod/manageUsers/editAttempt/${thread.id}">[User]</a>
%endif
%if c.userInst.isAdmin() and c.userInst.canManageMappings():
    <a href="/holySynod/manageMappings/show/${thread.id}">[Tags]</a>
%endif
</span>
%if thread.title:
    <span class="filetitle">${thread.title}</span>
%endif


<span
%if getattr(thread, 'mixed', False):
 style="color: red;"
%endif
>
${h.modTime(thread, c.userInst, g.OPT.secureTime)}
</span>
<span class="reflink">
%if c.board:
    <a href="/${thread.id}#i${thread.id}" ${c.currentUserCanPost and """onclick="doQuickReplyForm(event,%s,%s)" """ % (thread.id,thread.id) or ""}>#${g.OPT.secondaryIndex and thread.secondaryIndex or thread.id}</a>
%else:
    <a href="javascript:insert('&gt;&gt;${thread.id}')" ${c.currentUserCanPost and """onclick="doQuickReplyForm(event,%s,%s)" """ % (thread.id,thread.id) or ""}>#${g.OPT.secondaryIndex and thread.secondaryIndex or thread.id}</a>
%endif
%if g.OPT.hlAnonymizedPosts and thread.uidNumber == 0:
    <b class="signature"><a href="/static/finalAnonymity" target="_blank">FA</a></b>
%endif
</span>

    &nbsp;
    ${_('Posted in')}:
%for t in thread.tags:
    <a href="/${t.tag}/"
    %if t.options:
        title="${t.options.comment}"
    %endif
    >/${t.tag}/</a>
%endfor


&nbsp;
%if not c.userInst.Anonymous or g.OPT.allowAnonProfile:
[<a href="/ajax/hideThread/${thread.id}/${c.PostAction}${c.curPage and '/page/'+str(c.curPage) or ''}">${_('Hide Thread')}</a>]
%endif

%if c.currentUserCanPost:
%if thread.file and thread.file.width:
 [<a href="/${thread.id}/oekakiDraw">Draw</a>]
%endif
[<a href="/${thread.id}">Reply</a>]
%else:
[<a href="/${thread.id}">View thread</a>]
%endif

<blockquote class="postbody" id="quickReplyNode${thread.id}">
    %if (c.count > 1) and thread.messageShort and c.userInst.hideLongComments():
        ${h.modMessage(thread.messageShort, c.userInst, g.OPT.secureText)}
        <br />
        ${_('Comment is too long.')} <a href="/${thread.id}#i${thread.id}" onclick="getFullText(event,${thread.id},${thread.id});" class="expandPost">${_('Full version')}</a>
    %else:
        ${h.modMessage(thread.message, c.userInst, g.OPT.secureText)}
    %endif
    %if thread.messageInfo:
        ${thread.messageInfo}
    %endif
</blockquote>
%if 'omittedPosts' in dir(thread) and thread.omittedPosts:
    <span class="omittedposts">${_('%s posts omitted.') % thread.omittedPosts } </span>
%endif
