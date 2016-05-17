#!/usr/bin/env python
# encoding: UTF-8

from __future__ import with_statement
import re
import os.path
import datetime
import subprocess
import HTMLParser


class SqlplusCommando(object):

    CATCH_ERRORS = "WHENEVER SQLERROR EXIT SQL.SQLCODE;\nWHENEVER OSERROR EXIT 9;\n"
    EXIT_COMMAND = "\ncommit;\nexit;\n"
    ISO_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, configuration=None,
                 hostname=None, database=None,
                 username=None, password=None,
                 cast=True):
        if hostname and database and username and password:
            self.hostname = hostname
            self.database = database
            self.username = username
            self.password = password
        elif configuration:
            self.hostname = configuration['hostname']
            self.database = configuration['database']
            self.username = configuration['username']
            self.password = configuration['password']
        else:
            raise SqlplusException('Missing database configuration')
        self.cast = cast

    def run_query(self, query, parameters={}, cast=True,
                  check_unknown_command=True):
        if parameters:
            query = self._process_parameters(query, parameters)
        query = self.CATCH_ERRORS + query
        session = subprocess.Popen(['sqlplus', '-S', '-L', '-M', 'HTML ON',
                                    self._get_connection_url()],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        session.stdin.write(query)
        output, _ = session.communicate(self.EXIT_COMMAND)
        code = session.returncode
        if code != 0:
            raise SqlplusException(SqlplusErrorParser.parse(output), query)
        else:
            if output:
                result = SqlplusResultParser.parse(output, cast=cast,
                                                  check_unknown_command=check_unknown_command)
                return result

    def run_script(self, script, cast=True, check_unknown_command=True):
        if not os.path.isfile(script):
            raise SqlplusException("Script '%s' was not found" % script)
        with open(script) as stream:
            source = stream.read()
        return self.run_query(query=source, cast=cast, check_unknown_command=check_unknown_command)

    def _get_connection_url(self):
        return "%s/%s@%s/%s" % \
               (self.username, self.password, self.hostname, self.database)

    @staticmethod
    def _process_parameters(query, parameters):
        if not parameters:
            return query
        if isinstance(parameters, (list, tuple)):
            parameters = tuple(SqlplusCommando._format_parameters(parameters))
        elif isinstance(parameters, dict):
            values = SqlplusCommando._format_parameters(parameters.values())
            parameters = dict(zip(parameters.keys(), values))
        return query % parameters

    @staticmethod
    def _format_parameters(parameters):
        return [SqlplusCommando._format_parameter(param) for
                param in parameters]

    @staticmethod
    def _format_parameter(parameter):
        if isinstance(parameter, (int, long, float)):
            return str(parameter)
        elif isinstance(parameter, (str, unicode)):
            return "'%s'" % SqlplusCommando._escape_string(parameter)
        elif isinstance(parameter, datetime.datetime):
            return "'%s'" % parameter.strftime(SqlplusCommando.ISO_FORMAT)
        elif isinstance(parameter, list):
            return "(%s)" % ', '.join([SqlplusCommando._format_parameter(e)
                                       for e in parameter])
        elif parameter is None:
            return "NULL"
        else:
            raise SqlplusException("Type '%s' is not managed as a query parameter" %
                                   parameter.__class__.__name__)

    @staticmethod
    def _escape_string(string):
        return string.replace("'", "''")


class SqlplusResultParser(HTMLParser.HTMLParser):

    DATE_FORMAT = '%d/%m/%y %H:%M:%S'
    UNKNOWN_COMMAND = 'SP2-0734: unknown command'
    CASTS = (
        (r'-?\d+', int),
        (r'-?\d*,?\d*([Ee][+-]?\d+)?', lambda f: float(f.replace(',', '.'))),
        (r'\d\d/\d\d/\d\d \d\d:\d\d:\d\d,\d*',
         lambda d: datetime.datetime.strptime(d[:17],
                                              SqlplusResultParser.DATE_FORMAT)),
        (r'NULL', lambda d: None),
    )

    def __init__(self, cast):
        HTMLParser.HTMLParser.__init__(self)
        self.cast = cast
        self.active = False
        self.result = []
        self.fields = []
        self.values = []
        self.header = True
        self.data = ''

    @staticmethod
    def parse(source, cast, check_unknown_command):
        if not source.strip():
            return ()
        if SqlplusResultParser.UNKNOWN_COMMAND in source and check_unknown_command:
            raise SqlplusException(SqlplusErrorParser.parse(source))
        parser = SqlplusResultParser(cast)
        parser.feed(source)
        return tuple(parser.result)

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.active = True
        elif self.active:
            if tag == 'th':
                self.header = True
            elif tag == 'td':
                self.header = False

    def handle_endtag(self, tag):
        if tag == 'table':
            self.active = False
        elif self.active:
            if tag == 'tr' and not self.header:
                row = dict(zip(self.fields, self.values))
                self.result.append(row)
                self.values = []
            elif tag == 'th':
                self.fields.append(self.data.strip())
                self.data = ''
            elif tag == 'td':
                data = self.data.strip()
                if self.cast:
                    data = self._cast(data)
                self.values.append(data)
                self.data = ''

    def handle_data(self, data):
        if self.active:
            self.data += data

    @staticmethod
    def _cast(value):
        for regexp, function in SqlplusResultParser.CASTS:
            if re.match("^%s$" % regexp, value):
                return function(value)
        return value


class SqlplusErrorParser(HTMLParser.HTMLParser):

    UNKNOWN_COMMAND = 'SP2-0734: unknown command'

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.active = False
        self.message = ''

    @staticmethod
    def parse(source):
        parser = SqlplusErrorParser()
        parser.feed(source)
        return '\n'.join([l for l in parser.message.split('\n') if l.strip() != ''])

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.active = True

    def handle_endtag(self, tag):
        if tag == 'body':
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.message += data

# pylint: disable=W0231
class SqlplusException(Exception):

    def __init__(self, message, query=None):
        self.message = message
        self.query = query

    def __str__(self):
        return self.message
