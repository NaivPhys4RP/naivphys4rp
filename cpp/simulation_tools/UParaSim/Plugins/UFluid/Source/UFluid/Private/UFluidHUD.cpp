// Fill out your copyright notice in the Description page of Project Settings.


#include "UFluidHUD.h"
#include "Engine.h"
#include "Runtime/Engine/Classes/Engine/TextureRenderTarget2D.h"


void UFluidSceneCaptureComponent2D::Activate(bool bReset)
{
    Super::Activate();
}


/*

ActiveFluidID
AmountFluidTXT
EscapedFluidTXT
MissDetectedTXT
SpillageDetectedTXT
OverflowDetectedTXT
*/
#if WITH_EDITOR
void UFluidSceneCaptureComponent2D::OnRegister()
{
    Super::OnRegister();
}
#endif

