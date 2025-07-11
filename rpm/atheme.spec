## Define global settings
%global _hardened_build 1
%global major_version 7
%global minor_version 2
%global micro_version 12
# This is because the version of the package and the actual source tarball 
# differ pretty wildly
%global version_directory_number v%{major_version}.%{minor_version}.%{micro_version}
%global build_with_plugins 0

# Using atheme-services as a name would be fine, but that would
# require either A) Some folders named atheme and others named
# atheme-services or B) require me to list every directory
# on the configure line and make them point to -services.
# If this were to become an official package, I would consider it.
Name:		atheme
Version:	%{major_version}.%{minor_version}.%{micro_version}
Release:	1%{?dist}
Summary:	Services for IRC Networks

Group:		System Environment/Daemons
License:	MIT
URL:		https://atheme.net
Source0:	https://github.com/%{name}/%{name}/releases/download/%{version_directory_number}/%{name}-services-%{version_directory_number}.tar.xz
Source1:	%{name}.service
Source2:	%{name}.logrotate
Patch1:		%{name}-lockmodes.patch
Patch2:		%{name}-nodate.patch

BuildRequires:	cracklib-devel
BuildRequires:	perl-ExtUtils-Embed
BuildRequires:	openssl-devel
BuildRequires:	openldap-devel
BuildRequires:	qrencode-devel
BuildRequires:	gettext-devel
BuildRequires:	gcc
BuildRequires:	gcc-c++
BuildRequires:	git
# Fix future Fedora builds
BuildRequires:	perl(FindBin)

%if 0%{?rhel} >= 10
BuildRequires:	pcre2-devel
Requires:	pcre2
%else
BuildRequires:	pcre-devel
Requires:	pcre
%endif

Requires:	openssl
Requires:	cracklib

# OS Specific Requirements
BuildRequires:	systemd
Requires(post):	systemd
Requires(preun): systemd
Requires(postun): systemd
Requires:	systemd

Provides:	atheme = %{version}-%{release}
Provides:	atheme-services = %{version}-%{release}

%description
Atheme is a feature-packed, extremely customisable IRC services
daemon that is secure, stable and scalable. It is designed to
link with more than 20 kinds of IRCds and offers both a C API
and Perl interface.

%package	-n libathemecore1
Summary:	Atheme IRC Services core library
Group:		System Environment/Libraries

%description	-n libathemecore1
Atheme is a feature-packed, extremely customisable IRC services
daemon that is secure, stable and scalable. It is designed to
link with more than 20 kinds of IRCds and offers both a C API
and Perl interface.

%package	devel
Summary:	Atheme development headers
Requires:	atheme = %{version}-%{release}

%description	devel
Atheme is a feature-packed, extremely customisable IRC services
daemon that is secure, stable and scalable. It is designed to
link with more than 20 kinds of IRCds and offers both a C API
and Perl interface.

This package contains the development headers required for developing
against atheme.

%prep
%setup -q -n %{name}-services-%{version_directory_number}
%patch -P 1 -P 2 -p1

%build
# They decided to do submodules. Very anti-pattern.
#git submodule init
#git submodule update
# I am explicitly calling ldap, perl, pcre, cracklib support
%configure \
	--sysconfdir="%{_sysconfdir}/%{name}" \
	--bindir="%{_sbindir}" \
	--docdir="%{_docdir}/%{name}" \
	--enable-fhs-paths \
	--enable-warnings \
	--enable-contrib \
	--enable-large-net \
	--disable-rpath \
	--with-cracklib \
	--with-pcre \
	--with-perl \
	--with-ldap \
	--without-libmowgli

#make %{?_smp_mflags}
%make_build

%install
%make_install

%{__mkdir} -p ${RPM_BUILD_ROOT}%{_sysconfdir}/logrotate.d
%{__install} -m 0644 %{SOURCE2} \
	${RPM_BUILD_ROOT}%{_sysconfdir}/logrotate.d/%{name}

%{__mkdir} -p ${RPM_BUILD_ROOT}%{_sbindir}
%{__mkdir} -p ${RPM_BUILD_ROOT}%{_var}/log

# OS Specific
%{__install} -d -m 0755 ${RPM_BUILD_ROOT}%{_unitdir}
%{__install} -m 0644 %{SOURCE1} \
	${RPM_BUILD_ROOT}%{_unitdir}/atheme.service

# development headers
%{__mkdir} -p ${RPM_BUILD_ROOT}/%{_includedir}/%{name}/{inline,protocol}
%{__install} -m 0644 include/*.h \
	${RPM_BUILD_ROOT}%{_includedir}/%{name}
%{__install} -m 0644 include/inline/*.h \
	${RPM_BUILD_ROOT}%{_includedir}/%{name}/inline
%{__install} -m 0644 include/protocol/*.h \
	${RPM_BUILD_ROOT}%{_includedir}/%{name}/protocol

# missing tmpfiles
%{__mkdir} -p ${RPM_BUILD_ROOT}%{_tmpfilesdir}
cat > ${RPM_BUILD_ROOT}%{_tmpfilesdir}/%{name}.conf <<EOF
d /run/atheme 0755 atheme atheme -
EOF

%pre
# Since we are not an official Fedora build, we don't get an
# assigned uid/gid. This may make it difficult when installed
# on multiple systems that have different package sets.
%{_sbindir}/groupadd -r %{name} 2>/dev/null || :
%{_sbindir}/useradd -r -g %{name} \
	-s /sbin/nologin -d %{_datadir}/%{name} \
	-c 'Atheme IRC Services' %{name} 2>/dev/null || :

%preun
%systemd_preun %{name}.service

%post
%systemd_post %{name}.service
systemd-tmpfiles --create %{name}.conf || :

%postun
%systemd_postun_with_restart %{name}.service

%files
%defattr(-, root, root, -)
%doc /usr/share/doc/%{name}/*
%{_sbindir}/%{name}-services
%{_sbindir}/dbverify
%{_sbindir}/ecdsakeygen
%dir %attr(0750,root,atheme) %{_sysconfdir}/%{name}
%dir %attr(0700,atheme,atheme) %{_var}/log/%{name}
%dir %attr(0700,atheme,atheme) %{_sharedstatedir}/%{name}
%dir %{_datadir}/%{name}
%dir %{_libdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.motd
%config(noreplace) %attr(-,root,root) %{_sysconfdir}/logrotate.d/%{name}
%ghost %attr(0640,-,-) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%{_sysconfdir}/%{name}/*.example
%{_sysconfdir}/%{name}/*-example
%{_libdir}/%{name}/*
%{_datadir}/%{name}/*
%{_libdir}/libmowgli-2.so
%{_libdir}/libmowgli-2.so.0
%{_libdir}/libmowgli-2.so.0.0.0
%{_datadir}/locale/cy/LC_MESSAGES/atheme.mo
%{_datadir}/locale/da/LC_MESSAGES/atheme.mo
%{_datadir}/locale/de/LC_MESSAGES/atheme.mo
%{_datadir}/locale/es/LC_MESSAGES/atheme.mo
%{_datadir}/locale/fr/LC_MESSAGES/atheme.mo
%{_datadir}/locale/ru/LC_MESSAGES/atheme.mo
%{_datadir}/locale/tr/LC_MESSAGES/atheme.mo
%{_tmpfilesdir}/%{name}.conf

# OS Specific
%{_unitdir}/%{name}.service

%files -n libathemecore1
%defattr(-,root,root)
%{_libdir}/libathemecore.so.1
%{_libdir}/libathemecore.so.1.0.0

# development headers
%files devel
%defattr (0644,root,root,0755)
%dir %{_includedir}/%{name}
%dir %{_includedir}/%{name}/inline
%dir %{_includedir}/%{name}/protocol
%{_includedir}/%{name}/*.h
%{_includedir}/%{name}/inline/*.h
%{_includedir}/%{name}/protocol/*.h
%dir %{_includedir}/libmowgli-2
%{_includedir}/libmowgli-2/*
%{_libdir}/pkgconfig/atheme-services.pc
%{_libdir}/pkgconfig/libmowgli-2.pc
%{_libdir}/libathemecore.so

%changelog
* Sun Jan 30 2022 Louis Abel <tucklesepk@gmail.com> - 7.2.12-1
- Rebase to 7.2.12, which addresses auth bypass vulnerability
  when used with InspIRCd.

* Sun Aug 01 2021 Louis Abel <tucklesepk@gmail.com> - 7.2.11-2
- Add missing tmpfiles configuration
- Fix service file to not run as root

* Wed May 19 2021 Louis Abel <tucklesepk@gmail.com> - 7.2.11-1
- Update to 7.2.11

* Tue Oct 27 2020 Louis Abel <tucklesepk@gmail.com> - 7.2.10r2-3
- Replace some build pieces with macros, except make
- Add perl(FindBin) requirement

* Tue Feb 26 2019 Louis Abel <tucklesepk@gmail.com> - 7.2.10r2-2
- Automated build support
- Drop Fedora 28
- Add patch for lockmodes +k and +l as default locks
  This is to allow empty channel protection restoration when
  services are restarted
- Renamed atheme-libcore to be libathemecore

* Fri Nov 02 2018 Louis Abel <louis@shootthej.net> - 7.2.10r2-1
- Rebase to 7.2.10-r2
- Removed EL6 support
- Added git steps because they decided to have submodules.

* Wed Jan 17 2018 Louis Abel <louis@shootthej.net> - 7.2.9-2
- Fedora 27 Rebuild
- Separated libcore from main package
- Changed permissions to be more restrictive
- Rearranged libraries for devel package

* Wed Jul 12 2017 Louis Abel <louis@shootthej.net> - 7.2.9-2
- Fedora 26 Rebuild
- Version upgrade to 7.2.9

* Fri Feb 3 2017 Louis Abel <louis@shootthej.net> - 7.2.7-2
- Added atheme.conf as a ghost config file
- Fixed source0 url and name

* Wed Feb 1 2017 Louis Abel <louis@shootthej.net> - 7.2.7-1
- Rebase for version 7.2.7

* Wed Apr 6 2016 Louis Abel <louis@shootthej.net> - 7.2.6-1
- Initial build for Atheme 7.2.6

