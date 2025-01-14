-- Table to store user details
CREATE TABLE users (
  id SERIAL PRIMARY KEY,  -- Auto-incremented user ID (Supabase will handle this)
  username VARCHAR(255),  -- Optional: can be used if users set a username
  email VARCHAR(255) UNIQUE NOT NULL,  -- User's email address (from OAuth)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Timestamp when user is created
  profile_pic VARCHAR,  -- URL of user's profile picture (optional)
  provider VARCHAR(50),  -- OAuth provider (e.g., 'google')
  provider_id VARCHAR(255) UNIQUE NOT NULL  -- User's unique ID from the OAuth provider
);

-- Table to store questions
CREATE TABLE questions (
  id SERIAL PRIMARY KEY,  -- Auto-incremented question ID
  title VARCHAR(255) NOT NULL,  -- Title of the question
  description TEXT NOT NULL,  -- Description of the question
  difficulty VARCHAR(20) DEFAULT 'easy' CHECK (difficulty IN ('easy', 'medium', 'hard')),  -- Difficulty level
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Timestamp when question is created
);

-- Table to store test cases associated with questions
CREATE TABLE test_cases (
  id SERIAL PRIMARY KEY,  -- Auto-incremented test case ID
  question_id INTEGER NOT NULL,  -- Reference to the question
  input TEXT NOT NULL,  -- Input for the test case
  expected_output TEXT NOT NULL,  -- Expected output for the test case
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Timestamp when test case is created
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE  -- Foreign key reference to questions
);

-- Table to store solutions submitted by users
CREATE TABLE solutions (
  id SERIAL PRIMARY KEY,  -- Auto-incremented solution ID
  user_id INTEGER NOT NULL,  -- Reference to the user who submitted the solution
  question_id INTEGER NOT NULL,  -- Reference to the question
  submitted_code TEXT NOT NULL,  -- Code submitted by the user
  is_correct BOOLEAN DEFAULT FALSE,  -- Whether the solution is correct or not
  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Timestamp when solution is submitted
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,  -- Foreign key reference to users
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE  -- Foreign key reference to questions
);

-- Table to track user activities (e.g., viewed, started, solved a question)
CREATE TABLE user_activity (
  id SERIAL PRIMARY KEY,  -- Auto-incremented activity ID
  user_id INTEGER NOT NULL,  -- Reference to the user
  question_id INTEGER NOT NULL,  -- Reference to the question
  activity_type VARCHAR(20) DEFAULT 'viewed' CHECK (activity_type IN ('viewed', 'started', 'solved')),  -- Type of activity
  activity_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Timestamp when activity occurred
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,  -- Foreign key reference to users
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE  -- Foreign key reference to questions
);
