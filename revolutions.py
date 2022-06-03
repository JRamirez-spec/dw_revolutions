import os
import requests
import urllib.request
import re

def log(m):
  print(m)
  with open('log.txt', 'a') as l:
    l.write('{}\n'.format(m))

def fail(e):
  log(e)
  with open('fail.txt', 'a') as er:
    er.write('{}\n'.format(e))

def download_episode_list():
  log("Downloading index html...")
  ifp = urllib.request.urlopen("http://www.sal.wisc.edu/~jwp/revolutions-episode-index.html")
  ibytes = ifp.read()
  index_html = ibytes.decode("utf8")
  ifp.close()

  reLinks = ["https?://www.revolutionspodcast.com\/.+",
             "https?://thehistoryofrome.typepad.com\/.+"]

  def create_regex():
    return "href=\"(" + "|".join(reLinks) + ")\" "

  log("Downloading episode url list...")
  episode_url_list = re.findall(create_regex(), index_html)
  episode_url_list = list(set(episode_url_list))
  episode_url_list.sort()
  return episode_url_list

def is_done(url):
  if os.path.exists('done.txt'):
    with open('done.txt', 'r') as d:
      for line in d:
        if re.search(url, line):
          return True
  return False

def encode_non_ascii_text(unsafe):
  url = urllib.parse.urlsplit(unsafe)
  url = list(url)
  url[2] = urllib.parse.quote(url[2])
  url = urllib.parse.urlunsplit(url)
  return url

def download_episode_html(url):
  efp = urllib.request.urlopen(url)
  ebytes = efp.read()
  ehtml = ebytes.decode("utf8")
  efp.close()
  return ehtml

def find_mp3_link(episode_html):
  reMp3s = [".+\.mp3"]
  dlink = re.findall("href=\"(" + "|".join(reMp3s) + ")", episode_html)
  if not dlink:
    return ""
  return dlink[0]
  
def get_name_from_mp3_link(link):
  reNames = [".+\.mp3"]
  caps = re.findall("revolutionspodcast\/(" + "|".join(reNames) + ")", link)
  if not caps:
    return ""
  return caps[0]

def download_mp3(download_link, filename):
  with requests.Session() as sess:
    mp3 = sess.get(download_link)
    with open(filename, 'wb') as file:
      file.write(mp3.content)

def mark_as_done(url):
  with open('done.txt', 'a') as d:
    d.write('{}\n'.format(url))

def main():
  if os.path.exists('fail.txt'):
    os.remove('fail.txt')
  if os.path.exists('log.txt'):
    os.remove('log.txt')
  os.system('clear')

  episode_url_list = download_episode_list()

  log('{} episodes found.'.format(len(episode_url_list)))

  for e in episode_url_list:
    if is_done(e):
      log('\nAlready processed -> {}'.format(e))
      continue

    log('\nProcessing URL -> {}'.format(e))

    log('Encoding URL...')
    url = encode_non_ascii_text(e)
    log('Encoded URL -> {}'.format(url))

    log('Downloading episode from URL...')
    episode_html = download_episode_html(url)
    log('HTML downloaded.')

    log('Searching for MP3 link...')
    download_link = find_mp3_link(episode_html)
    if not download_link:
      fail('{} -> Could not find MP3 link.'.format(e))
      continue
    log('Found MP3 link -> {}'.format(download_link))

    log('Getting name from download link...')
    filename = get_name_from_mp3_link(download_link)
    if not filename:
      fail('{} -> Could not parse name from link.'.format(e))
      continue
    log('Found name -> {}'.format(filename))

    try:
      download_mp3(download_link, filename)
    except Exception as ex:
      fail('{} -> Failed to download file because: {}'.format(e, ex))
      continue

    mark_as_done(e)

  log('All done, buddy.')

main()
