# -*- coding: utf-8 -*-
# -*- Channel Series Antiguas -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from core.item import Item
from core import servertools
from core import scrapertools
from channelselector import get_thumb
from platformcode import config, logger
from channels import autoplay
from lib.AlfaChannelHelper import DictionaryAllChannel

IDIOMAS = {"Latino": "LAT"}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = []

canonical = {
             'channel': 'seriesantiguas', 
             'host': config.get_setting("current_host", 'seriesantiguas', default=''), 
             'host_alt': ["https://seriesantiguas.com/"], 
             'host_black_list': ["https://www.seriesantiguas.com/"], 
             'pattern': ['<a\s*href="([^"]+)"[^>]*>\s*(?:Principal|M.s\s*vistas)\s*<\/a>'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

timeout = 5
kwargs = {}

finds = {'find': {'find': [{'tag': ['div'], 'class': ['progression-masonry-margins']}], 
                  'find_all': [{'tag': ['div'], 'class': ['progression-masonry-item']}]}, 
         'categories': [], 
         'search': [], 
         'next_page': {'find': [{'tag': ['div'], 'class': ['nav-previous']}, {'tag': ['a'], '@ARG': 'href'}]}, 
         'next_page_rgx': [['\/page\/\d+', '/page/%s']], 
         'last_page': False, 
         'year': [], 
         'season_episode': [], 
         'seasons': {'find': [{'tag': ['ul'], 'class': ['video-tabs-nav-aztec nav']}], 'find_all': [['li']]}, 
         'episode_url': '', 
         'episodes': {'find': [{'tag': ['div'], 'id': ['aztec-tab-%s']}], 
                      'find_all': [{'tag': ['div'], 'class': ['progression-studios-season-item']}]}, 
         'episode_num': ['(?i)(\d+)\.\s*[^$]+$', '(?i)[a-z_0-9 ]+\s*\((?:temp|epis)\w*\s*(?:\d+\s*x\s*)?(\d+)\)'], 
         'episode_clean': ['(?i)\d+\.\s*([^$]+)$', '(?i)([a-z_0-9 ]+)\s*\((?:temp|epis)\w*\s*(?:\d+\s*x\s*)?\d+\)'], 
         'findvideos': {'find_all': [{'tag': ['div'], 'class': ['embed-code-remove-styles-aztec']}]}, 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'controls': {'duplicates': [], 'min_temp': False, 'url_base64': False}, 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path="/pelicula", tv_path='/ver', canonical=canonical, finds=finds,  
                                   channel=canonical['channel'], list_language=list_language, list_servers=list_servers, 
                                   language=['LAT'], actualizar_titulos=True)


def mainlist(item):
    logger.info()
    
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(
        Item(
            channel = item.channel,
            title = "Series de los 80s",
            action = "list_all",
            url = host + 'media-category/80s/', 
            fanart = item.fanart,
            c_type='series', 
            thumbnail = get_thumb("year", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Series de los 90s",
            action = "list_all",
            url = host + 'media-category/90s/', 
            fanart = item.fanart,
            c_type='series', 
            thumbnail = get_thumb("year", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Series del 2000",
            action = "list_all",
            url = host + 'media-category/00s/', 
            fanart = item.fanart,
            c_type='series', 
            thumbnail = get_thumb("year", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Todas las series",
            action = "list_all",
            url = host + 'series/', 
            fanart = item.fanart,
            c_type='series', 
            thumbnail = get_thumb("all", auto=True)
        )
    )
    itemlist.append(
        Item(
            channel = item.channel,
            title = "Buscar...",
            action = "search",
            url = host,
            fanart = item.fanart,
            c_type='series', 
            thumbnail = get_thumb("search", auto=True)
        )
    )

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item, matches_post=list_all_matches, **kwargs)


def list_all_matches(item, matches_int):
    logger.info()

    matches = []

    for elem in matches_int:
        elem_json = {}
        
        elem_json['url'] = elem.a.get('href', '')
        elem_json['title'] = elem.h2.get_text(strip=True)
        elem_json['thumbnail'] = elem.img.get('src', '')
        elem_json['quality'] = '*'
        elem_json['language'] = '*'
        elem_json['year'] = elem_json.get('year', '-')

        if not elem_json['url']: continue

        matches.append(elem_json.copy())

    return matches


def seasons(item):
    logger.info()

    itemlist = []
    item.url = item.url.rstrip('/') + '/'

    soup = AlfaChannel.create_soup(item.url)

    url =  soup.find('a', class_='video-play-button-single-aztec', string=re.compile("antigua"))
    url = url['href'] if url else ''
    if url: 
        item.url = url.rstrip('/') + '/'
        soup = {}
        finds['seasons'] = {'find': [{'tag': ['li'], 'class': ['megalist']}], 'find_all': [['li']]}

    return AlfaChannel.seasons(item, data=soup, finds=finds, **kwargs)


def episodesxseason(item):
    logger.info()
    
    if '/search' in item.url:
        finds['episodes'] = {'find': [{'tag': ['div'], 'class': ['blog-posts hfeed clearfix']}], 
                             'find_all': [{'tag': ['div'], 'class': ['post hentry']}]}
    else:
        finds['episodes']['find'][0]['id'][0] = finds['episodes']['find'][0]['id'][0] % str(item.contentSeason)

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, finds=finds, **kwargs)


def episodesxseason_matches(item, matches_int):
    logger.info()

    matches = []

    for x, elem in enumerate(matches_int):
        elem_json = {}

        elem_json['url'] = elem.a.get('href', '')
        elem_json['title'] = elem.h2.get_text(strip=True)
        elem_json['thumbnail'] = elem.img.get('src', '')
        elem_json['quality'] = '*'
        elem_json['language'] = '*'
        elem_json['server'] = elem.get('server', '')
        elem_json['size'] = elem.get('size', '')

        if not elem_json.get('url', ''): 
            continue

        matches.append(elem_json.copy())

    return matches


def episodios(item):
    logger.info()

    itemlist = []
    
    templist = seasons(item)
    
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def findvideos(item):
    logger.info()
    
    finds['controls'].update({'headers': {'Referer': host}})

    item.url = item.url.rstrip('/') + '/' if not item.url.endswith('.html') else item.url
    if not '/episodio' in item.url:
        finds['findvideos'] = {'find_all': [{'tag': ['div'], 'class': ['post-body entry-content']}]}

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=False, findvideos_proc=True, finds=finds, **kwargs)


def findvideos_matches(item, matches_int, langs, response, videolibrary=False):
    logger.info()

    matches = []

    for elem in matches_int:
        logger.error(elem)

        elem_json = {}
        
        elem_json['server'] = ''
        elem_json['url'] = elem.iframe.get('src', '')

        if not elem_json['url']: continue

        matches.append(elem_json.copy())

    return matches, langs


def actualizar_titulos(item):
    logger.info()
    from lib.generictools import update_title
    
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    item = update_title(item)
    
    #Volvemos a la siguiente acción en el canal
    return item


def search(item, texto):
    logger.info()

    itemlist = []

    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + '?post_type=video_skrn&search_keyword=' + texto
        
        if texto != '':
            return list_all(item)
        else:
            return []

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
