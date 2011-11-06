#!/usr/bin/python

# TODO: need to validate source and destination directories
# TODO: Define the output format string specification.

import mimetypes
from optparse import OptionParser
import os
import sys

SUPPORTED_TYPES = ['audio/mpeg', 'audio/ogg']
DEFAULT_FORMAT = ''

  

def IsSong(path):
  return mimetypes.guess_type(path)[0] in SUPPORTED_TYPES


class Song(object):
  """Song Class."""

  def __init__(self, path):
    self._path = path

  def GetType(self):
    return mimetypes.guess_type(self._path)[0]

  def __str__(self):
    return self._path
  
  def __repr__(self):
    return str(self)


class Collection(object):
  """A collection of songs."""

  def __init__(self, format=DEFAULT_FORMAT):
    self._format = format
    self.songs = []
  
  def add(self, song):
    if not isinstance(song, Song):
      song = Song(song)
    self.songs.append(song)

  def __str__(self):
    return ', '.join([str(s) for s in self.songs])

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
  
  def ExamineSource(self):
    """Build a representation of files in source.

    Look at the files in the source directory and extract information for each
    of the files.

    Returns:
      A representation of the music in the directory.
    """
    collection = Collection()

    for root, dirs, files in os.walk(self._source, followlinks=True):
      for f in files:
        path = os.path.join(root, f)
        if IsSong(path):
          collection.add(Song(path))
    
    print(collection)



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

  muname.ExamineSource()


if __name__ == "__main__":
	main()