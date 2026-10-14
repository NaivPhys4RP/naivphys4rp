// Copyright Kenghagho Kenfack Franklin. All Rights Reserved.

using UnrealBuildTool;

public class USceneRandomizer : ModuleRules
{
	public USceneRandomizer(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"Engine",
				"CoreUObject"
			});
			
		PublicIncludePaths.AddRange(new string[] {"USceneRandomizer/Public"});

		PrivateIncludePaths.AddRange(new string[] { "USceneRandomizer/Private"  });

		// Uncomment if you are using Slate UI
		PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore", "RHI", "Renderer","Projects"});
	}
}
