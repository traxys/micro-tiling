/*
 * mkcache - creates the .cache files for the gofish gopher daemon
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
#include <unistd.h>
#include <dirent.h>
#include <errno.h>
#include <ctype.h>
#include <sys/stat.h>

#include "gofish.h"


int verbose;
static int recurse;
static int sorttype;

int mmap_cache_size; /* needed by config */

/*
 * TODO
 *   + does not work except from root dir
 *   + does not look at extensions
 *   + recursive
 *   - does not handle symbolic links correctly
 *     - does not know if they are dirs or files
 *   - empty dirs are a problem if non-recursive
 *   - needs a config file
 *   - read .names
 *   - read .links
 *   - read .ignore
 *   - if a directory .cache can not be created,
 *     we still get the entry in the upper layer
 */


static struct extension {
	char *ext;
	char type;
	int binary;
} exts[] = {
	{ "txt",	'0', 0 },
	{ "html",	'h', 0 },
	{ "htm",	'h', 0 },
	{ "gif",	'I', 1 },
	{ "jpg",	'I', 1 },
	{ "png",	'I', 1 },
	{ "jpeg",	'I', 1 },
	{ "gz",		'9', 1 },
	{ "tgz",	'9', 1 },
	{ "tar",	'9', 1 },
	{ "rpm",	'9', 1 },
	{ "zip",	'9', 1 },
	{ "Z",		'9', 1 },
	{ "pdf",	'9', 1 },
	{ "ogg",	'9', 1 },
	{ "mp3",	'9', 1 },
};
#define N_EXTS	(sizeof(exts) / sizeof(struct extension))

struct entry {
	char *name;
	char type;
	char ftype;
};

static int read_dir(struct entry **entries, char *path, int level);
static int output_dir(struct entry *entries, int n, char *path, int level);


/* 0 */
static int simple_compare(const void *a, const void *b)
{
	return strcmp(((struct entry *)a)->name, ((struct entry *)b)->name);
}

/* 1 */
static int dirs_compare(const void *a, const void *b)
{
	const struct entry *ea = a, *eb = b;

	if (ea->ftype == '1') {
		if (eb->ftype == '1')
			return strcmp(ea->name, eb->name);
		else
			return -1;
	}
	if (eb->ftype == '1')
		return 1;

	return strcmp(ea->name, eb->name);
}

/* 2 */
static int dirs_type_compare(const void *a, const void *b)
{
	const struct entry *ea = a, *eb = b;
	int t;

	if (ea->ftype == '1') {
		if (eb->ftype == '1')
			return strcmp(ea->name, eb->name);
		else
			return -1;
	}
	if (eb->ftype == '1')
		return 1;

	t = ea->type - eb->type;
	if (t == 0)
		return strcmp(ea->name, eb->name);
	else
		return t;
}


static void free_entries(struct entry *entries, int nentries)
{
	struct entry *entry;
	int i;

	for (entry = entries, i = 0; i < nentries; ++i, ++entry)
		free(entry->name);
	free(entries);
}


/* Returns the number of entries in the .cache file */
static int process_dir(char *path, int level)
{
	int nfiles;
	struct entry *entries = NULL;

	if (verbose)
		printf("Processing [%d] %s\n", level, path);

	nfiles = read_dir(&entries, path, level);
	if (nfiles == 0)
		return 0;

	switch (sorttype) {
	default:
		printf("Unsupported sorttype %d\n", sorttype);
		/* fall thru */
	case 0:
		qsort(entries, nfiles, sizeof(struct entry), simple_compare);
		break;
	case 1:
		qsort(entries, nfiles, sizeof(struct entry), dirs_compare);
		break;
	case 2:
		qsort(entries, nfiles, sizeof(struct entry), dirs_type_compare);
		break;
	}

	output_dir(entries, nfiles, path, level);

	free_entries(entries, nfiles);

	return nfiles;
}


static int output_dir(struct entry *entries, int n, char *path, int level)
{
	FILE *fp;
	char fname[PATH_MAX];
	struct entry *e;
	int i;

	sprintf(fname, "%s/.cache", path);

	fp = fopen(fname, "w");
	if (!fp) {
		perror(path ? path : "root");
		return 0;
	}

	for (e = entries, i = 0; i < n; ++i, ++e)
		if (process_cache) {
			if (level == 0)
				fprintf(fp, "%c%s\t%c/%s\n",
					e->type, e->name, e->ftype,
					e->name);
			else
				fprintf(fp, "%c%s\t%c/%s/%s\n",
					e->type, e->name, e->ftype, path,
					e->name);
		} else {
			if (level == 0)
				fprintf(fp, "%c%s\t%c/%s\t%s\t%d\n",
					e->type, e->name, e->ftype, e->name,
					hostname, port);
			else
				fprintf(fp, "%c%s\t%c/%s/%s\t%s\t%d\n",
					e->type, e->name, e->ftype, path,
					e->name, hostname, port);
		}

	fclose(fp);

	return n;
}


static void add_entry(struct entry **entries, int n, char *name, int isdir)
{
	struct entry *entry;
	char *ext;

	*entries = realloc(*entries, (n + 1) * sizeof(struct entry));
	if (*entries == NULL) {
		printf("Out of memory\n");
		exit(1);
	}

	entry = (*entries) + n;

	entry->name = must_strdup(name);
	ext = strrchr(name, '.');
	if (isdir) {
		entry->type = entry->ftype = '1';
		return;
	} else if (ext) {
		int i;
		char *mime;

		++ext;
		for (i = 0; i < N_EXTS; ++i)
			if (strcasecmp(ext, exts[i].ext) == 0) {
				entry->type = exts[i].type;
				entry->ftype = exts[i].binary ? '9' : '0';
				return;
			}

		/* If there is an extension, default to binary */
		/* Most formats are binary. */
		entry->type = entry->ftype = '9';

		mime = mime_find(ext);
		if (mime) {
			/* try to intuit the type from the mime... */
			if (strncmp(mime, "text/html", 9) == 0) {
				entry->type  = 'h';
				entry->ftype = '0';
			} else if (strncmp(mime, "text/", 5) == 0)
				entry->type = entry->ftype = '0';
			else if (strncmp(mime, "image/", 6) == 0) {
				entry->type = 'I';
				entry->ftype = '9';
			}
		}
	} else
		/* Default to text as per gopher spec */
		entry->ftype = entry->type = '0';
}


static int isdir(struct dirent *ent, char *path, int len)
{
	struct stat sbuf;
	char *full;

	/* +2 for / and \0 */
	full = malloc(len + strlen(ent->d_name) + 2);
	if (!full) {
		printf("Out of memory\n");
		exit(1);
	}
	sprintf(full, "%s/%s", path, ent->d_name);
	if (stat(full, &sbuf)) {
		perror(full);
		exit(1);
	}
	free(full);

	return S_ISDIR(sbuf.st_mode);
}

static char *level0_ignores[] = {
	"favicon.ico",
	"icons",
	"etc",
	"tmp"
};
#define N_LEVEL0_IGNORES (sizeof(level0_ignores) / sizeof(char *))

static inline int level0_ignore(char *ent)
{
	int i;

	for (i = 0; i < N_LEVEL0_IGNORES; ++i)
		if (strcmp(ent, level0_ignores[i]) == 0)
			return 1; /* ignore it */
	return 0;
}

static char *ignores[] = {
	"gophermap"
};
#define N_IGNORES (sizeof(ignores) / sizeof(char *))

static inline int ignore(char *ent)
{
	int i;

	for (i = 0; i < N_IGNORES; ++i)
		if (strcmp(ent, ignores[i]) == 0)
			return 1; /* ignore it */
	return 0;
}

static int read_dir(struct entry **entries, char *path, int level)
{
	DIR *dir;
	struct dirent *ent;
	int nfiles = 0;
	int len = strlen(path);

	dir = opendir(path);
	if (!dir) {
		perror("opendir");
		return 0;
	}

	while ((ent = readdir(dir))) {
		if (*ent->d_name == '.')
			continue;

		if (ignore(ent->d_name))
			continue;

		if (level == 0 && level0_ignore(ent->d_name))
			continue;

		if (isdir(ent, path, len)) {
			add_entry(entries, nfiles, ent->d_name, 1);
			++nfiles;

			if (recurse) {
				char *full;

				/* note: +2 for / and \0 */
				full = malloc(len + strlen(ent->d_name) + 2);
				if (!full) {
					printf("Out of memory\n");
					exit(1);
				}
				if (level == 0)
					strcpy(full, ent->d_name);
				else
					sprintf(full, "%s/%s",
						path, ent->d_name);
				process_dir(full, level + 1);
				free(full);
			} else if (verbose > 1)
				printf("  %s/\n", ent->d_name);
		} else {
			if (verbose > 1)
				printf("  %s\n", ent->d_name);
			add_entry(entries, nfiles, ent->d_name, 0);
			++nfiles;
		}
	}

	closedir(dir);

	return nfiles;
}


int main(int argc, char *argv[])
{
	char *dir = NULL;
	char *config = GOPHER_CONFIG;
	char full[PATH_MAX];
	int c;
	int level;

	while ((c = getopt(argc, argv, "c:prs:v")) != -1)
		switch (c) {
		case 'c':
			config = strdup(optarg);
			break;
		case 'p':
			process_cache = 1;
			break;
		case 'r':
			recurse = 1;
			break;
		case 's':
			sorttype = strtol(optarg, NULL, 0);
			break;
		case 'v':
			++verbose;
			break;
		default:
			printf("usage: %s [-rv] [dir]\n", *argv);
			exit(1);
		}

	read_config(config);

	mime_init();

	if (!realpath(root_dir, full)) {
		perror(root_dir);
		exit(1);
	}
	if (strcmp(root_dir, full)) {
		free(root_dir);
		root_dir = strdup(full);
		if (root_dir == NULL) {
			printf("Out of memory\n");
			exit(1);
		}
	}

	if (chdir(root_dir)) {
		perror(root_dir);
		exit(1);
	}

	if (optind < argc) {
		dir = argv[optind];
		if (!realpath(dir, full)) {
			perror(dir);
			exit(1);
		}
		if (strncmp(root_dir, full, strlen(root_dir))) {
			printf("%s is not a subdir of %s\n", dir, root_dir);
			exit(1);
		}
		dir = full + strlen(root_dir);
		if (*dir == '/')
			++dir;
	}

	if (dir == NULL || *dir == '\0')
		dir = ".";

	if (verbose > 1)
		printf("hostname '%s' port '%d'\nbase '%s' dir '%s'\n",
		       hostname, port, root_dir, dir);

	level = strcmp(dir, ".") ? 1 : 0;
	process_dir(dir, level);

	/* This is for valgrind and will not be 100% correct if you */
	/* have anything other than a stock gofish.conf */
	free(root_dir);
	free(hostname);

	return 0;
}


/* Dummy functions for config */
void set_listen_address(char *addr) {}
void http_set_header(char *fname, int header) {}

/*
 * Kernel coding standard.
 * Local Variables:
 * tab-width: 8
 * c-basic-offset: 8
 * indent-tabs-mode: t
 * End:
 */
