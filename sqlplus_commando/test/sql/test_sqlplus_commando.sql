DROP TABLE IF EXISTS test;

CREATE TABLE test (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(50) COLLATE utf8_bin NOT NULL,
  age int(11) DEFAULT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

INSERT INTO test (name, age) VALUES ('Réglisse', 14);

SELECT * FROM test;
