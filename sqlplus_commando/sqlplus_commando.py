#!/usr/bin/env python
# encoding: UTF-8

from __future__ import with_statement
import re
import os.path
import datetime
import tempfile
import subprocess
import HTMLParser


class SqlplusCommando(object):

    QUERY_ERROR_HANDLER = '''WHENEVER SQLERROR EXIT SQL.SQLCODE;
WHENEVER OSERROR EXIT 9;
'''
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
            raise Exception('Missing database configuration')
        self.cast = cast

    def run_query(self, query, cast=True, check_unknown_command=True):
        command = self.QUERY_ERROR_HANDLER + query
        return self._run_command(command, cast=cast,
            check_unknown_command=check_unknown_command)

    def run_script(self, script, cast=True, check_unknown_command=True):
        if not os.path.isfile(script):
            raise Exception("Script '%s' was not found" % script)
        with open(script) as stream:
            source = stream.read()
        filename = tempfile.mkstemp(prefix='sqlplus_commando-',
                                    suffix='.sql')[1]
        with open(filename, 'wb') as stream:
            stream.write(self.QUERY_ERROR_HANDLER + source)
        try:
            return self._run_command("@%s" % filename, cast=cast,
                check_unknown_command=check_unknown_command)
        finally:
            os.remove(filename)

    def _run_command(self, command, cast, check_unknown_command):
        connection_url = self._get_connection_url()
        session = subprocess.Popen(['sqlplus', '-S', '-L', '-M', 'HTML ON',
                                    connection_url],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        session.stdin.write(command)
        output, _ = session.communicate()
        code = session.returncode
        if code != 0:
            raise Exception(output.strip())
        else:
            if output:
                result = OracleParser.parse(output, cast=cast,
                    check_unknown_command=check_unknown_command)
                return result

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
            raise Exception("Type '%s' is not managed as a query parameter" %
                            parameter.__class__.__name__)

    @staticmethod
    def _escape_string(string):
        return string.replace("'", "''")


class OracleParser(HTMLParser.HTMLParser):

    DATE_FORMAT = '%d/%m/%y %H:%M:%S'
    UNKNOWN_COMMAND = 'SP2-0734: unknown command'
    CASTS = (
        (r'-?\d+', int),
        (r'-?\d*,?\d*([Ee][+-]?\d+)?', lambda f: float(f.replace(',', '.'))),
        (r'\d\d/\d\d/\d\d \d\d:\d\d:\d\d,\d*',
         lambda d: datetime.datetime.strptime(d[:17],
                                              OracleParser.DATE_FORMAT)),
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
        if OracleParser.UNKNOWN_COMMAND in source and check_unknown_command:
            start = source.index(OracleParser.UNKNOWN_COMMAND)
            message = source[start:].split('\n')[0]
            raise Exception(message)
        parser = OracleParser(cast)
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
        for regexp, function in OracleParser.CASTS:
            if re.match("^%s$" % regexp, value):
                return function(value)
        return value
