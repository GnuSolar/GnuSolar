# Documents created from a project: quotes, invoices, documentation, ...
#
# No Qt here. Problems are raised as DocumentError, the caller shows them.

import os
import sys

# the libraries bundled with GnuSolar (relatorio, qrbill, pdfrw)
_sitepack = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site-packages")
if _sitepack not in sys.path:
    sys.path.insert(0, _sitepack)


class DocumentError(Exception):
    def __init__(self, title, message):
        super().__init__(message)
        self.title = title
