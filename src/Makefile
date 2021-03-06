###########################################################################
# Copyright (C) 2016 The Crown (i.e. Her Majesty the Queen in Right of Canada)
#
# This file is an add-on to RAVE.
#
# RAVE is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# RAVE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with RAVE.  If not, see <http://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------
# 
# rb52odim Makefile
# @file
# @author Daniel Michelson and Peter Rodriguez, Environment Canada
# @date 2016-08-17
#
###########################################################################
-include $(RAVEROOT)/rave/mkf/def.mk

RB52ODIMINC= -I. $(NUMPY_INCLUDE_DIR) $(INCLUDE_PYTHON) \
		-I$(HLHDF_INCLUDE_DIR) $(ZLIB_INCDIR) $(HDF5_INCDIR) \
		$(PROJ_INCLUDE_DIR) $(RAVE_INCLUDE_FLAG) \
		-I/usr/include/libxml2

LDFLAGS+= -L. -L$(HLHDF_LIB_DIR) $(ZLIB_LIBDIR) $(HDF5_LIBDIR) $(PROJ_LIB_DIR) \
		$(RAVE_LIB_FLAG)

ifeq ($(EXPAT_SUPPRESSED), no)
RB52ODIMINC+= $(EXPAT_INCLUDE_DIR)
LDFLAGS+= $(EXPAT_LIB_DIR)
endif

ifeq ($(BUFR_SUPPRESSED), no)
RB52ODIMINC+= $(BUFR_INCLUDE_DIR)
LDFLAGS+= $(BUFR_LIB_DIR)
endif

CFLAGS=	$(OPTS) $(CCSHARED) $(DEFS) $(CREATE_ITRUNC) $(RB52ODIMINC) -O0

# --------------------------------------------------------------------
# Fixed definitions

RB52ODIMSOURCES= rb52odim.c time_utils.c xml_utils.c RAVE_rb5_utils.c
INSTALL_HEADERS= rb52odim.h time_utils.h xml_utils.h rb5_utils.h
RB52ODIMOBJS= $(RB52ODIMSOURCES:.c=.o)
LIBRB52ODIM= librb52odim.so
RB52ODIMLIBS= -lrb52odim $(RAVE_MODULE_LIBRARIES) -lm -lz -lxml2

MAKEDEPEND=gcc -MM $(CFLAGS) -o $(DF).d $<
DEPDIR=.dep
DF=$(DEPDIR)/$(*F)
# --------------------------------------------------------------------
# Rules

# Contains dependency generation as well, so if you are not using
# gcc, comment out everything until the $(CC) statement.
%.o : %.c
	@$(MAKEDEPEND); \
	cp $(DF).d $(DF).P; \
	sed -e 's/#.*//' -e 's/^[^:]*: *//' -e 's/ *\\$$//' \
		-e '/^$$/ d' -e 's/$$/ :/' < $(DF).d >> $(DF).P; \
	\rm -f $(DF).d
	$(CC) -c $(CFLAGS) $<

# Ensures that the .dep directory exists
.PHONY=$(DEPDIR)
$(DEPDIR):
	+@[ -d $@ ] || mkdir -p $@

.PHONY=all
all:		$(LIBRB52ODIM)

$(LIBRB52ODIM): $(DEPDIR) $(RB52ODIMOBJS) 
	$(LDSHARED) -o $@ $(RB52ODIMOBJS)

.PHONY=install
install:
	@"$(HLHDF_INSTALL_BIN)" -f -o -C $(LIBRB52ODIM) "$(prefix)/lib/$(LIBRB52ODIM)"
	@for i in $(INSTALL_HEADERS) ; \
	do \
		"$(HLHDF_INSTALL_BIN)" -f -o -m644 -C $$i "$(prefix)/include/$$i"; \
	done

.PHONY=clean
clean:
		@\rm -f *.o core *~
		@\rm -fr $(DEPDIR)

.PHONY=distclean		 
distclean:	clean
		@\rm -f *.so

# NOTE! This ensures that the dependencies are setup at the right time so this should not be moved
-include $(RB52ODIMSOURCES:%.c=$(DEPDIR)/%.P)
