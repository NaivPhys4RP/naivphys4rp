// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class UParaSim : ModuleRules
{
	public UParaSim(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore","UMG", "URoboVision","URoboViz", "UFluid"});
		
		PublicIncludePaths.AddRange(new string[] {"URoboVision/Public","URoboViz/Public","URoboVizEditor/Public","UFluid/Public" });

		PrivateDependencyModuleNames.AddRange(new string[] {  });

		// Uncomment if you are using Slate UI
		PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore", "RHI", "Renderer","Projects"});
		
		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
