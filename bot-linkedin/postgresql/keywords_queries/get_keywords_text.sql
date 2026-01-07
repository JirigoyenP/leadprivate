CREATE OR REPLACE PROCEDURE sp_get_keywords_text( OUT array_keywords_text TEXT[])
LANGUAGE plpgsql

AS $$
	BEGIN/*  Selecciona y coloca todas las keywords no borradas en un array*/
		SELECT ARRAY_AGG(keyword_text)FROM keywords WHERE is_deleted=FALSE INTO array_keywords_text;
	END;
$$ ;