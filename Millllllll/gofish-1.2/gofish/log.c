/*
 * log.c - log file output for the gofish gopher daemon
 * Copyright (C) 2002 Sean MacLennan <seanm@seanm.ca>
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
#include <string.h>
#include <unistd.h>
#include <syslog.h>
#include <ctype.h>
#include <errno.h>
#include <signal.h>

#include "gofish.h"


/* #define LOG_HIT_DBG 1 */

static FILE *log_fp;
static char *log_name;

static void log_reopen(int sig)
{
	fclose(log_fp);

	log_fp = fopen(log_name, "a");
	if (log_fp == NULL)
		syslog(LOG_ERR, "Reopen %s: %m", log_name);

	syslog(LOG_WARNING, "Log file reopened.");
}


/* We are root and outside the chroot jail */
int log_open(char *logname)
{
	int len = strlen(root_dir);

	/* strip the chroot directory if necessary */
	if (strncmp(logname, root_dir, len) == 0) {
		log_name = logname + len;
		if (*log_name != '/')
			--log_name;
	} else
		log_name = logname;

	signal(SIGUSR1, log_reopen);

	log_fp = fopen(logname, "a");
	if (log_fp == NULL)
		return 0;

	if (fchown(fileno(log_fp), uid, gid))
		perror("chown log file");

	return 1;
}

/* Warning: This is destructive to str */
static char *trim_str(char *str, int skip)
{
	char *p;

	if (!str)
		return "-";

	str += skip;

	while (isspace(*str))
			++str;
	p = strpbrk(str, "\r\n");
	if (p)
		*p = '\0';
	else
		return "-";

	return str;
}

static void add_combined_log(struct connection *conn,
			     char *common, char *request, unsigned status)
{	/* This is 500 + hostname chars max */
	char *referer, *agent;
	int n;

	referer = trim_str(conn->referer, 8);
	agent = trim_str(conn->user_agent, 12);

	do {
		if (virtual_hosts && conn->host)
			n = fprintf(log_fp,
				    "%s %s/%.200s\" %u %u \"%.100s\" "
				    "\"%.100s\"\n",
				    common, conn->host, request, status,
				    conn->len, referer, agent);
		else
			n = fprintf(log_fp,
				    "%s /%.200s\" %u %u \"%.100s\" "
				    "\"%.100s\"\n",
				    common, request, status, conn->len,
				    referer, agent);
	} while (n < 0 && errno == EINTR);
}

static void add_normal_log(struct connection *conn,
			   char *common, char *request, unsigned status)
{	/* This is 600 + hostname chars max */
	int n;

	do {
		if (virtual_hosts && conn->host)
			n = fprintf(log_fp, "%s %s/%.200s\" %u %u\n",
				    common, conn->host, request, status,
				    conn->len);
		else
			n = fprintf(log_fp, "%s /%.200s\" %u %u\n",
				    common, request, status, conn->len);
	} while (n < 0 && errno == EINTR);
}

#ifdef LOG_HIT_DBG
static unsigned logcnt;
#endif

/* Common log file format */
void log_hit(struct connection *conn, unsigned status)
{
	char common[80], *p;
	time_t now;
	struct tm *t;
	int n;

	if (!log_fp)
		return; /* nowhere to write! */

	if (ignore_local &&
	    ((conn->addr & 0xffff0000) == 0xc0a80000 ||
	     conn->addr == 0x7f000001))
		return;

	time(&now);
	t = localtime(&now);

	/* Get some of the fixed length common stuff out of the way */
	strcpy(common, ntoa(conn->addr));
	p = common + strlen(common);
#ifdef LOG_HIT_DBG
	sprintf(p, " - %u ", logcnt++);
	p += strlen(p);
	strftime(p, sizeof(common) - 30, "[%d/%b/%Y:%T %z] \"", t);
#else
	strftime(p, sizeof(common) - 30, " - - [%d/%b/%Y:%T %z] \"", t);
#endif
	strcat(p, conn->http == HTTP_HEAD ? "HEAD" : "GET");

	if (conn->http) {
		char *request;

		/* SAM Save this? */
		request = conn->cmd;
		request += 4;
		while (isspace((int)*request))
			++request;
		if (*request == '/')
			++request;

		/* For gopher requests */
		if (*request && *(request + 1) == '/')
			request += 2;

		if (combined_log)
			add_combined_log(conn, common, request, status);
		else
			add_normal_log(conn, common, request, status);
	} else {
		char *name = conn->cmd ? conn->cmd : "[Empty]";

		if (*name == '/')
			++name;
		if (*name && *(name + 1) == '/')
			name += 2;

		/* This is 400 chars max */
		do
			n = fprintf(log_fp, "%s /%.300s\" %u %u\n",
				    common, name, status, conn->len);
		while (n < 0 && errno == EINTR);
	}

	/* every path */
	fflush(log_fp);
}


void log_close(void)
{
	if (log_fp) {
		(void)fclose(log_fp);
		log_fp = NULL;
	}
}


static void send_errno(int sock, char *name, int errnum)
{
	char error[1024];

	if (*name == '\0')
		sprintf(error, "3'<root>' %.500s (%d)\r\n",
			strerror(errnum), errnum);
	else
		sprintf(error, "3'%.500s' %.500s (%d)\r\n",
			name, strerror(errnum), errnum);
	while (write(sock, error, strlen(error)) < 0 && errno == EINTR)
		;
}


static struct errmsg {
	unsigned errnum;
	char *errstr;
} errors[] = {
	{ 408, "Request Timeout" },  /* client may retry later */
	{ 414, "Request-URL Too Large" },
	{ 500, "Server Error" },
	{ 503, "Server Unavailable" },
	{ 999, "Unknown error" } /* marker */
};
#define N_ERRORS	(sizeof(errors) / sizeof(struct errmsg))


/* Only called from close_request */
void send_error(struct connection *conn, unsigned error)
{
	char errstr[80];
	int i;

	if (error == 404) {
		send_errno(SOCKET(conn), conn->cmd, errno);
		return;
	}

	for (i = 0; i < N_ERRORS - 1 && error != errors[i].errnum; ++i)
		;

	sprintf(errstr, "3%s [%d]\r\n", errors[i].errstr, error);
	while (write(SOCKET(conn), errstr, strlen(errstr)) < 0 &&
	       errno == EINTR)
		;
}

/*
 * Kernel coding standard.
 * Local Variables:
 * tab-width: 8
 * c-basic-offset: 8
 * indent-tabs-mode: t
 * End:
 */
