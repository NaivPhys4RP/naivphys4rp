// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

#include "Core.h"
#include "Engine.h"
#include "UParaSimHUD.h"
#if ENGINE_MINOR_VERSION > 23 || ENGINE_MAJOR_VERSION >4
#include "Modules/ModuleManager.h"
#else
#include "ModuleManager.h"
#endif

class FUParaSimModule : public IUParaSimScene

{

public:
    /*\* IModuleInterface implementation \*/

    virtual void StartupModule() override;

    virtual void ShutdownModule() override;

    virtual TWeakObjectPtr<UTextureRenderTarget2D> GetTextureRenderTarget2D(int ID) override;

    virtual void SetTextureRenderTarget2D(UTextureRenderTarget2D* TexRenderTarget2D) override;

    /** This function will be bound to Command (by default it will bring up plugin window) */
    void PluginButtonClicked();
private:
    /**
    * Play Capture button handler
    */
    void AddToolbarExtension(FToolBarBuilder& Builder);

private:
    TSharedPtr<class FUICommandList> PluginCommands;
private:
    TArray<TWeakObjectPtr<UTextureRenderTarget2D>> TextureRenderTarget2D;

};
