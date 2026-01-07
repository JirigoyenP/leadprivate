CREATE OR REPLACE PROCEDURE sp_add_keywords(IN add_keyword_text TEXT)
LANGUAGE plpgsql
AS $$
	BEGIN/*Agrega una palabra que existe*/
		INSERT INTO keywords(keyword_text) VALUES (add_keyword_text);
	EXCEPTION WHEN unique_violation THEN /*Ya está agregada la keyword*/
		UPDATE keywords SET is_deleted=FALSE WHERE keyword_text=add_keyword_text;
	END;
$$;