---
type: sqlite_table
database: hospital.db
table: doctors
title: doctors table
description: Doctors, specialties, hospital names, offices, and contact details.
tags:
- sqlite
- schema
- doctors
columns:
- name: doctor_id
  type: VARCHAR(10)
  primary_key: true
  not_null: false
- name: name
  type: VARCHAR(50)
  primary_key: false
  not_null: true
- name: specialty
  type: VARCHAR(50)
  primary_key: false
  not_null: true
- name: hospital_name
  type: VARCHAR(100)
  primary_key: false
  not_null: true
- name: office
  type: VARCHAR(20)
  primary_key: false
  not_null: true
- name: phone
  type: VARCHAR(20)
  primary_key: false
  not_null: true
- name: email
  type: VARCHAR(100)
  primary_key: false
  not_null: true
foreign_keys: []
---

# doctors

Doctors, specialties, hospital names, offices, and contact details.

## Columns

| Name | Type | Primary Key | Not Null |
| --- | --- | --- | --- |
| `doctor_id` | `VARCHAR(10)` | true | false |
| `name` | `VARCHAR(50)` | false | true |
| `specialty` | `VARCHAR(50)` | false | true |
| `hospital_name` | `VARCHAR(100)` | false | true |
| `office` | `VARCHAR(20)` | false | true |
| `phone` | `VARCHAR(20)` | false | true |
| `email` | `VARCHAR(100)` | false | true |
