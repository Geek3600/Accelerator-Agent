if {$argc == 2} {
    set checkpoint [file normalize [lindex $argv 0]]
    set report_path [file normalize [lindex $argv 1]]
    if {![file exists $checkpoint]} {
        error "missing synthesis checkpoint: $checkpoint"
    }
    file mkdir [file dirname $report_path]
    open_checkpoint $checkpoint
    report_utilization -hierarchical -file $report_path
    close_design
    puts "PLAN6_SYNTH_HIERARCHY_COMPLETE $report_path"
    return
}

set report_root "/home/hyyuan/plan6_impl_20261021_1133_activation_windows/hierarchy_reports"
file mkdir $report_root

set checkpoints [list \
    huginn_vu9p /home/hyyuan/plan6_impl_20261021_1133_activation_windows/huginn_vu9p/output_vu9p/model_0/rtwsr_transformer_top_synth.dcp \
    huginn_u280 /home/hyyuan/plan6_impl_20261021_1133_activation_windows/huginn_u280/output_u280/model_0/rtwsr_transformer_top_synth.dcp \
    ouro_vu9p /home/hyyuan/plan6_impl_20261021_1133_activation_windows/ouro_vu9p/output_vu9p/model_1/rtwsr_transformer_top_synth.dcp \
    ouro_u280 /home/hyyuan/plan6_impl_20261021_1133_activation_windows/ouro_u280/output_u280/model_1/rtwsr_transformer_top_synth.dcp]

foreach {label checkpoint} $checkpoints {
    if {![file exists $checkpoint]} {
        error "missing synthesis checkpoint: $checkpoint"
    }
    open_checkpoint $checkpoint
    report_utilization -hierarchical -file [file join $report_root "${label}_hierarchical.rpt"]
    close_design
}

puts "PLAN6_SYNTH_HIERARCHY_COMPLETE"
