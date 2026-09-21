# Generate Vivado floating_point IPs that match the blackbox names emitted in
# generated/Top_vivado.sv when FpBackend.setVivadoIp() is enabled.
#
# Usage:
#   vivado -mode batch -source scripts/synthesis/gen_xilinx_fp_ips_23.tcl \
#     -tclargs /tmp/fp_ip_gen_proj /tmp/fp_ip xcvu9p-flga2104-2-i fpga_ip_modules.txt

proc get_arg_or_default {idx default_value} {
  if {[llength $::argv] > $idx} {
    return [lindex $::argv $idx]
  }
  return $default_value
}

proc create_fp_ip {name config_dict ip_dir} {
  puts "=== create_ip $name ==="
  create_ip -name floating_point -vendor xilinx.com -library ip -version 7.1 -module_name $name -dir $ip_dir
  set_property -dict $config_dict [get_ips $name]
  generate_target all [get_ips $name]
}

set project_dir [get_arg_or_default 0 "/tmp/fp_ip_gen_proj"]
set ip_dir [get_arg_or_default 1 "/home/hyyuan/workspace/opt_acc/fp_ip"]
set part_name [get_arg_or_default 2 "xcvu9p_CIV-flgb2104-2-i"]
set module_manifest [get_arg_or_default 3 ""]

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
  error "floating-point module manifest is empty: $module_manifest"
}

if {[file exists $project_dir]} {
  file delete -force $project_dir
}
if {[file exists $ip_dir]} {
  file delete -force $ip_dir
}
file mkdir $project_dir
file mkdir $ip_dir

create_project fp_ip_gen $project_dir -part $part_name -force

set common_single [list \
  CONFIG.A_Precision_Type {Single} \
  CONFIG.Result_Precision_Type {Single} \
  CONFIG.C_Optimization {Speed_Optimized} \
  CONFIG.Axi_Optimize_Goal {Resources} \
  CONFIG.Flow_Control {Blocking} \
  CONFIG.Maximum_Latency {false} \
  CONFIG.Has_RESULT_TREADY {false}]

proc create_i2f_ip {name in_width latency ip_dir} {
  create_fp_ip $name [list \
    CONFIG.Operation_Type {Fixed_to_float} \
    CONFIG.A_Precision_Type {Custom} \
    CONFIG.C_A_Exponent_Width $in_width \
    CONFIG.C_A_Fraction_Width {0} \
    CONFIG.Result_Precision_Type {Single} \
    CONFIG.C_Optimization {Speed_Optimized} \
    CONFIG.Axi_Optimize_Goal {Resources} \
    CONFIG.Flow_Control {Blocking} \
    CONFIG.Maximum_Latency {false} \
    CONFIG.C_Latency $latency \
    CONFIG.Has_RESULT_TREADY {false}] $ip_dir
}

proc create_f2i_ip {name out_width latency ip_dir} {
  create_fp_ip $name [list \
    CONFIG.Operation_Type {Float_to_fixed} \
    CONFIG.A_Precision_Type {Single} \
    CONFIG.Result_Precision_Type {Custom} \
    CONFIG.C_Result_Exponent_Width $out_width \
    CONFIG.C_Result_Fraction_Width {0} \
    CONFIG.C_Optimization {Speed_Optimized} \
    CONFIG.Axi_Optimize_Goal {Resources} \
    CONFIG.Flow_Control {Blocking} \
    CONFIG.Maximum_Latency {false} \
    CONFIG.C_Latency $latency \
    CONFIG.Has_RESULT_TREADY {false}] $ip_dir
}

foreach name $requested_modules {
  if {[regexp {^fp_(add|sub|mul|div|sqrt)_sp_([0-9]+)$} $name -> operation latency]} {
    switch -- $operation {
      add {
        set config [list CONFIG.Operation_Type {Add_Subtract} CONFIG.Add_Sub_Value {Add}]
      }
      sub {
        set config [list CONFIG.Operation_Type {Add_Subtract} CONFIG.Add_Sub_Value {Subtract}]
      }
      # A Linear PE is represented by exactly one fp_mul_sp_* IP instance.
      # Full_Usage prevents Vivado from implementing that PE multiplier in
      # LUT fabric; the exact DSP48 count remains Vivado-report authority.
      mul { set config [list CONFIG.Operation_Type {Multiply} CONFIG.C_Mult_Usage {Full_Usage}] }
      div { set config [list CONFIG.Operation_Type {Divide}] }
      sqrt { set config [list CONFIG.Operation_Type {Square_root}] }
    }
    create_fp_ip $name [concat $common_single $config [list CONFIG.C_Latency $latency]] $ip_dir
  } elseif {[regexp {^fp_cmp_(lt|eq|gt)_sp_([0-9]+)$} $name -> comparison latency]} {
    switch -- $comparison {
      lt { set compare_operation Less_Than }
      eq { set compare_operation Equal }
      gt { set compare_operation Greater_Than }
    }
    create_fp_ip $name [concat $common_single [list \
      CONFIG.Operation_Type {Compare} \
      CONFIG.C_Compare_Operation $compare_operation \
      CONFIG.C_Latency $latency]] $ip_dir
  } elseif {[regexp {^fp_i2f_([su])([0-9]+)_sp_([0-9]+)$} $name -> signedness width latency]} {
    create_i2f_ip $name $width $latency $ip_dir
  } elseif {[regexp {^fp_f2i_([su])([0-9]+)_sp_([0-9]+)$} $name -> signedness width latency]} {
    create_f2i_ip $name $width $latency $ip_dir
  } else {
    error "unsupported floating-point module name: $name"
  }
}

puts "=== generated [llength $requested_modules] Xilinx floating_point IPs under $ip_dir ==="
close_project
