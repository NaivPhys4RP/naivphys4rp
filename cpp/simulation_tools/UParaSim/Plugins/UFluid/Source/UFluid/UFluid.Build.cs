// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.IO;

public class UFluid : ModuleRules
{
    public UFluid(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "UMG",
            "PhysicsCore",
            "ProceduralMeshComponent" // <-- Added to link the fast procedural mesh geometry module
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "Slate",
            "SlateCore",
            "RHI",
            "Renderer",
            "Projects"
        });

        PublicIncludePaths.AddRange(new string[]
        {
            "UFluid/Public"
        });

        PrivateIncludePaths.AddRange(new string[]
        {
            "UFluid/Private"
        });

        // =========================================================================
        // OPENMP LINUX CONFIGURATION FOR UNREAL ENGINE 4.27
        // =========================================================================
        if (Target.Platform == UnrealTargetPlatform.Linux)
        {
            // 1. Safe macro definition for source code mapping
            PublicDefinitions.Add("WITH_OPENMP=1");

            // 2. The injection hack to pass -fopenmp directly to Clang
            PublicDefinitions.Add("OPENMP_HACK=1 -fopenmp");

            // 3. FORCE Clang to look at the standard Ubuntu system headers for omp.h
            PublicSystemIncludePaths.Add("/usr/lib/gcc/x86_64-linux-gnu/5/include");
            PublicSystemIncludePaths.Add("/usr/include");
            PublicSystemIncludePaths.Add("/usr/local/include");

            // 4. Official 4.27 API to search host system libraries
            PublicSystemLibraryPaths.Add("/usr/lib/x86_64-linux-gnu");

            // 5. Official 4.27 API to link the system level shared object library (-lomp)
            PublicSystemLibraries.Add("omp");
        }
    }
}
