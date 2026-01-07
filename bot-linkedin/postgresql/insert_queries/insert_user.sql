/*Borrar procedure*/
/*DROP PROCEDURE insert_users;*/
/*Insertar en la tabla users*/
CREATE OR REPLACE PROCEDURE sp_insert_user( IN new_user_name TEXT, IN new_profile_link TEXT, IN new_user_country TEXT,OUT new_id_user INTEGER)
LANGUAGE plpgsql

AS $$
	BEGIN/*  Si la persona no está agregada en la tabla users, se agrega y se retornael id*/
		INSERT INTO users (user_name ,user_profile_link,user_country) VALUES(new_user_name, new_profile_link, new_user_country) 
		ON CONFLICT ON CONSTRAINT unique_profile_link
		DO 
			UPDATE  SET user_country = new_user_country 
			RETURNING id_user INTO new_id_user;
		
	/*EXCEPTION WHEN unique_violation THEN  /*La persona está agregada, se actualiza la info y  se  retorna el id*/
		UPDATE users SET user_country = new_user_country WHERE user_name=new_user_name AND profile_link = new_profile_link
		RETURNING id_user into new_id_user;*/
	END;
$$ ;
call insert_user('funciono','larra', 'Peru',NULL);
/*delete from users where id_user=3
insert into users (user_name, profile_link) values ('prueba', 'prueba3');
 select * from users
alter table events
  drop constraint unique_profile_link;
ALTER TABLE users ADD CONSTRAINT unique_profile_link UNIQUE(profile_link);
ALTER TABLE users ADD COLUMN user_country TEXT DEFAULT NULL;*/