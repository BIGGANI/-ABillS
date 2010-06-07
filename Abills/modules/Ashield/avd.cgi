#!/usr/bin/perl -w
# AVD processing system
#

use vars qw($begin_time %FORM %LANG 
$DATE $TIME
$CHARSET 
@MODULES
$admin
$users 
$payments
);

BEGIN {
 my $libpath = '../';
 
 $sql_type='mysql';
 unshift(@INC, $libpath ."Abills/$sql_type/");
 unshift(@INC, $libpath);
 unshift(@INC, $libpath . 'libexec/');

 eval { require Time::HiRes; };
 if (! $@) {
    Time::HiRes->import(qw(gettimeofday));
    $begin_time = gettimeofday();
   }
 else {
    $begin_time = 0;
  }
}

require "config.pl";
use Abills::Base;
use Abills::SQL;
use Abills::HTML;
use Users;
use Finance;
use Admins;
use Ashield;
use Fees;

require "language/$conf{default_language}.pl";
my $debug  = $conf{ASHIELD_AVD_DEBUG} || 0;
my $html   = Abills::HTML->new();
my $sql    = Abills::SQL->connect($conf{dbtype}, $conf{dbhost}, $conf{dbname}, $conf{dbuser},
    $conf{dbpasswd}, { CHARSET => ($conf{dbcharset}) ? $conf{dbcharset} : undef  });
my $db     = $sql->{db};
#Operation status
my $status = '';

#Check allow ips
if ($conf{PAYSYS_IPS}) {
	$conf{PAYSYS_IPS}=~s/ //g;
	@ips_arr = split(/,/, $conf{PAYSYS_IPS});
	
	#Default DENY FROM all
	my $allow = 0;
	foreach my $ip (@ips_arr) {
		#Deny address
		if ($ip =~ /^!/  && $ip =~ /$ENV{REMOTE_ADDR}$/) {
      last;
		 }
		#allow address
		elsif ($ENV{REMOTE_ADDR} =~ /^$ip/) {
			$allow=1;
			last;
		 }
	  #allow from all networks
	  elsif ($ip eq '0.0.0.0') {
	  	$allow=1;
	  	last;
	   }
	 }

  #Address not allow
  #Send info mail to admin
  if (! $allow) {
  	print "Content-Type: text/html\n\n";
  	print "Error: IP '$ENV{REMOTE_ADDR}' DENY by System";
    sendmail("$conf{ADMIN_MAIL}", "$conf{ADMIN_MAIL}", "ABillS - Ashield", 
              "IP '$ENV{REMOTE_ADDR}' DENY by System", "$conf{MAIL_CHARSET}", "2 (High)");
  	exit;
   } 
}

if ($conf{PAYSYS_PASSWD}) {
	my($user, $password)=split(/:/, $conf{PAYSYS_PASSWD});
	if (defined($ENV{HTTP_CGI_AUTHORIZATION})) {
  $ENV{HTTP_CGI_AUTHORIZATION} =~ s/basic\s+//i;
  my ($REMOTE_USER,$REMOTE_PASSWD) = split(/:/, decode_base64($ENV{HTTP_CGI_AUTHORIZATION}));  

#  print "Content-Type: text/html\n\n";
#  print "($REMOTE_PASSWD ne $password || $REMOTE_USER ne $user)";

  if ((! $REMOTE_PASSWD) || ($REMOTE_PASSWD && $REMOTE_PASSWD ne $password) 
    || (! $REMOTE_USER) || ($REMOTE_USER && $REMOTE_USER ne $user)) {
    print "WWW-Authenticate: Basic realm=\"Billing system\"\n";
    print "Status: 401 Unauthorized\n";
    print "Content-Type: text/html\n\n";
    print "Access Deny";
    exit;
   }
  }
}

$admin = Admins->new($db, \%conf);
$admin->info($conf{SYSTEM_ADMIN_ID}, { IP => '127.0.0.1' });
$payments = Finance->payments($db, $admin, \%conf);
$users = Users->new($db, $admin, \%conf); 
my $Ashield = Ashield->new($db, $admin, \%conf);
my $Tariffs = Tariffs->new($db, \%conf, $admin);
my $Fees    = Fees->new($db, $admin, \%conf);


#debug =========================================
my $output2 = '';
while(my($k, $v)=each %FORM) {
 	$output2 .= "$k, $v\n"	if ($k ne '__BUFFER');
}
#my $rew `echo $output2 >> /tmp/ukrpays`;
#END debug =====================================

print "Content-Type: text/html\n\n";

#$FORM{'__BUFFER'}=qq{xml=<?xml version="1.0" encoding="UTF-8"?>
#<personal-office timestamp="20100607193208">
#  <login>test2</login>
#  <name>-</name>
#  <lastname>-</lastname>
#  <action>
#    <type>1</type>
#    <agentuuid>c4c4e78b-d21d-b211-b94d-f627387fdbbf</agentuuid>
#    <groupuuid>91644cc3-1dc1-42dc-a41e-5ea001f5538d</groupuuid>
#    <groupname>AV+AS+PC</groupname>
#    <tariffplancode>PREMIUM</tariffplancode>
#  </action>
#</personal-office>
#&checkword=827ccb0eea8a706c4c34a16891f84e7b};

mk_log($FORM{'__BUFFER'});

my @pairs = split(/&/, $FORM{'__BUFFER'});
foreach my $line (@pairs) {
	my ($key, $val)=split(/=/, $line, 2);
	$FORM{$key}=$val;
}

avd_add({ CONTENT    => $FORM{'xml'},
	        checkword  => $FORM{'checkword'}
     	});


#**********************************************************
# mak_log
#1. Оформление новой подписки.
#2. Смена тарифного плана.
#3. Возобновление подписки.
#4. Активация блокировки.
#5. Отказ от услуги.
#**********************************************************
sub avd_add {
  my ($attr) = @_;

eval { require XML::Simple; };
if (! $@) {
   XML::Simple->import();
 }
else {
   print "Content-Type: text/plain\n\n";
   print "Can't load 'XML::Simple' check http://www.cpan.org";
   mk_log("---- Error: Can't load 'XML::Simple' check http://www.cpan.org\n");
   exit;
 }

$FORM{xml} =~ s/encoding="windows-1251"//g;
my $_xml = eval { XMLin("$attr->{CONTENT}", forcearray=>1) };

if($@) {
  mk_log("---- Content:\n".
      $attr->{CONTENT}.
      "\n----XML Error:\n".
      $@
      ."\n----\n");
  return 0;
 }
else {
  if ($debug > 0) {
 	  mk_log($attr->{CONTENT});
   }
}

#Add fees
if ($_xml->{'action'}->[0]->{type}->[0] < 4) {
  my $login = $_xml->{'login'}->[0];
  my $list = $users->list({ LOGIN => $login });

  my $uid = $list->[0]->[5+$users->{SEARCH_FIELDS_COUNT}];
  if ($users->{error}) {
	  mk_log("Error user '$login'");
   }
  elsif($users->{TOTAL} < 1) {	
	  mk_log("Can't find user '$login'");
   }
  else {
  	require "Abills/modules/Ashield/webinterface";
	  my $user = $users->info($uid);
    $Tariffs->info(0, { NAME => "$_xml->{'action'}->[0]->{tariffplancode}->[0]" });
  
    if ($Tariffs->{TOTAL} < 1) {
    	mk_log("Tariff not exists. TP: '". $_xml->{'action'}->[0]->{tariffplancode}->[0]."'");
     }
    else {
      my $agents_result_hash=ashield_drweb_request('interfaces/user_agents.php', {
       	  login      => "$users->{LOGIN}",
      	  checkword  => $conf{ASHIELD_DRWEB_CABINET_PASSWD}
      	  },
      	  { SERVER_ADDR    => "$conf{ASHIELD_DRWEB_CABINET_HOST}",
      	  	});

     my $agetnt_count = $#{ $agents_result_hash->{agents}->[0]->{agent} };

      
      my $sum = $Tariffs->{MONTH_FEE};  
      $Tariffs->{PERIOD_ALIGNMENT}=1;
      if ($Tariffs->{PERIOD_ALIGNMENT}) {
        	my ($y, $m, $d)=split(/-/, $DATE);
          my $days_in_month=($m!=2?(($m%2)^($m>7))+30:(!($y%400)||!($y%4)&&($y%25)?29:28));
          $conf{START_PERIOD_DAY} = 1;
          $sum = sprintf("%.2f", ($sum / $days_in_month) * ($days_in_month - $d + $conf{START_PERIOD_DAY}));
        }
      
      if ($conf{ASHIELD_DRWEBAVD_FREE_PERIOD} &&  $agetnt_count == 0
            && $_xml->{'action'}->[0]->{type}->[0] == 1) {
        print "Free Activate\n" if ($debug > 0);    	
       }
      elsif($_xml->{'action'}->[0]->{type}->[0] < 4 && ($user->{DEPOSIT} + $user->{CREDIT} > 0 || $Tariffs->{PAYMENT_TYPE})) {
        $Fees->take($users, "$sum", 
                     { DESCRIBE  => "Dr.Web TP:". $_xml->{'action'}->[0]->{tariffplancode}->[0], 
 	                     DATE      => "$DATE $TIME"
  	                  });
  	    print "Activate\n" if ($debug > 0);    	
       }
      #block account
      else {
        my ($y, $m, $d)=split(/-/, $DATE, 3);
        my $cur_date="$y$m$d"; 

      	my $result = ashield_drweb_request('api/2.0/change-customer-info.ds', { 
 	     	 	   id       => $_xml->{'action'}->[0]->{agentuuid}->[0], 
 	     	 	   blockbeg => $cur_date,
 	     	 	   blockend => '20200101'
 	     	 	   }); 
 	       
 	      if ( $result->{error} ) { 	      	 
 	      	 my $code = $result->{error}->[0]->{code}->[0];
 	         if ($code == 17) {
 	         	 print "'$_xml->{'action'}->[0]->{agentuuid}->[0]', Customer Not Exist\n";
 	          }
           else {
           	 print "Block $line->[0] '$cur_date' $code / $result->{error}->[0]->{message}->[0]\n";
            }
 	       }
 	      else {
 	         print "$result->{customers}->[0]->{customer}->[0]->{id}->[0] ".
 	          "BLOCKING: $result->{customers}->[0]->{customer}->[0]->{blockbeg}->[0]\n" if ($debug > 0);
 	       }
       }

      if (! $Fees->{error}) {
        $Ashield->ashield_avd_add({ UID => $users->{UID},
      	 STATE      => $_xml->{'action'}->[0]->{type}->[0],
         AGENTUUID  => $_xml->{'action'}->[0]->{agentuuid}->[0],
         GROUPUUID  => $_xml->{'action'}->[0]->{groupuuid}->[0],
         GROUPNAME  => $_xml->{'action'}->[0]->{groupname}->[0],
         TARIFFPLANCODE  => $_xml->{'action'}->[0]->{tariffplancode}->[0],
         TP_ID      => $Tariffs->{TP_ID} });
       }
    }
  }
 }

}


#**********************************************************
# mak_log
#**********************************************************
sub mk_log {
  my ($message, $attr) = @_;
 
  if (open(FILE, ">>/tmp/avd.log")) {
    print FILE "\n$DATE $TIME $ENV{REMOTE_ADDR}=========================\n";
    print FILE $message;
	  close(FILE);
	 }
  else {
    print "Can't open file '/tmp/avd.log' $! \n";
   }
}

1
