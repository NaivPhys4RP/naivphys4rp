// Copyright 2019, Institute for Artificial Intelligence - University of Bremen

#include "SegmentationComponent.h"
#include "SkeletalSegmentationSceneProxy.h"
#include "StaticSegmentationSceneProxy.h"
#include <fstream>
#include <sstream>
#include "Components/SceneCaptureComponent2D.h"
#include "Camera/CameraComponent.h"

#if ENGINE_MINOR_VERSION > 23 || ENGINE_MAJOR_VERSION >4
#include "UObject/ConstructorHelpers.h"
#else
#include "ConstructorHelpers.h"
#endif

#include "EngineUtils.h"
#include "StopTime.h"
#include "Server.h"
#include "PacketBuffer.h"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <thread>
#include <mutex>
#include <cmath>
#include <condition_variable>


USegmentationComponent::USegmentationComponent(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    // Original segmentation material path
    //FString MaterialPath = TEXT("Material'/URoboVision/AnnotationColor.AnnotationColor'");
    //static ConstructorHelpers::FObjectFinder<UMaterial> SegmentationMaterialObject(*MaterialPath);
    SegmentationMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Models/M_Bowl.M_Bowl"));
;

    this->PrimaryComponentTick.bCanEverTick = true;

    SetUsingAbsoluteRotation(true);
    SetUsingAbsoluteScale(true);
}

void USegmentationComponent::OnRegister()
{
    Super::OnRegister();
}

void USegmentationComponent::SetSegmentationColor(FColor NewSegmentationColor)
{
    this->SegmentationColor = NewSegmentationColor;
}

FColor USegmentationComponent::GetSegmentationColor()
{
    return SegmentationColor;
}

FPrimitiveSceneProxy* USegmentationComponent::CreateSceneProxy()
{
    USceneComponent* ParentComponent = GetAttachParent();
    if (!IsValid(ParentComponent))
    {
        UE_LOG(LogTemp, Warning, TEXT("Parent component is invalid."));
        return nullptr;
    }

    // Create dynamic material instance per object
    if (!SegmentationMaterial)
    {
        UE_LOG(LogTemp, Warning, TEXT("SegmentationMaterial is missing."));
        return nullptr;
    }

    const float OneOver255 = 1.0f / 255.0f;
    FLinearColor LinearSegmentationColor(
        SegmentationColor.R * OneOver255,
        SegmentationColor.G * OneOver255,
        SegmentationColor.B * OneOver255,
        1.0f);

    UMaterialInstanceDynamic* LocalSegmentationMID = UMaterialInstanceDynamic::Create(SegmentationMaterial, this);
    if (!IsValid(LocalSegmentationMID))
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed to create dynamic material instance."));
        return nullptr;
    }

    LocalSegmentationMID->SetVectorParameterValue("AnnotationColor", LinearSegmentationColor);

    // Handle static mesh
    if (UStaticMeshComponent* StaticMeshComponent = Cast<UStaticMeshComponent>(ParentComponent))
    {
        UStaticMesh* StaticMesh = StaticMeshComponent->GetStaticMesh();
        if (StaticMesh && StaticMesh->RenderData && StaticMesh->RenderData->LODResources.Num() > 0)
        {
            return new FStaticSegmentationSceneProxy(StaticMeshComponent, false, LocalSegmentationMID);
        }
    }

    // Handle skeletal mesh
    if (USkeletalMeshComponent* SkeletalMeshComponent = Cast<USkeletalMeshComponent>(ParentComponent))
    {
        FSkeletalMeshRenderData* SkelMeshRenderData = SkeletalMeshComponent->GetSkeletalMeshRenderData();
        if (SkelMeshRenderData &&
            SkelMeshRenderData->LODRenderData.IsValidIndex(SkeletalMeshComponent->PredictedLODLevel) &&
            SkeletalMeshComponent->MeshObject)
        {
            return new FSkeletalSegmentationSceneProxy(SkeletalMeshComponent, SkelMeshRenderData, LocalSegmentationMID);
        }
    }

    UE_LOG(LogTemp, Warning, TEXT("Unsupported parent component for segmentation."));
    return nullptr;
}



FBoxSphereBounds USegmentationComponent::CalcBounds(const FTransform& LocalToWorld) const
{
    USceneComponent* Parent = this->GetAttachParent();
    if (Parent)
    {
        return Parent->CalcBounds(LocalToWorld);
    }else{
        UE_LOG(LogTemp, Warning, TEXT("++++++++++++++++++++++++++++++++++++ FAILED TO ATTACHED PARENT ++++++++++++++++++++++++++++++++"));

    }

    return FBoxSphereBounds();
}

