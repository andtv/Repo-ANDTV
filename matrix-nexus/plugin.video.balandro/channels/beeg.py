# -*- coding: utf-8 -*-

import re

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, jsontools


host = 'https://beeg.com/'

url_api = 'https://store.externulls.com/'


def mainlist(item):
    return mainlist_pelis(item)


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    descartar_xxx = config.get_setting('descartar_xxx', default=False)

    if descartar_xxx: return itemlist

    if config.get_setting('adults_password'):
        from modules import actions
        if actions.adults_password(item) == False:
            return itemlist

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = url_api + 'facts/tag?id=27173&limit=48&offset=0' ))

    itemlist.append(item.clone( title = 'Por canal', action = 'categorias', url = url_api + 'tag/facts/tags?get_original=true&slug=index', group = 'chs' ))
    itemlist.append(item.clone( title = 'Por categoría', action = 'categorias', url = url_api + 'tag/facts/tags?get_original=true&slug=index', group = 'cats' ))

    # ~ itemlist.append(item.clone( title = 'Buscar vídeo ...', action = 'search', search_type = 'movie' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    jdata = jsontools.load(data)

    for video in jdata:
        try:
            id = video['fc_file_id']
            th = video["fc_facts"][0]['fc_thumbs']

            stuff = video["file"]["stuff"]

            title = stuff["sf_name"]
        except:
            continue

        thumb = "https://thumbs-015.externulls.com/videos/%s/%s.jpg" % (id, th[0])

        url = url_api + 'facts/file/' + str(id)

        itemlist.append(item.clone( action = 'findvideos', url = url, title = title, thumbnail = thumb,
                                              contentType = 'movie', contentTitle = title, contentExtra='adults' ))

    if itemlist:
         page = int(scrapertools.find_single_match(item.url, '&offset=([0-9]+)'))
         next_page = (page + 48)

         if next_page:
             next_page = re.sub(r"&offset=\d+", "&offset={0}".format(next_page), item.url)

             itemlist.append(item.clone( title = 'Siguientes ...', url = next_page, action = 'list_all', text_color = 'coral' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    jdata = jsontools.load(data)

    for tag in jdata:
        thumb = ''

        try:
            id = tag["id"]
            title = tag["tg_name"]
            slug = tag["tg_slug"]

            if tag.get("thumbs", ""):
                th = tag["thumbs"]
                thumb = "https://thumbs-015.externulls.com/tags/%s" % th[0]

        except:
            continue

        url = url_api + 'facts/tag?slug=%s&limit=48&offset=0' % slug

        if item.group == 'chs':
            if not thumb: continue
        else:
            if thumb: continue

        title = title.capitalize()

        itemlist.append(item.clone( action = 'list_all', url = url, title = title, thumbnail = thumb ))

    return sorted(itemlist, key=lambda x: x.title)


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = re.compile('"fl_cdn_(\d+)": "([^"]+)"', re.DOTALL).findall(data)

    for qlty, url in matches:
        url = 'https://video.beeg.com/' + url

        itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', quality = qlty, url = url, language = 'VO' ))

    return sorted(itemlist, key=lambda it: it.quality)


def list_search(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    jdata = jsontools.load(data)

    for tag in jdata:
        title = tag['tg_name']
        url = url_api + 'facts/tag?slug=' + tag['tg_slug'] + '&get_original=true'

        itemlist.append(item.clone( action = 'list_all', url = url, thumbnail='', title = title ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        # ~  websocket
        # ~ # ws_send('{"type":"search","payload":{"Search_string":"' + texto.replace(" ", "+") + '","offset":0,"limit":30}}')
        item.url =  "wss://search.externulls.com/" + texto.replace(" ", "+")
        return list_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []