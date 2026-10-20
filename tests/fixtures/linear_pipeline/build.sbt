ThisBuild / scalaVersion := "2.13.16"
Compile / unmanagedSourceDirectories += baseDirectory.value / "../../../accagent/framework/templates/operator_chisel"
libraryDependencies += "org.chipsalliance" %% "chisel" % "7.0.0"
addCompilerPlugin("org.chipsalliance" % "chisel-plugin" % "7.0.0" cross CrossVersion.full)
scalacOptions += "-language:reflectiveCalls"
