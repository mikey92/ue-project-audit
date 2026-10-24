// Copyright (c) 2026 BCD.

using UnrealBuildTool;

public class ProjectAuditToolset : ModuleRules
{
	public ProjectAuditToolset(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] { "Core" });
	}
}
