#!/usr/bin/python

# requires PyRSS2Gen: http://www.dalkescientific.com/Python/PyRSS2Gen.html

import datetime
import os
import PyRSS2Gen
import stat
import time

SAMPLES_DIR = "/media/sdb1/melanson/samples-mirror"
DAYS_IN_HISTORY = 14
SECONDS_PER_DAY = 60 * 60 * 24
MPHQ_BASE_LINK = "http://samples.mplayerhq.hu/"
LIBAV_BASE_LINK = "http://samples.libav.org/"
OUTPUT_RSS_FILE = "samples-rss.xml"

# timestamp gymnastics -- first, get the current time, then use that to
# get last night's midnight timestamp
today = time.localtime()
last_midnight = time.mktime(time.struct_time([
  today.tm_year,
  today.tm_mon,
  today.tm_mday,
  0,
  0,
  0,
  today.tm_wday,
  today.tm_yday,
  today.tm_isdst
]))

# create a list of timestamp cutoffs; last night's midnight is first
# also create a list of empty lists for holding recent filenames
midnights = []
file_lists = []
for i in xrange(DAYS_IN_HISTORY):
  midnights.append(last_midnight - i * SECONDS_PER_DAY)
  file_lists.append([])

# iterate through the directory structure and find the recent files
for dirpath, dirnames, filenames in os.walk(SAMPLES_DIR):
  for f in filenames:
    path = "%s/%s" % (dirpath, f)
    # take the lazy method for dealing with, e.g., bad symlinks
    try:
      file_time = os.stat(path)[stat.ST_MTIME]
    except OSError:
      pass
    # if the file was created within the history period, search further
    if file_time > midnights[DAYS_IN_HISTORY - 1]:
      # search from the latest date in the history to the earliest;
      # a binary search would technically be faster but for 14 categories,
      # it doesn't matter
      for i in xrange(DAYS_IN_HISTORY):
        if file_time > midnights[i]:
          break
      file_lists[i].append(path)

# iterate through the file lists, sort, and generate RSS items (1 item per day)
items = []
for i in xrange(DAYS_IN_HISTORY):
  if file_lists[i]:
    title = "Samples added on %s" % (time.strftime("%Y %B %d", time.localtime(midnights[i])))
    description = "These samples were added or updated:\n<ul>\n"
    file_lists[i].sort()
    for f in file_lists[i]:
      size = os.path.getsize(f)
      if size < 1024:
        size = "%d bytes" % (size)
      elif size < (1024 * 1024):
        size = "%d KiB" % (size / 1024)
      else:
        size = "%d MiB" % (size / (1024 * 1024))
      # chop path down to relative path after obtaining filesize
      f = f[len(SAMPLES_DIR)+1:]
      description += """
        <li>%s, %s [<a href="%s%s">s.mphq</a>], [<a href="%s%s">s.libav</a>]</li>
      """ % (f, size, MPHQ_BASE_LINK, f, LIBAV_BASE_LINK, f)
    description += "</ul>\n"
    ts = time.localtime(midnights[i])
    pubDate = datetime.datetime(ts.tm_year, ts.tm_mon, ts.tm_mday, 0, 0, 0)
    items.append(PyRSS2Gen.RSSItem(
      title = title, 
      description = description,
      pubDate = pubDate))

# generate the main RSS object
rss = PyRSS2Gen.RSS2(
  title = "Multimedia Samples Archive",
  link = "http://samples.mplayerhq.hu/",
  description = "The latest multimedia samples to be added to the world-famous MPlayer samples archive",
  lastBuildDate = datetime.datetime.utcnow(),
  items = items)

# dump the RSS feed
rss.write_xml(open(OUTPUT_RSS_FILE, "w"))

