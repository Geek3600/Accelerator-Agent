# Export one Vivado-generated IP simulation closure per requested IP.
#
# This helper is intentionally independent of the generated-IP TCL.  The
# generator owns IP configuration; this file asks Vivado for the simulator's
# official source/library manifest after those IPs have been created.

proc get_arg_or_default {idx default_value} {
  if {[llength $::argv] > $idx} {
    return [lindex $::argv $idx]
  }
  return $default_value
}

set ip_dir [file normalize [get_arg_or_default 0 ""]]
set export_dir [file normalize [get_arg_or_default 1 ""]]
set part_name [get_arg_or_default 2 ""]
set module_manifest [file normalize [get_arg_or_default 3 ""]]

if {$ip_dir eq "" || ![file isdirectory $ip_dir]} {
  error "Vivado IP output directory is missing: $ip_dir"
}
if {$export_dir eq ""} {
  error "Vivado export directory is missing"
}
if {$part_name eq ""} {
  error "FPGA part is missing for Vivado simulation export"
}
if {$module_manifest eq "" || ![file isfile $module_manifest]} {
  error "floating-point module manifest is missing: $module_manifest"
}

set manifest_handle [open $module_manifest r]
set requested_modules {}
while {[gets $manifest_handle line] >= 0} {
  set name [string trim $line]
  if {$name ne "" && ![string match "#*" $name]} {
    lappend requested_modules $name
  }
}
close $manifest_handle
set requested_modules [lsort -unique $requested_modules]
if {[llength $requested_modules] == 0} {
  error "floating-point module manifest is empty"
}

if {[file exists $export_dir]} {
  file delete -force $export_dir
}
file mkdir $export_dir
create_project fpga_ip_vcs_export [file join $export_dir project] -part $part_name -force

foreach name $requested_modules {
  set xci [file join $ip_dir $name "$name.xci"]
  if {![file isfile $xci]} {
    error "generated IP XCI is missing for $name: $xci"
  }
  read_ip [file normalize $xci]
}

generate_target simulation [get_ips]
foreach name $requested_modules {
  set target_dir [file join $export_dir $name]
  export_simulation -of_objects [get_ips $name] \
    -directory [file normalize $target_dir] \
    -ip_user_files_dir [file normalize [file join $ip_dir ip_user_files]] \
    -simulator vcs -force
  set file_info [file join $target_dir vcs file_info.txt]
  if {![file isfile $file_info]} {
    error "Vivado export_simulation did not produce file_info.txt for $name"
  }
}

close_project
puts "SPATIALACC_VIVADO_VCS_EXPORT_PASS modules=[llength $requested_modules]"
