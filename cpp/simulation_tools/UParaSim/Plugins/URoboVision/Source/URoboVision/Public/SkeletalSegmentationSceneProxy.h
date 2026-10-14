// Copyright 2019, Institute for Artificial Intelligence - University of Bremen
#pragma once
#include "Runtime/Engine/Classes/Components/SkeletalMeshComponent.h"
#include "Runtime/Engine/Public/Rendering/SkeletalMeshRenderData.h"
#include "Runtime/CoreUObject/Public/UObject/ConstructorHelpers.h"
#include "Runtime/Engine/Classes/Materials/MaterialInstanceDynamic.h"
#include "Runtime/Engine/Classes/Components/SkeletalMeshComponent.h"
#include "Runtime/Launch/Resources/Version.h"
#include "Runtime/Engine/Public/MaterialShared.h"
#include "Runtime/Engine/Classes/Engine/Engine.h"
#include "Runtime/Engine/Public/Rendering/SkeletalMeshRenderData.h"
#if ENGINE_MINOR_VERSION > 23 || ENGINE_MAJOR_VERSION >4
#include "UObject/ConstructorHelpers.h"
#else
#include "ConstructorHelpers.h"
#endif
#include "EngineUtils.h"

class UMaterialInterface;
class USkinnedMeshComponent;
class FSkeletalMeshRenderData;
struct FPrimitiveViewRelevance;
class FSceneView;
class FMeshElementCollector;
class FMaterialRenderProxy;

class  FSkeletalSegmentationSceneProxy : public FSkeletalMeshSceneProxy
{
public:
        FSkeletalSegmentationSceneProxy(const USkinnedMeshComponent* Component, FSkeletalMeshRenderData* InSkeletalMeshRenderData, UMaterialInterface* SegmentationMID);
        virtual ~FSkeletalSegmentationSceneProxy() {}

        virtual FPrimitiveViewRelevance GetViewRelevance(const FSceneView* View) const override;
        virtual void GetDynamicMeshElements(const TArray<const FSceneView*>& Views, const FSceneViewFamily& ViewFamily, uint32 VisibilityMap, FMeshElementCollector& Collector) const override;

private:
        // A new member variable to store the material render proxy.
        const FMaterialRenderProxy* MaterialRenderProxy;
};
