# -*- coding: utf-8 -*-
<%inherit file="wakaba.main.mako" />

<ul style="padding-left: 16px;">
<li><b>${_('Found')}:</b> ${c.count}</li>
%if c.warnings:
%for w in c.warnings:
<li><i>${w}</i></li>
%endfor
%endif
</ul>

<form action="${h.url_for('searchBase')}" method="post">
    <input type="text" name="query" size="20" value="${c.query}"/>
    <input value="${_('Search again')}" type="submit" />
    [<a href="${h.url_for('static', page='markup', anchor='search')}" target="_blank">${_('Help')}</a>]
</form>

<%include file="wakaba.paginator.mako" args="routeName='search', kwargDict={'text' : c.query}"/>

<%def name="threadInfo(thread)">
    ${_('Thread')}
    <a href="${h.postUrl(thread.id, thread.id)}">#${g.OPT.secondaryIndex and thread.secondaryIndex or thread.id}</a>
    ${_('from')}:
    %for t in thread.tags:
      <a href="${h.url_for('boardBase', board=t.tag)}">/${t.tag}/</a>
    %endfor
</%def>

%for pt in c.posts:
%if h.postEnabledToShow(pt, c.userInst):
<table id="quickReplyNode${pt.id}">
    <tbody>
        <tr>
            <td class="doubledash">&gt;&gt;</td>
            <td class="reply" id="reply${pt.id}">
              &nbsp;
                <a name="i${pt.id}"></a>
                <label>
                    %if pt.sage:
                        <img src='${g.OPT.staticPathWeb}images/sage.png' alt='' />
                    %endif
                    %if pt.title:
                        <span class="replytitle">${pt.title}</span>
                    %endif
                    ${h.tsFormat(pt.date)}
                </label>
                <span class="reflink">
                %if pt.parentPost:
                    <a href="${h.postUrl(pt.parentPost.id, pt.id)}">#${g.OPT.secondaryIndex and pt.secondaryIndex or pt.id}</a>;
                    ${threadInfo(pt.parentPost)}
                %else:
                    <a href="${h.postUrl(pt.id, pt.id)}">#${g.OPT.secondaryIndex and pt.secondaryIndex or pt.id}</a>;
                    ${threadInfo(pt)}
                %endif
        </span>
        &nbsp;
                %if pt.attachments:
                %for attachment in pt.attachments
                %if attachment.attachedFile.id != 0:
                    <br /><span class="filesize">${_('File:')}

                    <a href="${g.OPT.filesPathWeb + h.modLink(attachment.attachedFile.path, c.userInst.secid())}"
                    %if attachment.attachedFile.extension.newWindow:
                        target="_blank"
                    %endif
                    >
                    ${h.modLink(attachment.attachedFile.path, c.userInst.secid(), True)}</a>
                    (<em>${'%.2f' % (attachment.attachedFile.size / 1024.0)} Kbytes, ${attachment.attachedFile.width}x${attachment.attachedFile.height}</em>)</span>
                    <span class="thumbnailmsg">${_('This is resized copy. Click it to view original image')}</span><br />
                    <a href="${g.OPT.filesPathWeb + h.modLink(attachment.attachedFile.path, c.userInst.secid())}"
                    %if attachment.attachedFile.extension.newWindow:
                        target="_blank"
                    %endif
                    >

                    <%include file="wakaba.thumbnail.mako" args="post=pt,attachment=attachment" />

                    </a>
                    %else:
                        <span class="thumbnailmsg">${_('Picture was removed by user or administrator')}</span><br/>
                        <img src='${g.OPT.staticPathWeb}images/picDeleted.png' class="thumb">
                    %endif
                  %endfor
                  %endif

                <blockquote class="postbody" id="postBQId${pt.id}">
                %if pt.id in c.highlights:
                    ${c.highlights[pt.id][1]}
                %else:
                    ${pt.message}
                %endif
                </blockquote>
            </td>
        </tr>
    </tbody>
</table>
%else:
<table>
    <tbody>
        <tr>
        <td class="reply">
          <blockquote class="postbody" id="postBQId${pt.id}">
          ${_("Can't show this post due security settings")}
          </blockquote>
        </td>
        </tr>
    </tbody>
</table>
%endif
%endfor

<br/>
<form action="${h.url_for('searchBase')}" method="post">
    <input type="text" name="query" size="20" value="${c.query}"/>
    <input value="${_('Search again')}" type="submit" />
</form>

<%include file="wakaba.jsService.mako" />

<%include file="wakaba.paginator.mako" args="routeName='search', kwargDict={'text' : c.query}"/>
