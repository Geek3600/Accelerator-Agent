set checkpoint [lindex $argv 0]
set output_file [lindex $argv 1]
set target_name "u_plan6_huginn_hbm_shell/u_recurrent_core/u_weight_memory/u_primary_pool/xpm_memory_base_inst_i_1848_n_0"
set output [open $output_file w]
proc emit {handle label values} {
    puts $handle "$label"
    foreach value $values {puts $handle "  $value"}
}
set handle [open $output_file w]
open_checkpoint $checkpoint
set matching_nets [get_nets -hierarchical -quiet -filter "NAME =~ *xpm_memory_base_inst_i_1848_n_0*"]
emit $handle "MATCHING_NETS" $matching_nets
foreach net $matching_nets {
    puts $handle "NET $net"
    foreach property {NAME ROUTE IS_ROUTE_FIXED IS_ROUTE_THROUGH} {
        if {[catch {set value [get_property $property $net]}]} {set value UNAVAILABLE}
        puts $handle "  $property=$value"
    }
    emit $handle "  PINS" [get_pins -quiet -of_objects $net]
}
set target_pin [get_pins -quiet -hierarchical -filter "NAME =~ *xpm_memory_base_inst_i_1847/CI"]
emit $handle "TARGET_PINS" $target_pin
foreach pin $target_pin {
    puts $handle "PIN $pin"
    foreach net [get_nets -quiet -of_objects $pin] {
        puts $handle "  CONNECTED_NET $net"
        foreach property {NAME ROUTE IS_ROUTE_FIXED IS_ROUTE_THROUGH} {
            if {[catch {set value [get_property $property $net]}]} {set value UNAVAILABLE}
            puts $handle "    $property=$value"
        }
    }
}
close $handle
close_design
exit
