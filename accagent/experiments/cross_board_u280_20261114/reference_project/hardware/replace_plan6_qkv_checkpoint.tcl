set qkv_run_dir "/home/hyyuan/workspace/rtwsr_plan6_qkv_pipeline_20261026"
set qkv_rtl [file join $qkv_run_dir rtwsr_qkv_head_buffer_timing_candidate.sv]
set qkv_manifest [file join $qkv_run_dir reports inputs.sha256]
set qkv_checkpoint [file join $qkv_run_dir reports rtwsr_qkv_head_buffer_synth.dcp]
set qkv_status_path [file join $qkv_run_dir reports status.txt]
set expected_qkv_sha "709c50d579022b8120e4c9c0e813dae9249ae3cc0be1852395926b7190ba8537"

if {[lindex [exec sha256sum $qkv_rtl] 0] ne $expected_qkv_sha} {
    error "The QKV RTL identity does not match the timing candidate"
}
exec sha256sum -c --status $qkv_manifest
set channel [open $qkv_status_path r]
set qkv_status_text [read $channel]
close $channel
if {![regexp {STATE (IMPLEMENTATION_RUNNING|REPORTS_COMPLETE)} $qkv_status_text] ||
    ![regexp {CHECKPOINT_SHA256 ([0-9a-f]+)} $qkv_status_text -> qkv_checkpoint_sha] ||
    [lindex [exec sha256sum $qkv_checkpoint] 0] ne $qkv_checkpoint_sha} {
    error "The QKV synthesized checkpoint is not ready or its identity changed"
}
set qkv_cell [get_cells -hier -filter {NAME =~ *u_recurrent_core/u_qkv_head_buffer}]
if {[llength $qkv_cell] != 1} { error "Expected one complete-core QKV buffer" }
set qkv_cell_name [get_property NAME $qkv_cell]
update_design -cell $qkv_cell -black_box
read_checkpoint -cell $qkv_cell_name $qkv_checkpoint
if {[llength [get_cells -hier -quiet -filter {IS_BLACKBOX == 1 && REF_NAME != dbg_hub_CV}]] != 0} {
    error "The complete shell must have no functional black boxes after QKV replacement"
}
puts "PLAN6_QKV_CHECKPOINT_LINKED $qkv_cell_name $qkv_checkpoint_sha"
