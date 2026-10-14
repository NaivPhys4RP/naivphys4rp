// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "Core.h"
#include "Components/SceneCaptureComponent2D.h"
#include "UObject/ObjectMacros.h"
#include "GameFramework/HUD.h"
#include "UFluidHUD.generated.h"

class SWindow;
class SViewport;
class FSceneViewport;
class UTextureRenderTarget2D;
/**
 *By Kenghagho Kenfack Franklin
 */


UCLASS(hidecategories = (Collision, Object, Physics, SceneComponent), ClassGroup = Rendering, editinlinenew, meta = (BlueprintSpawnableComponent))
class UFLUID_API UFluidSceneCaptureComponent2D : public USceneCaptureComponent2D
{
    GENERATED_BODY()

public:
    virtual void Activate(bool bReset) override;

#if WITH_EDITOR
    virtual void OnRegister() override;
#endif

};
