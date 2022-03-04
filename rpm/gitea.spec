%global major_version 1
%global minor_version 16
%global micro_version 3

# Default support for sqlite and pam (not provided by upstream by default)
%global gitea_tags "sqlite sqlite_unlock_notify pam"

%define debug_package %{nil}

Name:		gitea
Version:	%{major_version}.%{minor_version}.%{micro_version}
Release:	2%{?dist}
Summary:	A painless self-hosted Git service
License:	MIT
URL:		https://gitea.io
Source0:	https://github.com/go-gitea/gitea/releases/download/v%{version}/gitea-src-%{version}.tar.gz
Source1:	https://github.com/go-gitea/gitea/releases/download/v%{version}/gitea-docs-%{version}.tar.gz
Source2:	gitea.service
Source3:  gitea.firewalld
Source4:  README.EL+Fedora
Source5:  gitea.httpd
Source6:  gitea.nginx
Source7:  gitea.caddy

Patch1:		0001-gitea.app.ini.patch

BuildRequires:	systemd
BuildRequires:	go >= 1.16.0
BuildRequires:	git
BuildRequires:	make
BuildRequires:	nodejs-devel >= 16.0.0
BuildRequires:	npm
BuildRequires:	go-srpm-macros
BuildRequires:	pam-devel
Requires:	git
Requires:	systemd
Requires: openssh-server
Requires(pre):	shadow
Requires(post):	systemd
Requires(postun):	systemd
Requires(preun):	systemd

Conflicts:	git-web

# Suggesting httpd for now
Suggests:	httpd

%description
A painless self-hosted Git service.

Gitea is a community managed fork of Gogs. A lightweight code hosting solution
written in Go and published under the MIT license.

%package httpd
Summary:  Apache (httpd) configuration for %{name}
Requires: gitea
Requires: httpd

%description httpd
This subpackage contains Apache configuration files that can be used to reverse
proxy for Gitea.

%package nginx
Summary: nginx configuration for %{name}
Requires: gitea
Requires: nginx

%description nginx
This subpackage contains an nginx configuration file that can be used to reverse
proxy for Gitea.

%package caddy
Summary: caddy configuration for %{name}
Requires: gitea
Requires: caddy >= 2.0.0

%description caddy
This subpackage contains an caddy configuration file that can be used to reverse
proxy for Gitea.

%package docs
Summary: Documentation for %{name}

%description docs
This subpackage contains the Gitea documentation from https://docs.gitea.io

%prep
%setup -q -c
%patch1 -p1
install -m 0644 %{SOURCE4} .
for file in $(find . -type f - name "*.css"); do
  chmod -x ${file}
done

%build
export TAGS="%{gitea_tags}"
export LDFLAGS="-s -w -X \"main.Version=%{version}\" -X \"code.gitea.io/gitea/modules/setting.CustomPath=/etc/gitea\" -X \"code.gitea.io/gitea/modules/setting.AppWorkPath=/var/lib/gitea\""

# Probably not needed, but just in case I guess.
TAGS="${TAGS}" LDFLAGS="${LDFLAGS}" make build

%install
install -D -m 755 gitea $RPM_BUILD_ROOT%{_bindir}/gitea
install -D -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_unitdir}/gitea.service
install -D -m 644 custom/conf/app.example.ini $RPM_BUILD_ROOT%{_sysconfdir}/gitea/conf/app.ini
install -D -m 644 %{SOURCE3} $RPM_BUILD_ROOT%{_prefix}/lib/firewalld/services/%{name}.xml
install -D -m 644 %{SOURCE5} $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/%{name}.conf
install -D -m 644 %{SOURCE6} $RPM_BUILD_ROOT%{_sysconfdir}/nginx/conf.d/%{name}.conf
install -D -m 644 %{SOURCE7} $RPM_BUILD_ROOT%{_sysconfdir}/caddy/Caddyfile.d/%{name}.caddyfile
mkdir -p $RPM_BUILD_ROOT%{_datadir}/gitea \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data/lfs \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data/tmp \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data/tmp/uploads \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data/tmp/pprof \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data/sessions \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data/avatars \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data/attachments \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/data/repo-avatars \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/indexers \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/indexers/issues.bleve \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/indexers/issues.queue \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/indexers/repos.bleve \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/queues \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/gitea/repositories \
  $RPM_BUILD_ROOT%{_localstatedir}/log/gitea \
  $RPM_BUILD_ROOT%{_sysconfdir}/gitea/{conf,https,mailer}

cp -r options $RPM_BUILD_ROOT%{_datadir}/gitea/
cp -r public $RPM_BUILD_ROOT%{_datadir}/gitea/
cp -r templates $RPM_BUILD_ROOT%{_datadir}/gitea/
cp -r web_src/less $RPM_BUILD_ROOT%{_datadir}/gitea/public
install -d $RPM_BUILD_ROOT%{_datadir}/%{name}/docs.gitea.io/
tar -xvzf %{SOURCE1} -C $RPM_BUILD_ROOT%{_datadir}/%{name}/docs.gitea.io

mkdir -p $RPM_BUILD_ROOT%{_tmpfilesdir}/
cat > $RPM_BUILD_ROOT%{_tmpfilesdir}/%{name}.conf <<EOF
d /run/gitea 0755 git git -
EOF

%pre
# Not official
%{_sbindir}/groupadd -r git 2>/dev/null || :
%{_sbindir}/useradd -r -g git \
  -s /sbin/nologin -d %{_datadir}/%{name} \
  -c 'Gitea' git 2>/dev/null || :

%preun
%systemd_preun %{name}.service

%post
%systemd_post %{name}.service
systemd-tmpfiles --create %{name}.conf || :

%files
%doc README.EL+Fedora README.md custom/conf/app.example.ini
%license LICENSE
%exclude %{_datadir}/%{name}/docs.gitea.io
%{_unitdir}/gitea.service
%{_bindir}/gitea
%{_prefix}/lib/firewalld/services/%{name}.xml
%{_tmpfilesdir}/%{name}.conf

%defattr(0660,root,git,770)
%dir %{_sysconfdir}/gitea
%dir %{_sysconfdir}/gitea/conf
%dir %{_sysconfdir}/gitea/https
%dir %{_sysconfdir}/gitea/mailer
%dir %{_localstatedir}/log/gitea
%config(noreplace) %{_sysconfdir}/gitea/conf/app.ini

%defattr(0660,git,git,750)
%{_datadir}/gitea
%{_localstatedir}/lib/gitea

%files httpd
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf

%files nginx
%config(noreplace) %{_sysconfdir}/nginx/conf.d/%{name}.conf

%files caddy
%config(noreplace) %{_sysconfdir}/caddy/Caddyfile.d/%{name}.caddyfile

%files docs
%{_datadir}/%{name}/docs.gitea.io

%changelog
* Thu Mar 03 2022 Louis Abel <tucklesepk@gmail.com> - 1.16.3-2
- Update to 1.16.3
- Add nginx configuration
- Add caddy configuration

* Thu Feb 24 2022 Louis Abel <tucklesepk@gmail.com> - 1.16.2-1
- Update to 1.16.2

* Fri Feb 11 2022 Louis Abel <tucklesepk@gmail.com> - 1.16.1-2
- Initial release of 1.16.1 for Fedora and Enterprise Linux
- Clean up spec
