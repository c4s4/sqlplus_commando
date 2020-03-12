#!/usr/bin/env python
# encoding: UTF-8

#pylint: disable=W0403
import sys
if sys.version_info.major == 2:
    from sqlplus_commando import SqlplusCommando, SqlplusResultParser, SqlplusErrorParser
elif sys.version_info.major == 3:
    from .sqlplus_commando import SqlplusCommando, SqlplusResultParser, SqlplusErrorParser
