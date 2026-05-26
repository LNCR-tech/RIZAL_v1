allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
// camera_android_camerax (camera-core 1.5.x) references
// androidx.concurrent.futures.CallbackToFutureAdapter in @NonNull-annotated
// fields but does not expose concurrent-futures on its compile classpath, so its
// Java compile fails with "CallbackToFutureAdapter not found". Inject it when the
// Android library plugin is applied (before evaluationDependsOn forces eval).
subprojects {
    if (project.name == "camera_android_camerax") {
        project.plugins.withId("com.android.library") {
            project.dependencies.add(
                "implementation",
                "androidx.concurrent:concurrent-futures:1.2.0",
            )
        }
    }
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
