DO $$
DECLARE 
	keyword_used INTEGER;
	keywords_used_array INTEGER[]:=array[1,2,3];
BEGIN
	FOREACH keyword_used in ARRAY keywords_used_array LOOP
			/*INSERT INTO keywords_used VALUES(1,keyword_used);*/
			RAISE NOTICE '%', keyword_used;
	END LOOP;
END;
$$;
