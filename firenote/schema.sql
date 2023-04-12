DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS config;
DROP TABLE IF EXISTS notes_genres;

CREATE TABLE users (
  username TEXT PRIMARY KEY,
  password TEXT NOT NULL
);

CREATE TABLE notes (
  id TEXT PRIMARY KEY,
  title TEXT,
  description TEXT,
  content TEXT,
  user TEXT,

  FOREIGN KEY (user) REFERENCES users(username)
);

CREATE TABLE genres (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT
);

CREATE TABLE notes_genres ( -- genres being: None, Home, Work, Writing, School, Shopping
  note_id TEXT,
  genre_id INTEGER,

  PRIMARY KEY (note_id, genre_id),
  FOREIGN KEY (note_id) REFERENCES notes(id),
  FOREIGN KEY (genre_id) REFERENCES genres(id)

);

CREATE TABLE config (
	user TEXT PRIMARY KEY,
	darktheme INTEGER DEFAULT 0,
  fontsize INTEGER DEFAULT 16,

  FOREIGN KEY (user) REFERENCES users(username) ON DELETE CASCADE
);

INSERT INTO genres (name) VALUES ('None');
INSERT INTO genres (name) VALUES ('Home');
INSERT INTO genres (name) VALUES ('Work');
INSERT INTO genres (name) VALUES ('Writing');
INSERT INTO genres (name) VALUES ('School');
INSERT INTO genres (name) VALUES ('Shopping');