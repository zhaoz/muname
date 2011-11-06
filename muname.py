#!/usr/bin/python

# TODO: need to validate source and destination directories
# TODO: Define the output format string specification.

from optparse import OptionParser
from os import path
import sys

DEFAULT_FORMAT=''

class MuName(object):
  """MuName Class.

  Takes a source and destination directory, processes music files and outputs
  depending on given output_format.
  """

  def __init__(self, destination=None, source=None,
               output_format=DEFAULT_FORMAT):
    """MuName __init__

    Initialize the MuName object with given parameters.

    Args:
      destination: Destination directory.
      souce: Source directory.
      output_format: String format for output.
    """
    self._destination = destination
    self._output_format = output_format

    if path.isdir(source):
      self._source = source
    else:
      raise IOError('Given source directory does not exist')


def _GetParser():
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


def main():
  parser = _GetParser()

  (options, args) = parser.parse_args()

  print(options)
  print(args)


if __name__ == "__main__":
	main()