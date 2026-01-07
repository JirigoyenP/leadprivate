CREATE OR REPLACE PROCEDURE sp_get_keywords_id( OUT array_keywords_id TEXT[])
LANGUAGE plpgsql

AS $$
	BEGIN/*  Selecciona y coloca todas las keywords no borradas en un array*/
		SELECT ARRAY_AGG(id_keyword)FROM keywords WHERE is_deleted=FALSE INTO array_keywords_id;
	END;
$$ ;