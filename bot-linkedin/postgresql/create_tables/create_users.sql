CREATE TABLE users(
	id_user SERIAL PRIMARY KEY,
	user_name TEXT,
	user_profile_link TEXT UNIQUE,
	user_country TEXT
)