#!/bin/sh

config_file () {
    local NEW="$1.new"
    [ -f "$NEW" ] || { echo "$NEW does not exist!"; return; }

    if [ -f "$1" ] ; then
	if [ "$2" = "-rm" ] ; then
	    rm "$NEW"
	elif cmp -s "$1" "$NEW" ; then
	    rm "$NEW"
	else
	    echo
	    echo "You might want to check $NEW"
	    echo
	fi
    else
	mv $NEW $1
    fi
}

config_file etc/gofish.conf
config_file etc/gofish-www.conf

# We try to use uid 70 gid 70 for gopher for historical reasons.
# But we will use a different uid/gid if they are in use.
if ! grep -q "^gopher:" /etc/group ; then
    if cat /etc/group | cut -d: -f3 | fgrep -q 70 ; then
	# 70 exists, just add a group
	groupadd gopher
    else
	groupadd -g 70 gopher
    fi
    echo "Added group gopher"
fi
if ! grep -q "^gopher:" /etc/passwd ; then
    if cat /etc/passwd | cut -d: -f3 | fgrep -q 70 ; then
	# 70 exists, just add a user
	useradd -u 70 -g gopher -d /var/gopher -s /bin/false -c "Gopherd User" gopher
    else
	useradd -g gopher -d /var/gopher -s /bin/false -c "Gopherd User" gopher
    fi
    echo "Added user gopher"
fi

# Add some sample files if nothing exists
if [ ! -d var/gopher ] ; then
  mv var/gopher.sample var/gopher
  chown -R gopher.gopher var/gopher
fi
rm -rf var/gopher.sample
