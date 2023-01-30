CREATE TABLE user (
  user_id text PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  profile_pic TEXT,
  pwd TEXT
);
CREATE TABLE valid_tokens (
  token TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES user
);
CREATE TABLE projects (
  project_id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES user
  titile TEXT NOT NULL,
  description TEXT ,
);