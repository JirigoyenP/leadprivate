CREATE OR REPLACE PROCEDURE sp_insert_specific_search(IN id_person_searched INTEGER,
										 IN owner_post_name TEXT, IN owner_post_profile_link TEXT, IN owner_post_country TEXT,
										 IN post_text TEXT,  register_time TIMESTAMP, IN post_time TIMESTAMP,
										 IN amount_comments INTEGER)
LANGUAGE plpgsql
AS $$
	DECLARE
		owner_post_id INTEGER;
	BEGIN
		CALL sp_insert_user(owner_post_name,  owner_post_profile_link, owner_post_country, owner_post_id);
		INSERT INTO specific_searches(fk_id_person_searched, fk_id_owner_post, post_text, register_time,
									 post_time, post_link, post_status) 
		VALUES (id_person_searched, owner_post_id,post_text,  register_time,  post_time, amount_comments );
	END;
$$;