#! /usr/bin/make

check-source: flake8 mypy

flake8:
	flake8

mypy:
	mypy *.py
