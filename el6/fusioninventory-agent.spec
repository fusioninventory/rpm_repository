## Disabling debug package 
## Can't build as noarch due to dmidecode requires
%global debug_package %{nil}


Name:        fusioninventory-agent
Summary:     FusionInventory agent
Group:       Applications/System
License:     GPLv2+
URL:         http://fusioninventory.org/

Version:     2.5.2
Release:     1%{?dist}
Source0:     https://github.com/fusioninventory/%{name}/releases/download/%{version}/FusionInventory-Agent-%{version}.tar.gz
Source1:     %{name}.cron

Requires:  perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
BuildRequires: perl-generators
BuildRequires: perl(ExtUtils::MakeMaker)

Requires:  perl-FusionInventory-Agent = %{version}-%{release}
Requires:  logrotate
Requires:  cronie
%ifarch %{ix86} x86_64
Requires:  dmidecode
%endif

Requires(post):     /sbin/chkconfig
Requires(preun):    /sbin/chkconfig, /sbin/service
Requires(postun):   /sbin/service

# excluding internal requires and windows stuff
# excluding perl(setup) and windows stuff
%filter_from_requires /perl(setup)/d; /perl(Win32.*)/d
%filter_from_provides /perl(setup)/d
%filter_setup

%description
FusionInventory Agent is an application designed to help a network
or system administrator to keep track of the hardware and software
configurations of computers that are installed on the network.

This agent can send information about the computer to a OCS Inventory NG
or GLPI server with the FusionInventory for GLPI plugin.

You can add additional packages for optional tasks:

* fusioninventory-agent-task-network
    Network Discovery and Inventory support
* fusioninventory-agent-inventory
    Local inventory support for FusionInventory
* fusioninventory-agent-task-deploy
    Software deployment support
* fusioninventory-agent-task-esx
    vCenter/ESX/ESXi remote inventory
* fusioninventory-agent-task-collect
    Custom information retrieval support
* fusioninventory-agent-task-wakeonlan
    Wake o lan task

Edit the /etc/sysconfig/%{name} file for service configuration.

%package -n perl-FusionInventory-Agent
Summary:        Libraries for Fusioninventory agent
BuildArch:      noarch
Requires:       perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
Requires:       perl(LWP)
Requires:       perl(Net::CUPS)
Requires:       perl(Net::SSLeay)
Requires:       perl(Proc::Daemon)
Requires:       perl(Socket::GetAddrInfo)

%description -n perl-FusionInventory-Agent
Libraries for Fusioninventory agent.

%package task-esx
Summary:    FusionInventory plugin to inventory vCenter/ESX/ESXi
BuildArch:  noarch
Requires:   %{name} = %{version}-%{release}

%description task-esx
fusioninventory-agent-task-ESX ask the running service agent to inventory an 
VMWare vCenter/ESX/ESXi server through SOAP interface

%package yum-plugin
Summary:       Ask FusionInventory agent to send an inventory when yum exits
Group:         System Environment/Base
BuildArch:     noarch
Requires:      yum
Requires:      %{name}

%description yum-plugin
fusioninventory-agent-yum-plugin asks the running service agent to send an
inventory when yum exits.

This requires the service to be running with the --rpc-trust-localhost option.

%package task-network
Summary:    NetDiscovery and NetInventory task for FusionInventory
Group:      Applications/System
BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}

%description task-network
fusioninventory-task-netdiscovery and fusioninventory-task-netinventory

%package task-deploy
Summary:    Software deployment support for FusionInventory agent
Group:      Applications/System
BuildArch:  noarch
Requires:   %{name} = %{version}-%{release}
Requires:   perl(Archive::Extract)

%description task-deploy
This package provides software deployment support for FusionInventory-agent

%package task-wakeonlan
Summary:    WakeOnLan task for FusionInventory
Group:      Applications/System
BuildArch:  noarch
Requires:   %{name} = %{version}-%{release}

%description task-wakeonlan
fusioninventory-task-wakeonlan

%package task-inventory
Summary:    Inventory task for FusionInventory
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}
Requires:   perl(Net::CUPS)
#This one is not available on EL6 for now;
#and this is a "recommanded", not a required one.
#Requires:   perl(Parse::EDID)

%description task-inventory
fusioninventory-task-inventory

%package task-collect
Summary:    Custom information retrieval support for FusionInventory agent
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}

%description task-collect
This package provides custom information retrieval support for
FusionInventory agent

%package cron
Summary:    Cron for FusionInventory agent
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}

%description cron
fusioninventory cron task


%prep
%setup -q -n FusionInventory-Agent-%{version}

sed -i contrib/unix/%{name}.init.redhat \
    -e "s/Default-Start: 3 5/Default-Start:/"

cat <<EOF | tee logrotate
%{_localstatedir}/log/%{name}/*.log {
    weekly
    rotate 7
    compress
    notifempty
    missingok
}
EOF

sed \
    -e "s/logger = .*/logger = syslog/" \
    -e "s/logfacility = .*/logfacility = LOG_DAEMON/" \
    -e 's|#include "conf\.d/"|include "conf\.d/"|' \
    -i etc/agent.cfg

cat <<EOF | tee %{name}.conf
#
# Fusion Inventory Agent Configuration File
# used by hourly cron job and service launcher to override the %{name}.cfg setup.
#
# DONT FORGET to enable the service !
#
# Add tools directory if needed (tw_cli, hpacucli, ipssend, ...)
PATH=/sbin:/bin:/usr/sbin:/usr/bin
# Global options (debug for verbose log, rpc-trust-localhost for yum-plugin)
OPTIONS="--debug "

# Mode, change to "cron" to activate
# - none (default on install) no activity
# - cron (inventory only) use the cron.hourly
OCSMODE[0]=none
# OCS Inventory or FusionInventory server URI
# OCSSERVER[0]=your.ocsserver.name
# OCSSERVER[0]=http://your.ocsserver.name/ocsinventory
# OCSSERVER[0]=http://your.glpiserveur.name/glpi/plugins/fusioninventory/
# corresponds with --local=%{_localstatedir}/lib/%{name}
# OCSSERVER[0]=local
# Wait before inventory (for cron mode)
OCSPAUSE[0]=120
# Administrative TAG (optional, must be filed before first inventory)
OCSTAG[0]=

EOF


%build
perl Makefile.PL \
     PREFIX=%{_prefix} \
     SYSCONFDIR=%{_sysconfdir}/fusioninventory \
     LOCALSTATEDIR=%{_localstatedir}/lib/%{name} \
     VERSION=%{version}-%{release}

make %{?_smp_mflags}


%install
rm -rf %{buildroot}

make install DESTDIR=%{buildroot}
find %{buildroot} -type f -name .packlist -exec rm -f {} ';'

%{_fixperms} %{buildroot}/*

mkdir -p %{buildroot}%{_localstatedir}/{log,lib}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/fusioninventory/conf.d

install -m 644 -D  logrotate     %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -m 644 -D  %{name}.conf  %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -m 755 -Dp %{SOURCE1}    %{buildroot}%{_sysconfdir}/cron.hourly/%{name}
install -m 755 -D contrib/unix/%{name}.init.redhat    %{buildroot}%{_initrddir}/%{name}


# Yum plugin installation
install -m 644 -D contrib/yum-plugin/%{name}.py   %{buildroot}%{_prefix}/lib/yum-plugins/%{name}.py
install -m 644 -D contrib/yum-plugin/%{name}.conf %{buildroot}%{_sysconfdir}/yum/pluginconf.d/%{name}.conf

%check
#make test

%post
/sbin/chkconfig --add %{name}


%preun
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop &>/dev/null
    /sbin/chkconfig --del %{name}
fi
exit 0


%postun
if [ $1 -ge 1 ]; then
    /sbin/service %{name} condrestart &>/dev/null
fi
exit 0


%files
%dir %{_sysconfdir}/fusioninventory
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{_sysconfdir}/fusioninventory/agent.cfg
%config(noreplace) %{_sysconfdir}/fusioninventory/conf.d
%config(noreplace) %{_sysconfdir}/fusioninventory/inventory-server-plugin.cfg
%config(noreplace) %{_sysconfdir}/fusioninventory/server-test-plugin.cfg
%config(noreplace) %{_sysconfdir}/fusioninventory/ssl-server-plugin.cfg
%config(noreplace) %{_sysconfdir}/fusioninventory/proxy-server-plugin.cfg
%config(noreplace) %{_sysconfdir}/fusioninventory/proxy2-server-plugin.cfg


%{_sysconfdir}/cron.hourly/%{name}
%{_initrddir}/%{name}
%{_bindir}/fusioninventory-agent
%{_bindir}/fusioninventory-injector
%{_mandir}/man1/fusioninventory-agent*
%{_mandir}/man1/fusioninventory-injector*
%dir %{_localstatedir}/log/%{name}
%dir %{_localstatedir}/lib/%{name}
%dir %{_datadir}/fusioninventory
%dir %{_datadir}/fusioninventory/lib
%dir %{_datadir}/fusioninventory/lib/FusionInventory
%dir %{_datadir}/fusioninventory/lib/FusionInventory/Agent
%dir %{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task


%files -n perl-FusionInventory-Agent
%doc Changes LICENSE THANKS
#excluding sub-packages files
#%%exclude %%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/*
%{_datadir}/fusioninventory

%files yum-plugin
%config(noreplace) %{_sysconfdir}/yum/pluginconf.d/%{name}.conf
%{_prefix}/lib/yum-plugins/%{name}.*

%files task-esx
%{_bindir}/fusioninventory-esx
%{_mandir}/man1/fusioninventory-esx.1*
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/ESX.pm
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/SOAP

%files task-network
%{_bindir}/fusioninventory-netdiscovery
%{_bindir}/fusioninventory-netinventory
%{_mandir}/man1/fusioninventory-netdiscovery.1*
%{_mandir}/man1/fusioninventory-netinventory.1*
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/NetDiscovery.pm
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/NetInventory.pm

%files task-deploy
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Deploy.pm
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Deploy

%files task-wakeonlan
%{_bindir}/fusioninventory-wakeonlan
%{_mandir}/man1/fusioninventory-wakeonlan.1*
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/WakeOnLan.pm

%files task-inventory
%{_bindir}/fusioninventory-inventory
%{_bindir}/fusioninventory-remoteinventory
%{_mandir}/man1/fusioninventory-*inventory.1*
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Inventory.pm
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Inventory

%files task-collect
%{_datadir}/fusioninventory/lib/FusionInventory/Agent/Task/Collect.pm

%files cron
%{_sysconfdir}/cron.hourly/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}


%changelog
* Tue Dec 17 2019 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.5.2-1
- Last upstream release
- Drop patch applied upstream
- Add missing configuration files

* Tue Jul 16 2019 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.5.1-2
- Apply upstream patch that fixes issues on EL6/7

* Mon Jul 08 2019 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.5.1-1
- Last upstream release
- Remove patches applied upstream

* Tue May 07 2019 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.5-4
- Add patch to fix SSL on with http modules

* Thu May 02 2019 Guillaume Bougard <gbougard AT teclib DOT com> - 2.5-3
- Add patches to fix agent HTTP server plugins integration

* Thu Apr 18 2019 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.5-2
- Re-add tasks files in main perl package, to solve dependencies issues on package

* Mon Apr 15 2019 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.5-1
- Last upstream release
- Tasks files were provided also in main perl package
- Apply upstream minor fixes patch
- task-wakeonlan is back (see https://github.com/fusioninventory/fusioninventory-agent/issues/495#issuecomment-435110369 about dependancy issue)

* Thu Mar 07 2019 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.4.3-2
- Fix for HTTPD server not listening

* Mon Feb 25 2019 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.4.3-1
- Last upstream release

* Wed Oct 03 2018 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.4.2-1
- Last upstream release
- Drop patch applied upstream

* Tue Jul 10 2018 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.4.1-2
- Add patch for Net-Ping issue on EL versions
- Add upstream patch to fix wrong variable name
-
* Tue Jul 03 2018 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.4.1-1
- Last upstream release

* Mon Jan 15 2018 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.4-3
- Change logging according to upstream recommandations

* Thu Jan 11 2018 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.4-1
- Last upstream release
- Put cron stuff in a separate sub-package
- Provide conf.d configuration directory

* Sat Nov 25 2017 Mairanne Lombard <jehane@fedoraproject.org> - 2.3.21-4
- Fix perl filter issues; BZ #145919 - thanks to Jitka Plesnikova 

* Mon Oct 16 2017 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.3.21-3
- Do not provides perl(setup); BZ #1485919 - thanks to E. Seyman

* Thu Aug 10 2017 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.3.21-2
- Fix missing provides issue on perl(setup)

* Tue Aug 01 2017 Marianne Lombard <jehane@fedoraproject.org> - 2.3.21-1
- Last upstream release

* Tue Jun 06 2017 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.3.20-1
- Last upstream release
- Drop patches, upstream has provided fixes

* Mon Feb 20 2017 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.3.19-1
- Last upstream release

* Tue Jun 21 2016 Johan Cwiklinski <jcwiklinski AT teclib DOT com> - 2.3.18-1
- Last upstream release
- Add task-* subpackages
- Use upstream provided initscript
- Update according to EL7 specfile

* Sun Feb 26 2012 Remi Collet <remi@fedoraproject.org> - 2.1.14-1
- update to 2.1.14
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.14/Changes

* Mon Nov 28 2011 Remi Collet <remi@fedoraproject.org> - 2.1.12-1
- update to 2.1.12
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.12/Changes
- upstream patch for http://forge.fusioninventory.org/issues/1161

* Sat Aug 06 2011 Remi Collet <remi@fedoraproject.org> - 2.1.9-3
- adapt filter

* Mon Jul 25 2011 Petr Sabata <contyk@redhat.com> - 2.1.9-2
- Perl mass rebuild

* Sun Jun 26 2011 Remi Collet <Fedora@famillecollet.com> 2.1.9-1
- missing dist tag

* Wed Jun 15 2011 Remi Collet <Fedora@famillecollet.com> 2.1.9-1
- update to 2.1.9
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.9/Changes

* Sat Jun 11 2011 Remi Collet <Fedora@famillecollet.com> 2.1.9-0.1.git9bd1238
- update to 2.1.9 from git
- improved init script for systemd
- improved comment for use with glpi-fusioninventory

* Thu Mar 31 2011 Remi Collet <Fedora@famillecollet.com> 2.1.8-2
- revert change for issue 656 which breaks compatibility

* Wed Mar 30 2011 Remi Collet <Fedora@famillecollet.com> 2.1.8-1
- update to 2.1.8
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.8/Changes

* Thu Dec 30 2010 Remi Collet <Fedora@famillecollet.com> 2.1.7-2
- add the yum-plugin sub-package

* Mon Dec 13 2010 Remi Collet <Fedora@famillecollet.com> 2.1.7-1
- update to 2.1.7
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.7/Changes

* Sun Nov 28 2010 Remi Collet <Fedora@famillecollet.com> 2.1.7-0.1.beta1
- update to 2.1.7 beta1

* Sat Nov 13 2010 Remi Collet <Fedora@famillecollet.com> 2.1.6-1.1
- fix perl filter on EL-6

* Wed Oct 06 2010 Remi Collet <Fedora@famillecollet.com> 2.1.6-1
- update to 2.1.6
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.6/Changes
- fix init script for multi-server in daemon mode
- workaround for http://forge.fusioninventory.org/issues/414

* Wed Sep 15 2010 Remi Collet <Fedora@famillecollet.com> 2.1.5-1
- update to 2.1.5
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.5/Changes

* Fri Sep 10 2010 Remi Collet <Fedora@famillecollet.com> 2.1.3-2
- add %%check

* Sat Sep 04 2010 Remi Collet <Fedora@famillecollet.com> 2.1.3-1
- update to 2.1.3
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.3/Changes

* Wed Aug 25 2010 Remi Collet <Fedora@famillecollet.com> 2.1.2-1
- update to 2.1.2
  http://cpansearch.perl.org/src/FUSINV/FusionInventory-Agent-2.1.2/Changes

* Wed Aug 18 2010 Remi Collet <Fedora@famillecollet.com> 2.1.1-1
- update to 2.1.1

* Wed Aug 18 2010 Remi Collet <Fedora@famillecollet.com> 2.1-2.gita7532c0
- update to git snaphost which fix EL issues
- fix init script
- adapt perl filter for recent/old fedora or EL

* Mon Aug 16 2010 Remi Collet <Fedora@famillecollet.com> 2.1-1
- update to 2.1
- switch download URL back to CPAN
- add %%{perl_vendorlib}/auto
- filter perl(Win32*) from Requires
- add patch (from git) to reopen the file logger if needed

* Sat May 29 2010 Remi Collet <Fedora@famillecollet.com> 2.0.6-1
- update to 2.0.6
- swicth download URL to forge

* Wed May 12 2010 Remi Collet <Fedora@famillecollet.com> 2.0.5-1
- update to 2.0.5

* Tue May 11 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-4.gitf7c5492
- git snapshot fix perl 5.8.8 (EL5) issue

* Sat May 08 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-4.gitddfdeaf
- git snapshot fix daemon issue
- add FUSINVOPT for global options (p.e.--debug)

* Sat May 08 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-3
- add support for daemon mode

* Fri May 07 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-2
- info about perl-FusionInventory-Agent-Task-OcsDeploy
- spec cleanup
- french translation
- set Net::CUPS and Archive::Extract optionnal on RHEL4

* Fri May 07 2010 Remi Collet <Fedora@famillecollet.com> 2.0.4-1
- update to 2.0.4 which fixes important bugs when cron is used

* Sat May 01 2010 Remi Collet <Fedora@famillecollet.com> 2.0.3-1
- initial spec

