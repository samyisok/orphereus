"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('error/:action/:id', controller='error')

    # CUSTOM ROUTES HERE
    map.connect('', controller='fcc', action='GetOverview')
    map.connect('/:url/auth', controller='fcc', action='authorize', conditions=dict(method=['POST']))
    map.connect('/:post', controller='fcc', action='PostReply',conditions=dict(method=['POST']),requirements=dict(post='\d+'))
    map.connect('/:board', controller='fcc', action='PostThread',conditions=dict(method=['POST']))
    map.connect('/:post/delete', controller='fcc', action='DeletePost',conditions=dict(method=['POST']))
    map.connect('/:post', controller='fcc', action='GetThread',requirements=dict(post='\d+'))
    map.connect('/:board', controller='fcc', action='GetBoard')
    map.connect('*url', controller='fcc', action='UnknownAction')

    return map
