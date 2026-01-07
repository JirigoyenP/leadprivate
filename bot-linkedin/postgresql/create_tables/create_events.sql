/*drop table events2*/
CREATE TABLE IF NOT EXISTS  events(
	id_event SERIAL PRIMARY KEY,
	post_text TEXT UNIQUE NOT NULL,	
	register_time TIMESTAMP NOT NULL,
	post_time TIMESTAMP NOT NULL,
	post_link TEXT,
	amount_comments INTEGER NOT NULL,
	post_status VARCHAR(9) DEFAULT 'En Notion',
	is_deleted BOOLEAN DEFAULT FALSE,
	fk_id_user INTEGER REFERENCES users(id_user)
	
);
