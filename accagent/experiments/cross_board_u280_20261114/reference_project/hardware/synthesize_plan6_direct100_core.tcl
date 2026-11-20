set core_identity [file join $core_run_dir identity.txt]
if {[file isfile $core_identity]} {
    set channel [open $core_identity r]
    set identity [read $channel]
    close $channel
    if {[string first "INPUT_MANIFEST_SHA256 $expected_manifest_sha" $identity] < 0} {
        error "The reusable combined core has different synthesis inputs"
    }
    exec sha256sum -c --status [file join $core_run_dir outputs.sha256]
    set expected_core_checkpoint_sha [sha256_file $core_checkpoint]
    record_state CORE_SYNTHESIS_REUSED
    return
}
record_state CORE_SYNTHESIS_RUNNING
create_project -in_memory -part xcvu9p_CIV-flgb2104-2-i
set_param general.maxThreads 8
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
set_property default_lib xil_defaultlib [current_project]
set_property verilog_define {SYNTH_CARRY8 XILINX_XPM} [current_fileset]
set rtl_files [lsort [glob [file join $project_dir plan6_rtl *.sv]]]
read_verilog -library xil_defaultlib -sv $rtl_files
read_verilog -library xil_defaultlib [file join $project_dir plan6_rtl rtwsr_plan6_huginn_9p_axi_bd.v]
read_verilog -library xil_defaultlib [file join $project_dir core_wrapper.v]
synth_design -top app_shell_9p_rtwsr_9p_axi_0_6 -part xcvu9p_CIV-flgb2104-2-i \
    -control_set_opt_threshold 16 -mode out_of_context
if {[llength [get_cells -hier -quiet -filter {IS_BLACKBOX == 1}]] != 0} {
    error "The combined Attention/QKV accelerator synthesis has black boxes"
}
rename_ref -prefix_all app_shell_9p_rtwsr_9p_axi_0_6_
set_param constraints.enableBinaryConstraints false
report_utilization -file [file join $core_run_dir app_shell_9p_rtwsr_9p_axi_0_6_utilization_synth.rpt]
report_utilization -hierarchical -file [file join $core_run_dir utilization_hierarchical_synth.rpt]
write_checkpoint -force -noxdef $core_checkpoint
set expected_core_checkpoint_sha [sha256_file $core_checkpoint]
exec sha256sum -c --status $source_manifest
set channel [open [file join $core_run_dir outputs.sha256] w]
foreach path [list $core_checkpoint \
    [file join $core_run_dir app_shell_9p_rtwsr_9p_axi_0_6_utilization_synth.rpt] \
    [file join $core_run_dir utilization_hierarchical_synth.rpt]] {
    puts $channel "[sha256_file $path]  $path"
}
close $channel
set channel [open $core_identity w]
puts $channel "INPUT_MANIFEST_SHA256 $expected_manifest_sha"
close $channel
record_state CORE_SYNTHESIS_COMPLETE
close_project
