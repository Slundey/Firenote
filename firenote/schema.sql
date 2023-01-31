DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS directory;
DROP TABLE IF EXISTS config;

CREATE TABLE users (
  username TEXT PRIMARY KEY,
  password TEXT NOT NULL
);

CREATE TABLE notes (
  id TEXT PRIMARY KEY,
  title TEXT,
  content TEXT,
  
  user TEXT,
  dir TEXT,

  FOREIGN KEY (user) REFERENCES users(username),
  FOREIGN KEY (dir) REFERENCES directory(id)
);

CREATE TABLE directory (
  id TEXT PRIMARY KEY,
  name TEXT,
  parent TEXT DEFAULT NULL,

  FOREIGN KEY (parent) REFERENCES directory(id)
);

CREATE TABLE config (
	user TEXT PRIMARY KEY,

	darktheme INTEGER DEFAULT 0,
  bluelight INTEGER DEFAULT 0,
  autosave INTEGER DEFAULT 1,

  FOREIGN KEY (user) REFERENCES users(username) ON DELETE CASCADE
);

-- autuosave table?