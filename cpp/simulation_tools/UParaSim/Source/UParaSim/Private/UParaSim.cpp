// Copyright Epic Games, Inc. All Rights Reserved.

#include "UParaSim.h"
#include "UParaSimGameModeBase.h"
#include "LevelEditor.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"



void FUParaSimModule::StartupModule()
{
    // This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module

    // Initialize play button ui style
    FUParaSimSceneStyle::Initialize();
    FUParaSimSceneStyle::ReloadTextures();

    // Register play capture commands
    FUParaSimSceneCommands::Register();
    PluginCommands = MakeShareable(new FUICommandList);

    // Add play capture button command
    PluginCommands->MapAction(
        FUParaSimSceneCommands::Get().OpenPluginWindow,
        FExecuteAction::CreateRaw(this, &FUParaSimModule::PluginButtonClicked),
        FCanExecuteAction());

    FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");

    // Add play capture button to editor
    {
        TSharedPtr<FExtender> ToolbarExtender = MakeShareable(new FExtender);
        ToolbarExtender->AddToolBarExtension("Settings", EExtensionHook::After, PluginCommands, FToolBarExtensionDelegate::CreateRaw(this, &FUParaSimModule::AddToolbarExtension));

        LevelEditorModule.GetToolBarExtensibilityManager()->AddExtender(ToolbarExtender);
    }


}

void FUParaSimModule::ShutdownModule()
{
    // This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
    // we call this function before unloading the module.
    // This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
        // we call this function before unloading the module.
        FUParaSimSceneStyle::Shutdown();

        FUParaSimSceneCommands::Unregister();

        // Disable PlayScene Window
        UUParaSimSceneSlate::Shutdown();
}

TWeakObjectPtr<UTextureRenderTarget2D> FUParaSimModule::GetTextureRenderTarget2D(int ID)
{
    return TextureRenderTarget2D[ID];
}

void FUParaSimModule::SetTextureRenderTarget2D(UTextureRenderTarget2D * TexRenderTarget2D)
{
    TextureRenderTarget2D.Add(TexRenderTarget2D);
}

void FUParaSimModule::AddToolbarExtension(FToolBarBuilder& Builder)
{
    Builder.AddToolBarButton(FUParaSimSceneCommands::Get().OpenPluginWindow);
}

void FUParaSimModule::PluginButtonClicked()
{
    UUParaSimSceneSlate::NBR_OF_PARTICLES=AUParaSimGameModeBase::NumberOfMaps;
    // Init layCapture Window
    if(AUParaSimGameModeBase::ListWorldHandles[0]!=nullptr){
        UE_LOG(LogTemp, Warning, TEXT("********************** BY CLICKING WORLD HANDE IS VALID"));
        UUParaSimSceneSlate::Initialize(AUParaSimGameModeBase::ListWorldHandles[0]);
    }
    else
        UE_LOG(LogTemp, Warning, TEXT("********************** BY CLICKING WORLD HANDE IS INVALID!!!"));

}

IMPLEMENT_MODULE(FUParaSimModule, UParaSim);








