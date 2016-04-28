#!/usr/bin/env python
# encoding: UTF-8

import os
import unittest
from sqlplus_commando import SqlplusCommando


#pylint: disable=W0212
class TestSqlplusCommando(unittest.TestCase):

    CONFIG = {
        'hostname': 'localhost',
        'database': 'XE',
        'username': 'test',
        'password': 'test',
    }
    SQL_DIR = os.path.join(os.path.dirname(__file__), 'sql')

    def test_run_query_nominal(self):
        sqlplus = SqlplusCommando(configuration=self.CONFIG)
        result = sqlplus.run_query("SELECT 42 AS RESPONSE FROM DUAL;")
        self.assertEqual(({'RESPONSE': 42},), result)

    # def test_run_query_error(self):
    #     sqlplus = SqlplusCommando(configuration=self.CONFIG)
    #     try:
    #         sqlplus.run_query("BAD SQL QUERY;")
    #         self.fail('Should have failed')
    #     except Exception, e:
    #         self.assertTrue("You have an error in your SQL syntax" in e.message)
    #
    # def test_run_script_nominal(self):
    #     script = os.path.join(self.SQL_DIR, 'test_sqlplus_commando.sql')
    #     sqlplus = SqlplusCommando(configuration=self.CONFIG)
    #     expected = ({'id': 1, 'name': 'Réglisse', 'age': 14},)
    #     actual = sqlplus.run_script(script)
    #     self.assertEqual(expected, actual)
    #
    # def test_run_script_error(self):
    #     sqlplus = SqlplusCommando(configuration=self.CONFIG)
    #     try:
    #         sqlplus.run_script("script_that_doesnt_exist.sql")
    #         self.fail('Should have failed')
    #     except Exception, e:
    #         self.assertTrue("No such file or directory: 'script_that_doesnt_exist.sql'" in str(e))
    #
    # def test_run_script_syntax_error(self):
    #     script = os.path.join(self.SQL_DIR, 'test_sqlplus_commando_error.sql')
    #     sqlplus = SqlplusCommando(configuration=self.CONFIG)
    #     try:
    #         sqlplus.run_script(script)
    #         self.fail('Should have failed')
    #     except Exception, e:
    #         self.assertTrue("You have an error in your SQL syntax" in e.message)
    #
    # def test_process_parameters(self):
    #     query = "%s %s %s"
    #     parameters = [1, 'deux', datetime.datetime(2014, 01, 22, 13, 10, 33)]
    #     expected = "1 'deux' '2014-01-22 13:10:33'"
    #     actual = SqlplusCommando._process_parameters(query, parameters) #pylint: disable=W0212
    #     self.assertEqual(expected, actual)
    #
    # def test_cast(self):
    #     expected = 1
    #     actual = SqlplusCommando._cast("1")
    #     self.assertEqual(expected, actual)
    #     expected = 1.23
    #     actual = SqlplusCommando._cast("1.23")
    #     self.assertEqual(expected, actual)
    #     expected = 1.23e-45
    #     actual = SqlplusCommando._cast("1.23e-45")
    #     self.assertEqual(expected, actual)
    #     expected = datetime.datetime(2014, 3, 29, 11, 18, 0)
    #     actual = SqlplusCommando._cast('2014-03-29 11:18:00')
    #     self.assertEqual(expected, actual)
    #     expected = 'test'
    #     actual = SqlplusCommando._cast('test')
    #     self.assertEqual(expected, actual)
    #     expected = None
    #     actual = SqlplusCommando._cast('NULL')
    #     self.assertEqual(expected, actual)
    #
    # def test_cast_query(self):
    #     driver = SqlplusCommando(configuration=self.CONFIG)
    #     driver.run_script(os.path.join(self.SQL_DIR, 'test_sqlplus_commando_cast_query.sql'))
    #     expected = (
    #         {'i': 123, 'f': 1.23, 'd': datetime.datetime(2014, 3, 29, 11, 18, 0), 's': 'test'},
    #         {'i': -456, 'f': -1.2e-34, 'd': datetime.datetime(2014, 3, 29), 's': ' 123'},
    #     )
    #     actual = driver.run_query("SELECT i, f, d, s FROM test", cast=True)
    #     self.assertEqual(expected, actual)
    #     driver.run_script(os.path.join(self.SQL_DIR, 'test_sqlplus_commando_cast_query.sql'))
    #     expected = (
    #         {'i': '123', 'f': '1.23', 'd': '2014-03-29 11:18:00', 's': 'test'},
    #         {'i': '-456', 'f': '-1.2e-34', 'd': '2014-03-29 00:00:00', 's': ' 123'},
    #     )
    #     actual = driver.run_query("SELECT i, f, d, s FROM test", cast=False)
    #     self.assertEqual(expected, actual)
    #
    # def test_last_insert_id(self):
    #     driver = SqlplusCommando(configuration=self.CONFIG)
    #     driver.run_script(os.path.join(self.SQL_DIR, 'test_sqlplus_commando_last_insert_id.sql'))
    #     expected = 1
    #     actual = driver.run_query("INSERT INTO test (name, age) VALUES ('Reglisse', 14)", last_insert_id=True)
    #     self.assertEqual(expected, actual)
    #     expected = ({'id': 2},)
    #     actual = driver.run_script(os.path.join(self.SQL_DIR, 'test_sqlplus_commando_last_insert_id_insert.sql'))
    #     self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()

