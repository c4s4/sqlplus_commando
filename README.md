sqlplus_commando
================

Installing a Oracle driver on a machine is sometime a pain, or even impossible.
Furthermore you may want to distribute self contained scripts that access Oracle
without having to ask for additional software installation.

**sqlplus_commando** is a pure Python Oracle driver that calls Oracle running
*sqlplus* on the command line. It was designed so that you may use it by
dropping its module in your source tree or even copy its class in your own
source code.

Installation
------------

To install **sqlplus_commando**, you may use one of the following methods:

- Extract classes `SqlplusCommando` and `OracleParser` from tarball (in file
  *sqlplus_commando/sqlplus_commando.py*) and put it in your own source code.
- Drop its module (file *sqlplus_commando/sqlplus_commando.py* in the tarball)
  in your source directory.
- Install it using PIP, typing `pip install sqlplus_commando`.
- Install from tarball typing `python setup.py install`.

The Apache license grants you a right to use this driver in any of your project
(even commercial) provided that you mention that you are using
**sqlplus_commando** in your copyright notice.

Usage
-----

You can use this driver in your code just like so::

```python
from sqlplus_commando import SqlplusCommando

mysql = SqlplusCommando(hostname='localhost', database='test',
                        username='test', password='test')
result = mysql.run_query("SELECT 42 AS response, 'This is a test' AS question FROM DUAL;")
print result
```

When query returns nothing (after an `INSERT` for instance), method
`run_query()` will return an empty tuple `()`. If query returns a result set,
this will be a tuple of dictionaries. For instance, previous sample code could
print:

```python
({'RESPONSE': 42, 'QUESTION': 'This is a test'},)
```

Instead of running a query you may run a script as follows::

```python
result = mysql.run_script('my_script.sql')
```

Parameters
----------

You can have values such as `%(foo)s` in you query that will be replaced
with corresponding value of the parameters dictionary. For instance::

```python
from mysql_commando import MysqlCommando

mysql = MysqlCommando(hostname='localhost', database='test',
                      username='test', password='test')
parameters = {'name': 'reglisse'}
result = mysql.run_query(query="SELECT * FROM animals WHERE name=%(name)s",
                         parameters=parameters)
print result
```

You may not provide parameters running a script. To do so, call `run_query()`
with parameters passing query `open('my_script.sql').read()`.

Result set types
----------------

**mysql_commando** performs auto casting before returning result sets. As it
calls MySQL on command line, every value in the result set is a string. For
convenience, it casts integers, floats, dates and NULL into native Python types.

There are situations where this might not be accurate. For instance, if a column
is of SQL type `VARCHAR(10)` and contain phone numbers, all its values will be
casted to Python integers. It should not because phone numbers can start with
*0* and it should not be turned to integer.

To avoid this, you may pass `cast=False` when calling `run_query()` or
`run_script()`, like so:

```python
from mysql_commando import MysqlCommando

mysql = MysqlCommando(hostname='localhost', database='test',
                      username='test', password='test')
result = mysql.run_query("SELECT phone FROM users WHERE name='bob')", cast=False)
print result
```

You may also disable casting when instantiating the driver, passing
`cast=False` to the constructor. This casting configuration will apply on all
calls to `run_query()` or `run_script()` except if you pass a different
value while calling these methods.

Note
----

This module is not intended to replace an genuine Oracle driver that you
**SHOULD** use if you can install it on the target machine.

Enjoy!
