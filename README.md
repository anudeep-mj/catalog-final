## Synopsis

This project is a small app which shows a catalog app which has crud and authentication funcationalities using 
Flask, sqllite and google api

## Pre-requisites
- Have sqlalchemy, flask, sqlalchemy.orm, oauth2client.client, httplib2, json, sqllite packages for python

## Installation

Git clone the project.  
run: python database_setup.py <- Sets up the database  
run: python datapopulation.py <- Populates test data  
run: python project.py  

## Functionalities

User can do the following functionalities:
- Add category
- Add category item
- Edit category item
- Delete category item
- See item description

## Authentication and Authorization features
- Google Authentication
- Authenticated users can only perform: Add, Edit and Delete category item
- A user can edit and delete only his own items
