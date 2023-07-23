# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import traceback

from channelselector import get_thumb
from core import scrapertools
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from lib.AlfaChannelHelper import DictionaryAllChannel

# Canal común con Cinetorrent(muerto), Magnetpelis, Pelispanda, Yestorrent


IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'Version Original': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['torrent']

canonical = {
             'channel': 'magnetpelis', 
             'host': config.get_setting("current_host", 'magnetpelis', default=''), 
             'host_alt': ['https://magnetpelis.re/'], 
             'host_black_list': ['https://magnetpelis.org/', 'https://magnetpelis.com/'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
channel = canonical['channel']
categoria = channel.capitalize()
tv_path = "/series"
page = ''
weirdo_channels = ['yestorrent']
sufix = '-y002/' if channel in weirdo_channels else ''

timeout = config.get_setting('timeout_downloadpage', channel)
kwargs = {}

finds = {'find': {'find_all': [{'tag': ['div'], 'class': ['col-6 col-sm-4 col-lg-3 col-xl-2']}]}, 
         'categories': [], 
         'search': [], 
         'next_page': [], 
         'next_page_rgx': [['\/page\/\d+', '/page/%s/']], 
         'last_page': {'find': [{'tag': ['ul'], 'class': ['pagination']}, {'tag': ['a'], 'class': ['next page-numbers']}], 
                       'find_previous': [{'tag': ['a'], 'class': ['page-numbers']}], 'get_text': [{'@TEXT': '(\d+)'}]}, 
         'year': [], 
         'season_episode': [], 
         'seasons': {'find_all': [{'tag': ['div'], 'class': ['card-header']}]}, 
         'episode_url': '', 
         'episodes': {'find_all': [{'tag': ['div'], 'class': ['accordion__card']}]}, 
         'episode_num': [], 
         'episode_clean': [], 
         'findvideos': {'find_all': [{'tag': ['tr']}]}, 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie', ''],
                         ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'url_replace': [], 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, tv_path=tv_path, canonical=canonical, finds=finds, channel=channel, 
                                   list_language=list_language, list_servers=list_servers, language=['LAT'], 
                                   actualizar_titulos=True)


def mainlist(item):
    logger.info()

    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_genero = get_thumb("genres.png")
    thumb_anno = get_thumb("years.png")
    thumb_calidad = get_thumb("top_rated.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Películas", action="submenu", 
                url=host, thumbnail=thumb_pelis, c_type="peliculas"))
    itemlist.append(Item(channel=item.channel, title="    - por Género", action="section", 
                url=host, thumbnail=thumb_genero, extra='Genero', c_type="peliculas"))
    itemlist.append(Item(channel=item.channel, title="    - por Año", action="section", 
                url=host, thumbnail=thumb_anno, extra='AÑO', c_type="peliculas"))
    if channel not in ['magnetpelis']:
        itemlist.append(Item(channel=item.channel, title="    - por Calidad", action="section", 
                url=host, thumbnail=thumb_calidad, extra='CALIDAD', c_type="peliculas"))
    if channel in weirdo_channels:
        itemlist.append(Item(channel=item.channel, title="    - por Idiomas", action="section", 
                url=host, thumbnail=thumb_calidad, extra='Idioma', c_type="peliculas"))
    
    itemlist.append(Item(channel=item.channel, title="Series", action="submenu", 
                url=host, thumbnail=thumb_series, c_type="series"))
    itemlist.append(Item(channel=item.channel, title="    - por Año", action="section", 
                url=host, thumbnail=thumb_anno, extra='AÑO', c_type="series"))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                url=host, thumbnail=thumb_buscar, c_type="search"))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                folder=False, thumbnail=thumb_separador))
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                thumbnail=thumb_settings))
    
    autoplay.show_option(item.channel, itemlist)                                #Activamos Autoplay

    return itemlist
    
    
def configuracion(item):
    from platformcode import platformtools

    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()

    return


def submenu(item):
    logger.info()
    global sufix

    itemlist = []

    if item.c_type == 'peliculas':
        find = {'find': [{'tag': ['a'], 'class': ['header__nav-link'], 'string': re.compile('Pel.culas'), '@ARG': 'href'}]}
    else:
        find = {'find': [{'tag': ['a'], 'class': ['header__nav-link'], 'string': re.compile('Series'), '@ARG': 'href'}]}
        sufix = ''

    soup = AlfaChannel.create_soup(item.url, **kwargs)
    item.url = AlfaChannel.parse_finds_dict(soup, find).rstrip('/') + sufix + '/' + page

    return list_all(item)


def section(item):
    logger.info()
    
    finds['controls'] = {
                         'page': page,
                         'year': True if item.extra in ['AÑO'] else False,
                         'reverse': True if channel in weirdo_channels and item.extra in ['AÑO'] else False
                        }
    finds['categories'] = {'find': [{'tag': ['a'], 'class': ['dropdown-toggle header__nav-link'], 
                                     'string': re.compile('(?i)%s' % item.extra)}], 
                           'find_next': [{'tag': ['ul']}], 
                           'find_all': [{'tag': ['li']}]}

    return AlfaChannel.section(item, finds=finds, **kwargs)


def list_all(item):
    logger.info()
    
    finds['controls'] = {
                         'duplicates': []
                        }
                       
    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=finds, **kwargs)


def list_all_matches(item, matches_int):
    logger.info()
    
    matches = []

    for elem in matches_int:
        elem_json = {}
        promos = False
        
        elem_json['url'] = elem.a.get('href', '')
        if item.c_type == 'peliculas' and tv_path in elem_json['url']: continue
        if item.c_type in ['series', 'documentales'] and tv_path not in elem_json['url']: continue
        for promo in ['netflix', 'disney', 'diney', 'hbo', 'spotify']:
            if promo in elem_json['url']:
                promos = True
        if promos: 
            continue
        elem_json['title'] = elem.h3.get_text(strip=True)
        elem_json['title'] = scrapertools.remove_htmltags(elem_json['title']).strip().strip('.').strip()
        elem_json['thumbnail'] = elem.img.get('data-src', '')
        elem_json['quality'] = '*%s' % elem.ul.get_text(strip=True)
        if item.c_type in ['series', 'documentales'] and 'x' in elem_json['quality'].lower():
            if elem_json['quality'].lower() != 'x': elem_json['title_subs'] = [elem_json['quality'].lower().replace('*', '')]
            elem_json['quality'] = '*'
        if 'Dual' in elem_json['quality']:
            elem_json['language'] = ['DUAL']
            elem_json['quality'] = elem_json['quality'].replace(' Dual', '')
        if elem.find('ul', 'card__list right'):
            elem_json['language'] = '*%s' % elem.find('ul', 'card__list right').get_text(strip=True)\
                                            .lower().replace('cas', 'castellano').replace('lat', 'latino')
        elem_json['language'] = elem_json.get('language', '*')
        
        matches.append(elem_json.copy())
    
    return matches


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item, matches_post=None, generictools=True, **kwargs)


def episodesxseason(item):
    logger.info()
    
    finds['controls'] = {
                         'min_temp': False
                        }

    return AlfaChannel.episodes(item, matches_post=episodesxseason_matches, generictools=True, finds=finds, **kwargs)


def episodesxseason_matches(item, matches_int):
    logger.info()
    
    matches = []

    for elem_season in matches_int:
        season = int(scrapertools.find_single_match(elem_season.span.text, '\d+') or '1')
        if season != item.contentSeason: continue
        
        for elem in elem_season.find_all('tr'):
            elem_json = {}

            for x, td in enumerate(elem.find_all('td')):
                if x == 0: elem_json['episode'] = int(scrapertools.find_single_match(str(td.get_text()), '\d+') or '1')
                if x == 1: elem_json['quality'] = '*%s' % td.get_text()
                if x == 2: 
                    elem_json['language'] = '*%s' % td.get_text()
                    if 'Dual' in elem_json['quality']:
                        elem_json['language'] += ' DUAL'
                        elem_json['quality'] = elem_json['quality'].replace(' Dual', '')
                if x == 5: elem_json['url'] = td.a.get('href', '')
                elem_json['server'] = 'torrent'
                elem_json['size'] = ''
                elem_json['torrent_info'] = ''

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
    
    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         verify_links=play, generictools=True, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, videolibrary=False):
    logger.info(videolibrary)
    from core import servertools

    matches = []

    if videolibrary:
        for x, (episode_num, _scrapedserver, _scrapedquality, _scrapedlanguage, scrapedsize, scrapedurl) in enumerate(matches_int):
            elem_json = {}

            elem_json['episode'] = episode_num
            if _scrapedserver not in ['torrent', 'Torrent', 'array', 'Array']:
                elem_json['server'] = 'torrent'
                elem_json['quality'] = _scrapedserver
                elem_json['language'] = _scrapedquality
            else:
                elem_json['server'] = _scrapedserver
                elem_json['quality'] = _scrapedquality
                elem_json['language'] = _scrapedlanguage
            if not elem_json['quality'].startswith('*'): elem_json['quality'] = '*%s' % elem_json['quality']
            if not elem_json['language'].startswith('*'): elem_json['language'] = '*%s' % elem_json['language']
            elem_json['size'] = scrapedsize
            elem_json['url'] = scrapedurl
            elem_json['torrent_info'] = ''

            matches.append(elem_json.copy())
            item.emergency_urls[1][x] = elem_json.copy()

    else:
        for elem in matches_int:
            elem_json = {}
            x = 0
            
            for td in elem.find_all('td'):
                if item.contentType == 'movie':
                    if x == 0:
                        if len(elem.find_all('td')) < 7:
                            elem_json['server'] = 'torrent'
                            x += 1
                        else:
                            elem_json['server'] = 'torrent' if td.get_text().lower() in ['torrent', 'array'] else 'directo'
                    if x == 1: elem_json['quality'] = '*%s' % td.get_text()
                    if x == 2: 
                        elem_json['language'] = '*%s' % td.get_text()
                        if 'Dual' in elem_json['quality']:
                            elem_json['language'] += ' DUAL'
                            elem_json['quality'] = elem_json['quality'].replace(' Dual', '')
                    if x == 4: elem_json['torrent_info'] =  elem_json['size'] = td.get_text().replace('-', '')
                    if x == 6: elem_json['url'] = td.a.get('href', '')
                else:
                    if x == 0: elem_json['episode'] = int(scrapertools.find_single_match(str(td.get_text()), '\d+') or '1')
                    if x == 1: elem_json['quality'] = '*%s' % td.get_text()
                    if x == 2: 
                        elem_json['language'] = '*%s' % td.get_text()
                        if 'Dual' in elem_json['quality']:
                            elem_json['language'] += ' DUAL'
                            elem_json['quality'] = elem_json['quality'].replace(' Dual', '')
                    if x == 5: elem_json['url'] = td.a.get('href', '')
                    elem_json['server'] = 'torrent'
                    elem_json['size'] = ''
                    elem_json['torrent_info'] = ''
                x += 1

            if not elem_json.get('url', ''): 
                continue

            matches.append(elem_json.copy())
    
    return matches, langs


def play(item):

    kwargs = {'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 0, 'timeout': 5, 'CF': True, 'canonical': {}}

    if 'cinestart' in item.url:
        url, post = item.url.split('?')
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Referer': item.url}
        response = AlfaChannel.create_soup(url.replace('player.php', 'r.php'), post=post, headers=headers, 
                                           follow_redirects=False, soup=False, hide_infobox=True, **kwargs)

        if response.code in AlfaChannel.REDIRECTION_CODES:
            item.url = '%s|Referer=%s' % (response.headers.get('location', ''), AlfaChannel.obtain_domain(item.url, scheme=True))

    return [item]


def actualizar_titulos(item):
    logger.info()
    from lib.generictools import update_title
    
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    item = update_title(item)
    
    #Volvemos a la siguiente acción en el canal
    return item


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    
    try:
        item.url = host + 'buscar/%s?buscar=%s' % (page, texto)
        item.extra = 'search'

        if texto:
            return list_all(item)
        else:
            return []
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc(1))
        return []
 
 
def newest(categoria):
    logger.info()

    itemlist = []
    item = Item()

    item.title = "newest"
    item.category_new = "newest"
    item.channel = channel
    
    try:
        if categoria in ['peliculas', 'latino', 'torrent']:
            item.url = host + "peliculas/" + page
            if channel in weirdo_channels:
                item.url = host + "Descargar-peliculas-completas%s/%s" % (sufix, page)
            item.extra = "peliculas"
            item.extra2 = "novedades"
            item.action = "list_all"
            itemlist.extend(list_all(item))
                
        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()
        
        if categoria in ['series', 'latino', 'torrent']:
            item.category_new= 'newest'
            item.url = host + "series/" + page
            item.extra = "series"
            item.extra2 = "novedades"
            item.action = "list_all"
            itemlist.extend(list_all(item))

        if len(itemlist) > 0 and ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc(1))
        return []

    return itemlist
