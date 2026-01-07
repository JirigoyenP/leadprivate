
CREATE OR REPLACE PROCEDURE sp_insert_event(OUT id_event INTEGER, 
										 IN new_user_name TEXT, IN new_profile_link TEXT, IN new_user_country TEXT,
										 IN post_text TEXT,  register_time TIMESTAMP, IN post_time TIMESTAMP,
										 IN amount_comments INTEGER,
										   IN keywords_found_array INTEGER[],
										   IN keywords_used_array INTEGER[])
LANGUAGE plpgsql

AS $$
	DECLARE 
		id_user INTEGER;
		new_id_event INTEGER;
	BEGIN
		CALL sp_insert_user(new_user_name , new_profile_link , new_user_country , id_user);/*agregar parametros*/
		INSERT INTO events (fk_id_user,post_text, register_time,
							post_time, amount_comments)
		VALUES(id_user, post_text, register_time, post_time, amount_comments) 
		RETURNING id_event INTO new_id_event;
		CALL sp_insert_keywords_found(keywords_found_array, new_id_event);
		CALL sp_insert_keywords_used(keywords_used_array, new_id_event);

		
	END;
$$;
