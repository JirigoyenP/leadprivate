CREATE OR REPLACE PROCEDURE sp_delete_keywords(IN delete_keyword_text TEXT, OUT deleted_keyword_text TEXT)
LANGUAGE plpgsql
AS $$
	BEGIN/*Borra una palabra que existe*/
		UPDATE keywords SET is_deleted=TRUE
		WHERE keyword_text=delete_keyword_text
		RETURNING keyword_text INTO deleted_keyword_text;
		/*RAISE 'Se eliminó la keyword';*/
	/*EXCEPTION */
	END;
$$;
/*Si no existe la palabra UPDATE 0, si es que si, UPDATE 1*/
/*Si el dato ya está como se queire dejar, no pasa ningun error*/
/*UPDATE keywords set is_deleted=TRUE
WHERE keyword_text='UWU';*/