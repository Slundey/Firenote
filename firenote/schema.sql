DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE note (
  uid int,
  content text,
  -- maybe include some metadata

  FOREIGN KEY (uid) REFERENCES user(id) ON DELETE CASCADE
)