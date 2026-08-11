-- Runs once, on first container init (fresh volume), alongside the POSTGRES_DB database.
-- Gives the `test` config profile its own isolated database.
CREATE DATABASE ai200_test;
