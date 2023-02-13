# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import traceback

from channelselector import get_thumb
from core import scrapertools
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from lib.AlfaChannelHelper import DictionaryAllChannel


IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'Version Original': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['torrent']

canonical = {
             'channel': 'torrentpelis', 
             'host': config.get_setting("current_host", 'torrentpelis', default=''), 
             'host_alt': ['https://torrentpelis.org/'], 
             'host_black_list': ['https://www2.torrentpelis.com/', 'https://www1.torrentpelis.com/', 'https://torrentpelis.com/'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant_if_proxy': True, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
channel = canonical['channel']
categoria = channel.capitalize()

IDIOMAS_TMDB = {0: 'es', 1: 'en', 2: 'es,en'}
timeout = config.get_setting('timeout_downloadpage', channel) * 2

finds = {'find': {'find': [{'tag': ['div'], 'id': ['archive-content', 'items normal']}], 
                  'find_all': [{'tag': ['article'], 'class': ['item']}]}, 
         'categories': {'find': [{'tag': ['ul'], 'class': ['sub-menu']}], 
                        'find_all': [{'tag': ['li']}]}, 
         'search': {'find_all': [{'tag': ['div'], 'class': ['result-item']}]}, 
         'next_page': [], 
         'next_page_rgx': [['\/page\/\d+', '/page/%s']], 
         'last_page': {'find': [{'tag': ['div'], 'class': ['pagination']}, {'tag': ['span']}], 
                       'get_text': [{'@TEXT': '..gina \d+ de (\d+)'}]}, 
         'season_episode': [], 
         'season': [], 
         'episode_url': '', 
         'episodes': [], 
         'episode_num': [], 
         'episode_clean': [], 
         'findvideos': {'find': [{'tag': ['tbody']}], 'find_all': [{'tag': ['tr']}]}, 
         'title_clean': [['(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie', ''], ['[\(|\[]\s*[\)|\]]', '']],
         'quality_clean': [['(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', '']],
         'language_clean': [], 
         'timeout': timeout}
AlfaChannel = DictionaryAllChannel(host, movie_path="/peliculas", canonical=canonical, finds=finds, 
                                   channel=channel, list_language=list_language, list_servers=list_servers)


def mainlist(item):
    logger.info()

    itemlist = []

    thumb_pelis = get_thumb("channels_movie.png")
    thumb_genero = get_thumb("genres.png")
    thumb_calidad = get_thumb("top_rated.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all", c_type='peliculas', 
                url=host + 'peliculas/page/1/', thumbnail=thumb_pelis, extra2="PELICULA"))
    itemlist.append(Item(channel=item.channel, title="    - por Género", action="genero", c_type='peliculas', 
                url=host, thumbnail=thumb_genero, extra2="GENERO"))
    itemlist.append(Item(channel=item.channel, title="    - por Tendencias", action="list_all", c_type='peliculas', 
                url=host + 'tendencias/page/1/', thumbnail=thumb_calidad, extra2="TENDENCIAS"))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                url=host, thumbnail=thumb_buscar, extra="search"))

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


def genero(item):
    logger.info()

    return AlfaChannel.section(item)


def list_all(item):
    logger.info()

    if item.extra2 in ["GENERO", "TENDENCIAS"]: 
        finds['find'] = {
                         'find': [{'tag': ['div'], 'class': ['items normal']}], 
                         'find_all': [{'tag': ['article'], 'class': ['item']}]
                        }
    elif item.extra == "search":
        finds['find'] = finds.get('search', {})
                       
    return AlfaChannel.list_all(item, matches_post=list_all_matches, generictools=True, finds=finds)
                        

def list_all_matches(item, matches_int):
    logger.info()
    
    matches = []

    for elem in matches_int:
        elem_json = {}
        
        elem_json['url'] = elem.a.get('href', '')
        elem_json['title'] = elem.img.get('alt', '')
        elem_json['thumbnail'] = elem.img.get('src', '')
        if item.extra == "search":
            elem_json['year'] = elem.find('span', class_="year").text
        else:
            elem_json['year'] = elem.find('div', class_='data').find('span').text
        elem_json['year'] = scrapertools.find_single_match(elem_json['year'], '\d{4}')
        
        matches.append(elem_json.copy())
    
    return matches


def findvideos(item):
    logger.info()

    kwargs = {'follow_redirects': False}

    return AlfaChannel.get_video_options(item, item.url, data='', matches_post=findvideos_matches, 
                                         generictools=True, findvideos_proc=True, **kwargs)


def findvideos_matches(item, matches_int, langs, response, armagedon=False):
    logger.info()
    
    matches = []
    
    for elem in matches_int:
        elem_json = {}
        elem_json['server'] = 'torrent'

        for x, td in enumerate(elem.find_all('td')):
            if x == 0: elem_json['url'] = td.a['href']
            if x == 1: elem_json['quality'] = '*%s' % td.get_text()
            if x == 2: elem_json['language'] = '*latino'
            if x == 3: elem_json['torrent_info'] = td.get_text()
        
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
    
    texto = texto.replace(" ", "+")
    
    try:
        item.url = host + '?s=' + texto
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
            item.url = host + "peliculas/"
            item.extra = "peliculas"
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
