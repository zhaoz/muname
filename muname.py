#!/usr/bin/python2.7
# vim: expandtab ts=2 sw=2 :

# TODO: need to validate source and destination directories
# TODO: Define the output format string specification.

import mimetypes
from optparse import OptionParser
import os
import sys

from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis


SUPPORTED_TYPES = ['audio/mpeg', 'audio/ogg']
TAGS = ['artist', 'track', 'album', 'album_artist', 'title', 'genre']
DEFAULT_FORMAT = '{artist}/{album}/{track} - {title}'
  

def GetType(path):
  return mimetypes.guess_type(path)[0]


def IsSong(path):
  return GetType(path) in SUPPORTED_TYPES


class Song(object):
  """Song Class."""

  def __init__(self, path):
    self._path = path

    tags = self._GetTagInfo()

    self._tag_info = self._NormalizeTags(tags)

    for tag in TAGS:
      setattr(self, tag, self._tag_info.get(tag, None))

  def _NormalizeTags(self, tags):
    tags['track'] = tags.get('track', None) or tags.get('tracknumber', None)

    tag_info = {}
    for k, v in tags.items():
      tag_info[k] = v[0].encode('utf-8')

    return tag_info

  def __str__(self):
    return ('{artist} - {track} - {album} - {title}'.format(**self._tag_info))

  def __repr__(self):
    return str(self)

  def _GetTagInfo(self):
    raise NotImplementedError


class Mp3(Song):
  def _GetTagInfo(self):
    tags = EasyID3(self._path)
    return dict(tags)


class Ogg(Song):
  def _GetTagInfo(self):
    tags = OggVorbis(self._path)
    return dict(tags)


def GetSong(path):
  t = GetType(path)

  if t == 'audio/mpeg':
    return Mp3(path)
  elif t == 'audio/ogg':
    return Ogg(path)
  else:
    return None


class Collection(object):
  """A collection of songs."""

  def __init__(self, format_string=DEFAULT_FORMAT):
    self._format = format_string
    self.songs = []
  
  def add(self, song):
    if not isinstance(song, Song):
      song = Song(song)
    self.songs.append(song)

  def __str__(self):
    return '\n'.join([str(s) for s in self.songs])

  def __repr__(self):
    return str(self)


class MuName(object):
  """MuName Class.

  Takes a source and destination directory, processes music files and outputs
  depending on given output_format.
  """

  def __init__(self, destination=None, source=None, no_action=True,
               output_format=DEFAULT_FORMAT):
    """MuName __init__

    Initialize the MuName object with given parameters.

    Args:
      destination: Destination directory.
      souce: Source directory.
      output_format: String format for output.
    """
    self._destination = os.path.abspath(destination)
    self._output_format = output_format

    if os.path.isdir(source):
      self._source = os.path.abspath(source)
    else:
      raise IOError('Given source directory does not exist')
  
  def CreateCollection(self, collection=None):
    """Build a representation of files in source.

    Look at the files in the source directory and extract information for each
    of the files.

    Args:
      collection: Given collection to update, creates a collection if none
                  given.

    Returns:
      A representation of the music in the directory.
    """
    if not collection:
      collection = Collection(format_string=self._output_format)

    for root, dirs, files in os.walk(self._source, followlinks=True):
      for f in files:
        path = os.path.join(root, f)
        song = GetSong(path)
        if song:
          collection.add(song)
    
    print(collection)
    return collection



def _GetParser():
  """Create the parser with defaults."""
  parser = OptionParser()
  parser.add_option('-s', '--source',
                    dest='source',
                    help='Source Directory')
  parser.add_option('-d', '--destination',
                    dest='destination',
                    help='Destination Directory')
  parser.add_option('-n', '--no-action',
                    dest='no_action',
                    action='store_true',
                    help='Do not actually do the operation')

  parser.set_defaults(no_action=False)

  return parser


def _GetOptions():
  """Fetch command line args."""
  parser = _GetParser()

  (options, args) = parser.parse_args()
  opt_dict = vars(options)

  # TODO at some point, positional args for src and dest would be nice.

  return opt_dict


def main():
  options = _GetOptions()
  muname = MuName(**options)

  muname.CreateCollection()


if __name__ == "__main__":
  main()
