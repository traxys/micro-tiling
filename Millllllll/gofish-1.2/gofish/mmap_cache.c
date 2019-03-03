/*
 * mmap-cache.c - GoFish mmap caching for performance
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

/* All knowledge of mmap is isolated to this file. */

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
#include <sys/stat.h>

#include "gofish.h"

#ifdef HAVE_MMAP
#include <sys/mman.h>
#else

#define PROT_READ	0
#define MAP_SHARED	0
#define MAP_FAILED	((void *)-1)


/* This is an incomplete implementation of mmap just for GoFish start,
 * prot, flags, and offset args ignored
 */
void *mmap(void *start,  size_t length, int prot ,
		   int flags, int fd, off_t offset)
{
	char *buf;

	buf = malloc(length);
	if (buf == NULL)
		return MAP_FAILED;

	lseek(fd, 0, SEEK_SET);
	if (READ(fd, buf, length) != length) {
		free(buf);
		return MAP_FAILED;
	}

	return buf;
}

int munmap(void *start, size_t length)
{
	free(start);
	return 0;
}
#endif

unsigned bad_munmaps;


#ifdef MMAP_CACHE

int mmap_cache_size = MMAP_CACHE_SIZE;


struct cache {
	unsigned char *mapped;
	int len;
	time_t time;
	time_t mtime;
	ino_t ino;
	int in_use;
};

static struct cache *mmap_cache;


void mmap_init()
{
	int i;

	if (mmap_cache_size < max_conns) {
		syslog(LOG_ERR, "mmap_cache_size must be >= %d", max_conns);
		exit(1);
	}

	mmap_cache = calloc(mmap_cache_size, sizeof(struct cache));
	if (mmap_cache == NULL) {
		syslog(LOG_ERR, "mmap_init: out of memory");
		exit(1);
	}

	/* this is hacky but it gets the lrus in order */
	for (i = 0; i < mmap_cache_size; ++i)
		mmap_cache[i].time = i;
}


unsigned char *mmap_get(struct connection *conn, int fd)
{
	int i;
	struct cache *lru, *m;
	time_t t = LONG_MAX;
	struct stat sbuf;

	if (fstat(fd, &sbuf)) {
		perror("fstat");
		return NULL;
	}

	lru = NULL;
	for (i = 0, m = mmap_cache; i < mmap_cache_size; ++i, ++m)
		if (sbuf.st_ino == m->ino) { /* can we have a zero ino? */
			/* match */
			if (sbuf.st_mtime != m->mtime)
				break;
			m->in_use++;
			time(&m->time);
			return m->mapped;
		} else if (m->in_use == 0) {
			if (m->time < t) {
				t = m->time;
				lru = m;
			}
		}

	/* no matches */

	if (lru == NULL) {
		syslog(LOG_DEBUG, "REAL PROBLEMS: no lru!!!\n");
		return NULL;
	}

	if (lru->mapped)
		munmap(lru->mapped, lru->len);


	lru->mapped = mmap(NULL, conn->len, PROT_READ, MAP_SHARED, fd, 0);
	if (lru->mapped == MAP_FAILED) {
		syslog(LOG_DEBUG, "REAL PROBLEMS: mmap failed!!");
		return NULL;
	}

	lru->ino = sbuf.st_ino;
	lru->len = conn->len;
	time(&lru->time);
	lru->in_use = 1;
	lru->mtime = sbuf.st_mtime;

	return lru->mapped;
}


void mmap_release(struct connection *conn)
{
	struct cache *m;
	int i;

	for (i = 0, m = mmap_cache; i < mmap_cache_size; ++i, ++m)
		if (m->mapped == conn->buf) {
			m->in_use--;
			return;
		}

	syslog(LOG_DEBUG, "PROBLEMS: buffer not in cache\n");
}

#else

void mmap_init(void) {}


unsigned char *mmap_get(struct connection *conn, int fd)
{
	unsigned char *mapped;

	/* We mess around with conn->len */
	conn->mapped = conn->len;
	mapped = mmap(NULL, conn->mapped, PROT_READ, MAP_SHARED, fd, 0);
	if (mapped == MAP_FAILED)
		return NULL;

#ifdef MADV_SEQUENTIAL
	/* folkert@vanheusden.com */
	(void)madvise(mapped, conn->mapped, MADV_SEQUENTIAL);
#endif

	return mapped;
}


void mmap_release(struct connection *conn)
{
	if (munmap(conn->buf, conn->mapped)) {
		++bad_munmaps;
		syslog(LOG_ERR, "munmap %p %d", conn->buf, conn->mapped);
	}
}

#endif /* MMAP_CACHE */

/*
 * Kernel coding standard.
 * Local Variables:
 * tab-width: 8
 * c-basic-offset: 8
 * indent-tabs-mode: t
 * End:
 */
