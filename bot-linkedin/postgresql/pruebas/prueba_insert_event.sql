DO 
$$
DECLARE 
	 new_user_name TEXT:='pruebaEvent';
	 new_profile_link TEXT:='pruebaEvent';
	 new_user_country TEXT:='pruebaEvent';
	 id_user INTEGER;
BEGIN
	CALL insert_user (new_user_name , new_profile_link , new_user_country, id_user );
	raise notice '%', id_user;
END;
$$;
Select *  from users;