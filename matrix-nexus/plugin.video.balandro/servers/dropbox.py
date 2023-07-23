# -*- coding: utf-8 -*-

import codecs

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    resp = httptools.downloadpage(page_url, only_headers=True).headers)

    if resp.code == 404:
        return 'El archivo no existe o ha sido borrado'

    video_urls.append(['mp4', page_url])

    return video_urls
