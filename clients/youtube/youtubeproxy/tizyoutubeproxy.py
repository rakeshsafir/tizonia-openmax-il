# Copyright (C) 2017 Aratelia Limited - Juan A. Rubio
#
# This file is part of Tizonia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""@package tizyoutubeproxy
Simple YouTube proxy/wrapper.

Access YouTube to retrieve audio stream URLs and create a playback queue.

"""

from __future__ import print_function, unicode_literals

import sys
import os
import logging
import random
import unicodedata
import re
import pafy

# For use during debugging
# import pprint
# from traceback import print_exception

logging.captureWarnings(True)
logging.getLogger().addHandler(logging.NullHandler())
logging.getLogger().setLevel(logging.DEBUG)

ISO8601_TIMEDUR_EX = re.compile(r'PT((\d{1,3})H)?((\d{1,3})M)?((\d{1,2})S)?')

API_KEY = 'AIzaSyAv9KX5r5WfzfAKlf4mhQMHKmHr-Uw-WOc'

NOT_UTF8_ENVIRONMENT = "UTF-8" not in os.environ.get("LANG", "")

class _Colors:
    """A trivial class that defines various ANSI color codes.

    """
    BOLD = '\033[1m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

# This code is here for debugging purposes
def utf8_replace(txt):
    """ Replace unsupported characters in unicode string, returns unicode. """
    sse = sys.stdout.encoding
    txt = txt.encode(sse, "replace").decode("utf8", "ignore")
    return txt

# This code is here for debugging purposes
def xenc(stuff):
    """ Replace unsupported characters. """
    if sys.stdout.isatty():
        return utf8_replace(stuff) if NOT_UTF8_ENVIRONMENT else stuff

    else:
        return stuff.encode("utf8", errors="replace")

# This code is here for debugging purposes
def xprint(stuff, end=None):
    """ Compatible print. """
    print(xenc(stuff), end=end)

# This code is here for debugging purposes
def dump_stream_info(streams):
    """ Dump stream info. """

    fstring = "{0:<7}{1:<8}{2:<7}{3:<15}{4:<10}       "
    out = []
    length = len(streams)
    text = " [Fetching stream info]      >"

    for num, stream in enumerate(streams):
        sys.stdout.write(text + "-" * num + ">" + " " * (length - num - 1) + "<\r")
        sys.stdout.flush()
        megs = "%3.f" % (stream.get_filesize() / 1024 ** 2) + " MB"
        qual = "[%s]" % stream.quality
        out.append(fstring.format(num + 1, stream.mediatype, stream.extension, qual, megs))

    sys.stdout.write("\r")
    xprint(fstring.format("Stream", "Type", "Format", "Quality", " Size"))
    xprint(fstring.format("------", "----", "------", "-------", " ----"))

    for line in out:
        xprint(line)

def pretty_print(color, msg=""):
    """Print message with color.

    """
    print(color + msg + _Colors.ENDC)

def print_msg(msg=""):
    """Print a normal message.

    """
    pretty_print(_Colors.OKGREEN + msg + _Colors.ENDC)

def print_nfo(msg=""):
    """Print an info message.

    """
    pretty_print(_Colors.OKBLUE + msg + _Colors.ENDC)

def print_wrn(msg=""):
    """Print a warning message.

    """
    pretty_print(_Colors.WARNING + msg + _Colors.ENDC)

def print_err(msg=""):
    """Print an error message.

    """
    pretty_print(_Colors.FAIL + msg + _Colors.ENDC)

def exception_handler(exception_type, exception, traceback):
    """A simple exception handler that prints the excetion message.

    """

    print_err("[YouTube] (%s) : %s" % (exception_type.__name__, exception))
    del traceback # unused
    # print_exception(exception_type, exception, traceback)

sys.excepthook = exception_handler

class TizEnumeration(set):
    """A simple enumeration class.

    """
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

def to_ascii(msg):
    """Unicode to ascii helper.

    """

    return unicodedata.normalize('NFKD', unicode(msg)).encode('ASCII', 'ignore')

def get_track_id_from_json(item):
    """ Try to extract a video Id from a pafy query response """
    fields = ['contentDetails/videoId',
              'snippet/resourceId/videoId',
              'id/videoId',
              'id']
    for field in fields:
        node = item
        for part in field.split('/'):
            if node and isinstance(node, dict):
                node = node.get(part)
        if node:
            return node
    return ''

def get_tracks_from_json(jsons):
    """ Get search results from pafy's call_gdata response """

    items = jsons.get("items")
    if not items:
        logging.info("got unexpected data or no search results")
        return ()

    # fetch detailed information about items from videos API
    query_string = {'part':'contentDetails,statistics,snippet',
                    'id': ','.join([get_track_id_from_json(i) for i in items])}

    wdata = pafy.call_gdata('videos', query_string)

    items_vidinfo = wdata.get('items', [])
    # enhance search results by adding information from videos API response
    for searchresult, vidinfoitem in zip(items, items_vidinfo):
        searchresult.update(vidinfoitem)

    # populate list of video objects
    songs = []
    for item in items:

        try:

            ytid = get_track_id_from_json(item)
            snippet = item.get('snippet', {})
            title = snippet.get('title', '').strip()
            info = VideoInfo(ytid=ytid, title=title)

        except Exception as exception:

            logging.info('Error during metadata extraction/instantiation of ' +
                         'search result {}\n{}'.format(ytid, exception))

        songs.append(info)

    # return video objects
    return songs

def generate_search_query(term):
    """ Return the query string for pafy's call_gdata. """

    query_string = {
        'q': term,
        'maxResults': 50,
        'safeSearch': "none",
        'order': 'relevance',
        'part': 'id,snippet',
        'type': 'video',
        'videoDuration': 'any',
        'key': API_KEY,
        'videoCategoryId' : 10 # search music
    }

    return query_string

class VideoInfo(object):
    """ Class to represent a YouTube video.

    """

    def __init__(self, ytid, title):
        """ class members. """
        self.ytid = ytid
        self.title = title

class tizyoutubeproxy(object):
    """A class that accesses YouTube, retrieves stream URLs and creates and manages
    a playback queue.

    """

    def __init__(self):
        self.queue = list()
        self.queue_index = -1
        self.play_queue_order = list()
        self.play_modes = TizEnumeration(["NORMAL", "SHUFFLE"])
        self.current_play_mode = self.play_modes.NORMAL
        self.now_playing_stream = None

    def set_play_mode(self, mode):
        """ Set the playback mode.

        :param mode: current valid values are "NORMAL" and "SHUFFLE"

        """
        self.current_play_mode = getattr(self.play_modes, mode)
        self.__update_play_queue_order()

    def enqueue_audio_stream(self, arg):
        """Add the audio stream of a YouTube video to the
        playback queue.

        :param arg: a search string

        """
        logging.info('enqueue_audio_stream : %s', arg)
        try:

            yt_video = pafy.new(arg)
            yt_audio = yt_video.getbestaudio(preftype="webm")
            if not yt_audio:
                raise ValueError(str("No WebM audio stream for : %s" % arg))

            yt_info = VideoInfo(ytid=arg, title=yt_audio.title)
            self.add_to_playback_queue(audio=yt_audio, video=yt_video, info=yt_info)

            self.__update_play_queue_order()

        except ValueError:
            raise ValueError(str("Video not found : %s" % arg))

    def enqueue_audio_playlist(self, arg):
        """Add all audio streams in a YouTube playlist to the playback queue.

        :param arg: a YouTube playlist id

        """
        logging.info('enqueue_audio_playlist : %s', arg)
        try:
            count = len(self.queue)

            playlist = pafy.get_playlist2(arg)
            yt_video = None
            if len(playlist) > 0:
                if yt_video:
                    video_id = yt_video.videoid
                    video_title = yt_video.title
                    yt_info = VideoInfo(ytid=video_id, title=video_title)
                    self.add_to_playback_queue(video=yt_video, info=yt_info)

            if count == len(self.queue):
                raise ValueError

            self.__update_play_queue_order()

        except ValueError:
            raise ValueError(str("Playlist not found : %s" % arg))

    def enqueue_audio_search(self, arg):
        """Search YouTube and add the audio streams to the
        playback queue.

        :param arg: a search string

        """
        logging.info('enqueue_audio_search : %s', arg)
        try:
            query = generate_search_query(arg)
            wdata = pafy.call_gdata('search', query)

            wdata2 = wdata
            count = 0
            while True:
                for track_info in get_tracks_from_json(wdata2):
                    self.add_to_playback_queue(info=track_info)
                    count += 1

                if count > 100:
                    break
                if not wdata2.get('nextPageToken'):
                    break
                query['pageToken'] = wdata2['nextPageToken']
                wdata2 = pafy.call_gdata('search', query)

            self.__update_play_queue_order()

        except ValueError:
            raise ValueError(str("No videos found : %s" % arg))

    def enqueue_audio_mix(self, arg):
        """Obtain a YouTube mix associated to a given video id or url and add all audio
        streams in the mix playlist to the playback queue.

        :param arg: a YouTube video id

        """
        logging.info('enqueue_audio_mix : %s', arg)
        try:
            count = len(self.queue)

            yt_video = pafy.new(arg)
            playlist = yt_video.mix
            if len(playlist) > 0:
                for yt_video in playlist:
                    video_id = yt_video.videoid
                    video_title = yt_video.title
                    yt_info = VideoInfo(ytid=video_id, title=video_title)
                    self.add_to_playback_queue(video=yt_video, info=yt_info)

            if count == len(self.queue):
                raise ValueError

            self.__update_play_queue_order()

        except ValueError:
            raise ValueError(str("No videos found : %s" % arg))

    def current_audio_stream_title(self):
        """ Retrieve the current stream's title.

        """
        stream = self.now_playing_stream
        title = ''
        if stream:
            title = to_ascii(stream['a'].title).encode("utf-8")
        logging.info("current_audio_stream_title : %s", title)
        return title

    def current_audio_stream_author(self):
        """ Retrieve the current stream's author.

        """
        logging.info("current_audio_stream_author")
        stream = self.now_playing_stream
        author = ''
        if stream:
            author = to_ascii(stream['v'].author).encode("utf-8")
        return author

    def current_audio_stream_file_size(self):
        """ Retrieve the current stream's file size.

        """
        logging.info("current_audio_stream_file_size")
        stream = self.now_playing_stream
        size = 0
        if stream:
            size = stream['a'].get_filesize()
        return size

    def current_audio_stream_duration(self):
        """ Retrieve the current stream's duration.

        """
        logging.info("current_audio_stream_duration")
        stream = self.now_playing_stream
        duration = ''
        if stream:
            duration = to_ascii(stream['v'].duration).encode("utf-8")
        return duration

    def current_audio_stream_bitrate(self):
        """ Retrieve the current stream's bitrate.

        """
        logging.info("current_audio_stream_bitrate")
        stream = self.now_playing_stream
        bitrate = ''
        if stream:
            bitrate = stream['a'].bitrate
        return bitrate

    def current_audio_stream_view_count(self):
        """ Retrieve the current stream's view count.

        """
        logging.info("current_audio_stream_view_count")
        stream = self.now_playing_stream
        viewcount = 0
        if stream:
            viewcount = stream['v'].viewcount
        return viewcount

    def current_audio_stream_description(self):
        """ Retrieve the current stream's description.

        """
        logging.info("current_audio_stream_description")
        stream = self.now_playing_stream
        description = ''
        if stream:
            description = to_ascii(stream['v'].description).encode("utf-8")
        return description

    def current_audio_stream_file_extension(self):
        """ Retrieve the current stream's file extension.

        """
        logging.info("current_audio_stream_file_extension")
        stream = self.now_playing_stream
        file_extension = ''
        if stream:
            file_extension = to_ascii(stream['a'].extension).encode("utf-8")
        return file_extension

    def current_audio_stream_video_id(self):
        """ Retrieve the current stream's video id.

        """
        logging.info("current_audio_stream_video_id")
        stream = self.now_playing_stream
        video_id = ''
        if stream:
            video_id = to_ascii(stream['i'].ytid).encode("utf-8")
        return video_id

    def current_audio_stream_published(self):
        """ Retrieve the current stream's upload date and time.

        """
        logging.info("current_audio_stream_published")
        stream = self.now_playing_stream
        if stream:
            published = to_ascii(stream['v'].published).encode("utf-8")
        return published

    def clear_queue(self):
        """ Clears the playback queue.

        """
        self.queue = list()
        self.queue_index = -1

    def remove_current_url(self):
        """Remove the currently active url from the playback queue.

        """
        logging.info("remove_current_url")
        if len(self.queue) and self.queue_index:
            stream = self.queue[self.queue_index]
            print_nfo("[YouTube] [Stream] '{0}' removed." \
                      .format(to_ascii(stream['i'].title).encode("utf-8")))
            del self.queue[self.queue_index]
            self.queue_index -= 1
            if self.queue_index < 0:
                self.queue_index = 0
            self.__update_play_queue_order()

    def next_url(self):
        """ Retrieve the url of the next stream in the playback queue.

        """
        logging.info("next_url")
        try:
            if len(self.queue):
                self.queue_index += 1
                if (self.queue_index < len(self.queue)) \
                   and (self.queue_index >= 0):
                    next_stream = self.queue[self.play_queue_order \
                                            [self.queue_index]]
                    return self.__retrieve_stream_url(next_stream).rstrip()
                else:
                    self.queue_index = -1
                    return self.next_url()
            else:
                return ''
        except (KeyError, AttributeError):
            del self.queue[self.queue_index]
            logging.info(" exception - removing from queue")
            return self.next_url()

    def prev_url(self):
        """ Retrieve the url of the previous stream in the playback queue.

        """
        logging.info("prev_url")
        try:
            if len(self.queue):
                self.queue_index -= 1
                if (self.queue_index < len(self.queue)) \
                   and (self.queue_index >= 0):
                    prev_stream = self.queue[self.play_queue_order \
                                            [self.queue_index]]
                    return self.__retrieve_stream_url(prev_stream).rstrip()
                else:
                    self.queue_index = len(self.queue)
                    return self.prev_url()
            else:
                return ''
        except (KeyError, AttributeError):
            del self.queue[self.queue_index]
            return self.prev_url()

    def __update_play_queue_order(self):
        """ Update the queue playback order.

        A sequential order is applied if the current play mode is "NORMAL" or a
        random order if current play mode is "SHUFFLE"

        """
        total_streams = len(self.queue)
        if total_streams:
            if not len(self.play_queue_order):
                # Create a sequential play order, if empty
                self.play_queue_order = range(total_streams)
            if self.current_play_mode == self.play_modes.SHUFFLE:
                random.shuffle(self.play_queue_order)
            print_nfo("[YouTube] [Streams in queue] '{0}'." \
                      .format(total_streams))

    def __retrieve_stream_url(self, stream):
        """ Retrieve a stream url

        """
        try:
            if not stream.get('v') or not stream.get('a'):
                logging.info("__retrieve_stream_url ytid : %s", stream['i'].ytid)
                video = pafy.new(stream['i'].ytid)
                audio = video.getbestaudio(preftype="webm")
                if not audio:
                    logging.info("__retrieve_stream_url : no suitable audio found")
                    raise AttributeError()
                stream.update({'a': audio, 'v': video})

            # streams = stream.get('v').audiostreams[::-1]
            # pprint.pprint(streams)
            # dump_stream_info(streams)

            self.now_playing_stream = stream
            logging.info("__retrieve_stream_url url       : %s", stream['a'].url)
            logging.info("__retrieve_stream_url bitrate   : %s", stream['a'].bitrate)
            logging.info("__retrieve_stream_url extension : %s", stream['a'].extension)
            return stream['a'].url.encode("utf-8")

        except AttributeError:
            logging.info("Could not retrieve the stream url!")
            raise

    def add_to_playback_queue(self, audio=None, video=None, info=None):
        """ Add to the playback queue. """

        if audio:
            print_nfo("[YouTube] [Stream] '{0}' [{1}]." \
                      .format(to_ascii(audio.title).encode("utf-8"), \
                              to_ascii(audio.extension)))
        if info:
            print_nfo("[YouTube] [Stream] '{0}'." \
                      .format(to_ascii(info.title).encode("utf-8")))

        self.queue.append(
            dict(a=audio, v=video, i=info))

if __name__ == "__main__":
    tizyoutubeproxy()
