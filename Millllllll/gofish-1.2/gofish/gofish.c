/*
 * gofish.c - the mainline for the gofish gopher daemon
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

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>
#include <fcntl.h>
#include <assert.h>
#include <syslog.h>
#include <signal.h>
#include <errno.h>
#include <sys/time.h>
#include <pwd.h>
#include <grp.h>
#include <sys/stat.h>
#include <sys/wait.h>

#include "gofish.h"
#include "version.h"

int verbose;

/* Stats */
static unsigned max_requests;
static unsigned max_length;
static unsigned n_requests;
static unsigned gopher_requests;
static int      n_connections; /* yes signed, I want to know if it goes -ve */
static time_t   started;

/* Add an extra connection for error replies */
static struct connection *conns;

#ifdef HAVE_POLL
static struct pollfd *ufds;
static int npoll;

static void start_polling(int csock);
#else
static fd_set readfds, writefds;
static int nfds;
static int accept_sock;

static void start_selecting(int csock);

void set_writeable(struct connection *conn)
{
	FD_CLR(conn->sock, &readfds);
	FD_SET(conn->sock, &writefds);
}
#endif


static uid_t root_uid;

/* forward references */
static void gofish(char *name);
static void create_pidfile(char *fname);
static int new_connection(int csock);
static int read_request(struct connection *conn);
static int write_request(struct connection *conn);
static int gofish_stats(struct connection *conn);
static void check_old_connections(void);
static int open_cache(char *fname);


/* SIGUSR1 is handled in log.c */
static void sighandler(int signum)
{
	switch (signum) {
	case SIGHUP:
	case SIGTERM:
	case SIGINT:
		/* Somebody wants us to quit */
		syslog(LOG_INFO, "GoFish stopping.");
		log_close();
		exit(0);
	case SIGPIPE:
		/* We get a SIGPIPE if the client closes the
		 * connection on us. */
		break;
	default:
		syslog(LOG_WARNING, "Got an unexpected %d signal\n", signum);
		break;
	}
}


static void cleanup(void)
{
	struct connection *conn;
	int i;

	http_cleanup();

#ifdef HAVE_POLL
	close(ufds[0].fd); /* accept socket */
#else
	close(accept_sock); /* accept socket */
#endif

	/*
	 * This is mainly for valgrind.
	 * Close any outstanding connections.
	 * Free any cached memory.
	 */
	for (conn = conns, i = 0; i < max_conns; ++i, ++conn) {
		if (SOCKET(conn) != -1)
			close_connection(conn, 500);
		if (conn->cmd)
			free(conn->cmd);
	}

	free(root_dir);
	free(hostname);
	free(logfile);
	free(pidfile);

	free(conns);
#ifdef HAVE_POLL
	free(ufds);
#endif

	mime_cleanup();

	closelog();
}


int main(int argc, char *argv[])
{
	char *config = GOPHER_CONFIG;
	int c, go_daemon = 0;
	char *prog;

	prog = strrchr(argv[0], '/');
	if (prog)
		++prog;
	else
		prog = argv[0];

	while ((c = getopt(argc, argv, "c:dm:pv")) != -1)
		switch (c) {
		case 'c':
			config = optarg;
			break;
		case 'd':
			go_daemon = 1;
			break;
		case 'm':
			max_conns = strtol(optarg, NULL, 0);
			break;
		case 'p':
			process_cache = 1;
			break;
		case 'v':
			++verbose;
			break;
		default:
			printf("usage: %s [-dpv] [-m max_conns] [-c config]\n",
			       *argv);
			exit(1);
		}

	if (read_config(config))
		exit(1);

	if (max_conns == 0)
		max_conns = 25;

	conns = calloc(max_conns, sizeof(struct connection));
	if (!conns) {
		syslog(LOG_CRIT, "Not enough memory."
		       " Try reducing max-connections.");
		exit(1);
	}

	mime_init();

	http_init();

	if (go_daemon) {
		if (daemon(0, 0) == -1)
			syslog(LOG_CRIT, "Could not become daemon-process!");
		else
			gofish(prog); /* never returns */
	} else
		gofish(prog); /* never returns */

	return 1;
}

static void setup_privs(void)
{
	root_uid = getuid();

	if (uid == (uid_t)-1 || gid == (uid_t)-1) {
		struct passwd *pwd = getpwnam(user);
		if (!pwd) {
			syslog(LOG_ERR, "No such user: `%s'.", user);
			closelog();
			exit(1);
		}
		if (uid == (uid_t)-1)
			uid = pwd->pw_uid;
		if (gid == (uid_t)-1)
			gid = pwd->pw_gid;
#ifdef HAVE_INITGROUPS
		initgroups(pwd->pw_name, pwd->pw_gid);
#endif
	}

	setgid(gid);
}

static void gofish(char *name)
{
	int csock, i;

	openlog(name, LOG_CONS, LOG_DAEMON);
	syslog(LOG_INFO, "GoFish " GOFISH_VERSION " (%s) starting.", name);
	time(&started);

	/* Create *before* chroot */
	create_pidfile(pidfile);

	if (chdir(root_dir)) {
		perror(root_dir);
		exit(1);
	}

	setup_privs();

	/* Do this *before* chroot */
	log_open(logfile);

	if (do_chroot && chroot(root_dir)) {
		perror("chroot");
		exit(1);
	} else
		syslog(LOG_WARNING, "No chroot.");

	signal(SIGHUP,  sighandler);
	signal(SIGTERM, sighandler);
	signal(SIGINT,  sighandler);
	signal(SIGPIPE, sighandler);
	signal(SIGCHLD, sighandler);

	/* connection socket */
	csock = listen_socket(port);
	if (csock < 0) {
		syslog(LOG_ERR, "Unable to create socket: %m");
		exit(1);
	}

	seteuid(uid);

	memset(conns, 0, sizeof(conns));
	for (i = 0; i < max_conns; ++i) {
		conns[i].status = 200;
		conns[i].conn_n = i;
	}

	mmap_init();

	/* These never return */
#ifdef HAVE_POLL
	start_polling(csock);
#else
	start_selecting(csock);
#endif
}


#ifdef HAVE_POLL
static void start_polling(int csock)
{
	struct connection *conn;
	int i, n;
	int timeout;

	ufds = calloc(max_conns + 1, sizeof(struct pollfd));
	if (!ufds) {
		syslog(LOG_CRIT, "Not enough memory."
		       " Try reducing max-connections.");
		exit(1);
	}

	for (i = 0; i < max_conns; ++i) {
		conns[i].ufd = &ufds[i + 1];
		conns[i].ufd->fd = -1;
	}

	/* Now it is safe to install */
	atexit(cleanup);

	ufds[0].fd = csock;
	ufds[0].events = POLLIN;
	npoll = 1;

	while (1) {
		timeout = n_connections ? (POLL_TIMEOUT * 1000) : -1;
		n = poll(ufds, npoll, timeout);
		if (n < 0) {
			syslog(LOG_WARNING, "poll: %m");
			continue;
		}

		/* Simplistic timeout to start with.
		 * Only check for old connections on a timeout.
		 * Low overhead, but under high load may leave connections
		 * around longer.
		 */
		if (n == 0) {
			check_old_connections();
			continue;
		}

		if (ufds[0].revents) {
			new_connection(ufds[0].fd);
			--n;
		}

		for (conn = conns, i = 0; n > 0 && i < npoll; ++i, ++conn)
			if (conn->ufd->revents & POLLIN) {
				read_request(conn);
				--n;
			} else if (conn->ufd->revents & POLLOUT) {
				write_request(conn);
				--n;
			} else if (conn->ufd->revents) {
				/* Error */
				int status;

				if (conn->ufd->revents & POLLHUP) {
					syslog(LOG_DEBUG, "Connection hung up");
					status = 504;
				} else if (conn->ufd->revents & POLLNVAL) {
					syslog(LOG_DEBUG, "Connection invalid");
					status = 410;
				} else {
					syslog(LOG_DEBUG, "Revents = 0x%x",
					       conn->ufd->revents);
					status = 501;
				}

				close_connection(conn, status);
				--n;
			}

		if (n > 0)
			syslog(LOG_DEBUG, "Not all requests processed");
	}
}

#else
static inline struct connection *find_conn(fd)
{
	int i;

	for (i = 0; i < max_conns; ++i)
		if (conns[i].sock == fd)
			return &conns[i];

	return NULL;
}


static void start_selecting(int csock)
{
	int n, fd;
	struct connection *conn;
	fd_set cur_reads, cur_writes;
	struct timeval *timeout, timeoutval;

	for (n = 0; n < max_conns; ++n)
		conns[n].sock = -1;

	FD_ZERO(&readfds);
	FD_ZERO(&writefds);

	FD_SET(csock, &readfds);
	nfds = csock + 1;

	accept_sock = csock;

	atexit(cleanup);


	while (1) {
		memcpy(&cur_reads,  &readfds, sizeof(fd_set));
		memcpy(&cur_writes, &writefds, sizeof(fd_set));

		if (n_connections) {
			/* We must reset the timeout every time! */
			timeoutval.tv_sec  = POLL_TIMEOUT;
			timeoutval.tv_usec = 0;
			timeout = &timeoutval;
		} else
			timeout = NULL;
		n = select(nfds, &cur_reads, &cur_writes, NULL, timeout);
		if (n < 0) {
			if (errno != EINTR)
				syslog(LOG_WARNING, "select: %m");
			continue;
		}

		/* Simplistic timeout to start with.
		 * Only check for old connections on a timeout.
		 * Low overhead, but under high load may leave connections
		 * around longer.
		 */
		if (n == 0) {
			check_old_connections();
			continue;
		}

		if (FD_ISSET(csock, &cur_reads)) {
			--n;
			FD_CLR(csock, &cur_reads);
			new_connection(csock);
		}

		for (fd = 0; n > 0 && fd < nfds; ++fd) {
			if (FD_ISSET(fd, &cur_reads)) {
				--n;
				conn = find_conn(fd);
				if (conn)
					read_request(conn);
			} else if (FD_ISSET(fd, &cur_writes)) {
				--n;
				conn = find_conn(fd);
				if (conn)
					write_request(conn);
			}
		}

		if (n > 0)
			syslog(LOG_DEBUG, "Not all requests processed");
	}
}
#endif

#ifdef ALLOW_NON_ROOT
static int checkpath(char *path)
{
#if 0
	/* This does not work in a chroot environment */
	char full[PATH_MAX + 2];
	char real[PATH_MAX + 2];
	int  len = strlen(root_dir);

	strcpy(full, root_dir);
	strcat(full, "/");
	strncat(full, path, PATH_MAX - len);
	full[PATH_MAX] = '\0';

	if (!realpath(full, real))
		return 1;

	if (strncmp(real, root_dir, len)) {
		errno = EACCES;
		return -1;
	}
#else
	/* A .. at the end is safe since it will never specify a file,
	 * only a directory. */
	if (strncmp(path, "../", 3) == 0 || (int)strstr(path, "/../")) {
		errno = EACCES;
		return -1;
	}
#endif

	return 0;
}
#endif


/* This handles parsing the name and opening the file We allow the
 * following /?<selector>/<path> || nothing Returns the selector type
 * in `selector'
 */
int smart_open(char *name, char *type)
{
	FILE *fp;
	int fd;
	struct stat sbuf;
	char dirname[MAX_LINE + 10], *p, *e;

	if (*name == '/')
		++name;

	/* This is worth optimizing */
	if (*name == '\0') {
		*type = '1';
		return open_cache(".cache");
	}

	/* Fast path - type specified */
	if (*(name + 1) == '/') {
		*type = *name;
		name += 2;

		switch (*type) {
		case '0':
		case '4':
		case '5':
		case '6':
		case '9':
		case 'g':
		case 'h':
		case 'I':
			return file_open(name);
		case '1':
			strcpy(dirname, name);
			p = dirname + strlen(dirname);
			if (*(p - 1) != '/')
				*p++ = '/';
			strcpy(p, ".cache");
			return open_cache(dirname);
		default:
			errno = EINVAL;
			return -1;
		}
	}

#ifndef STRICT_GOPHER
	/* Regular path */
	fd = file_open(name);
	if (fd < 0)
		return -1;

	if (fstat(fd, &sbuf)) {
		close(fd);
		return -1;
	}

	strcpy(dirname, name);

	if (S_ISDIR(sbuf.st_mode)) {
		*type = '1';
		close(fd);

		p = dirname + strlen(dirname);
		if (*(p - 1) != '/')
			*p++ = '/';
		strcpy(p, ".cache");
		return open_cache(dirname);
	}

	p = strrchr(dirname, '/');
	if (p)
		strcpy(p + 1, ".cache");
	else
		strcpy(dirname, ".cache");

	fp = file_fopen(dirname);
	if (!fp) {
		close(fd);
		return -1;
	}

	while (fgets(dirname, sizeof(dirname), fp)) {
		p = strchr(dirname, '\t');
		if (p) {
			p += 3;
			e = strchr(p, '\t');
			if (e) {
				*e = '\0';
				if (strcmp(name, p) == 0) {
					fclose(fp);
					*type = *dirname;
					return fd;
				}
			}
		}
	}

	fclose(fp);

	/* This works well for robots.txt and favicon.ico */
	*type = '0'; /* default */
	return fd;
#endif

	errno = EINVAL;
	return -1;
}


void close_connection(struct connection *conn, int status)
{
	if (verbose > 2)
		printf("Close request\n");

	--n_connections;

	if (conn->cmd) {
		/* Make we have a clean cmd */
		char *p;

		for (p = conn->cmd; *p && *p != '\r' && *p != '\n'; ++p)
			;
		*p = '\0';

		if (strncmp(conn->cmd, "GET ", 4) == 0 ||
		    strncmp(conn->cmd, "HEAD ", 5) == 0)
			conn->http = 1;
	}

	/* Log hits in one place. Do not log stat requests. */
	if (status != 1000) {
		log_hit(conn, status);

		/* Send gopher errors in one place also */
		if (status != 200 && status != 504 && !conn->http) {
			syslog(LOG_WARNING, "Gopher error %d http %d\n",
			       status, conn->http);
			send_error(conn, status);
		}
	}

	if (conn->conn_n > MIN_REQUESTS && conn->cmd) {
		free(conn->cmd);
		conn->cmd = NULL;
	}

	conn->len = conn->offset = 0;

	if (conn->buf) {
		mmap_release(conn);
		conn->buf = NULL;
	}

	if (SOCKET(conn) >= 0) {
		close(SOCKET(conn));
#ifdef HAVE_POLL
		conn->ufd->fd = -1;
		conn->ufd->revents = 0;
		while (npoll > 1 && ufds[npoll - 1].fd == -1)
			--npoll;
#else
		FD_CLR(conn->sock, &readfds);
		FD_CLR(conn->sock, &writefds);
		if (conn->sock >= nfds - 1)
			for (nfds = conn->sock - 1; nfds > 0; --nfds)
				if (FD_ISSET(nfds, &readfds) ||
				    FD_ISSET(nfds, &writefds)) {
					nfds++;
					break;
				}
		conn->sock = -1;
#endif
	}

	if (conn->http_header) {
		free(conn->http_header);
		conn->http_header = NULL;
	}
	if (conn->outname) {
		if (unlink(conn->outname))
			syslog(LOG_WARNING, "unlink %s: %m", conn->outname);
		free(conn->outname);
		conn->outname = NULL;
	}
	conn->html_header  = NULL;
	conn->html_trailer = NULL;

	conn->http = 0;
	conn->host = NULL;
	conn->referer = NULL;
	conn->user_agent = NULL;

	conn->status = 200;

	memset(conn->iovs, 0, sizeof(conn->iovs));

#ifdef HAVE_POLL
	ufds[0].events = POLLIN; /* in case we throttled */
#else
	FD_SET(accept_sock, &readfds);  /* in case we throttled */
#endif
}


static int new_connection(int csock)
{
	int sock;
	unsigned addr;
	int i;
	struct connection *conn;

	seteuid(root_uid);

	while (1) {
		/*
		 * Find a free connection. If we do not have a free
		 * connection, throttle incoming requests and let the backlog
		 * queue hold it.
		 */
		for (conn = conns, i = 0; i < max_conns; ++i, ++conn)
			if (SOCKET(conn) == -1)
				break;
		if (i == max_conns) {
			syslog(LOG_WARNING, "Too many connections.");
#ifdef HAVE_POLL
			ufds[0].events = 0;
#else
			FD_CLR(accept_sock, &readfds);
#endif
			return -1;
		}

		sock = accept_socket(csock, &addr);
		if (sock < 0) {
			seteuid(uid);

			if (errno == EWOULDBLOCK)
				return 0;

			syslog(LOG_WARNING, "Accept connection: %m");
			return -1;
		}

		/* Set *before* any closes */
		set_readable(conn, sock);
		++n_connections;
		++n_requests;
		if (i > max_requests)
			max_requests = i;

		conn->addr   = addr;
		conn->offset = 0;
		conn->len    = 0;
		time(&conn->access);

		if (!conn->cmd) {
			conn->cmd = malloc(MAX_LINE + 1);
			if (!conn->cmd) {
				syslog(LOG_WARNING, "Out of memory.");
				close_connection(conn, 503);
			}
		}
	}
}


static int read_request(struct connection *conn)
{
	int fd;
	int n;
	char *p, type;

	do
		n = read(SOCKET(conn), conn->cmd + conn->offset,
			 MAX_LINE - conn->offset);
	while (n < 0 && errno == EINTR);

	if (n < 0) {
		if (errno == EAGAIN) {
			syslog(LOG_DEBUG, "EAGAIN\n");
			return 0;
		}

		syslog(LOG_WARNING, "Read error (%d): %m", errno);
		close_connection(conn, 408);
		return 1;
	}
	if (n == 0) {
		syslog(LOG_WARNING, "Read: unexpected EOF");
		close_connection(conn, 408);
		return 1;
	}

	conn->offset += n;
	time(&conn->access);

	/* We alloced an extra space for the '\0' */
	conn->cmd[conn->offset] = '\0';

	if (conn->cmd[conn->offset - 1] != '\n') {
		if (conn->offset >= MAX_LINE) {
			syslog(LOG_WARNING, "Line overflow");
			if (strncmp(conn->cmd, "GET ",  4) == 0 ||
			    strncmp(conn->cmd, "HEAD ", 5) == 0)
				return http_error(conn, 414);
			else {
				close_connection(conn, 414);
				return 1;
			}
		}
		return 0; /* not an error */
	}

	if (conn->offset > max_length)
		max_length = conn->offset;

	if (strcmp(conn->cmd, "STATS\r\n") == 0)
		return gofish_stats(conn);

	if (strncmp(conn->cmd, "GET ",  4) == 0 ||
	    strncmp(conn->cmd, "HEAD ", 5) == 0) {
		/* We must look for \r\n\r\n */
		/* This is mainly for telnet sessions */
		if (strstr(conn->cmd, "\r\n\r\n")) {
			if (verbose > 2)
				printf("Http: %s\n", conn->cmd);
			return http_get(conn);
		}
		conn->http = 1;
		return 0;
	}

	/* ----------------------------------------------------------------- */
	/* From here on is gopher only */

	conn->cmd[conn->offset - 1] = '\0';
	if (conn->offset > 1 && conn->cmd[conn->offset - 2] == '\r')
		conn->cmd[conn->offset - 2] = '\0';

	if (verbose)
		printf("Gopher request: '%s'\n", conn->cmd);
	++gopher_requests;

	/* For gopher+ clients - ignore tab and everything after it */
	p = strchr(conn->cmd, '\t');
	if (p) {
		if (verbose)
			printf("  Gopher+\n");
		if (strcmp(conn->cmd, "\t$") == 0)
			/* UMN client - got this idea from floodgap.com */
			strcpy(conn->cmd, "0/.gopher+");
		else
			*p = '\0';
	}

	fd = smart_open(conn->cmd, &type);
	if (fd < 0) {
		close_connection(conn, 404);
		return 1;
	}
	conn->len = lseek(fd, 0, SEEK_END);

	if (conn->len) {
		conn->buf = mmap_get(conn, fd);
		if (conn->buf == NULL) {
			syslog(LOG_ERR, "mmap: %m");
			close(fd);
			close_connection(conn, 408);
			return 1;
		}
	}

	close(fd);

	conn->iovs[0].iov_base = conn->buf;
	conn->iovs[0].iov_len  = conn->len;

	if (type == '0') {
		if (conn->len > 0 && conn->buf[conn->len - 1] != '\n') {
			conn->iovs[1].iov_base = "\r\n.\r\n";
			conn->iovs[1].iov_len  = 5;
		} else {
			conn->iovs[1].iov_base = ".\r\n";
			conn->iovs[1].iov_len  = 3;
		}
		conn->len += conn->iovs[1].iov_len;
		conn->n_iovs = 2;
	} else
		conn->n_iovs = 1;

	set_writeable(conn);

	return 0;
}


static int write_request(struct connection *conn)
{
	int n, i;
	struct iovec *iov;

	do
		n = writev(SOCKET(conn), conn->iovs, conn->n_iovs);
	while (n < 0 && errno == EINTR);

	if (n < 0) {
		if (errno == EAGAIN)
			return 0;

		syslog(LOG_ERR, "writev: %m");
		close_connection(conn, 408);
		return 1;
	}
	if (n == 0) {
		syslog(LOG_ERR, "writev unexpected EOF");
		close_connection(conn, 408);
		return 1;
	}

	for (iov = conn->iovs, i = 0; i < conn->n_iovs; ++i, ++iov)
		if (n >= iov->iov_len) {
			n -= iov->iov_len;
			iov->iov_len = 0;
		} else {
			iov->iov_len -= n;
			iov->iov_base += n;
			time(&conn->access);
			return 0;
		}

	close_connection(conn, conn->status);

	return 0;
}


static void check_old_connections(void)
{
	struct connection *c;
	int i;
	time_t checkpoint;

	checkpoint = time(NULL) - MAX_IDLE_TIME;

	/* Do not close the listen socket */
	for (c = conns, i = 0; i < max_conns; ++i, ++c)
		if (SOCKET(c) >= 0 && c->access < checkpoint) {
			syslog(LOG_WARNING, "%s: Killing idle connection.",
			       ntoa(c->addr));
			close_connection(c, 408);
		}
}


static void create_pidfile(char *fname)
{
	FILE *fp;
	int n;
	int pid;

	fp = fopen(fname, "r");
	if (fp) {
		n = fscanf(fp, "%d\n", &pid);
		fclose(fp);

		if (n == 1) {
			if (kill(pid, 0) == 0) {
				syslog(LOG_ERR,
				       "gopherd already running (pid = %d)",
				       pid);
				exit(1);
			}
		} else {
			syslog(LOG_ERR, "Unable to read %s", fname);
			exit(1);
		}
	} else if (errno != ENOENT) {
		syslog(LOG_ERR, "Open %s: %m", fname);
		exit(1);
	}

	fp = fopen(fname, "w");
	if (fp == NULL) {
		syslog(LOG_ERR, "Create %s: %m", fname);
		exit(1);
	}

	pid = getpid();
	fprintf(fp, "%d\n", pid);

	fclose(fp);
}


#define NEED_WRITE(fd, b, l)			\
	do {					\
		rc = write(fd, b, l);		\
		if (rc != l)			\
			goto write_failed;	\
	} while (0)

/* SAM This could be optimized */
static int open_cache(char *fname)
{
	FILE *fp;
	int fd, rc;
	char tempname[20], portstr[12];
	char line[1024];

	if (process_cache == 0)
		return file_open(fname);

	fp = file_fopen(fname);
	if (fp == NULL)
		return -1;

	sprintf(tempname, "%s/gocacheXXXXXX", tmpdir);
	fd = mkstemp(tempname);
	if (fd < 0) {
		fclose(fp);
		return fd;
	}
	unlink(tempname);

	while (fgets(line, sizeof(line), fp)) {
		int len, fields = 1;
		char *p;

		for (p = line; *p && *p != '\n' && *p != '\r'; ++p)
			if (*p == '\t')
				++fields;

		len = p - line;
		NEED_WRITE(fd, line, len);

		switch (fields) {
		case 2: /* host missing */
			NEED_WRITE(fd, "\t", 1);
			NEED_WRITE(fd, hostname, strlen(hostname));
			/* fallthru */
		case 3: /* port missing */
			sprintf(portstr, "\t%d", port);
			NEED_WRITE(fd, portstr, strlen(portstr));
		}

		NEED_WRITE(fd, "\n", 1);
	}

	fclose(fp);
	lseek(fd, 0, SEEK_SET);

	return fd;

write_failed:
	if (rc < 0)
		syslog(LOG_WARNING, "open_cache %s: write failed: %m", fname);
	else
		syslog(LOG_WARNING, "open_cache %s: short write", fname);
	fclose(fp);
	close(fd);
	return -1;
}


int file_open(char *fname)
{
	if (user_dirs) {
		struct passwd *pw;
		char fullname[1024], *p;

		if (*fname != '~')
			return open(fname, O_RDONLY);

		p = strchr(fname, '/');
		if (p)
			*p = '\0';
		pw = getpwnam(fname + 1);
		if (p)
			*p = '/';
		if (pw == NULL)
			return -errno;

		if (p)
			snprintf(fullname, sizeof(fullname), "%s/gopher%s",
				 pw->pw_dir, p);
		else
			snprintf(fullname, sizeof(fullname), "%s/gopher",
				 pw->pw_dir);

		return open(fullname, O_RDONLY);
	} else
		return open(fname, O_RDONLY);
}

FILE *file_fopen(char *fname)
{
	int fd = file_open(fname);
	if (fd < 0)
		return NULL;
	return fdopen(fd, "r");
}


#define SECONDS_IN_A_MINUTE	(60)
#define SECONDS_IN_AN_HOUR	(SECONDS_IN_A_MINUTE * 60)
#define SECONDS_IN_A_DAY	(SECONDS_IN_AN_HOUR * 24)

static char *uptime(char *str)
{
	time_t up = time(NULL) - started;

	if (up >= SECONDS_IN_A_DAY) {
		up /= SECONDS_IN_A_DAY;
		sprintf(str, "%ld %s", up, up == 1 ? "day" : "days");
	} else if (up >= SECONDS_IN_AN_HOUR) {
		up /= SECONDS_IN_AN_HOUR;
		sprintf(str, "%ld %s", up, up == 1 ? "hour" : "hours");
	} else
		strcpy(str, "< 1 hour");

	return str;
}


static int gofish_stats(struct connection *conn)
{
	char buf[200], up[12];

	sprintf(buf,
		"GoFish " GOFISH_VERSION " %12s\r\n"
		"Requests:     %10u/%u\r\n"
		"Max parallel: %10u\r\n"
		"Max length:   %10u\r\n"
		"Connections:  %10d\r\n",
		uptime(up),
		gopher_requests, n_requests,
		max_requests, max_length,
		/* we are an outstanding connection */
		n_connections - 1);

	if (bad_munmaps) {
		char *p = buf + strlen(buf);
		sprintf(p, "BAD UNMAPS:   %10u\r\n", bad_munmaps);
	}

	while (write(SOCKET(conn), buf, strlen(buf)) < 0 && errno == EINTR)
		;

	close_connection(conn, 1000);

	return 0;
}


#ifndef HAVE_DAEMON
/* Minimal daemon call for solaris */
int daemon(int nochdir, int noclose)
{
	pid_t pid;

	pid = fork();
	if (pid == 0)
		return 0;

	if (pid == -1)
		return -1;

	exit(0); /* parent exits */
}
#endif

/*
 * Kernel coding standard.
 * Local Variables:
 * tab-width: 8
 * c-basic-offset: 8
 * indent-tabs-mode: t
 * End:
 */
