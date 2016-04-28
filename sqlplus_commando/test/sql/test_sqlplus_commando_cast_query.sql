DROP TABLE IF EXISTS test;

CREATE TABLE test
  (i INTEGER, f FLOAT, d DATETIME, s VARCHAR(255));

INSERT INTO test
  (i, f, d, s)
VALUES
  (123, 1.23, '2014-03-29 11:18:00', 'test'),
  (-456, -1.2e-34, '2014-03-29', ' 123');
