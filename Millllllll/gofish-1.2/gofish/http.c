/*
 * http.c - http handler for the gofish gopher daemon
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
 * along with XEmacs; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <syslog.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <ctype.h>
#include <sys/utsname.h>
#include <sys/stat.h>

#include "gofish.h"
#include "version.h"

/* Does not always return errors */
/* Does not proxy external links */
/* Maybe implement buffering in write_out */
/* Better binary mime handling */
/* Better image mime handling */

#define MAX_SERVER_STRING	600
static char *server_str;

static char *mime_html = "text/html; charset=iso-8859-1";


static char *html_header =
	"<!DOCTYPE HTML PUBLIC " \
	"\"-//W3C//DTD HTML 4.01 Transitional//EN\">\n" \
	"<html lang=\"en\">\n" \
	"<head>\n<title>GoFish gopher to http gateway.</title>\n" \
	"<style type=\"text/css\">\n" \
	"<!--\nBODY { margin: 1em 15%; }\n-->\n</style>\n" \
	"</head>\n" \
	"<body>\n<p><pre>\n";
static int html_set_header;

static char *html_trailer = "</pre>\n<hr>\n<p><small>" \
	"<a href=\"http://gofish.sourceforge.net/\">" \
	"GoFish " GOFISH_VERSION \
	"</a> gopher to http gateway.</small>\n" \
	"</body>\n</html>\n";
static int html_set_trailer;

#define HTML_INDEX_FILE	"index.html"
#define HTML_INDEX_TYPE	mime_html


static int isdir(char *name);

static int go_chdir(const char *path);

inline int write_out(int fd, char *buf, int len)
{
	return WRITE(fd, buf, len);
}


inline int write_str(int fd, char *str)
{
	return write_out(fd, str, strlen(str));
}


static void unquote(char *str)
{
	char *p, quote[3], *e;
	int n;

	for (p = str; (p = strchr(p, '%')); ) {
		quote[0] = *(p + 1);
		quote[1] = *(p + 2);
		quote[2] = '\0';
		n = strtol(quote, &e, 16);
		if (e == (quote + 2)) {
			*p++ = (char)n;
			memmove(p, p + 2, strlen(p + 2) + 1);
		} else
			++p; /* skip over % */
	}
}


static char *msg_400 =
	"Your browser sent a request that this server could not understand.";

static char *msg_404 =
	"The requested URL was not found on this server.";

static char *msg_414 =
	"The requested URL was too large.";

static char *msg_500 =
	"An internal server error occurred. Try again later.";


/* This is a very specialized build_response just for errors.
   The request field is for the 301 errors.
*/
static int http_error1(struct connection *conn, int status, char *request)
{
	char str[MAX_LINE + MAX_LINE + MAX_SERVER_STRING + 512];
	char *title, *p, *msg;

	switch (status) {
	case 301:
		/* Be nice and give the moved address. */
		title = "301 Moved Permanently";
		sprintf(str,
			"The document has moved <a href=\"/%s/\">here</a>.",
			request);
		msg = strdup(str);
		if (msg == NULL) {
			syslog(LOG_WARNING, "http_error: Out of memory.");
			close_connection(conn, status);
			return 1;
		}
		break;
	case 400:
		title = "400 Bad Request";
		msg = msg_400;
		break;
	case 403:
		title = "403 Forbidden";
		msg = msg_404;
		break;
	case 404:
		title = "404 Not Found";
		msg = msg_404;
		break;
	case 414:
		title = "414 Request URL Too Large";
		msg = msg_414;
		break;
	case 500:
		title = "500 Server Error";
		msg = msg_500;
		break;
	default:
		syslog(LOG_ERR, "Unknow error status %d", status);
		title = "500 Unknown";
		msg = msg_500;
		break;
	}

	sprintf(str,
		"HTTP/1.0 %s\r\n"
		"Server: %s"
		"Content-Type: text/html\r\n",
		title, server_str);

	if (status == 301) {
		/* we must add the *real* location */
		p = str + strlen(str);
		sprintf(p, "Location: /%s/\r\n", request);
	}

	strcat(str, "\r\n");

	/* Build the html body */
	p = str + strlen(str);
	sprintf(p,
		"<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">\r\n"
		"<html lang=\"en\">\n<head>\n"
		"<title>%s</title>\r\n"
		"</head>\n<body><h1>%s</h1>\r\n"
		"<p>%s\r\n"
		"</body></html>\r\n",
		title, title, msg);

	if (status == 301)
		free(msg);

	conn->http_header = strdup(str);
	if (conn->http_header == NULL) {
		syslog(LOG_WARNING, "http_error: Out of memory.");
		if (status == 302)
			free(msg);
		close_connection(conn, status);
		return 1;
	}

	conn->status = status;

	conn->iovs[0].iov_base = conn->http_header;
	conn->iovs[0].iov_len  = strlen(conn->http_header);
	conn->n_iovs = 1;

	set_writeable(conn);

	return 0;
}


/* For all but 301 errors */
int http_error(struct connection *conn, int status)
{
	return http_error1(conn, status, "bogus");
}


static int http_build_response(struct connection *conn, char *type)
{
	char str[1024], *p;
	int len;

	strcpy(str, "HTTP/1.1 200 OK\r\n");
	strcat(str, server_str);
	/* SAM We do not support persistant connections */
	strcat(str, "Connection: close\r\n");
	p = str;
	if (type) {
		p += strlen(p);
		sprintf(p, "Content-Type: %s\r\n", type);
	}
	p += strlen(p);
	len = conn->len;
	if (conn->html_header)
		len += strlen(conn->html_header);
	if (conn->html_trailer)
		len += strlen(conn->html_trailer);
	sprintf(p, "Content-Length: %d\r\n\r\n", len);

	conn->http_header = strdup(str);
	if (conn->http_header == NULL) {
		/* Just closing the connection is the best we can do */
		syslog(LOG_WARNING, "Low on memory.");
		close_connection(conn, 500);
		return 1;
	}

	conn->status = 200;

	return 0;
}


static int http_dir_line(int out, char *line)
{
	char *desc, *url, *host, *port;
	char *p, *icon;
	char buf[200];

	for (desc = p = line + 1; *p && *p != '\t'; ++p)
		;
	*p++ = '\0';
	for (url = p; *p && *p != '\t'; ++p)
		;
	*p++ = '\0';
	for (host = p; *p && *p != '\t'; ++p)
		;
	*p++ = '\0';
	for (port = p; *p && *p != '\t'; ++p)
		;
	*p++ = '\0';

	if (*line == 'i') {
		write_str(out, line + 1);
		write_str(out, "<br>\n");
	} else {
		switch (*line) {
		case '0':
			icon = "text";
			break;
		case '1':
			icon = "menu";
			break;
		case '9':
			icon = "binary";
			break;
		case 'h':
			icon = "html";
			break;
		case 'I':
			icon = "image";
			break;
		default:
			icon = "unknown";
			break;
		}

		sprintf(buf,
			"<img src=\"/g/icons/gopher_%s.gif\" "
			"width=%d height=%d alt=\"[%s]\">\n ",
			icon, icon_width, icon_height, icon);
		write_str(out, buf);

		if (strcmp(host, hostname) && strcmp(host, "localhost")) {
			if (strcmp(port, "70") == 0)
				sprintf(buf, "gopher://%.40s/", host);
			else
				sprintf(buf, "gopher://%.40s:%s/", host, port);
			if (!(*line == '1' &&
			      (strcmp(url, "/") == 0 || !*url))) {
				p = buf + strlen(buf);
				sprintf(p, "%c%.80s", *line, url);
			}
			write_str(out, desc);
			write_str(out, " <a href=\"");
			write_str(out, buf);
			write_str(out, "\">");
			write_str(out, buf);
			write_str(out, "</a><br>\n");
		} else {
			write_str(out, "<a href=\"/");
#ifdef STRICT_GOPHER
			write_out(out, line, 1);
			write_str(out, url + 1);
#else
			write_str(out, url + 2);
#endif
			write_str(out, "\">");
			write_str(out, desc);
			write_str(out, "</a><br>\n");
		}
	}

	return 0;
}


#define BUFSIZE		2048

/* return the outfd or -1 for error */
static int http_directory(struct connection *conn, int fd, char *dir)
{
	int out;
	char buffer[BUFSIZE + 1], outname[80];
	char url[256];
	char *buf, *p, *s;
	int n, len, left;


	snprintf(outname, sizeof(outname), "%s/.gofish-XXXXXX", tmpdir);
	out = mkstemp(outname);
	if (out == -1) {
		syslog(LOG_ERR, "%s: %m", outname);
		return -1;
	}
	conn->outname = strdup(outname);
	if (conn->outname == NULL) {
		syslog(LOG_ERR, "Out of memory");
		return -1;
	}

	if (*dir == '/')
		++dir;
	if (strncmp(dir, "1/", 2) == 0)
		dir += 2;
	sprintf(url, "http://%.80s:%d/%.80s", hostname, port, dir);
	p = url + strlen(url);
	if (*(p - 1) != '/')
		strcpy(p, "/");

	sprintf(buffer,
		"<!DOCTYPE HTML PUBLIC "
		"\"-//W3C//DTD HTML 4.01 Transitional//EN\">\n"
		"<html lang=\"en\">\n"
		"<head>\n<title>%.80s</title>\n"
		"<style type=\"text/css\">\n"
		"<!--\nBODY { margin: 1em 10%%; }\n-->\n</style>\n"
		"</head>\n"
		"<body>\n"
		"<h1>Index of %s</h1>\n"
		"<hr>\n<p>",
		url, url);
	write_str(out, buffer);


	buf = buffer;
	len = BUFSIZE;
	while ((n = READ(fd, buf, len)) > 0) {
		buf[n] = '\0';
		for (s = buffer; (p = strchr(s, '\n')); s = p) {
			if (p > buffer && *(p - 1) == '\r')
				*(p - 1) = '\0';
			*p++ = '\0';

			http_dir_line(out, s); /* do it */
		}

		if (s == buffer) {
			syslog(LOG_WARNING, "%s: line too long", dir);
			return -1;
		}

		/* Move the leftover bytes down */
		left = n - (s - buf);
		memmove(buffer, s, left);

		/* update for next read */
		buf = buffer + left;
		len = BUFSIZE - left;
	}

	if (n < 0) {
		syslog(LOG_ERR, "%s: read error", dir);
		return -1;
	}

	write_str(out, "<hr>\n"
		  "<small>"
		  "<a href=\"http://gofish.sourceforge.net/\">"
		  "GoFish " GOFISH_VERSION
		  "</a> gopher to http gateway.</small>\n"
		  "</body>\n</html>\n");

	return out;
}

struct mark {
	char *pos;
	char data;
};

#define MSAVE(m, p) do { (m)->pos = (p); (m)->data = *(p); } while (0)
#define MRESTORE(m) do { *(m)->pos = (m)->data; } while (0)

int http_get(struct connection *conn)
{
	char *e;
	int fd, new;
	char *mime, type;
	struct mark save;
	char *request = conn->cmd;

	conn->http = *request == 'H' ? HTTP_HEAD : HTTP_GET;

	/* This works for both GET and HEAD */
	request += 4;
	while (isspace((int)*request))
		++request;

	e = strstr(request, "HTTP/");
	if (e == NULL)
		/* probably a local lynx request */
		return http_error(conn, 400);

	while (*(e - 1) == ' ')
		--e;
	MSAVE(&save, e);
	*e++ = '\0';

	if (*request == '/')
		++request;

	unquote(request);

	if (combined_log) {
		/* Save these up front for logging */
		conn->referer = strstr(e, "Referer:");
		conn->user_agent = strstr(e, "User-Agent:");
	}

	if (is_gopher) {
		fd = smart_open(request, &type);
		if (fd >= 0) {
			/* valid gopher request */
			if (verbose)
				printf("HTTP Gopher request '%s'\n", request);
			switch (type) {
			case '1':
				new = http_directory(conn, fd, request);
				close(fd);
				fd = new;
				if (fd < 0) {
					MRESTORE(&save);
					return http_error(conn, 500);
				}
				mime = mime_html;
				break;
			case '0':
				if (htmlizer) {
					conn->html_header  = html_header;
					conn->html_trailer = html_trailer;
					mime = mime_html;
				} else
					mime = "text/plain";
				break;
			case '4':
			case '5':
			case '6':
			case '9':
				mime = mime_find(request);
				if (mime == NULL)
					mime = "application/octet-stream";
				break;
			case 'g':
				mime = "image/gif";
				break;
			case 'h':
				mime = mime_html;
				break;
			case 'I':
				mime = mime_find(request);
				break;
			default:
				/* Safe default - let the user handle it */
				mime = "application/octet-stream";
				syslog(LOG_WARNING, "Bad file type %c", type);
				break;
			}
		} else {
			if (verbose)
				printf("HTTP Gopher invalid '%s'\n", request);
			syslog(LOG_WARNING, "%s: %m", request);
			MRESTORE(&save);
			return http_error(conn, 404);
		}
	} else {/* real http request */
		if (virtual_hosts) {
			char *host;
			int rc;

			host = strstr(e, "Host:");
			if (e) {
				/* isolate the host. ignore the port (if any) */
				for (host += 5; isspace((int)*host); ++host)
					;
				for (e = host;
				     *e && !isspace((int)*e) && *e != ':';
				     ++e)
					;
				*e = '\0';
			}

			if (!host || !*host) {
				syslog(LOG_WARNING, "Request with no host '%s'",
				       request);
				MRESTORE(&save);
				return http_error(conn, 403);
			}

			/* root it */
			--host;
			*host = '/';

			conn->host = host;

			/* SAM Is this an expensive call? */
			/* SAM Cache current? */
			rc = go_chdir(host);

			if (rc) {
				syslog(LOG_WARNING, "host '%s': %m", host);
				MRESTORE(&save);
				return http_error(conn, 404);
			}

			if (verbose)
				printf("Http request %s '%s'\n", host + 1,
				       request);
		} else if (verbose)
			printf("Http request '%s'\n", request);

		if (*request) {
			if (isdir(request)) {
				char dirname[MAX_LINE + 20], *p;

				strcpy(dirname, request);
				p = dirname + strlen(dirname);
				if (*(p - 1) != '/') {
					/* We must send back a 301
					 * response or relative
					 * URLs will not work */
					int rc;

					rc = http_error1(conn, 301, request);

					/* restore *after* call */
					MRESTORE(&save);
					return rc;
				}
				strcpy(p, HTML_INDEX_FILE);
				fd = file_open(dirname);
				mime = HTML_INDEX_TYPE;
			} else {
				fd = file_open(request);
				mime = mime_find(request);
			}
		} else {
			fd = open(HTML_INDEX_FILE, O_RDONLY);
			mime = HTML_INDEX_TYPE;
		}
	}

	if (fd < 0) {
		syslog(LOG_WARNING, "%s: %m", request);
		MRESTORE(&save);
		return http_error(conn, 404);
	}

	MRESTORE(&save);

	conn->len = lseek(fd, 0, SEEK_END);

	if (http_build_response(conn, mime)) {
		syslog(LOG_WARNING, "Out of memory");
		return -1;
	}

	conn->iovs[0].iov_base = conn->http_header;
	conn->iovs[0].iov_len  = strlen(conn->http_header);

	if (conn->http == HTTP_HEAD) {
		/* no body to send */
		close(fd);

		conn->len = 0;
		conn->n_iovs = 1;
		set_writeable(conn);

		return 0;
	}

	conn->buf = mmap_get(conn, fd);

	close(fd); /* done with this */

	/* Zero length files will fail */
	if (conn->buf == NULL && conn->len) {
		syslog(LOG_ERR, "mmap: %m");
		return http_error(conn, 500);
	}

	if (conn->html_header) {
		conn->iovs[1].iov_base = conn->html_header;
		conn->iovs[1].iov_len  = strlen(conn->html_header);
	}

	if (conn->buf) {
		conn->iovs[2].iov_base = conn->buf;
		conn->iovs[2].iov_len  = conn->len;
	}

	if (conn->html_trailer) {
		conn->iovs[3].iov_base = conn->html_trailer;
		conn->iovs[3].iov_len  = strlen(conn->html_trailer);
	}

	conn->len =
		conn->iovs[0].iov_len +
		conn->iovs[1].iov_len +
		conn->iovs[2].iov_len +
		conn->iovs[3].iov_len;

	conn->n_iovs = 4;

	set_writeable(conn);

	return 0;
}


static int isdir(char *name)
{
	struct stat sbuf;

	if (stat(name, &sbuf) == -1)
		return 0;
	return S_ISDIR(sbuf.st_mode);
}


int http_init(void)
{
	char str[600];
	struct utsname uts;

	uname(&uts);

	sprintf(str, "Server: GoFish/%.8s (%.512s)\r\n",
		GOFISH_VERSION, uts.sysname);

	server_str = strdup(str);
	if (!server_str) {
		syslog(LOG_ERR, "http_init: Out of memory");
		exit(1);
	}

	return 0;
}


void http_cleanup(void)
{
	if (server_str)
		free(server_str);
}


void http_set_header(char *fname, int header)
{
	int fd;
	char *msg;
	int n;
	struct stat sbuf;

	fd = open(fname, O_RDONLY);
	if (fd < 0 || fstat(fd, &sbuf)) {
		syslog(LOG_ERR, "Unable to open %s", fname);
		exit(1);
	}

	msg = must_alloc(sbuf.st_size + 1);
	n = read(fd, msg, sbuf.st_size);
	if (n != sbuf.st_size) {
		syslog(LOG_ERR, "Unable to read %s: %d/%ld",
		       fname, n, sbuf.st_size);
		exit(1);
	}

	close(fd);

	if (header) {
		if (html_set_header)
			free(html_header);
		html_header = msg;
		html_set_header = 1;
	} else {
		if (html_set_trailer)
			free(html_trailer);
		html_trailer = msg;
		html_set_trailer = 1;
	}
}


/* added by folkert@vanheusden.com */
/* This function takes away all the hassle when working
 * with read(). Blocking reads only.
 */
int READ(int handle, char *whereto, int len)
{
	int cnt = 0;

	while (1) {
		int rc;

		rc = read(handle, whereto, len);

		if (rc == -1) {
			if (errno != EINTR) {
				syslog(LOG_DEBUG,
				       "READ(): io-error [%d - %s]",
				       errno, strerror(errno));
				return -1;
			}
		} else if (rc == 0)
			return cnt;
		else {
			whereto += rc;
			len -= rc;
			cnt += rc;
		}
	}

	return cnt;
}


/* added by folkert@vanheusden.com */
/* this function takes away all the hassle when working
 * with write(). Blocking writes only.
 */
int WRITE(int handle, char *whereto, int len)
{
	int cnt = 0;

	while (len > 0) {
		int rc;

		rc = write(handle, whereto, len);

		if (rc == -1) {
			if (errno != EINTR) {
				syslog(LOG_DEBUG,
				       "WRITE(): io-error [%d - %s]",
				       errno, strerror(errno));
				return -1;
			}
		} else if (rc == 0)
			return cnt;
		else {
			whereto += rc;
			len -= rc;
			cnt += rc;
		}
	}

	return cnt;
}


/* All directories are rooted */
static int go_chdir(const char *path)
{
	if (do_chroot)
		return chdir(path);
	else {
		char fulldir[PATH_MAX + 1];

		if (strlen(root_dir) + strlen(path) >= PATH_MAX)
			return ENAMETOOLONG;
		sprintf(fulldir, "%s%s", root_dir, path);
		return chdir(fulldir);
	}
}


/*
 * Kernel coding standard.
 * Local Variables:
 * tab-width: 8
 * c-basic-offset: 8
 * indent-tabs-mode: t
 * End:
 */
