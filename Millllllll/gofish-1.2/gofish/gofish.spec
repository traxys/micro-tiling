Summary: A Gopher Server
Name: gofish
Version: 1.2
Release: 1
Copyright: GPL
Group: Networking/Daemons
Source: gopher://seanm.ca/9/gofish/gofish-%{version}.tar.gz
BuildRoot: /var/tmp/%{name}-buildroot
Conflicts: gopher, gopherd

%description
GoFish is a simple gopher / web server. It is designed with security
and low resource usage in mind. GoFish uses a single process that
handles all the connections. This provides low resource usage, good
latency (no context switches), and good scalability.

GoFish runs in a chroot(2) environment. This means that GoFish can
only serve files from the root directory or below. While GoFish must
run at root privilege to be able to use port 70, it drops to a normal
user while accessing files.

%package setup
Summary: Initial files for GoFish
Group: Networking/Daemons
Copyright: GPL

%description setup
This package contains the files needed to get GoFish up and running.
Only install this package the first time you install GoFish since it
overwrites files in the gopher root directory.

%prep
%setup
./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var

%build
make

%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR=$RPM_BUILD_ROOT install

# This is not installed by make install
mkdir -p $RPM_BUILD_ROOT/etc/rc.d/init.d
install init-gofish $RPM_BUILD_ROOT/etc/rc.d/init.d/gofish
install init-gopherd $RPM_BUILD_ROOT/etc/rc.d/init.d/gopherd

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc COPYING README INSTALL NEWS AUTHORS ChangeLog

/usr/sbin/gofish
/usr/sbin/gopherd
/usr/bin/mkcache
/usr/bin/gmap2cache
/usr/bin/check-files
/etc/rc.d/init.d/gopherd
/etc/rc.d/init.d/gofish
/usr/man/man1/*
/usr/man/man5/*

%files setup
%defattr(-,root,root)
/etc/gofish.conf
/etc/gofish-www.conf
/var/gopher/icons/*
/var/gopher/.gopher+
/var/gopher/.cache
/var/gopher/Configure_GoFish

%changelog
* Sun Dec  8 2002 Sean MacLennan <seanm@seanm.ca>
- Updated to 0.25
- /var/lib/gopherd -> /var/gopher
- webtest now part of make check

* Sat Nov  9 2002 Sean MacLennan <seanm@seanm.ca>
- Updated to 0.21
- Added webtest

* Sat Nov  2 2002 Sean MacLennan <seanm@seanm.ca>
- Updated to 0.20
- Added gofish-www.conf

* Sat Oct 26 2002 Sean MacLennan <seanm@seanm.ca>
- Updated to 0.19
- Added gmap2cache

* Sun Sep 22 2002 Sean MacLennan <seanm@seanm.ca>
- Updated to 0.11
- Split into two rpms

* Sat Aug 24 2002 Sean MacLennan <seanm@seanm.ca>
- Updated to 0.9
- Now using configure

* Fri Aug 16 2002 Sean MacLennan <seanm@seanm.ca>
- Updated to 0.7
- Added man pages

* Fri Aug  2 2002 Sean MacLennan <seanm@seanm.ca>
- Created spec file
