CREATE TABLE IF NOT EXISTS specific_searches(
	id_specific_search SERIAL PRIMARY KEY,
	fk_id_person_searched INTEGER REFERENCES users(id_user),
	fk_id_owner_post INTEGER REFERENCES users(id_user),
	post_text TEXT UNIQUE,
	register_time TIMESTAMP NOT NULL,
	post_time TIMESTAMP NOT NULL,
	post_link TEXT DEFAULT NULL,
	post_status VARCHAR(9) DEFAULT 'En Notion',
	is_deleted BOOLEAN DEFAULT FALSE
);