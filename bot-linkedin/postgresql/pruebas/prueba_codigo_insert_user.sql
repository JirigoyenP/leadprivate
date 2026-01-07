DO $$
DECLARE 
	new_id_user INTEGER :=1;
	new_user_name TEXT :='codsrueba';
	new_profile_link TEXT :='linkdPrueba';
BEGIN
	INSERT INTO users  VALUES(new_user_name, new_profile_link);
	SELECT id_user INTO new_id_user FROM users WHERE user_name=new_user_name AND profile_link = new_profile_link ;
EXCEPTION WHEN unique_violation THEN
	SELECT id_user INTO new_id_user FROM users WHERE user_name=new_user_name AND profile_link = new_profile_link;
	INSERT INTO users(user_name, profile_link) VALUES ('Nl','Entrp');
END $$;
Select * from users;


	