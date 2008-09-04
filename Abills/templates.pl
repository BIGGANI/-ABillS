# Base ABIllS Templates Managments

use FindBin '$Bin';

#**********************************************************
# templates
#**********************************************************
sub _include {
  my ($tpl, $module, $attr) = @_;
  my $result = '';
  
  my $sufix = ($attr->{pdf}) ? '.pdf' : '.tpl';
  
  $tpl = '' if (! $tpl);
  
  if (-f '../../Abills/templates/'. $module . '_' . $tpl . $sufix) {
    return ($FORM{pdf}) ? '../../Abills/templates/'. $module . '_' . $tpl . $sufix : tpl_content('../../Abills/templates/'. $module . '_' . $tpl . $sufix);
   }
  elsif (-f '../Abills/templates/'. $module . '_' . $tpl .$prefix) {
    return ($FORM{pdf}) ? '../Abills/templates/'. $module . '_' . $tpl. '.tpl' : tpl_content('../Abills/templates/'. $module . '_' . $tpl. $sufix);
   }
  elsif (-f $Bin .'/../Abills/templates/'. $module . '_' . $tpl .$sufix) {
    return ($FORM{pdf}) ? $Bin .'/../Abills/templates/'. $module . '_' . $tpl .$sufix : tpl_content($Bin .'/../Abills/templates/'. $module . '_' . $tpl .$sufix);
   }
  elsif (defined($module)) {
    $tpl	= "modules/$module/templates/$tpl";
   }

  foreach my $prefix (@INC) {
     my $realfilename = "$prefix/Abills/$tpl$sufix";
     if (-f $realfilename) {
        return ($FORM{pdf}) ? $realfilename :  tpl_content($realfilename);
      }
   }

  return "No such template [$tpl]\n";
}


#**********************************************************
# templates
#**********************************************************
sub tpl_content {
  my ($filename, $attr) = @_;
  my $tpl_content = '';
  
  open(FILE, "$filename") || die "Can't open file '$filename' $!";
    while(<FILE>) {
      $tpl_content .= eval "\"$_\"";
    }
  close(FILE);
 	
	return $tpl_content;
}

#**********************************************************
# templates
#**********************************************************
sub templates {
  my ($tpl_name) = @_;

  if (-f $Bin."/../../Abills/templates/_"."$tpl_name".".tpl") {
    return tpl_content("$Bin/../../Abills/templates/_". "$tpl_name".".tpl");
   }
  elsif (-f "$Bin/../Abills/templates/_"."$tpl_name".".tpl") {
    return tpl_content("$Bin/../Abills/templates/_"."$tpl_name".".tpl");
   }
  elsif (-f "$Bin/../../Abills/main_tpls/$tpl_name".".tpl") {
    return tpl_content("$Bin/../../Abills/main_tpls/$tpl_name".".tpl");
   }
  elsif (-f "$Bin/../Abills/main_tpls/$tpl_name".".tpl") {
    return tpl_content("$Bin/../Abills/main_tpls/$tpl_name".".tpl");
   }
  
  return "No such template [$tpl_name]";
}




1

