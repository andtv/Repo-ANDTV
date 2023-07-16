# -*- coding: utf-8 -*-
import xbmcgui, xbmcaddon, sys, xbmc, os, time, json, xbmcplugin
PY2 = sys.version_info[0] == 2
if PY2:
	from urlparse import urlparse, parse_qsl
	from urllib import urlencode, quote_plus
	translatePath = xbmc.translatePath
else:
	from urllib.parse import urlencode, urlparse, parse_qsl, quote_plus
	import xbmcvfs
	translatePath = xbmcvfs.translatePath
	unicode = str

def py2dec(msg):
	if PY2:
		return msg.decode("utf-8")
	return msg
	
def py2enc(msg):
	if PY2:
		return msg.encode("utf-8")
	return msg

addon = xbmcaddon.Addon()
addonInfo = addon.getAddonInfo
addonID = addonInfo('id')
addonprofile = py2dec(translatePath(addonInfo('profile')))
addonpath = py2dec(translatePath(addonInfo('path')))
cachepath = os.path.join(addonprofile, "cache")
if not os.path.exists(cachepath):
	os.makedirs(cachepath)

def selectDialog(list, heading=None, multiselect = False):
	if heading == 'default' or heading is None: heading = addonInfo('name')
	if multiselect:
		return xbmcgui.Dialog().multiselect(str(heading), list)
	return xbmcgui.Dialog().select(str(heading), list)

home = xbmcgui.Window(10000)

def set_cache(key, value, timeout=300):
	data={"sigValidUntil": int(time.time()) +timeout,"value": value}
	home.setProperty(key, json.dumps(data))
	file = os.path.join(cachepath, key)
	with open(file+".json", "w") as k:
		json.dump(data, k, indent=4)
	
def get_cache(key):
	keyfile = home.getProperty(key)
	if keyfile:
		r = json.loads(keyfile)
		if r.get('sigValidUntil', 0) > int(time.time()):
			return r.get('value')
		home.clearProperty(key)
	try:
		file = os.path.join(cachepath, key)
		with open(file+".json") as k:
			r = json.load(k)
		sigValidUntil = r.get('sigValidUntil', 0) 
		if sigValidUntil > int(time.time()):
			value = r.get('value')
			data={"sigValidUntil": sigValidUntil,"value": value}
			home.setProperty(key, json.dumps(data))
			return value
		os.remove(file)
	except:
		return

def log(*args):
	msg=""
	for arg in args:
		msg += repr(arg)
	xbmc.log(msg, xbmc.LOGINFO)

def yesno(heading, line1, line2='', line3='', nolabel='', yeslabel=''):
	if PY2: return xbmcgui.Dialog().yesno(heading, line1,line2,line3, nolabel, yeslabel)
	else: return xbmcgui.Dialog().yesno(heading, line1+"\n"+line2+"\n"+line3, nolabel, yeslabel)
	
def ok(heading, line1, line2='', line3=''):
	if PY2: return xbmcgui.Dialog().ok(heading, line1,line2,line3)
	else: return xbmcgui.Dialog().ok(heading, line1+"\n"+line2+"\n"+line3)

def getIcon(name):
	if os.path.exists("%s/resources/art/%s.png" % (addonpath ,name)):return "%s/resources/art/%s.png" % (addonpath ,name)
	else: return  name

def end(succeeded=True, cacheToDisc=True):
	return xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=succeeded, cacheToDisc=cacheToDisc)
	
def add(params, o, isFolder=False):
	return xbmcplugin.addDirectoryItem(int(sys.argv[1]), url_for(params), o, isFolder)

def set_category(cat):
	xbmcplugin.setPluginCategory(int(sys.argv[1]), cat)


def set_content(cont):
	xbmcplugin.setContent(int(sys.argv[1]), cont)
	
def set_resolved(item):
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def sort_method():
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

def convertPluginParams(params):
	p = []
	for key, value in list(params.items()):
		if isinstance(value, unicode):
			value = py2enc(value)
		p.append(urlencode({key: value}))
	return ('&').join(sorted(p))

def url_for(params):
	return "%s?%s" % (sys.argv[0], convertPluginParams(params))
	