#pragma once

#include "Modules/ModuleInterface.h"

/**
 * The public interface to the Procedural Object Interpreter module.
 * * This class inherits from IModuleInterface and acts as the main entry point
 * for the plugin when the Unreal Editor loads.
 */
class FUProceduralObjectInterpreterModule : public IModuleInterface
{
public:

    /** * Called when the module is being loaded.
     * This is where we register our asset factory and developer settings.
     */
    virtual void StartupModule() override;

    /** * Called when the module is being unloaded.
     * This is where we unregister any custom assets or settings.
     */
    virtual void ShutdownModule() override;
};



