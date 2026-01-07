
do $$
DECLARE
	new_user_name TEXT :='Nana';
	new_profile_link TEXT:='Entro';
	new_user_country TEXT:='llaalaal';
	new_id_user INTEGER;
BEGIN
		INSERT INTO users (user_name ,profile_link,user_country) VALUES(new_user_name, new_profile_link, new_user_country) 
		ON CONFLICT ON CONSTRAINT unique_profile_link
		DO 
			UPDATE  SET user_country = new_user_country 
			RETURNING id_user INTO new_id_user;

	RAISE NOTICE 'id: %', new_id_user;
END;
$$;
select * from users;
