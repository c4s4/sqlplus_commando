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
CREATE TABLE test
  (i INTEGER, f FLOAT, d TIMESTAMP, s VARCHAR(255));

INSERT INTO test
  (i, f, d, s)
VALUES
  (123, 1.23, to_timestamp('2014-03-29 11:18:00', 'YYYY-MM-DD HH24:MI:SS'), 'test');
INSERT INTO test
  (i, f, d, s)
VALUES
  (-456, -1.2e-34, to_timestamp('2014-03-29', 'YYYY-MM-DD'), '  123');
