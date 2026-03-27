-- Tworzenie schematu dla Metabase
CREATE SCHEMA IF NOT EXISTS metabase;
GRANT ALL ON SCHEMA metabase TO dashboard_admin;
ALTER USER dashboard_admin SET search_path = public, metabase;