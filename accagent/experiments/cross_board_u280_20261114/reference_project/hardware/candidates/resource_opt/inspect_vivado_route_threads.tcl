puts "GENERAL_MAX_THREADS=[get_param general.maxThreads]"
foreach parameter [list_param] {
    if {[regexp -nocase {thread|route|cpu} $parameter]} {
        if {[catch {set value [get_param $parameter]}]} {
            continue
        }
        puts "$parameter=$value"
    }
}
puts "ROUTE_DESIGN_HELP_BEGIN"
route_design -help
puts "ROUTE_DESIGN_HELP_END"
