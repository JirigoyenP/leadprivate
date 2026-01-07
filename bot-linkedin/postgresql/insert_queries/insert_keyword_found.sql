CREATE PROCEDURE sp_insert_keywords_found(IN keywords_found_array INTEGER[],IN id_event INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE 
	keyword_found INTEGER;
	BEGIN
		FOREACH keyword_found in ARRAY keywords_found_array LOOP
			INSERT INTO(fk_id_event,fk_id_keyword_found)keywords_found VALUES(id_event,keyword_found);
		END LOOP;
	END;
$$;