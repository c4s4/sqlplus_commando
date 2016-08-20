#!/usr/bin/env python
# encoding: UTF-8

from __future__ import with_statement
import re
import os.path
import datetime
import subprocess
import HTMLParser


class SqlplusCommando(object):

    """
    Oracle driver that calls sqlplus on command line to run queries or scripts.
    WHENEVER statements are added to interrupt on SQL and OS errors.
    Nevertheless some errors (such as compilation errors in package bodies) do
    not interrupt scripts on error. Thus, this tool parses sqlplus output to
    raise an error on 'error', 'warning' or 'unknown'.
    """

    CATCH_ERRORS = "WHENEVER SQLERROR EXIT SQL.SQLCODE;\nWHENEVER OSERROR EXIT 9;\n"
    EXIT_COMMAND = "\nCOMMIT;\nEXIT;\n"
    ISO_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, configuration=None,
                 hostname=None, database=None,
                 username=None, password=None,
                 encoding=None, cast=True):
        """
        Constructor.
        :param configuration: configuration as a dictionary with four following
               parameters.
        :param hostname: database hostname.
        :param database: database name.
        :param username: database user name.
        :param password: database password.
        :param encoding: database encoding.
        :param cast: tells if we should cast result
        """
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
        self.encoding = encoding
        self.cast = cast

    def run_query(self, query, parameters={}, cast=True, check_errors=True):
        """
        Run a given query.
        :param query: the query to run
        :param parameters: query parameters as a dictionary (with references as
               '%(name)s' in query) or tuple (with references such as '%s')
        :param cast: tells if we should cast result
        :param check_errors: check for errors in output
        :return: result query as a tuple of dictionaries
        """
        if parameters:
            query = self._process_parameters(query, parameters)
        query = self.CATCH_ERRORS + query
        session = subprocess.Popen(['sqlplus', '-S', '-L', '-M', 'HTML ON',
                                    self._get_connection_url()],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        if self.encoding:
            session.stdin.write(query.encode(self.encoding))
        else:
            session.stdin.write(query)
        output, _ = session.communicate(self.EXIT_COMMAND)
        code = session.returncode
        if code != 0:
            raise SqlplusException(SqlplusErrorParser.parse(output), query, raised=True)
        else:
            if output:
                result = SqlplusResultParser.parse(output, cast=cast, check_errors=check_errors)
                return result

    def run_script(self, script, cast=True, check_errors=True):
        """
        Run a given script.
        :param script: the path to the script to run
        :param cast: tells if we should cast result
        :param check_errors: check for errors in output
        :return: result query as a tuple of dictionaries
        """
        if not os.path.isfile(script):
            raise SqlplusException("Script '%s' was not found" % script)
        query = "@%s\n" % script
        return self.run_query(query=query, cast=cast, check_errors=check_errors)

    def _get_connection_url(self):
        """
        Return connection URL
        :return: connection URL
        """
        return "%s/%s@%s/%s" % \
               (self.username, self.password, self.hostname, self.database)

    @staticmethod
    def _process_parameters(query, parameters):
        """
        Replace parameters references in query with their value.
        :param query: the query to process
        :param parameters: parameters as a dictionary or a tuple
        :return: query with parameters references replaced with their value
        """
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
        """
        Format parameters to SQL syntax.
        :param parameters: parameters to format as a list
        :return: formatted parameters
        """
        return [SqlplusCommando._format_parameter(param) for
                param in parameters]

    @staticmethod
    def _format_parameter(parameter):
        """
        Format a single parameter:
        - Let integers alone
        - Surround strings with quotes
        - Lists with parentheses
        :param parameter: parameters to format
        :return: formatted parameter
        """
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
        """
        Replace quotes with two quotes.
        :param string: string to escape
        :return: escaped string
        """
        return string.replace("'", "''")


class SqlplusResultParser(HTMLParser.HTMLParser):

    """
    Sqlplus result is formatted as HTML with 'HTML ON' option. This parser
    extracts result in HTML table and returns it as a tuple of dictionaries.
    """

    DATE_FORMAT = '%d/%m/%y %H:%M:%S'
    REGEXP_ERRORS = ('^.*unknown.*$|^.*warning.*$|^.*error.*$')
    CASTS = (
        (r'-?\d+', int),
        (r'-?\d*,?\d*([Ee][+-]?\d+)?', lambda f: float(f.replace(',', '.'))),
        (r'\d\d/\d\d/\d\d \d\d:\d\d:\d\d,\d*',
         lambda d: datetime.datetime.strptime(d[:17],
                                              SqlplusResultParser.DATE_FORMAT)),
        (r'NULL', lambda d: None),
    )

    def __init__(self, cast):
        """
        Constructor.
        :param cast: tells if we should cast result
        """
        HTMLParser.HTMLParser.__init__(self)
        self.cast = cast
        self.active = False
        self.result = []
        self.fields = []
        self.values = []
        self.header = True
        self.data = ''

    @staticmethod
    def parse(source, cast, check_errors):
        """
        Parse sqlplus output.
        :param source: the output
        :param cast: tells if we should cast result
        :param check_errors: tells if we should parse output for errors
        :return: result as a tuple of dictionaries
        """
        if not source.strip():
            return ()
        if check_errors:
            errors = re.findall(SqlplusResultParser.REGEXP_ERRORS, source,
                                re.MULTILINE + re.IGNORECASE)
            if errors:
                raise SqlplusException('\n'.join(errors), raised=False)
        parser = SqlplusResultParser(cast)
        parser.feed(source)
        return tuple(parser.result)

    def handle_starttag(self, tag, attrs):
        """
        Called by HTML parser on an opening tag
        :param tag: opened tag
        :param attrs: attributes
        """
        if tag == 'table':
            self.active = True
        elif self.active:
            if tag == 'th':
                self.header = True
            elif tag == 'td':
                self.header = False

    def handle_endtag(self, tag):
        """
        Called by HTML parser on an ending tag
        :param tag: closed tag
        """
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
        """
        Handle text
        :param data: text
        """
        if self.active:
            self.data += data

    @staticmethod
    def _cast(value):
        """
        Cast given value
        :param value: value to cast
        :return: casted value
        """
        for regexp, function in SqlplusResultParser.CASTS:
            if re.match("^%s$" % regexp, value):
                return function(value)
        return value


class SqlplusErrorParser(HTMLParser.HTMLParser):

    """
    Parse error output.
    """

    NB_ERROR_LINES = 4

    def __init__(self):
        """
        Constructor.
        """
        HTMLParser.HTMLParser.__init__(self)
        self.active = False
        self.message = ''

    @staticmethod
    def parse(source):
        """
        Parse error ourput.
        :param source: text to parse
        :return: return formatted error message
        """
        parser = SqlplusErrorParser()
        parser.feed(source)
        lines = [l for l in parser.message.split('\n') if l.strip() != '']
        return '\n'.join(lines[-SqlplusErrorParser.NB_ERROR_LINES:])

    def handle_starttag(self, tag, attrs):
        """
        Called on an opening tag
        :param tag: opened tag
        :param attrs: attributes
        """
        if tag == 'body':
            self.active = True

    def handle_endtag(self, tag):
        """
        Called on closed tag
        :param tag: clased tag
        """
        if tag == 'body':
            self.active = False

    def handle_data(self, data):
        """
        Called on text
        :param data: text
        """
        if self.active:
            self.message += data


# pylint: disable=W0231
class SqlplusException(Exception):

    """
    Exception raised by this driver.
    """

    def __init__(self, message, query=None, raised=False):
        """
        Constructor.
        :param message: the error message
        :param query: query that raised an error
        :param raised: raised is set to True if sqlplus stops on error running
               a script, it is set to False if the error was detected in output
               (with a text such as "Package compilation error")
        """
        self.message = message
        self.query = query
        self.raised = raised

    def __str__(self):
        """
        String representation of this error
        :return: representation as a string
        """
        return self.message
