# Makefile for sqlplus_commando (see https://github.com/c4s4/make-tools)

# Parent makefiles at https://github.com/c4s4/make
include ~/.make/help.mk
include ~/.make/python.mk
include ~/.make/git.mk

release: clean lint test tag upload # Release project on Pypi
	@echo "$(YEL)Released project on Pypi$(END)"
