#!/usr/bin/python2.7
# vim: expandtab ts=2 sw=2 :

import mimetypes
from optparse import OptionParser
import os
import pprint
import re
import shutil
import string
import sys

from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis


SUPPORTED_TYPES = ['audio/mpeg', 'audio/ogg']
TAGS = ['artist', 'track', 'album', 'album_artist', 'title', 'genre']
DEFAULT_FORMAT = '{artist}/{album}/{track} - {title}'

_TRACK_RE = re.compile(r'^\d+')
_FILE_ESCAPE_RE = re.compile(r'([/])')
_SAFE_TRANS_TABLE = string.maketrans(
    ':',
    '_'
    )


def GetType(path):
  return mimetypes.guess_type(path)[0]


def IsSong(path):
  return GetType(path) in SUPPORTED_TYPES


def SanitizeFilename(name):
  return _FILE_ESCAPE_RE.sub(r'\\\1',
      name.translate(_SAFE_TRANS_TABLE))


class Song(object):
  """Song Class."""

  def __init__(self, path):
    self.path = path

    tags = self._GetTagInfo()

    self.tag_info = self._NormalizeTags(tags)

    for tag in TAGS:
      setattr(self, tag, self.tag_info.get(tag, None))

  def _NormalizeTags(self, tags):
    tag_info = {}
    for k, v in tags.items():
      tag_info[k] = v[0].encode('utf-8')

    track = tags.get('track', None) or tags.get('tracknumber', None)

    if track:
      track = int(_TRACK_RE.findall(track[0])[0])
      tag_info['track'] = '{0:02}'.format(track)

    return tag_info

  def __str__(self):
    return ('{artist} - {track} - {album} - {title}'.format(**self.tag_info))

  def __repr__(self):
    return str(self)

  def _GetTagInfo(self):
    raise NotImplementedError


class Mp3(Song):
  EXTENSION = 'mp3'

  def _GetTagInfo(self):
    tags = EasyID3(self.path)
    return dict(tags)


class Ogg(Song):
  EXTENSION = 'ogg'

  def _GetTagInfo(self):
    tags = OggVorbis(self.path)
    return dict(tags)


def GetSong(path):
  t = GetType(path)

  if t == 'audio/mpeg':
    return Mp3(path)
  elif t == 'audio/ogg':
    return Ogg(path)
  else:
    return None


def _ParseFormatString(path):
  parts = []
  while path:
    (path, end) = os.path.split(path)
    parts.insert(0, end)
  return parts


class Collection(object):
  """A collection of songs."""

  def __init__(self, format_string=DEFAULT_FORMAT):
    self._format = format_string
    self._path_parts = _ParseFormatString(self._format)
    self._songs = []
    self._structure = {}

  def add(self, song):
    """Add a song to the collection.

    Given a song add to collection, place in the collection structure.

    Args:
      song: Song to put in, either string path or song object.
    """

    if not isinstance(song, Song):
      song = Song(song)
    self._songs.append(song)

    self._PutInStructure(song)

  def _PutInStructure(self, song):
    """Place song in dir structure."""

    level = self._structure
    last_level = None
    piece = None

    for part in self._path_parts:
      piece = part.format(**song.tag_info)

      next_level = level.get(piece, None)
      if not next_level:
        level[piece] = {}
        next_level = level[piece]
      last_level = level
      level = next_level

    # place song at the last level
    last_level['{0}.{1}'.format(piece, song.EXTENSION)] = song

  def songs(self):
    """Generator that returns tuples of (path, song)."""
    levels = [('', self._structure)]

    while levels:
      path, cur_level = levels.pop()

      if not isinstance(cur_level, Song):
        for name, obj in cur_level.iteritems():
          levels.append((os.path.join(path, SanitizeFilename(name)), obj))
        continue

      # we've hit a song
      yield path, cur_level

  def __str__(self):
    return pprint.pformat(self._structure)

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

    self._no_action = no_action

    if os.path.isdir(source):
      self._source = os.path.abspath(source)
    else:
      raise IOError('Given source directory does not exist')

    self._collection = None

  def Scan(self, collection=None):
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

    self._collection = collection
    return collection

  def _FileOp(self, src, dest, file_op=None):
    if os.path.exists(dest) and not overwrite:
      raise IOError('File {0} already exists!'.format(dest))

    dest_dir = os.path.dirname(dest)
    if not os.path.exists(dest_dir):
      os.makedirs(dest_dir)

    file_op(src, dest)

  def _TransformCollection(self, file_op=None):
    if not file_op:
      raise ValueError('No file operation given.')

    if self._no_action:
      print 'No action specified, no file operations will be performed.'

    for path, song in self._collection.songs():
      new_path = os.path.join(self._destination, path)
      print '{0} -> {1}'.format(song.path, new_path)

      if not self._no_action:
        # ensure that path exists
        try:
          self._FileOp(song.path, new_path, file_op=file_op)
        except IOError as (errno, strerror) :
          sys.stderr.write('IOError: {0} - {1}\n'.format(errno, strerror))

  def Copy(self):
    """Copy the collection to the given destination folder."""
    self._TransformCollection(shutil.copy)

  def Move(self):
    """Move the collection to the given destination folder."""
    self._TransformCollection(shutil.move)

  def Symlink(self):
    """Create symlinks."""
    self._TransformCollection(os.symlink)


def _GetParser():
  """Create the parser with defaults."""
  parser = OptionParser()
  parser.add_option('-s', '--source',
                    dest='source',
                    help='Source Directory')
  parser.add_option('-d', '--destination',
                    dest='destination',
                    help='Destination Directory')
  parser.add_option('-o', '--operation',
                    dest='operation',
                    help='Operation: move, copy, link')
  parser.add_option('-n', '--no-action',
                    dest='no_action',
                    action='store_true',
                    help='Do not actually do the operation')

  parser.set_defaults(no_action=False, operation='move',
                      output_format=DEFAULT_FORMAT)

  return parser


def _GetOptions():
  """Fetch command line args."""
  parser = _GetParser()

  (options, args) = parser.parse_args()

  return options


def main():
  opts = _GetOptions()

  muname = MuName(destination=opts.destination,
                  source=opts.source,
                  no_action=opts.no_action,
                  output_format=opts.output_format)
  muname.Scan()

  if opts.operation == 'move':
    muname.Move()
  elif opts.operation == 'copy':
    muname.Copy()
  elif opts.operation == 'symlink':
    muname.Symlink()


if __name__ == "__main__":
  main()
