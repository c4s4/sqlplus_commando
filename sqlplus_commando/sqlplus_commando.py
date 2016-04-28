#!/usr/bin/env python
# encoding: UTF-8

from __future__ import with_statement
from subprocess import Popen, PIPE
import re
import datetime


# pylint: disable=E1103
class SqlplusCommando(object):

    QUERY_ERROR_HANDLER = "WHENEVER SQLERROR EXIT SQL.SQLCODE\n"
    CASTS = (
        (r'-?\d+', int),
        (r'-?\d*\.?\d*([Ee][+-]?\d+)?', float),
        (r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d',
         lambda d: datetime.datetime.strptime(d, SqlplusCommando.ISO_FORMAT)),
        (r'NULL', lambda d: None),
    )

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

    def run_query(self, query,cast=None):
        query = self.QUERY_ERROR_HANDLER + query
        connection_url = self._get_connection_url()
        session = Popen(['sqlplus', '-S', '-L', connection_url], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        session.stdin.write(query)
        output, _ = session.communicate()
        code = session.returncode
        if code != 0:
            raise Exception(output.strip())
        else:
            if cast is None:
                cast = self.cast
            if output:
                return self._output_to_result(output, cast=cast)

    def _get_connection_url(self):
        return "%s/%s@%s/%s" % \
            (self.username, self.password, self.hostname, self.database)

    def _output_to_result(self, output, cast):
        result = []
        lines = output.strip().split('\n')
        fields = lines[0].split(' ')
        for line in lines[2:]:
            values = [e.strip() for e in line.split(' ')]
            if cast:
                values = SqlplusCommando._cast_list(values)
            result.append(dict(zip(fields, values)))
        return tuple(result)

    @staticmethod
    def _cast_list(values):
        return [SqlplusCommando._cast(value) for value in values]

    @staticmethod
    def _cast(value):
        for regexp, function in SqlplusCommando.CASTS:
            if re.match("^%s$" % regexp, value):
                return function(value)
        return value

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


# # pylint: disable=E1103
# class SqlplusCommando(object):
#
#     ISO_FORMAT = '%Y-%m-%d %H:%M:%S'
#     CASTS = (
#         (r'-?\d+', int),
#         (r'-?\d*\.?\d*([Ee][+-]?\d+)?', float),
#         (r'\d{4}-\d\d-\d\d \d\d:\d\d:\d\d',
#          lambda d: datetime.datetime.strptime(d, SqlplusCommando.ISO_FORMAT)),
#         (r'NULL', lambda d: None),
#     )
#     QUERY_LAST_INSERT_ID = """
#     ;SELECT last_insert_id() as last_insert_id;
#     """
#
#     def __init__(self, configuration=None,
#                  hostname=None, database=None,
#                  username=None, password=None,
#                  encoding=None, cast=True):
#         if hostname and database and username and password:
#             self.hostname = hostname
#             self.database = database
#             self.username = username
#             self.password = password
#         elif configuration:
#             self.hostname = configuration['hostname']
#             self.database = configuration['database']
#             self.username = configuration['username']
#             self.password = configuration['password']
#         else:
#             raise Exception('Missing database configuration')
#         self.cast = cast
#
#     def run_query(self, query, parameters=None, cast=None,
#                   last_insert_id=False):
#         query = self._process_parameters(query, parameters)
#         if last_insert_id:
#             query += self.QUERY_LAST_INSERT_ID
#         connection_url = self._get_connection_url()
#         command = ['sqlplus', connection_url, query]
#         output = self._execute_with_output(command)
#         if cast is None:
#             cast = self.cast
#         if output:
#             result = self._output_to_result(output, cast=cast)
#             if last_insert_id:
#                 return int(result[0]['last_insert_id'])
#             else:
#                 return result
#
#     def run_script(self, script, cast=None):
#         command = ['sqlplus', selg.get_connection_url(), "@%s" % script]
#         if cast is None:
#             cast = self.cast
#         with open(script) as stdin:
#             output = self._execute_with_output(command, stdin=stdin)
#         if output:
#             return self._output_to_result(output, cast=cast)
#
#     def _get_connection_url(self):
#         return "%s/%s@%s/%s" % \
#             (self.username, self.password, self.hostname, self.database)
#
#     def _output_to_result(self, output, cast):
#         result = []
#         lines = output.strip().split('\n')
#         fields = lines[0].split('\t')
#         for line in lines[1:]:
#             values = line.split('\t')
#             if cast:
#                 values = SqlplusCommando._cast_list(values)
#             result.append(dict(zip(fields, values)))
#         return tuple(result)
#
#     @staticmethod
#     def _cast_list(values):
#         return [SqlplusCommando._cast(value) for value in values]
#
#     @staticmethod
#     def _cast(value):
#         for regexp, function in SqlplusCommando.CASTS:
#             if re.match("^%s$" % regexp, value):
#                 return function(value)
#         return value
#
#     @staticmethod
#     def _execute_with_output(command, stdin=None):
#         if stdin:
#             process = subprocess.Popen(command, stdout=subprocess.PIPE,
#                                        stderr=subprocess.PIPE, stdin=stdin)
#         else:
#             process = subprocess.Popen(command, stdout=subprocess.PIPE,
#                                        stderr=subprocess.PIPE)
#         output, errput = process.communicate()
#         if process.returncode != 0:
#             raise Exception(errput.strip())
#         return output
#
#     @staticmethod
#     def _process_parameters(query, parameters):
#         if not parameters:
#             return query
#         if isinstance(parameters, (list, tuple)):
#             parameters = tuple(SqlplusCommando._format_parameters(parameters))
#         elif isinstance(parameters, dict):
#             values = SqlplusCommando._format_parameters(parameters.values())
#             parameters = dict(zip(parameters.keys(), values))
#         return query % parameters
#
#     @staticmethod
#     def _format_parameters(parameters):
#         return [SqlplusCommando._format_parameter(param) for
#                 param in parameters]
#
#     @staticmethod
#     def _format_parameter(parameter):
#         if isinstance(parameter, (int, long, float)):
#             return str(parameter)
#         elif isinstance(parameter, (str, unicode)):
#             return "'%s'" % SqlplusCommando._escape_string(parameter)
#         elif isinstance(parameter, datetime.datetime):
#             return "'%s'" % parameter.strftime(SqlplusCommando.ISO_FORMAT)
#         elif isinstance(parameter, list):
#             return "(%s)" % ', '.join([SqlplusCommando._format_parameter(e)
#                                        for e in parameter])
#         elif parameter is None:
#             return "NULL"
#         else:
#             raise Exception("Type '%s' is not managed as a query parameter" %
#                             parameter.__class__.__name__)
#
#     @staticmethod
#     def _escape_string(string):
#         return string.replace("'", "''")
