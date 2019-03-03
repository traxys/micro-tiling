# Rules for GoFish gopher/web server

AUTOMAKE_OPTIONS = no-dependencies

DEFS = -DSYSCONFDIR=\"${sysconfdir}\" -DLOCALSTATEDIR=\"${localstatedir}\" \
       -DGOPHER_ROOT=\"@gopherroot@\"

sbin_PROGRAMS = gofish
gofish_SOURCES = gofish.c log.c socket.c config.c http.c mmap_cache.c mime.c

check_PROGRAMS = webtest
webtest_SOURCES=webtest.c socket.c

EXTRA_DIST = COPYING README INSTALL NEWS AUTHORS ChangeLog \
	init-gofish gofish.spec

man_MANS = gofish.1 gofish.5 dotcache.5 gopherd.1 mkcache.1

# Keep the old name around.
install-exec-hook:
	ln -s $(sbindir)/gofish $(DESTDIR)$(sbindir)/gopherd

# Do not override the gofish.conf or icons directories if they exist
install-data-local: install-root-dir
	$(mkinstalldirs) $(DESTDIR)$(sysconfdir)
	if test -f $(DESTDIR)$(sysconfdir)/gofish.conf; then \
	  $(INSTALL_DATA) gofish.conf $(DESTDIR)$(sysconfdir)/gofish.conf.new; \
	else \
	  $(INSTALL_DATA) gofish.conf $(DESTDIR)$(sysconfdir)/gofish.conf; \
	fi
	if test -f $(DESTDIR)$(sysconfdir)/gofish-www.conf; then \
	  $(INSTALL_DATA) gofish-www.conf $(DESTDIR)$(sysconfdir)/gofish-www.conf.new; \
	else \
	  $(INSTALL_DATA) gofish-www.conf $(DESTDIR)$(sysconfdir)/gofish-www.conf; \
	fi

# 1. Only install Configure_GoFish if /var/gopher does not exist.
#    We don't want to keep installing it for users who are upgrading.
# 2. Only install the .gopher+ file if it dosen't exist. We don't want to
#    override any user changes.
# 3. Only install icon directory if it dosen't exist. We don't want to
#    override any user installed icons.
install-root-dir:
	if test ! -d $(DESTDIR)$(gopherroot); then \
	  $(mkinstalldirs) $(DESTDIR)$(gopherroot); \
	  $(INSTALL_DATA) Configure_GoFish $(DESTDIR)$(gopherroot)/Configure_GoFish; \
	  $(INSTALL_DATA) _cache $(DESTDIR)$(gopherroot)/.cache; \
	fi
	if test ! -f $(DESTDIR)$(gopherroot)/.gopher+; then \
	  $(INSTALL_DATA) _gopher+ $(DESTDIR)$(gopherroot)/.gopher+; \
	fi
	if test ! -f $(DESTDIR)$(gopherroot)/icons; then \
	  $(mkinstalldirs) $(DESTDIR)$(gopherroot)/icons; \
	  $(INSTALL_DATA) $(srcdir)/icons/*.gif $(DESTDIR)$(gopherroot)/icons; \
	fi

# Do not remove the root_dir or any part of it
uninstall-local:
	rm -f  $(DESTDIR)$(sysconfdir)/gofish.conf
	rm -f  $(DESTDIR)$(sysconfdir)/gofish.conf.new
	rm -f  $(DESTDIR)$(sysconfdir)/gofish-www.conf
	rm -f  $(DESTDIR)$(sysconfdir)/gofish-www.conf.new

# Create version.h from gofish.spec
# Don't use BUILT_SOURCES
gofish.o http.o: version.h

version.h: gofish.spec
	@version=`fgrep Version: gofish.spec | cut -d' ' -f2`; \
	echo "#define GOFISH_VERSION \"$$version\"" > version.h; \
	echo "Updated version.h to $$version"

*.o: gofish.h config.h

# Extra helper programs

bin_PROGRAMS = mkcache
mkcache_SOURCES = mkcache.c config.c mime.c
bin_SCRIPTS = check-files
