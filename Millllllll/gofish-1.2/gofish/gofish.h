/*
 * gofish.h - defines for the gofish gopher daemon
 * Copyright (C) 2002-2008 Sean MacLennan <seanm@seanm.ca>
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2, or (at your option) any
 * later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 * for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this project; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */
#ifndef _GOFISH_H_
#define _GOFISH_H_

#include "config.h"

#include <unistd.h>
#include <time.h>
#include <sys/uio.h>

#ifdef HAVE_LIMITS_H
#include <limits.h>
#endif

#define MAX_HOSTNAME	65
#define MAX_LINE	1280
#define MIN_REQUESTS	4
#define GOPHER_BACKLOG	100 /* helps when backed up */

/*
 * Simplistic connection timeout mechanism.
 * Every connection has a `last access time' associated with it. An
 * access is a new connection, a read, or a write. When we have been
 * idle for POLL_TIMEOUT seconds, we check all the connections. If a
 * connection has been idle for more than MAX_IDLE_TIME, we close the
 * connection.
 */
#define POLL_TIMEOUT	 1	/* seconds */
#define MAX_IDLE_TIME	60	/* seconds */


/* If you leave GOPHER_HOST unset, it will default to your
 * your hostname. */
#define GOPHER_LOGFILE	LOCALSTATEDIR "/log/gofish.log"
#define GOPHER_PIDFILE	LOCALSTATEDIR "/run/gofish.pid"
#define GOPHER_CONFIG	SYSCONFDIR "/gofish.conf"
/* #define GOPHER_HOST		"" */
#define GOPHER_PORT		70

/* Supplied icons are this size */
#define ICON_WIDTH		24
#define ICON_HEIGHT		23


/* Set to 1 to not log the local network (192.168.x.x).
 * Set to 0 to log everything. Do not undefine.
 */
#define IGNORE_LOCAL	1

#define GOPHER_UID		-1
#define GOPHER_GID		-1


/*
 * Size of the mmap cache (i.e. max number of mmaps to cache).
 * This number must be >= MAX_REQUESTS.
 * Can be overridden with config file option.
 * This only has meaning if MMAP_CACHE defined.
 */
#define MMAP_CACHE_SIZE	1000


struct connection {
	int conn_n;
#ifdef HAVE_POLL
	struct pollfd *ufd;
#else
	int sock;
#endif
	unsigned addr;
	char *cmd;
	off_t offset;
	unsigned len;
	unsigned char *buf;
	unsigned mapped;
	int   status;
	struct iovec iovs[4];
	int n_iovs;

	time_t access;

	/* http stuff */
	int http;
#define	HTTP_GET	1
#define HTTP_HEAD	2
	char *host;       /* vhost only */
	char *user_agent; /* combined log only */
	char *referer;    /* combined log only */
	char *http_header;
	char *html_header;
	char *html_trailer;
	char *outname;
};


/* exported from gofish.c */
extern int verbose;

void close_connection(struct connection *conn, int status);
int checkpath(char *path);

/* exported from log.c */
int  log_open(char *log_name);
void log_hit(struct connection *conn, unsigned status);
void log_close(void);
void send_error(struct connection *conn, unsigned error);

/* exported from socket.c */
int listen_socket(int port);
int accept_socket(int sock, unsigned *addr);
char *ntoa(unsigned n); /* helper */
void set_listen_address(char *addr);


/* exported from config.c */
extern char *config;
extern char *root_dir;
extern char *logfile;
extern char *pidfile;
extern char *hostname;
extern char *tmpdir;
extern int   port;
extern char *user;
extern uid_t uid;
extern gid_t gid;
extern int   ignore_local;
extern int   icon_width;
extern int   icon_height;
extern int   virtual_hosts;
extern int   combined_log;
extern int   is_gopher;
extern int   htmlizer;
extern int   max_conns;
extern int   process_cache;
extern int   do_chroot;
extern int   user_dirs;


int read_config(char *fname);
char *must_strdup(char *str);
char *must_alloc(int size);


/* exported from http.c */
int http_init(void);
void http_cleanup(void);
int http_get(struct connection *conn);
int http_send_response(struct connection *conn);
int http_error(struct connection *conn, int status);
void http_set_header(char *fname, int header);
int smart_open(char *name, char *type);

/* exported from mime.c */
void mime_init(void);
char *mime_find(char *fname);
void mime_cleanup(void);
void set_mime_file(char *fname);



/* exported from mmap_cache.c */
extern unsigned bad_munmaps;
extern int mmap_cache_size;
void mmap_init(void);
unsigned char *mmap_get(struct connection *conn, int fd);
void mmap_release(struct connection *conn);
int READ(int handle, char *whereto, int len);
int WRITE(int handle, char *whereto, int len);

int file_open(char *name);
FILE *file_fopen(char *fname);


#ifdef HAVE_POLL
#include <sys/poll.h>

#define SOCKET(c)	((c)->ufd->fd)

#define set_readable(c, sock)				\
	do {						\
		(c)->ufd->fd = sock;			\
		(c)->ufd->events = POLLIN;		\
		if ((c)->conn_n + 2 > npoll)		\
			npoll = (c)->conn_n + 2;	\
	} while (0)

#define set_writeable(c)			\
	do {					\
		(c)->ufd->events = POLLOUT;	\
	} while (0)

#else

#define SOCKET(c)	((c)->sock)

#define set_readable(c, sock)			\
	do {					\
		(c)->sock = sock;		\
		FD_SET(sock, &readfds);		\
		if (sock + 1 > nfds)		\
			nfds = sock + 1;	\
	} while (0)

void set_writeable(struct connection *conn);

#endif

#ifndef HAVE_DAEMON
int daemon(int nochdir, int noclose);
#endif

#endif /* _GOFISH_H_ */

/*
 * Kernel coding standard.
 * Local Variables:
 * tab-width: 8
 * c-basic-offset: 8
 * indent-tabs-mode: t
 * End:
 */
