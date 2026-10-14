// Copyright 2019, Institute for Artificial Intelligence - University of Bremen

#include "SkeletalSegmentationSceneProxy.h"

FSkeletalSegmentationSceneProxy::FSkeletalSegmentationSceneProxy(
        const USkinnedMeshComponent* Component,
        FSkeletalMeshRenderData* InSkeletalMeshRenderData,
        UMaterialInterface* SegmentationMID)
        : FSkeletalMeshSceneProxy(Component, InSkeletalMeshRenderData)
{
        bVerifyUsedMaterials = false;
        bCastDynamicShadow = false;

#if (ENGINE_MINOR_VERSION >= 22)
        MaterialRenderProxy = SegmentationMID->GetRenderProxy();
#else
        MaterialRenderProxy = SegmentationMID->GetRenderProxy(false, false);
#endif
}

FPrimitiveViewRelevance FSkeletalSegmentationSceneProxy::GetViewRelevance(const FSceneView* View) const
{
        FPrimitiveViewRelevance ViewRelevance;

        ViewRelevance.bDrawRelevance = View->Family->EngineShowFlags.Materials;
        ViewRelevance.bOpaque = true;
        ViewRelevance.bNormalTranslucency = true;
        ViewRelevance.bRenderInMainPass = true;

        return ViewRelevance;
}

void FSkeletalSegmentationSceneProxy::GetDynamicMeshElements(
        const TArray<const FSceneView*>& Views,
        const FSceneViewFamily& ViewFamily,
        uint32 VisibilityMap,
        FMeshElementCollector& Collector) const
{
        if (!MeshObject || MeshObject->GetSkeletalMeshRenderData().LODRenderData.Num() == 0)
        {
                return;
        }

        const FSkeletalMeshRenderData& RenderData = MeshObject->GetSkeletalMeshRenderData();

        for (int32 ViewIndex = 0; ViewIndex < Views.Num(); ++ViewIndex)
        {
                if (!(VisibilityMap & (1 << ViewIndex)))
                {
                        continue;
                }

                const FSceneView* View = Views[ViewIndex];

                // Loop through LODs and Sections
                for (int32 LODIndex = 0; LODIndex < LODSections.Num(); ++LODIndex)
                {
                        const FSkeletalMeshSceneProxy::FLODSectionElements& LODSection = LODSections[LODIndex];
                        const FSkeletalMeshLODRenderData& LODData = RenderData.LODRenderData[LODIndex];

                        for (int32 SectionIndex = 0; SectionIndex < LODSection.SectionElements.Num(); ++SectionIndex)
                        {
                                const FSkelMeshRenderSection& Section = LODData.RenderSections[SectionIndex];
                                const FSectionElementInfo& SectionInfo = LODSection.SectionElements[SectionIndex];

                                // 🔁 Use UE's internal helper — this handles vertex factory, bone transforms, and more
                                GetDynamicElementsSection(
                                    Views,       // ✅ This is the TArray<const FSceneView*>&
                                    ViewFamily,
                                    VisibilityMap,
                                    LODData,
                                    LODIndex,
                                    SectionIndex,
                                    false,       // bSectionSelected
                                    SectionInfo,
                                    false,       // bInSelectable
                                    Collector
                                );

                        }
                }
        }
}
