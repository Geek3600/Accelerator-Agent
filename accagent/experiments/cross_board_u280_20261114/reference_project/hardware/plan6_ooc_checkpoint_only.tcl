foreach command_name {write_verilog write_vhdl} {
    rename ::$command_name ::plan6_original_$command_name
    proc ::$command_name {args} [string map [list @COMMAND@ $command_name] {
        if {[lsearch -exact $args funcsim] >= 0} {
            puts "PLAN6_OOC_CHECKPOINT_ONLY: skipped @COMMAND@ functional netlist"
            return
        }
        return [uplevel 1 [list ::plan6_original_@COMMAND@ {*}$args]]
    }]
}
