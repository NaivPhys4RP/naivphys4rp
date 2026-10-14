#include "UProceduralObjectInterpreter.h"
#include "Modules/ModuleManager.h"
#include "Interfaces/IPluginManager.h"

#define LOCTEXT_NAMESPACE "FUProceduralObjectInterpreterModule"

void FUProceduralObjectInterpreterModule::StartupModule()
{
    // Startup hooks if needed
}

void FUProceduralObjectInterpreterModule::ShutdownModule()
{
    // Cleanup if needed
}

IMPLEMENT_MODULE(FUProceduralObjectInterpreterModule, UProceduralObjectInterpreter)

#undef LOCTEXT_NAMESPACE

