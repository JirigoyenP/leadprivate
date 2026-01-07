CREATE PROCEDURE insert_keywords_used(IN keywords_used_array INTEGER[],IN id_event INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE 
	keyword_used INTEGER;
	BEGIN
		FOREACH keyword_used in ARRAY keywords_used_array LOOP
			INSERT INTO keywords_used VALUES(id_event,keyword_used);
		END LOOP;
	END;
$$;