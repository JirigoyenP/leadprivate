CREATE TABLE IF NOT EXISTS keywords_used(
	fk_id_keyword_used INTEGER REFERENCES keywords(id_keyword),
	id_keyword_used SERIAL PRIMARY KEY,
	id_event INTEGER REFERENCES events(id_event)
);
CREATE TABLE IF NOT EXISTS keywords_found(
	fk_id_keyword_found INTEGER REFERENCES keywords(id_keyword),
	id_keyword_found SERIAL PRIMARY KEY,
	id_event INTEGER REFERENCES events(id_event)
);
