%global major_version 1
%global minor_version 20
%global micro_version 2
%global append_tag 0
%global attachment_uuid d7d1ee1b-c6c4-40ea-ad48-b8417fecb001

%define debug_package %{nil}

Name:		forgejo
Version:	%{major_version}.%{minor_version}.%{micro_version}
Release:	%{append_tag}%{?dist}
Summary:	Self-hosted lightweight software forge
License:	MIT
URL:		https://forgejo.org
Source0:	https://codeberg.org/attachments/%{attachment_uuid}
#Source0:	https://github.com/go-gitea/gitea/releases/download/v%{version}/%{name}-src-%{version}.tar.gz
#Source1:	https://github.com/go-gitea/gitea/releases/download/v%{version}/%{name}-docs-%{version}.tar.gz
Source2:	forgejo.service
Source3:  forgejo.firewalld
Source4:  README.EL+Fedora
Source5:  forgejo.httpd
Source6:  forgejo.nginx
Source7:  forgejo.caddy
Source8:  forgejo.sysusers

Patch1:		0001-forgejo.app.ini.patch

BuildRequires:	systemd
BuildRequires:	go >= 1.17.0
BuildRequires:	git
BuildRequires:	make
BuildRequires:	nodejs-devel >= 16.0.0
BuildRequires:	npm
BuildRequires:	go-srpm-macros
BuildRequires:	pam-devel
Requires:	git
Requires:	systemd
Requires: openssh-server
Requires(pre):	shadow-utils
Requires(post):	systemd
Requires(postun):	systemd
Requires(preun):	systemd

Conflicts:	git-web
Conflicts:  gitea

# Suggesting httpd for now
Suggests:	httpd

%description
Forgejo is a self-hosted lightweight software forge.
Easy to install and low maintenance, it just does the job

Brought to you by an inclusive community under the umbrella
of Codeberg e.V., a democratic non-profit organization,
Forgejo can be trusted to be exclusively Free Software. It
is a "soft" fork of Gitea with a focus on scaling, federation
and privacy.

%package httpd
Summary:  Apache (httpd) configuration for %{name}
Requires: forgejo
Requires: httpd

%description httpd
This subpackage contains Apache configuration files that can be used to reverse
proxy for Gitea.

%package nginx
Summary: nginx configuration for %{name}
Requires: forgejo
Requires: nginx

%description nginx
This subpackage contains an nginx configuration file that can be used to reverse
proxy for Gitea.

%package caddy
Summary: caddy configuration for %{name}
Requires: forgejo
Requires: caddy >= 2.0.0

%description caddy
This subpackage contains an caddy configuration file that can be used to reverse
proxy for Gitea.

#%package docs
#Summary: Documentation for %{name}

#%description docs
#This subpackage contains the Gitea documentation from https://docs.gitea.io

%prep
%setup -q -n %{name}-src-%{version}-%{append_tag}
%patch1 -p1

install -m 0644 %{SOURCE4} .
for file in $(find . -type f -name "*.css"); do
  chmod -x ${file}
done

%build
# Default support for sqlite and pam (not provided by upstream by default)
export TAGS="sqlite sqlite_unlock_notify pam"
export LDFLAGS="-s -w -X \"main.Version=%{version}\" -X \"code.gitea.io/gitea/modules/setting.CustomPath=/etc/forgejo\" -X \"code.gitea.io/gitea/modules/setting.AppWorkPath=/var/lib/forgejo\""

# Probably not needed, but just in case I guess.
TAGS="${TAGS}" LDFLAGS="${LDFLAGS}" make build

%install
# The binary comes out as "gitea" for now
install -D -m 755 gitea $RPM_BUILD_ROOT%{_bindir}/forgejo
install -D -m 644 %{SOURCE2} $RPM_BUILD_ROOT/%{_unitdir}/forgejo.service
install -D -m 644 custom/conf/app.example.ini $RPM_BUILD_ROOT%{_sysconfdir}/forgejo/conf/app.ini
install -D -m 644 %{SOURCE3} $RPM_BUILD_ROOT%{_prefix}/lib/firewalld/services/%{name}.xml
install -D -m 644 %{SOURCE5} $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/%{name}.conf
install -D -m 644 %{SOURCE6} $RPM_BUILD_ROOT%{_sysconfdir}/nginx/conf.d/%{name}.conf
install -D -m 644 %{SOURCE7} $RPM_BUILD_ROOT%{_sysconfdir}/caddy/Caddyfile.d/%{name}.caddyfile
install -D -m 644 %{SOURCE8} $RPM_BUILD_ROOT%{_sysusersdir}/%{name}.conf
mkdir -p $RPM_BUILD_ROOT%{_datadir}/forgejo \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data/lfs \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data/tmp \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data/tmp/uploads \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data/tmp/pprof \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data/sessions \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data/avatars \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data/attachments \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/data/repo-avatars \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/indexers \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/indexers/issues.bleve \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/indexers/issues.queue \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/indexers/repos.bleve \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/queues \
  $RPM_BUILD_ROOT%{_localstatedir}/lib/forgejo/repositories \
  $RPM_BUILD_ROOT%{_localstatedir}/log/forgejo \
  $RPM_BUILD_ROOT%{_sysconfdir}/forgejo/{conf,https,mailer}

cp -r options $RPM_BUILD_ROOT%{_datadir}/forgejo/
cp -r public $RPM_BUILD_ROOT%{_datadir}/forgejo/
cp -r templates $RPM_BUILD_ROOT%{_datadir}/forgejo/
#cp -r web_src/less $RPM_BUILD_ROOT%{_datadir}/forgejo/public
#install -d $RPM_BUILD_ROOT%{_datadir}/%{name}/docs.gitea.io/
#tar -xvzf %{SOURCE1} -C $RPM_BUILD_ROOT%{_datadir}/%{name}/docs.gitea.io

mkdir -p $RPM_BUILD_ROOT%{_tmpfilesdir}/
cat > $RPM_BUILD_ROOT%{_tmpfilesdir}/%{name}.conf <<EOF
d /run/forgejo 0755 git git -
EOF

%pre
# Not official
%if 0%{?fedora} || 0%{?rhel} >= 9
%sysusers_create_compat %{SOURCE8}
%else
%{_sbindir}/groupadd -r git 2>/dev/null || :
%{_sbindir}/useradd -r -g git \
  -s /sbin/nologin -d %{_datadir}/%{name} \
  -c 'Gitea' git 2>/dev/null || :
%endif

%preun
%systemd_preun %{name}.service

%post
%systemd_post %{name}.service
systemd-tmpfiles --create %{name}.conf || :

%postun
%systemd_postun_with_restart %{name}.service

%files
%doc README.EL+Fedora README.md custom/conf/app.example.ini
%license LICENSE
#%exclude %{_datadir}/%{name}/docs.gitea.io
%{_unitdir}/forgejo.service
%{_bindir}/forgejo
%{_prefix}/lib/firewalld/services/%{name}.xml
%{_tmpfilesdir}/%{name}.conf
%{_sysusersdir}/%{name}.conf

%defattr(0660,root,git,770)
%dir %{_sysconfdir}/forgejo
%dir %{_sysconfdir}/forgejo/conf
%dir %{_sysconfdir}/forgejo/https
%dir %{_sysconfdir}/forgejo/mailer
%dir %{_localstatedir}/log/forgejo
%config(noreplace) %{_sysconfdir}/forgejo/conf/app.ini

%defattr(0660,git,git,750)
%{_datadir}/forgejo
%{_localstatedir}/lib/forgejo

%files httpd
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf

%files nginx
%config(noreplace) %{_sysconfdir}/nginx/conf.d/%{name}.conf

%files caddy
%config(noreplace) %{_sysconfdir}/caddy/Caddyfile.d/%{name}.caddyfile

#%files docs
#%{_datadir}/%{name}/docs.gitea.io

%changelog
* Sun Jul 30 2023 Louis Abel <tucklesepk@gmail.com> - 1.20.2-0
- Update to 1.20.2-0

* Mon Jul 24 2023 Louis Abel <tucklesepk@gmail.com> - 1.20.1-0
- Update to 1.20.1-0

* Wed Jul 05 2023 Louis Abel <tucklesepk@gmail.com> - 1.19.4-0
- Updates to 1.19.4-0

* Wed May 03 2023 Louis Abel <tucklesepk@gmail.com> - 1.19.3-0
- Updates to 1.19.3-0

* Fri Apr 28 2023 Louis Abel <tucklesepk@gmail.com> - 1.19.2-0
- Updates to 1.19.2-0

* Sun Apr 16 2023 Louis Abel <tucklesepk@gmail.com> - 1.19.1-0
- Updates to 1.19.1-0

* Wed Apr 05 2023 Louis Abel <tucklesepk@gmail.com> - 1.19.0-3
- Updates to 1.19.0-3

* Tue Mar 21 2023 Louis Abel <tucklesepk@gmail.com> - 1.19.0-2
- Updates to 1.19.0-2

* Tue Mar 07 2023 Louis Abel <tucklesepk@gmail.com> - 1.18.5-0.0.1
- Fix requires

* Tue Feb 28 2023 Louis Abel <tucklesepk@gmail.com> - 1.18.5-0
- Update to 1.18.5
