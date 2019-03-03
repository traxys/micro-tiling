/*
 * config.c - read the config file for the gofish gopher daemon
 * Copyright (C) 2000-2008  Sean MacLennan <seanm@seanm.ca>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this project; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>
#include <fcntl.h>
#include <assert.h>
#include <syslog.h>
#include <signal.h>
#include <errno.h>

#include "gofish.h"


char *root_dir;
char *logfile;
char *pidfile;
char *hostname;
char *tmpdir;

int   port = GOPHER_PORT;
char *user = GOPHER_USER;
uid_t uid  = GOPHER_UID;
gid_t gid  = GOPHER_GID;
int   ignore_local  = IGNORE_LOCAL;
int   icon_width    = ICON_WIDTH;
int   icon_height   = ICON_HEIGHT;
int   virtual_hosts;
int   combined_log;
int   is_gopher     = 1;
int   htmlizer      = 1;
int   max_conns     = 25;
int   process_cache;
int   do_chroot     = 1;
int   user_dirs;


/* If we are already out of memory, we are in real trouble */
char *must_strdup(char *str)
{
	char *new = strdup(str);
	if (!new) {
		syslog(LOG_ERR, "read_config: out of memory");
		exit(1);
	}
	return new;
}


/* only set if a number specified */
void must_strtol(char *str, int *value)
{
	char *end;
	long n = strtol(str, &end, 0);
	if (str != end)
		*value = (int)n;
}


char *must_alloc(int size)
{
	char *mem;

	mem = calloc(size, 1);
	if (mem == NULL) {
		syslog(LOG_ERR, "Out of memory.");
		exit(1);
	}

	return mem;
}


int read_config(char *fname)
{
	FILE *fp;
	char line[100], *s, *p;

	/* These values must be malloced */
	user = must_strdup(user);

	fp = fopen(fname, "r");
	if (fp) {
		while (fgets(line, sizeof(line), fp)) {
			if (!isalpha((int)*line))
				continue;

			for (p = line + strlen(line);
			     isspace((int)*(p - 1)); --p)
				;
			*p = '\0';

			p = strchr(line, '=');
			if (p == NULL) {
				printf("Bad line '%s'\n", line);
				continue;
			}
			s = p++;

			while (isspace((int)*(s - 1)))
				--s;
			*s++ = '\0';

			while (isspace((int)*p))
				++p;
			if (*p == '\0') {
				printf("No value for '%s'\n", line);
				continue;
			}

			/* Convert _ to - */
			for (s = line; (s = strchr(s, '_')); ++s)
				*s = '-';

			if (strcmp(line, "root") == 0) {
				if (root_dir)
					free(root_dir);
				root_dir = must_strdup(p);
			} else if (strcmp(line, "logfile") == 0) {
				if (logfile)
					free(logfile);
				logfile = must_strdup(p);
			} else if (strcmp(line, "pidfile") == 0) {
				if (pidfile)
					free(pidfile);
				pidfile = must_strdup(p);
			} else if (strcmp(line, "tmpdir") == 0) {
				if (tmpdir)
					free(tmpdir);
				tmpdir = must_strdup(p);
			} else if (strcmp(line, "port") == 0)
				must_strtol(p, &port);
			else if (strcmp(line, "listen-address") == 0)
				set_listen_address(p);
			else if (strcmp(line, "user") == 0) {
				if (user)
					free(user);
				user = must_strdup(p);
			} else if (strcmp(line, "uid") == 0)
				must_strtol(p, (int *)&uid);
			else if (strcmp(line, "gid") == 0)
				must_strtol(p, (int *)&gid);
			else if (strcmp(line, "no-local") == 0)
				must_strtol(p, &ignore_local);
			else if (strcmp(line, "locals") == 0) {
				must_strtol(p, &ignore_local);
				ignore_local = !ignore_local;
			} else if (strcmp(line, "host") == 0) {
				if (hostname)
					free(hostname);
				hostname = must_strdup(p);
			} else if (strcmp(line, "icon-width") == 0)
				must_strtol(p, &icon_width);
			else if (strcmp(line, "icon-height") == 0)
				must_strtol(p, &icon_height);
			else if (strcmp(line, "mimefile") == 0)
				set_mime_file(p);
			else if (strcmp(line, "virtual-hosts") == 0)
				must_strtol(p, &virtual_hosts);
			else if (strcmp(line, "combined-log") == 0)
				must_strtol(p, &combined_log);
			else if (strcmp(line, "is-http") == 0) {
				int is_http = -1;
				must_strtol(p, &is_http);
				if (is_http != -1)
					is_gopher = !is_http;
			} else if (strcmp(line, "mmap-cache-size") == 0) {
#ifdef MMAP_CACHE
				must_strtol(p, &mmap_cache_size);
#endif
			} else if (strcmp(line, "htmlize") == 0)
				must_strtol(p, &htmlizer);
			else if (strcmp(line, "max-connections") == 0)
				must_strtol(p, &max_conns);
			else if (strcmp(line, "html-header-file") == 0)
				http_set_header(p, 1);
			else if (strcmp(line, "html-trailer-file") == 0)
				http_set_header(p, 0);
			else if (strcmp(line, "preprocess-cache") == 0)
				must_strtol(p, &process_cache);
			else if (strcmp(line, "chroot") == 0)
				must_strtol(p, &do_chroot);
			else if (strcmp(line, "user-dirs") == 0)
				user_dirs = 1;
			else
				printf("Unknown config '%s'\n", line);
		}

		fclose(fp);
	} else if (errno != ENOENT || strcmp(fname, GOPHER_CONFIG)) {
		syslog(LOG_WARNING, "%s: %m", fname);
		return 1;
	}

	if (user_dirs && do_chroot) {
		syslog(LOG_ERR,
		       "user_dirs and chroot are mutually exclusive.\n");
		exit(1);
	}

	/* Make sure hostname is set to something */
	/* Make sure it is malloced */
	if (hostname == NULL) {
#ifdef GOPHER_HOST
		hostname = must_strdup(GOPHER_HOST);
#else
		if (gethostname(line, sizeof(line) - 1)) {
			puts("Warning: setting hostname to localhost.\n"
				 "This is probably not what you want.");
			strcpy(line, "localhost");
		}
		hostname = must_strdup(line);
#endif
	}

	/* Default'em */
	if (root_dir == NULL)
		root_dir = must_strdup(GOPHER_ROOT);
	if (logfile == NULL)
		logfile  = must_strdup(GOPHER_LOGFILE);
	if (pidfile == NULL)
		pidfile  = must_strdup(GOPHER_PIDFILE);
	if (tmpdir == NULL) {
		tmpdir = getenv("TMPDIR");
		if (!tmpdir)
			tmpdir = "/tmp";
		tmpdir = must_strdup(tmpdir);
	}

	if (strlen(root_dir) >= PATH_MAX) {
		printf("Root directory too long\n");
		exit(1);
	}

	return 0;
}

/*
 * Kernel coding standard.
 * Local Variables:
 * tab-width: 8
 * c-basic-offset: 8
 * indent-tabs-mode: t
 * End:
 */
