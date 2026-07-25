/*
===============================================================================
DDL Script: Create file metadata table
===============================================================================
Script Purpose:
    This script creates a metadata table for the files already uploaded, dropping existing tables 
    if they already exist.
	  Run this script to re-define the DDL structure
===============================================================================
*/

DROP TABLE IF EXISTS file_metadata;

CREATE TABLE file_metadata(
    file_id SERIAL PRIMARY KEY,
    file_name TEXT
);