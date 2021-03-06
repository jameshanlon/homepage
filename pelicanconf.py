#!/usr/bin/env python

from __future__ import unicode_literals
import sys
import os
import logging
sys.path.insert(0, os.getcwd())
from thumbnail import get_thumbnail

AUTHOR = u'James W. Hanlon'
SITENAME = u'James W. Hanlon'
SITEURL = 'http://jameswhanlon.com'

ASSETS_PREFIX = 'https://jwh.ams3.digitaloceanspaces.com/homepage'

def get_asset_url(filepath):
    return ASSETS_PREFIX+'/'+filepath

JINJA_FILTERS = { 'asset': get_asset_url,
                  'thumbnail': get_thumbnail, }

PATH = 'content'
IMAGE_PATH = 'images'
THUMBNAIL_DIR = 'images'
THUMBNAIL_SIZES = { 'thumb': '150x?', }
THUMBNAIL_KEEP_TREE = True
GALLERY_PATH = 'images'

RESIZE = [
    ('gallery', False, 200, 200),
]

TIMEZONE = 'Europe/Paris'

DEFAULT_LANG = u'en'
DEFAULT_DATE_FORMAT = "%d %b %Y"
DEFAULT_PAGINATION = False

PAGE_SAVE_AS = '{slug}.html'

MENU_ITEMS = [
    ('notes',    'index.html'),
    ('projects', 'projects.html'),
    ('archive',  'archive.html'),
    ('about',    'about.html'),
]

STATIC_PATHS = [
    'images',
    'files',
    'includes',
    'files/favicon.png',
    'files/robots.txt',
    'CNAME',
]

ARTICLE_EXCLUDES = [
    'vim-commands', # vim-commands directory
]

EXTRA_PATH_METADATA = {
    'files/robots.txt': {'path': 'robots.txt'},
    'files/favicon.png': {'path': 'favicon.png'},
}

DEFAULT_METADATA = {
    'status': 'draft',
}

THEME = 'theme'

TYPOGRIFY = True

RELATIVE_URLS = True

FEED_ATOM = 'reeds/atom.xml'
FEED_RSS = 'reeds/rss.xml'

PLUGIN_PATHS = ['pelican-plugins', ]
PLUGINS = ['jinja_content']
