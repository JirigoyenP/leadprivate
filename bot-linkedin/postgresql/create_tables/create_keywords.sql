DROP TABLE keywords2;
CREATE TABLE keywords(
	id_keyword SERIAL PRIMARY KEY,
	keyword_text TEXT UNIQUE,
	is_deleted BOOLEAN DEFAULT FALSE
);