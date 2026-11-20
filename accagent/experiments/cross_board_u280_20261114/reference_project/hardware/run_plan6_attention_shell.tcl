set project_dir "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261026_attn_pipeline"
set plan6_ooc_pre_hook [file join $project_dir plan6_ooc_checkpoint_only.tcl]
set argv [list $project_dir attn_pipeline_full]
set argc [llength $argv]
source [file join $project_dir run_plan6_fixplan_p2_default.tcl]
