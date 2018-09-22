"""Top-level package for redpil."""

__author__ = 'Mark Harfouche'
__email__ = 'mark.harfouche@gmail.com'

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
