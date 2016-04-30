BEGIN
  FOR cur_rec IN (SELECT object_name, object_type
                  FROM   user_objects
                  WHERE  object_type IN ('TABLE', 'VIEW', 'PACKAGE', 'PROCEDURE', 'FUNCTION', 'SEQUENCE')) LOOP
    BEGIN
      IF cur_rec.object_type = 'TABLE' THEN
        EXECUTE IMMEDIATE 'DROP ' || cur_rec.object_type || ' "' || cur_rec.object_name || '" CASCADE CONSTRAINTS';
      ELSE
        EXECUTE IMMEDIATE 'DROP ' || cur_rec.object_type || ' "' || cur_rec.object_name || '"';
      END IF;
      EXCEPTION
      WHEN OTHERS THEN
      DBMS_OUTPUT.put_line('FAILED: DROP ' || cur_rec.object_type || ' "' || cur_rec.object_name || '"');
    END;
  END LOOP;
END;
/
CREATE TABLE test (
  id   INTEGER     NOT NULL,
  name VARCHAR(50) NOT NULL,
  age  INTEGER     DEFAULT NULL,
  PRIMARY KEY (id)
);

INSERT INTO test (id, name, age) VALUES (1, 'Réglisse', 14);

SELECT id, name, age FROM test;
