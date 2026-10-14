// Copyright Kenghagho Kenfack Franklin. All Rights Reserved.
using UnrealBuildTool;

public class UProceduralObjectInterpreter : ModuleRules
{
    public UProceduralObjectInterpreter(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        // Public dependencies available in both Editor and Runtime (if applicable)
        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "RenderCore",
            "RHI",
            "PhysicsCore",
            "AssetRegistry"
        });

        // Editor-only dependencies and specialized modules
        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.AddRange(new string[]
            {
                "UnrealEd",
                "AssetTools",
                "MeshDescription",
                "StaticMeshDescription",
                "ApexDestruction", // Required for UDestructibleMesh in 4.27
                "MaterialEditor",
                "MeshUtilities",
                "RawMesh",         // Required for FRawMesh in 4.27
                "Slate",
                "SlateCore",
                "Projects",
                "PropertyEditor",
                "LevelEditor"
            });
        }

        // Ensure RTTI is enabled for complex parsing/type checks if needed
        //bUseRTTI = true;
    }
}
