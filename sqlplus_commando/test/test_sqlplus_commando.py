#!/usr/bin/env python
# encoding: UTF-8

import os
import datetime
import unittest
from sqlplus_commando import SqlplusCommando, OracleResultParser


# pylint: disable=W0212
class TestSqlplusCommando(unittest.TestCase):

    CONFIG = {
        'hostname': 'localhost',
        'database': 'xe',
        'username': 'test',
        'password': 'test',
    }
    SQL_DIR = os.path.join(os.path.dirname(__file__), 'sql')

    def test_run_query_nominal(self):
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        result = sqlplus.run_query("SELECT 42 AS response, 'This is a test' "
                                   "AS question FROM DUAL;")
        self.assertEqual(({'RESPONSE': 42, 'QUESTION': 'This is a test'},),
                         result)

    def test_run_query_parameters(self):
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        params = {'response': 42}
        result = sqlplus.run_query("SELECT %(response)s AS response FROM DUAL;",
                                   parameters=params)
        self.assertEqual(({'RESPONSE': 42},), result)

    def test_run_unknown_command(self):
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        try:
            sqlplus.run_query("BAD SQL QUERY;")
            self.fail('Should have failed')
        except Exception, e:
            self.assertTrue("unknown command" in e.message)

    def test_run_unknown_command_disable(self):
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        result = sqlplus.run_query("SELECT '%s' AS message FROM DUAL;" %
                                   OracleResultParser.UNKNOWN_COMMAND,
                                   check_unknown_command=False)
        self.assertTrue(OracleResultParser.UNKNOWN_COMMAND in result[0]['MESSAGE'])

    def test_run_query_error(self):
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        try:
            sqlplus.run_query("SELECT 42 FROM DUO;")
            self.fail('Should have failed')
        except Exception, e:
            self.assertTrue("ERROR at line 1" in e.message)

    def test_run_query_empty(self):
        script = os.path.join(self.SQL_DIR, 'test_sqlplus_commando.sql')
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        sqlplus.run_script(script)
        result = sqlplus.run_query("INSERT INTO test (id, name, age) VALUES "
                                   "(2, 'Mignonne', 12);")
        self.assertEqual((), result)

    def test_run_script_nominal(self):
        script = os.path.join(self.SQL_DIR, 'test_sqlplus_commando.sql')
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        expected = ({'ID': 1, 'NAME': 'Réglisse', 'AGE': 14},)
        actual = sqlplus.run_script(script)
        self.assertEqual(expected, actual)

    def test_run_script_error(self):
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        try:
            sqlplus.run_script("unknown.sql")
            self.fail('Should have failed')
        except Exception, e:
            self.assertTrue("Script 'unknown.sql' was not found" in str(e))

    def test_run_script_syntax_error(self):
        script = os.path.join(self.SQL_DIR, 'test_sqlplus_commando_error.sql')
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        try:
            sqlplus.run_script(script)
            self.fail('Should have failed')
        except Exception, e:
            self.assertTrue("ORA-00942: table or view does not exist" in
                            e.message)

    def test_run_script_unknown_command(self):
        script = os.path.join(self.SQL_DIR,
                              'test_sqlplus_commando_unknown_command.sql')
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        try:
            sqlplus.run_script(script)
            self.fail('Should have failed')
        except Exception, e:
            self.assertTrue("unknown command" in e.message)

    def test_process_parameters(self):
        query = "%s %s %s"
        parameters = [1, 'deux', datetime.datetime(2014, 01, 22, 13, 10, 33)]
        expected = "1 'deux' '2014-01-22 13:10:33'"
        actual = SqlplusCommando._process_parameters(query, parameters)
        self.assertEqual(expected, actual)

    def test_cast(self):
        expected = 1
        actual = OracleResultParser._cast("1")
        self.assertEqual(expected, actual)
        expected = 1.23
        actual = OracleResultParser._cast("1,23")
        self.assertEqual(expected, actual)
        expected = 1.23e-45
        actual = OracleResultParser._cast("1,23e-45")
        self.assertEqual(expected, actual)
        expected = datetime.datetime(2014, 3, 29, 11, 18, 0)
        actual = OracleResultParser._cast('29/03/14 11:18:00,000000')
        self.assertEqual(expected, actual)
        expected = 'test'
        actual = OracleResultParser._cast('test')
        self.assertEqual(expected, actual)
        expected = None
        actual = OracleResultParser._cast('NULL')
        self.assertEqual(expected, actual)

    def test_cast_query(self):
        driver = SqlplusCommando(configuration=self.CONFIG)
        driver.run_script(os.path.join(self.SQL_DIR,
                                       'test_sqlplus_commando_cast_query.sql'))
        expected = (
            {'I': 123, 'F': 1.23,
             'D': datetime.datetime(2014, 3, 29, 11, 18, 0), 'S': 'test'},
            {'I': -456, 'F': -1.2e-34,
             'D': datetime.datetime(2014, 3, 29), 'S': 123},
        )
        actual = driver.run_query("SELECT i, f, d, s FROM test;", cast=True)
        self.assertEqual(expected, actual)
        driver.run_script(os.path.join(self.SQL_DIR,
                                       'test_sqlplus_commando_cast_query.sql'))
        expected = (
            {'I': '123', 'F': '1,23',
             'D': '29/03/14 11:18:00,000000', 'S': 'test'},
            {'I': '-456', 'F': '-1,200E-34',
             'D': '29/03/14 00:00:00,000000', 'S': '123'},
        )
        actual = driver.run_query("SELECT i, f, d, s FROM test;", cast=False)
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
