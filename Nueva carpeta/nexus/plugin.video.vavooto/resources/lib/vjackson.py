# -*- coding: utf-8 -*-

# edit 2023-04-04
import sys, xbmc, os, json, requests, urllib3, xbmcplugin, vavoosigner
from resources.lib import utils
from resources.lib.player import cPlayer
from xbmcgui import ListItem, Dialog

urllib3.disable_warnings()
session = requests.session()
from base64 import b64encode, b64decode 
BASEURL = "https://www2.vavoo.to/ccapi/"

try: import resolveurl as resolver
except:
	try: import urlresolver as resolver
	except: resolver = False

try: lines = json.loads(utils.addon.getSetting("favs"))
except: lines=[]

# TODO https://kodi.wiki/view/Default_Icons
def _index(params):
	utils.set_content("files")
	if len(lines)>0: addDir2("TV Favoriten (Live)", "pvr", "favchannels")
	addDir2("Live", "pvr", "channels")
	addDir2("Filme", "movies", "indexMovie")
	addDir2("Serien", "series", "indexSerie")
	utils.end()

def _indexMovie(params):
	utils.set_content("movies")
	addDir2("Beliebte Filme", "movies", "list", id="movie.popular")
	addDir2("Angesagte Filme", "movies", "list", id="movie.trending")
	addDir2("Genres", "DefaultGenre.png", "genres", id="movie.popular")
	addDir2("Suche", "search", "search", id="movie.popular", isFolder=False)
	utils.end()

def _indexSerie(params):
	utils.set_content("tvshows")
	addDir2("Beliebte Serien", "series", "list", id="series.popular")
	addDir2("Angesagte Serien", "series", "list", id="series.trending")
	addDir2("Genres", "DefaultGenre.png", "genres", id="series.popular")
	addDir2("Suche", "search", "search", id="series.popular", isFolder=False)
	utils.end()

def createListItem(params, e):
	infos = {}
	season=params.get("s")
	ep = e.get("current_episode")
	
	def setInfo(key, value):
		if value:
			infos[key] = value

	setInfo("originaltitle", e.get("originalName"))
	setInfo("year", e.get("year"))
	if e.get("description"): setInfo("plot", e.get("description"))
	else: setInfo("plot", " ")	# alt255
	setInfo("premiered", e.get("releaseDate"))
	if ep:
		setInfo("mediatype", "episode")
		setInfo("season", int(season))
		episode = ep["episode"]
		setInfo("title", "Staffel %s Episode %s" % (season, episode))
		setInfo("episode", int(episode))
		episode_title = ep.get("name")
		if episode_title and not episode_title.startswith("Episode "): setInfo("title", "S%sE%s  %s" % (season, episode, episode_title))
	elif season:
		setInfo("mediatype", "season")
		setInfo("season", int(season))
		setInfo("title", "Staffel %s" % (season))
	else:
		if params["id"].startswith("series"):
			setInfo("tvshowtitle", e.get("name"))
			setInfo("mediatype", "tvshow")
		else: setInfo("mediatype", "movie")
		setInfo("title", e.get("name"))
	setInfo("genre", e.get("genres"))
	setInfo("country", e.get("country"))
	setInfo("cast", e.get("cast"))
	setInfo("director", e.get("director"))
	setInfo("writer", e.get("writer"))
	o = ListItem(infos["title"])
	o.setInfo("Video", infos)
	o.setArt({"icon": e.get("poster", "DefaultVideo.png"), "thumb": e.get("poster", "DefaultVideo.png"), "poster": e.get("poster", "DefaultVideo.png"), "banner": e.get("backdrop", "DefaultVideo.png")})
	return o

def _list(params):
	data = cachedcall("list", params)
	content, isFolder = "tvshows", True
	params["action"] = "seasons"
	if params["id"].startswith("movie"):
		content, isFolder = "movies", False
		params["action"] = "get"
	utils.set_content(content)
	for e in data["data"]:
		params["id"] = e["id"]
		o = createListItem(params, e)
		if not isFolder:
			o.setProperty("IsPlayable", "true")
			o.addContextMenuItems([("Manuelle Stream Auswahl", "RunPlugin(%s?%s&manual=true)" % (sys.argv[0], utils.urlencode(params)))])
		utils.add(params, o, isFolder)
	if data["next"]: addDir(">>> Weiter", {"action": "list", "id": data["next"]})
	utils.end()
	
def _search(params):
	query = None
	if params.get("query"): query = params.get("query")
	else:
		heading="VAVOO.TO - SERIEN SUCHE" if params["id"].startswith("serie") else "VAVOO.TO - FILM SUCHE"
		kb = xbmc.Keyboard("", heading, False)
		kb.doModal()
		if (kb.isConfirmed()): query = kb.getText()
	if query:
		id = "%s.search=%s" % (params["id"], query.replace(".", "%2E"))
		url = "%s?action=list&id=%s" % (sys.argv[0], id)
		xbmc.executebuiltin("Container.Update(%s)" % url)
	return

def _genres(params):
	genrelist= ["Action & Adventure", "Animation", "Komödie", "Krimi", "Dokumentarfilm", "Drama", "Familie", "Kids", "Mystery", "News", "Reality", "Sci-Fi & Fantasy", "Soap", "Talk", "War & Politics", "Western"] if params["id"].startswith("serie") else ["Action", "Abenteuer", "Animation", "Komödie", "Krimi", "Dokumentarfilm", "Drama", "Familie", "Fantasy", "Historie", "Horror", "Musik", "Mystery", "Liebesfilm", "Science Fiction", "TV-Film", "Thriller", "Kriegsfilm", "Western"]
	for genre in genrelist:
		addDir2(genre, "DefaultGenre.png", "list", id="%s.genre=%s" % (params["id"], genre))
	utils.end()

def _seasons(params):
	utils.set_content("seasons")
	data = cachedcall("info", {"id": params["id"], "language": "de"})
	data["seasons"].pop("0", None)
	seasons = list(data["seasons"].keys())
	if len(seasons) == 1:
		params["s"] = "1"
		_episodes(params)
	params["action"] = "episodes"
	for season in seasons:
		params["s"] = season
		o = createListItem(params, data)
		utils.add(params, o, True)
	utils.end()

def _episodes(params):
	utils.set_content("episodes")
	data = cachedcall("info", {"id": params["id"], "language": "de"})
	for i in data["seasons"][params["s"]]:
		data["current_episode"] = i
		params["action"] = "get"
		params["e"] = str(i["episode"])
		o = createListItem(params, data)
		o.setProperty("IsPlayable", "true")
		o.addContextMenuItems([("Manuelle Stream Auswahl", "RunPlugin(%s?%s&manual=true)" % (sys.argv[0], utils.urlencode(params)))])
		utils.add(params, o)
	utils.end()

def showFailedNotification(msg="Keine Streams gefunden"):
	xbmc.executebuiltin("Notification(%s,%s,%s,%s)" % ("VAVOO.TO",msg,5000,utils.addonInfo("icon")))
	sys.exit()

def _get(params):
	manual = True if params.get("manual") == "true" else False
	if params.get("e"): mirrors = callApi2("links", {"id": "%s.%s.%s" % (params["id"], params["s"], params["e"]), "language": "de"})
	else: mirrors = callApi2("links", {"id": params["id"], "language": "de"})
	if not mirrors: return showFailedNotification()
	newurllist , url = [], None
	for i ,a in enumerate(mirrors, 1):
		a["hoster"] = utils.urlparse(a["url"]).netloc
		if "streamz" in a["hoster"]: continue # den hoster kann man vergessen
		if "language" in a:
			if "de" in a["language"] :
				if "1080p" in a["name"]:
					if int(utils.addon.getSetting("stream_quali")) > 0: continue
					a["name"] = "%s %s" %(a["hoster"], "1080p")
					a["weight"] = 1080+i
				elif "720p" in a["name"]:
					if int(utils.addon.getSetting("stream_quali")) > 1: continue
					a["name"] = "%s %s" %(a["hoster"], "720p")
					a["weight"] = 720+i
				elif "480p" in a["name"]:
					a["name"] = "%s %s" %(a["hoster"], "480p")
					a["weight"] = 480+i
				elif "360p" in a["name"]:
					a["name"] = "%s %s" %(a["hoster"], "360p")
					a["weight"] = 360+i
				else:
					a["name"] = a["hoster"]
					a["weight"] = i
				newurllist.append(a)
		else:
			a["name"] = a["hoster"]
			a["weight"] = i
			newurllist.append(a)
	mirrors = list(sorted(newurllist, key=lambda x: x["weight"], reverse=True))
	for i, a in enumerate(mirrors, 1): a["name"] = "%s. %s" % (i, a["name"])
	if utils.addon.getSetting("stream_select") == "0" or manual:
		captions = [ mirror["name"] for mirror in mirrors ]
		index = Dialog().select("VAVOO", captions)
		if index == -1: return
		if utils.addon.getSetting("auto_try_next_stream") !="true": mirrors = [mirrors[index]]
		else: mirrors = mirrors[index:]
	for mirror in mirrors:
		if resolver and resolver.relevant_resolvers(utils.urlparse(mirror["url"]).hostname):
			try: url = resolver.resolve(mirror["url"])
			except: continue
		elif "hd-stream" in mirror["url"]:
			try:
				id = mirror["url"].split("/")[-1]
				posturl = "https://hd-stream.to/api/source/%s" % id
				data = {"r": "https://kinoger.to/", "d": "hd-stream.to"}
				response = session.post(posturl, data)
				if response.status_code != 200: continue
				links = response.json()["data"]
				links = sorted(links, key=lambda x: int(x["label"].replace("p", "")), reverse=True)
				url = links[0]["file"]
			except: continue
		else:
			res = callApi2("open", {"link": mirror["url"]})
			url = res[-1].get("url")
		if url:
			try:
				newurl = url
				headers = {}; params = {}
				if "|" in newurl:
					newurl, headers = newurl.split("|")
					headers = dict(utils.parse_qsl(headers))
				if "?" in newurl:
					newurl, params = newurl.split("?")
					params = dict(utils.parse_qsl(params))
				res = session.get(newurl, headers=headers, params=params, stream=True)
				if not res.ok:
					utils.log("Kann Seite nicht erreichen")
					continue
				if "text" in res.headers.get("Content-Type","text"):
					utils.log("Keine Videodatei")
					continue
				else:
					return _play(url)
			except:
				import traceback
				utils.log(traceback.format_exc())
				continue
	return showFailedNotification()

def _play(url):
	utils.log("Spiele :%s" % url)
	o = ListItem(xbmc.getInfoLabel("ListItem.Title"))
	o.setPath(url)
	o.setProperty("IsPlayable", "true")
	if ".m3u8" in url:
		o.setMimeType("application/vnd.apple.mpegurl")
		if utils.PY2: o.setProperty("inputstreamaddon", "inputstream.adaptive")
		else: o.setProperty("inputstream", "inputstream.adaptive")
		o.setProperty("inputstream.adaptive.manifest_type", "hls")
	if int(sys.argv[1]) > 0: utils.set_resolved(o)
	else: xbmc.Player().play(url, o)
	return cPlayer().startPlayer()

def addDir(name, params, iconimage="DefaultFolder.png", isFolder=True):
	liz = ListItem(name)
	liz.setArt({"icon":iconimage, "thumb":iconimage})
	plot , cm = " ", []
	cm.append(("Einstellungen", "RunPlugin(%s?action=settings)" % sys.argv[0]))
	if name == "TV Favoriten (Live)":
		plot = "[COLOR gold]Liste der eigenen Live Favoriten[/COLOR]"
		cm.append(("Alle Favoriten entfernen", "RunPlugin(%s?action=delallTvFavorit)" % sys.argv[0]))
	liz.addContextMenuItems(cm)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot})
	utils.add(params, liz, isFolder)

def addDir2(name_, icon_, action, isFolder=True, **params):
	params["action"] = action
	iconimage = utils.getIcon(icon_) if utils.getIcon(icon_) else icon_
	addDir(name_, params, iconimage, isFolder)

def cachedcall(action, params):
	cacheKey = action + "?" + ("&").join([ str(key) + "=" + str(value) for key, value in sorted(list(params.items())) ])
	content = utils.get_cache(cacheKey)
	if content:
		utils.log("from cache")
		return content
	else:
		content = callApi2(action, params)
		utils.set_cache(cacheKey, content, timeout=1800)
		return content

def callApi(action, params, method="GET", headers=None, **kwargs):
	utils.log("Action:%s params: %s" % (action,json.dumps(params)))
	if not headers: headers = dict()
	headers["auth-token"] = vavoosigner.getAuthSignature()
	resp = session.request(method, (BASEURL + action), params=params, headers=headers, **kwargs)
	resp.raise_for_status()
	data = resp.json()
	utils.log("callApi res: %s" % json.dumps(data))
	return data

def callApi2(action, params):
	res = callApi(action, params, verify=False)
	while True:
		if type(res) is not dict or "id" not in res or "data" not in res:
			return res
		data = res["data"]
		if type(data) is dict and data.get("type") == "fetch":
			params = data["params"]
			body = params.get("body")
			headers = params.get("headers")
			try: resp = session.request(params.get("method", "GET").upper(), data["url"], headers={k:v[0] if type(v) in (list, tuple) else v for k, v in headers.items()} if headers else None, data=body.decode("base64") if body else None, allow_redirects=params.get("redirect", "follow") == "follow")
			except: return
			headers = dict(resp.headers)
			resData = {"status": resp.status_code, "url": resp.url, "headers": headers, "data": b64encode(resp.content).decode("utf-8").replace("\n", "") if data["body"] else None}
			utils.log(json.dumps(resData))
			utils.log(resp.text)
			res = callApi("res", {"id": res["id"]}, method="POST", json=resData, verify=False)
		elif type(data) is dict and data.get("error"):
			utils.log(data.get("error"))
			return
		else: return data
	# return