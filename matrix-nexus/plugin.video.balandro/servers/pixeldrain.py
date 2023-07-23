# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data

    vid = scrapertools.find_single_match(page_url, "/u/([^$]+)")

    if vid:
        url = "https://pixeldrain.com/api/file/%s?download" % vid

        video_urls.append(['mp4', url])

    return video_urls
